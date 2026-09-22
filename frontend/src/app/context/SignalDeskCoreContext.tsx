'use client';

import React, { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';
import { useSignalLifecycle } from './SignalLifecycleContext';
import { useSignalFollowUp } from './SignalFollowUpContext';

export type SignalDeskLaneCandidate = {
    id: number;
    run_id: number | null;
    ticker: string;
    side: string;
    entry_price: number;
    stop_loss: number;
    target_price: number;
    target_price_2: number;
    score: number;
    confidence: number;
    horizon_days: number;
    scan_type: string | null;
    lane: 'intraday' | 'swing' | 'position';
    source_module?: string | null;
    strategy_profile_id?: number | null;
    strategy_profile_name?: string | null;
    strategy_profile_source_type?: string | null;
    strategy_profile_market?: string | null;
    strategy_profile_timeframe?: string | null;
    rationale?: Record<string, unknown> | null;
    created_at?: string | null;
};

export type SignalDeskLane = {
    key: 'intraday' | 'swing' | 'position';
    label: string;
    count: number;
    candidates: SignalDeskLaneCandidate[];
};

export type SignalDeskAutopilot = {
    status?: 'IDLE' | 'READY' | 'RUNNING' | 'BLOCKED' | 'COMPLETED' | 'FAILED' | string;
    last_run_id?: number | null;
    last_attempted_at?: string | null;
    last_published_at?: string | null;
    last_error?: string | null;
    summary?: Record<string, unknown>;
};

export type SignalDesk = {
    name?: string;
    operating_mode: 'MANUAL' | 'AI_ASSIST' | 'AUTOPILOT';
    autopilot_armed: boolean;
    publish_policy?: Record<string, unknown>;
    autopilot?: SignalDeskAutopilot;
    lane_preferences?: Record<string, unknown>;
    lanes: {
        intraday: SignalDeskLane;
        swing: SignalDeskLane;
        position: SignalDeskLane;
    };
    active_run?: Record<string, unknown> | null;
    latest_delivery?: Record<string, unknown> | null;
    latest_failed_delivery?: Record<string, unknown> | null;
    failed_delivery_count?: number;
    updated_at?: string | null;
};

export type SignalDeskCoreContextValue = {
    desk: SignalDesk | null;
    deskLoading: boolean;
    deskError: string | null;
    refreshDesk: () => Promise<void>;
    setOperatingMode: (operatingMode: SignalDesk['operating_mode'], autopilotArmed?: boolean) => Promise<boolean>;
    promoteCandidate: (candidate: Record<string, unknown>) => Promise<boolean>;
    runAutopilot: () => Promise<boolean>;
};

const SignalDeskCoreContext = createContext<SignalDeskCoreContextValue | undefined>(undefined);

export function emptyLane(key: SignalDeskLane['key'], label: string): SignalDeskLane {
    return {
        key,
        label,
        count: 0,
        candidates: [],
    };
}

export function normalizeDesk(payload: Partial<SignalDesk> | null | undefined): SignalDesk {
    return {
        operating_mode: (payload?.operating_mode ?? 'MANUAL') as SignalDesk['operating_mode'],
        autopilot_armed: Boolean(payload?.autopilot_armed),
        name: payload?.name,
        publish_policy: payload?.publish_policy ?? {},
        autopilot: payload?.autopilot ?? {},
        lane_preferences: payload?.lane_preferences ?? {},
        lanes: {
            intraday: payload?.lanes?.intraday ?? emptyLane('intraday', 'Intraday'),
            swing: payload?.lanes?.swing ?? emptyLane('swing', 'Swing'),
            position: payload?.lanes?.position ?? emptyLane('position', 'Position'),
        },
        active_run: payload?.active_run ?? null,
        latest_delivery: payload?.latest_delivery ?? null,
        latest_failed_delivery: payload?.latest_failed_delivery ?? null,
        failed_delivery_count: Number(payload?.failed_delivery_count ?? 0),
        updated_at: payload?.updated_at ?? null,
    };
}

export function SignalDeskCoreProvider({ 
    children, 
    enabled = true
}: { 
    children: ReactNode; 
    enabled?: boolean;
}) {
    const [desk, setDesk] = useState<SignalDesk | null>(null);
    const [deskLoading, setDeskLoading] = useState<boolean>(enabled);
    const [deskError, setDeskError] = useState<string | null>(null);
    
    // We optionally fetch these if they exist, but to avoid circular deps we just use them if they are in the tree
    // Actually, we enforce SignalDeskCoreProvider is nested inside Lifecycle and FollowUp providers.
    const { refreshLifecycle } = useSignalLifecycle();
    const { refreshFollowUps } = useSignalFollowUp();

    const refreshDesk = useCallback(async () => {
        if (!enabled) {
            setDeskLoading(false);
            setDeskError(null);
            setDesk(null);
            return;
        }

        setDeskLoading(true);
        try {
            const response = await apiFetch('/api/v1/signals/desk', { cache: 'no-store' });
            const payload = await readJsonSafe<{ desk?: SignalDesk }>(response);
            if (!response.ok) {
                throw new Error(pickApiMessage(payload, 'Failed to load signal desk.'));
            }
            setDesk(normalizeDesk(payload?.desk));
            setDeskError(null);
        } catch (error) {
            setDeskError(error instanceof Error ? error.message : 'Failed to load signal desk.');
        } finally {
            setDeskLoading(false);
        }
    }, [enabled]);

    useEffect(() => {
        void refreshDesk();
    }, [refreshDesk]);

    const setOperatingMode = useCallback(async (
        operatingMode: SignalDesk['operating_mode'],
        autopilotArmed?: boolean,
    ) => {
        if (!enabled) return false;

        try {
            const response = await apiFetch('/api/v1/signals/desk/mode', {
                method: 'POST',
                body: JSON.stringify({
                    operating_mode: operatingMode,
                    autopilot_armed: autopilotArmed,
                }),
            });
            const payload = await readJsonSafe<{ desk?: SignalDesk }>(response);
            if (!response.ok) {
                throw new Error(pickApiMessage(payload, 'Failed to update signal desk mode.'));
            }
            setDesk(normalizeDesk(payload?.desk));
            setDeskError(null);
            await refreshLifecycle();
            await refreshFollowUps();
            return true;
        } catch (error) {
            setDeskError(error instanceof Error ? error.message : 'Failed to update signal desk mode.');
            return false;
        }
    }, [enabled, refreshLifecycle, refreshFollowUps]);

    const promoteCandidate = useCallback(async (candidate: Record<string, unknown>) => {
        if (!enabled) return false;

        try {
            const response = await apiFetch('/api/v1/signals/desk/promote', {
                method: 'POST',
                body: JSON.stringify(candidate),
            });
            const payload = await readJsonSafe<{ desk?: SignalDesk }>(response);
            if (!response.ok) {
                throw new Error(pickApiMessage(payload, 'Failed to promote signal candidate.'));
            }
            setDesk(normalizeDesk(payload?.desk));
            setDeskError(null);
            await refreshLifecycle();
            await refreshFollowUps();
            return true;
        } catch (error) {
            setDeskError(error instanceof Error ? error.message : 'Failed to promote signal candidate.');
            return false;
        }
    }, [enabled, refreshLifecycle, refreshFollowUps]);

    const runAutopilot = useCallback(async () => {
        if (!enabled) return false;

        try {
            const response = await apiFetch('/api/v1/signals/desk/autopilot', {
                method: 'POST',
                body: JSON.stringify({}),
            });
            const payload = await readJsonSafe<{ desk?: SignalDesk; status?: string }>(response);
            if (!response.ok) {
                throw new Error(pickApiMessage(payload, 'Failed to trigger signal desk autopilot.'));
            }
            if (payload?.desk) {
                setDesk(normalizeDesk(payload.desk));
            } else {
                await refreshDesk();
            }
            setDeskError(null);
            await refreshLifecycle();
            await refreshFollowUps();
            return payload?.status === 'completed';
        } catch (error) {
            setDeskError(error instanceof Error ? error.message : 'Failed to trigger signal desk autopilot.');
            return false;
        }
    }, [enabled, refreshDesk, refreshLifecycle, refreshFollowUps]);

    const value = useMemo(() => ({
        desk,
        deskLoading,
        deskError,
        refreshDesk,
        setOperatingMode,
        promoteCandidate,
        runAutopilot,
    }), [
        desk,
        deskLoading,
        deskError,
        refreshDesk,
        setOperatingMode,
        promoteCandidate,
        runAutopilot,
    ]);

    return (
        <SignalDeskCoreContext.Provider value={value}>
            {children}
        </SignalDeskCoreContext.Provider>
    );
}

export function useSignalDeskCore() {
    const context = useContext(SignalDeskCoreContext);
    if (context === undefined) {
        throw new Error('useSignalDeskCore must be used within a SignalDeskCoreProvider');
    }
    return context;
}
