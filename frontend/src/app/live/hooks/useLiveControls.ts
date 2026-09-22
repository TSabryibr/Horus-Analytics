'use client';

import { useMemo } from 'react';
import { useLiveContext, type LiveStatusResponse } from '../../context/LiveContext';

export type { LiveStatusResponse };

interface UseLiveControlsArgs {
    onSetError: (message: string | null) => void;
    onEnableAutoRefresh: () => void;
    onStartSuccess: () => void | Promise<void>;
}

export function useLiveControls({
    onSetError,
    onEnableAutoRefresh,
    onStartSuccess,
}: UseLiveControlsArgs) {
    const {
        liveStatus,
        liveRunning,
        marketOpen,
        handleLiveFeedAction: handleActionInContext,
    } = useLiveContext();

    const handleLiveFeedAction = async (action: 'start' | 'stop') => {
        try {
            const response = await handleActionInContext(action);
            if (action === 'start') {
                if (response?.status === 'market_closed') {
                    onSetError(response.message || 'Market is closed.');
                } else {
                    onSetError(null);
                    onEnableAutoRefresh();
                    await onStartSuccess();
                }
            }
        } catch (err) {
            console.error('Feed action failed:', err);
            onSetError('Failed to execute feed action');
        }
    };

    const lastUpdate = liveStatus?.last_update;
    const liveLastUpdate = useMemo(() => {
        if (!lastUpdate) return 'N/A';
        const parsed = new Date(lastUpdate);
        if (Number.isNaN(parsed.getTime())) return String(lastUpdate);
        return parsed.toLocaleTimeString();
    }, [lastUpdate]);

    return {
        liveStatus,
        liveRunning,
        marketOpen,
        liveLastUpdate,
        fetchLiveStatus: () => {}, // Handled by global context polling
        handleLiveFeedAction,
    };
}
