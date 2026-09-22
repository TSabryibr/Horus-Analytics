'use client';

import React, { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';

export type SignalFollowUpSummary = {
    configured: boolean;
    total: number;
    pending_count: number;
    ready_count: number;
    sent_count: number;
    failed_count: number;
    suppressed_count: number;
    stale_pending_count: number;
    destination_counts?: Record<string, number>;
    service_tier_counts?: Record<string, number>;
    latest_created_at?: string | null;
};

export type SignalFollowUpRecord = {
    id: number;
    lifecycle_id?: number | null;
    recommendation_id?: number | null;
    run_id?: number | null;
    delivery_id?: number | null;
    portfolio_id?: number | null;
    portfolio_name?: string | null;
    ticker: string;
    side: string;
    lane: string;
    source_module?: string | null;
    operating_mode?: string;
    channel?: string;
    service_tier?: string;
    destination_type?: string;
    destination_id?: string | null;
    destination_name?: string | null;
    destination_chat_id?: string | null;
    trigger_state: string;
    message_type: string;
    queue_state: string;
    draft_message?: string | null;
    telegram_message_id?: string | null;
    retry_count: number;
    last_attempted_at?: string | null;
    ready_at?: string | null;
    sent_at?: string | null;
    suppressed_at?: string | null;
    suppression_reason?: string | null;
    last_error?: string | null;
    details?: Record<string, unknown>;
    created_at?: string | null;
    updated_at?: string | null;
};

export type SignalFollowUpContextValue = {
    followUpSummary: SignalFollowUpSummary | null;
    followUpRecords: SignalFollowUpRecord[];
    followUpLoading: boolean;
    followUpError: string | null;
    refreshFollowUps: () => Promise<void>;
    processFollowUps: (limit?: number) => Promise<boolean>;
    actOnFollowUp: (followUpId: number, action: 'SEND_NOW' | 'RETRY' | 'SUPPRESS' | 'RESEND', reason?: string) => Promise<boolean>;
};

const SignalFollowUpContext = createContext<SignalFollowUpContextValue | undefined>(undefined);

export function normalizeFollowUpSummary(payload: Partial<SignalFollowUpSummary> | null | undefined): SignalFollowUpSummary {
    return {
        configured: Boolean(payload?.configured),
        total: Number(payload?.total ?? 0),
        pending_count: Number(payload?.pending_count ?? 0),
        ready_count: Number(payload?.ready_count ?? 0),
        sent_count: Number(payload?.sent_count ?? 0),
        failed_count: Number(payload?.failed_count ?? 0),
        suppressed_count: Number(payload?.suppressed_count ?? 0),
        stale_pending_count: Number(payload?.stale_pending_count ?? 0),
        latest_created_at: payload?.latest_created_at ?? null,
    };
}

export function SignalFollowUpProvider({ 
    children, 
    enabled = true 
}: { 
    children: ReactNode; 
    enabled?: boolean;
}) {
    const [followUpSummary, setFollowUpSummary] = useState<SignalFollowUpSummary | null>(null);
    const [followUpRecords, setFollowUpRecords] = useState<SignalFollowUpRecord[]>([]);
    const [followUpLoading, setFollowUpLoading] = useState<boolean>(enabled);
    const [followUpError, setFollowUpError] = useState<string | null>(null);

    const refreshFollowUps = useCallback(async () => {
        if (!enabled) {
            setFollowUpLoading(false);
            setFollowUpError(null);
            setFollowUpSummary(null);
            setFollowUpRecords([]);
            return;
        }

        setFollowUpLoading(true);
        try {
            const [summaryResponse, listResponse] = await Promise.all([
                apiFetch('/api/v1/signals/followups/summary', { cache: 'no-store' }),
                apiFetch('/api/v1/signals/followups?limit=24', { cache: 'no-store' }),
            ]);
            const summaryPayload = await readJsonSafe<SignalFollowUpSummary>(summaryResponse);
            const listPayload = await readJsonSafe<{ summary?: SignalFollowUpSummary; followups?: SignalFollowUpRecord[] }>(listResponse);
            if (!summaryResponse.ok) {
                throw new Error(pickApiMessage(summaryPayload, 'Failed to load follow-up summary.'));
            }
            if (!listResponse.ok) {
                throw new Error(pickApiMessage(listPayload, 'Failed to load follow-up queue.'));
            }
            setFollowUpSummary(normalizeFollowUpSummary(summaryPayload ?? listPayload?.summary));
            setFollowUpRecords(Array.isArray(listPayload?.followups) ? listPayload.followups : []);
            setFollowUpError(null);
        } catch (error) {
            setFollowUpError(error instanceof Error ? error.message : 'Failed to load follow-up queue.');
        } finally {
            setFollowUpLoading(false);
        }
    }, [enabled]);

    useEffect(() => {
        void refreshFollowUps();
    }, [refreshFollowUps]);

    const processFollowUps = useCallback(async (limit = 20) => {
        if (!enabled) return false;

        try {
            const response = await apiFetch('/api/v1/signals/followups/process', {
                method: 'POST',
                body: JSON.stringify({ limit }),
            });
            const payload = await readJsonSafe<{ summary_snapshot?: SignalFollowUpSummary }>(response);
            if (!response.ok) {
                throw new Error(pickApiMessage(payload, 'Failed to process follow-up queue.'));
            }
            if (payload?.summary_snapshot) {
                setFollowUpSummary(normalizeFollowUpSummary(payload.summary_snapshot));
            }
            setFollowUpError(null);
            await refreshFollowUps();
            return true;
        } catch (error) {
            setFollowUpError(error instanceof Error ? error.message : 'Failed to process follow-up queue.');
            return false;
        }
    }, [enabled, refreshFollowUps]);

    const actOnFollowUp = useCallback(async (
        followUpId: number,
        action: 'SEND_NOW' | 'RETRY' | 'SUPPRESS' | 'RESEND',
        reason?: string,
    ) => {
        if (!enabled) return false;

        try {
            const response = await apiFetch(`/api/v1/signals/followups/${followUpId}/action`, {
                method: 'POST',
                body: JSON.stringify({
                    action,
                    reason,
                }),
            });
            const payload = await readJsonSafe<{ followup?: SignalFollowUpRecord; summary?: SignalFollowUpSummary }>(response);
            if (!response.ok) {
                throw new Error(pickApiMessage(payload, 'Failed to update follow-up queue item.'));
            }
            if (payload?.followup) {
                setFollowUpRecords((current) => {
                    const next = current.filter((item) => item.id !== payload.followup?.id);
                    return [payload.followup as SignalFollowUpRecord, ...next];
                });
            }
            if (payload?.summary) {
                setFollowUpSummary(normalizeFollowUpSummary(payload.summary));
            }
            setFollowUpError(null);
            await refreshFollowUps();
            return true;
        } catch (error) {
            setFollowUpError(error instanceof Error ? error.message : 'Failed to update follow-up queue item.');
            return false;
        }
    }, [enabled, refreshFollowUps]);

    const value = useMemo(() => ({
        followUpSummary,
        followUpRecords,
        followUpLoading,
        followUpError,
        refreshFollowUps,
        processFollowUps,
        actOnFollowUp,
    }), [
        followUpSummary,
        followUpRecords,
        followUpLoading,
        followUpError,
        refreshFollowUps,
        processFollowUps,
        actOnFollowUp,
    ]);

    return (
        <SignalFollowUpContext.Provider value={value}>
            {children}
        </SignalFollowUpContext.Provider>
    );
}

export function useSignalFollowUp() {
    const context = useContext(SignalFollowUpContext);
    if (context === undefined) {
        throw new Error('useSignalFollowUp must be used within a SignalFollowUpProvider');
    }
    return context;
}
