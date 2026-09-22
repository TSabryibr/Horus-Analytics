import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { resolveRuntimeSurfaceState } from '@/app/lib/runtimeStatus';
import { getBaseUrl, isIgnorableNetworkError } from '@/lib/api';

import {
    resolveDriftValue,
    resolveHistoryAgeHours,
    resolveHistorySymbolCount,
    resolveSourceEngine,
} from '../lib/statusTransforms';
import { createBootstrapRequest } from '../lib/bootstrapRequest';

export interface StatusPayload {
    [key: string]: any;
}

interface UseStatusRuntimeOptions {
    isSyncing?: boolean;
}

const bootstrapStatusRequest = createBootstrapRequest<StatusPayload>();
const FULL_STATUS_ENRICHMENT_TIMEOUT_MS = 1500;
const RUNTIME_UNIVERSE_TIMEOUT_MS = 1500;

export function resetStatusRuntimeBootstrapCache() {
    bootstrapStatusRequest.reset();
}

async function requestJsonPayload(apiBase: string, path: string, timeoutMs = 8000): Promise<StatusPayload> {
    const controller = new AbortController();
    let timeout: ReturnType<typeof setTimeout> | null = null;
    const timeoutPromise = new Promise<never>((_, reject) => {
        timeout = setTimeout(() => {
            controller.abort();
            reject(new Error(`Timed out fetching ${path}`));
        }, timeoutMs);
    });

    try {
        const res = await Promise.race<Response>([
            fetch(`${apiBase}${path}`, {
                cache: 'no-store',
                signal: controller.signal,
            }),
            timeoutPromise,
        ]);
        if (!res.ok) {
            throw new Error(`Failed to fetch ${path}`);
        }

        return await res.json();
    } finally {
        if (timeout) {
            clearTimeout(timeout);
        }
    }
}

async function requestFullStatusPayload(apiBase: string, timeoutMs = 8000): Promise<StatusPayload> {
    return requestJsonPayload(apiBase, '/api/v1/system/full-status', timeoutMs);
}

async function requestFallbackStatusPayload(apiBase: string): Promise<StatusPayload> {
    const [bootStatus, dataStatus] = await Promise.all([
        requestJsonPayload(apiBase, '/api/v1/system/boot-status'),
        requestJsonPayload(apiBase, '/api/v1/data/status').catch(() => null),
    ]);

    return {
        ...bootStatus,
        alerts: bootStatus.alerts ?? {
            telegram: bootStatus.telegram,
        },
        data_status: dataStatus ?? bootStatus.data_status ?? null,
    };
}

function mergeStatusPayload(fallbackPayload: StatusPayload, fullPayload: StatusPayload): StatusPayload {
    return {
        ...fallbackPayload,
        ...fullPayload,
        alerts: fullPayload.alerts ?? fallbackPayload.alerts,
        data_status: fullPayload.data_status ?? fallbackPayload.data_status,
        freshness: fullPayload.freshness ?? fallbackPayload.freshness,
        scheduler: fullPayload.scheduler ?? fallbackPayload.scheduler,
    };
}

async function requestStatusPayload(apiBase: string): Promise<StatusPayload> {
    let fallbackPayload: StatusPayload;

    try {
        fallbackPayload = await requestFallbackStatusPayload(apiBase);
    } catch (fallbackError) {
        try {
            return await requestFullStatusPayload(apiBase);
        } catch {
            throw fallbackError;
        }
    }

    try {
        const fullPayload = await requestFullStatusPayload(apiBase, FULL_STATUS_ENRICHMENT_TIMEOUT_MS);
        return mergeStatusPayload(fallbackPayload, fullPayload);
    } catch {
        return fallbackPayload;
    }
}

async function requestRuntimeUniversePayload(apiBase: string): Promise<Record<string, unknown> | null> {
    try {
        return await requestJsonPayload(apiBase, '/api/v1/data/runtime-universe', RUNTIME_UNIVERSE_TIMEOUT_MS);
    } catch {
        return null;
    }
}

async function loadStatusSurface(apiBase: string): Promise<StatusPayload> {
    const status = await requestStatusPayload(apiBase);
    const runtimeUniverse = await requestRuntimeUniversePayload(apiBase);

    return {
        ...status,
        runtime_universe: runtimeUniverse,
    };
}

function preserveRichTelemetry(prev: StatusPayload | null, next: StatusPayload): StatusPayload {
    if (!prev) return next;
    return {
        ...prev,
        ...next,
        alerts: next.alerts ?? prev.alerts,
        data_status: next.data_status ?? prev.data_status,
        freshness: next.freshness ?? prev.freshness,
        scheduler: (next.scheduler?.jobs && next.scheduler.jobs.length > 0)
            ? next.scheduler
            : (prev.scheduler?.jobs?.length ? prev.scheduler : (next.scheduler ?? prev.scheduler)),
        database_backup: next.database_backup ?? prev.database_backup,
        delivery_sla: next.delivery_sla ?? prev.delivery_sla,
        metrics: next.metrics ?? prev.metrics,
        runtime_universe: next.runtime_universe ?? prev.runtime_universe,
    };
}

export function useStatusRuntime({ isSyncing = false }: UseStatusRuntimeOptions = {}) {
    const [status, setStatus] = useState<StatusPayload | null>(null);
    const [loading, setLoading] = useState(true);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
    const hasBootstrappedRef = useRef(false);

    const apiBase = getBaseUrl();

    const fetchStatus = useCallback(async () => {
        setLoading(true);

        try {
            const data = await loadStatusSurface(apiBase);
            setStatus((prev) => preserveRichTelemetry(prev, data));
            setLastRefresh(new Date());
        } catch (err) {
            if (isIgnorableNetworkError(err)) {
                return;
            }
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [apiBase]);

    useEffect(() => {
        let cancelled = false;

        if (hasBootstrappedRef.current) {
            return undefined;
        }
        hasBootstrappedRef.current = true;

        setLoading(true);
        void bootstrapStatusRequest(apiBase, () => loadStatusSurface(apiBase))
            .then((data) => {
                if (cancelled) {
                    return;
                }
                setStatus((prev) => preserveRichTelemetry(prev, data));
                setLastRefresh(new Date());
            })
            .catch((err) => {
                if (cancelled) {
                    return;
                }
                if (isIgnorableNetworkError(err)) {
                    return;
                }
                console.error(err);
            })
            .finally(() => {
                if (!cancelled) {
                    setLoading(false);
                }
            });

        return () => {
            cancelled = true;
        };
    }, [apiBase]);

    const intradayProvider = String(status?.data_status?.source?.intraday_provider || '').toUpperCase();
    const intradayAgeMins = status?.data_status?.intraday?.age_mins;
    const historyLastUpdated = status?.data_status?.history?.last_updated;

    const runtimeState = useMemo(() => resolveRuntimeSurfaceState({
        isSyncing,
        backendKnown: Boolean(status?.data_status),
        provisioningStatus: status?.provisioning_status,
        pipelineState: status?.pipeline_state,
        marketOpen: status?.freshness?.market_open,
        historyStatus: status?.data_status?.history?.status,
        intradayStatus: status?.data_status?.intraday?.status,
        historyOk: status?.data_status?.history?.ok,
        intradayOk: status?.data_status?.intraday?.ok,
    }), [isSyncing, status]);

    const sourceEngine = useMemo(() => resolveSourceEngine(intradayProvider), [intradayProvider]);
    const driftValue = useMemo(() => resolveDriftValue(intradayAgeMins), [intradayAgeMins]);
    const historySymbolCount = useMemo(
        () => resolveHistorySymbolCount(status?.data_status?.history),
        [status?.data_status?.history]
    );
    const historyAgeHours = useMemo(
        () => resolveHistoryAgeHours(historyLastUpdated, lastRefresh),
        [historyLastUpdated, lastRefresh]
    );

    return {
        status,
        setStatus,
        loading,
        lastRefresh,
        apiBase,
        fetchStatus,
        runtimeState,
        sourceEngine,
        driftValue,
        historySymbolCount,
        historyAgeHours,
    };
}
