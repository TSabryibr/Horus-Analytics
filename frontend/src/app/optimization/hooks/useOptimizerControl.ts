'use client';

import { useState } from 'react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';
import { usePolling } from '@/hooks/usePolling';

import type { OptimizationMode } from '../components/OptimizationShell';

type UiMessage = {
    type: 'error' | 'success';
    text: string;
} | null;

type UseOptimizerControlOptions = {
    mode: OptimizationMode;
    showMessage: (message: UiMessage) => void;
};

export function useOptimizerControl({ mode, showMessage }: UseOptimizerControlOptions) {
    const [optStatus, setOptStatus] = useState<any>({ status: 'IDLE' });
    const [optIndex, setOptIndex] = useState('ALL');
    const [optLoading, setOptLoading] = useState(false);

    const optimizerStatus = String(optStatus?.status || 'IDLE').toUpperCase();
    const optimizerIsActive =
        optimizerStatus === 'RUNNING' ||
        optimizerStatus === 'PREPARING' ||
        optimizerStatus.startsWith('VALIDATING');
    const optimizerHasResults = Array.isArray(optStatus?.result) && optStatus.result.length > 0;

    usePolling(
        async () => {
            try {
                const res = await apiFetch('/api/v1/strategy/status');
                const data = await res.json();
                setOptStatus(data);
                const status = String(data?.status || '').toUpperCase();
                setOptLoading(status === 'RUNNING' || status === 'PREPARING' || status.startsWith('VALIDATING'));
            } catch (error) {
                console.error('Optimization Polling Error:', error);
            }
        },
        {
            enabled: mode === 'OPTIMIZER' || optLoading || optimizerIsActive,
            intervalMs: 1000,
            runImmediately: true,
            pauseWhenHidden: true,
        }
    );

    const runOptimizer = async () => {
        try {
            const res = await apiFetch(`/api/v1/strategy/start?index=${optIndex}`, { method: 'POST' });
            const body = await readJsonSafe<any>(res);
            if (!res.ok) {
                showMessage({
                    type: 'error',
                    text: pickApiMessage(body, 'Failed to start optimizer.'),
                });
                return;
            }
            showMessage(null);
            setOptStatus((prev: any) => ({
                ...prev,
                status: 'PREPARING',
                error: null,
                index: body?.index ?? optIndex,
            }));
            setOptLoading(true);
        } catch (error) {
            showMessage({
                type: 'error',
                text: 'Network error while starting optimizer.',
            });
        }
    };

    return {
        optStatus,
        setOptStatus,
        optIndex,
        setOptIndex,
        optLoading,
        setOptLoading,
        optimizerStatus,
        optimizerIsActive,
        optimizerHasResults,
        runOptimizer,
    };
}
