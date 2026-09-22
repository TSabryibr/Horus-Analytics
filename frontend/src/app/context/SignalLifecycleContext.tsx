'use client';

import React, { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';

export type PublishedSignalLifecycleSummary = {
    configured: boolean;
    total: number;
    active_count: number;
    ambiguous_count: number;
    stale_active_count?: number;
    monitor_status?: string;
    counts_by_state?: Record<string, number>;
    counts_by_lane?: Record<string, number>;
    latest_published_at?: string | null;
};

export type PublishedSignalLifecycleEvent = {
    id: number;
    lifecycle_id: number;
    event_type: string;
    from_state?: string | null;
    to_state?: string | null;
    event_source?: string;
    actor_type?: string;
    actor_id?: string | null;
    event_time?: string | null;
    price_context?: Record<string, unknown>;
    notes?: string | null;
};

export type PublishedSignalLifecycleRecord = {
    id: number;
    recommendation_id?: number | null;
    run_id?: number | null;
    delivery_id?: number | null;
    portfolio_id?: number | null;
    portfolio_name?: string | null;
    ticker: string;
    side: string;
    lane: 'intraday' | 'swing' | 'position' | string;
    source_module?: string | null;
    operating_mode?: string;
    channel?: string;
    published_message_id?: string | null;
    state: string;
    resolution_source?: string;
    published_at?: string | null;
    expires_at?: string | null;
    opened_at?: string | null;
    tp1_hit_at?: string | null;
    closed_at?: string | null;
    entry_price_planned?: number | null;
    entry_price_filled?: number | null;
    stop_loss_initial?: number | null;
    stop_loss_active?: number | null;
    target_price_1?: number | null;
    target_price_2?: number | null;
    close_price?: number | null;
    close_reason?: string | null;
    override_notes?: string | null;
    last_market_event_at?: string | null;
    details?: Record<string, unknown>;
    updated_at?: string | null;
    events?: PublishedSignalLifecycleEvent[];
};

export type SignalLifecycleContextValue = {
    lifecycleSummary: PublishedSignalLifecycleSummary | null;
    lifecycleRecords: PublishedSignalLifecycleRecord[];
    lifecycleLoading: boolean;
    lifecycleError: string | null;
    refreshLifecycle: () => Promise<void>;
    overrideLifecycle: (lifecycleId: number, payload: Record<string, unknown>) => Promise<boolean>;
};

const SignalLifecycleContext = createContext<SignalLifecycleContextValue | undefined>(undefined);

export function normalizeLifecycleSummary(payload: Partial<PublishedSignalLifecycleSummary> | null | undefined): PublishedSignalLifecycleSummary {
    return {
        configured: Boolean(payload?.configured),
        total: Number(payload?.total ?? 0),
        active_count: Number(payload?.active_count ?? 0),
        ambiguous_count: Number(payload?.ambiguous_count ?? 0),
        stale_active_count: Number(payload?.stale_active_count ?? 0),
        monitor_status: payload?.monitor_status ?? 'READY',
        counts_by_state: payload?.counts_by_state ?? {},
        counts_by_lane: payload?.counts_by_lane ?? {},
        latest_published_at: payload?.latest_published_at ?? null,
    };
}

export function SignalLifecycleProvider({ 
    children, 
    enabled = true,
    onCrossContextRefresh
}: { 
    children: ReactNode; 
    enabled?: boolean;
    onCrossContextRefresh?: () => Promise<void>;
}) {
    const [lifecycleSummary, setLifecycleSummary] = useState<PublishedSignalLifecycleSummary | null>(null);
    const [lifecycleRecords, setLifecycleRecords] = useState<PublishedSignalLifecycleRecord[]>([]);
    const [lifecycleLoading, setLifecycleLoading] = useState<boolean>(enabled);
    const [lifecycleError, setLifecycleError] = useState<string | null>(null);

    const refreshLifecycle = useCallback(async () => {
        if (!enabled) {
            setLifecycleLoading(false);
            setLifecycleError(null);
            setLifecycleSummary(null);
            setLifecycleRecords([]);
            return;
        }

        setLifecycleLoading(true);
        try {
            const [summaryResponse, listResponse] = await Promise.all([
                apiFetch('/api/v1/signals/lifecycle/summary', { cache: 'no-store' }),
                apiFetch('/api/v1/signals/lifecycle?limit=24', { cache: 'no-store' }),
            ]);
            const summaryPayload = await readJsonSafe<PublishedSignalLifecycleSummary>(summaryResponse);
            const listPayload = await readJsonSafe<{ summary?: PublishedSignalLifecycleSummary; lifecycles?: PublishedSignalLifecycleRecord[] }>(listResponse);
            if (!summaryResponse.ok) {
                throw new Error(pickApiMessage(summaryPayload, 'Failed to load lifecycle summary.'));
            }
            if (!listResponse.ok) {
                throw new Error(pickApiMessage(listPayload, 'Failed to load lifecycle ledger.'));
            }
            setLifecycleSummary(normalizeLifecycleSummary(summaryPayload ?? listPayload?.summary));
            setLifecycleRecords(Array.isArray(listPayload?.lifecycles) ? listPayload.lifecycles : []);
            setLifecycleError(null);
        } catch (error) {
            setLifecycleError(error instanceof Error ? error.message : 'Failed to load lifecycle ledger.');
        } finally {
            setLifecycleLoading(false);
        }
    }, [enabled]);

    useEffect(() => {
        void refreshLifecycle();
    }, [refreshLifecycle]);

    const overrideLifecycle = useCallback(async (lifecycleId: number, payload: Record<string, unknown>) => {
        if (!enabled) return false;

        try {
            const response = await apiFetch(`/api/v1/signals/lifecycle/${lifecycleId}/override`, {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            const body = await readJsonSafe<{ lifecycle?: PublishedSignalLifecycleRecord }>(response);
            if (!response.ok) {
                throw new Error(pickApiMessage(body, 'Failed to override lifecycle.'));
            }
            if (body?.lifecycle) {
                setLifecycleRecords((current) => {
                    const next = current.filter((item) => item.id !== body.lifecycle?.id);
                    return [body.lifecycle as PublishedSignalLifecycleRecord, ...next];
                });
            }
            setLifecycleError(null);
            await refreshLifecycle();
            if (onCrossContextRefresh) await onCrossContextRefresh();
            return true;
        } catch (error) {
            setLifecycleError(error instanceof Error ? error.message : 'Failed to override lifecycle.');
            return false;
        }
    }, [enabled, refreshLifecycle, onCrossContextRefresh]);

    const value = useMemo(() => ({
        lifecycleSummary,
        lifecycleRecords,
        lifecycleLoading,
        lifecycleError,
        refreshLifecycle,
        overrideLifecycle,
    }), [
        lifecycleSummary,
        lifecycleRecords,
        lifecycleLoading,
        lifecycleError,
        refreshLifecycle,
        overrideLifecycle,
    ]);

    return (
        <SignalLifecycleContext.Provider value={value}>
            {children}
        </SignalLifecycleContext.Provider>
    );
}

export function useSignalLifecycle() {
    const context = useContext(SignalLifecycleContext);
    if (context === undefined) {
        throw new Error('useSignalLifecycle must be used within a SignalLifecycleProvider');
    }
    return context;
}
