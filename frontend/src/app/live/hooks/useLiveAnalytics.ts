'use client';

import { useCallback, useEffect, useState } from 'react';

import { getApiBase, isIgnorableNetworkError } from '@/lib/api';

const API_BASE = getApiBase();

export interface AnalyticsItem {
    Ticker: string;
    Status?: string;
    Signal_Score?: number;
    Price?: number;
    Risk_Reward_Ratio?: number;
    Resistance_20D?: number;
    Key_Resistance_1?: number;
}

interface UseLiveAnalyticsOptions {
    pollDelayMs?: number;
}

interface AnalyticsStatusResponse {
    status?: string;
    scan_id?: string | null;
    rows?: number;
    last_updated?: string | null;
    error?: string | null;
}

const toAnalyticsArray = (payload: unknown): AnalyticsItem[] => {
    if (Array.isArray(payload)) {
        return payload as AnalyticsItem[];
    }
    if (payload && typeof payload === 'object' && Array.isArray((payload as { data?: unknown }).data)) {
        return (payload as { data: AnalyticsItem[] }).data;
    }
    if (payload && typeof payload === 'object' && Array.isArray((payload as { rows?: unknown }).rows)) {
        return (payload as { rows: AnalyticsItem[] }).rows;
    }
    if (payload && typeof payload === 'object' && Array.isArray((payload as { results?: unknown }).results)) {
        return (payload as { results: AnalyticsItem[] }).results;
    }
    return [];
};

const waitForPollDelay = (delayMs: number, signal?: AbortSignal): Promise<boolean> => {
    if (delayMs <= 0) {
        return Promise.resolve(!(signal?.aborted));
    }

    return new Promise((resolve) => {
        const timer = window.setTimeout(() => {
            cleanup();
            resolve(true);
        }, delayMs);

        const handleAbort = () => {
            window.clearTimeout(timer);
            cleanup();
            resolve(false);
        };

        const cleanup = () => {
            signal?.removeEventListener('abort', handleAbort);
        };

        if (signal) {
            signal.addEventListener('abort', handleAbort, { once: true });
        }
    });
};

export function useLiveAnalytics(options: UseLiveAnalyticsOptions = {}) {
    const [analyticsData, setAnalyticsData] = useState<AnalyticsItem[]>([]);
    const [analyticsLoading, setAnalyticsLoading] = useState(false);
    const pollDelayMs = options.pollDelayMs ?? 2500;

    const safeFetch = useCallback(async <T,>(path: string, init?: RequestInit, signal?: AbortSignal): Promise<T | null> => {
        if (signal?.aborted) {
            return null;
        }

        try {
            const res = await fetch(`${API_BASE}${path}`, {
                cache: 'no-store',
                ...init,
                signal: init?.signal ?? signal,
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json() as T;
        } catch (err) {
            if (signal?.aborted) {
                return null;
            }
            if (!isIgnorableNetworkError(err)) {
                console.warn(`Fetch failed for ${path}:`, err);
            }
            return null;
        }
    }, []);

    const fetchAnalytics = useCallback(async (signal?: AbortSignal) => {
        if (signal?.aborted) {
            return;
        }

        setAnalyticsLoading(true);
        try {
            let nextData = toAnalyticsArray(await safeFetch<unknown>('/analytics', undefined, signal));
            if (signal?.aborted) {
                return;
            }

            if (nextData.length === 0) {
                const refresh = await safeFetch<{ scan_id?: string; status?: string }>('/analytics/refresh', { method: 'POST' }, signal);
                const expectedScanId = refresh?.scan_id ?? null;
                for (let i = 0; i < 30; i += 1) {
                    const shouldContinue = await waitForPollDelay(pollDelayMs, signal);
                    if (!shouldContinue || signal?.aborted) {
                        return;
                    }

                    const scanStatus = await safeFetch<AnalyticsStatusResponse>('/analytics/status', undefined, signal);
                    if (signal?.aborted) {
                        return;
                    }

                    if (scanStatus?.status === 'ERROR') {
                        break;
                    }
                    const sameScan = !expectedScanId || !scanStatus?.scan_id || scanStatus.scan_id === expectedScanId;
                    if (sameScan && scanStatus?.status !== 'RUNNING') {
                        nextData = toAnalyticsArray(await safeFetch<unknown>('/analytics', undefined, signal));
                        if (signal?.aborted) {
                            return;
                        }
                        if (nextData.length > 0) {
                            break;
                        }
                    }
                }
            }

            if (signal?.aborted) {
                return;
            }

            setAnalyticsData(nextData);
        } finally {
            if (!signal?.aborted) {
                setAnalyticsLoading(false);
            }
        }
    }, [pollDelayMs, safeFetch]);

    useEffect(() => {
        const controller = new AbortController();
        void fetchAnalytics(controller.signal);

        return () => {
            controller.abort();
        };
    }, [fetchAnalytics]);

    return {
        analyticsData,
        analyticsLoading,
        fetchAnalytics,
    };
}
