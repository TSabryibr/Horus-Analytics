'use client';

import { useState } from 'react';
import { apiFetch, readJsonSafe } from '@/lib/api';
import { usePolling } from '@/hooks/usePolling';
import { ScannerData } from '@/types';

export type StaleMeta = {
    lastUpdated: string | null;
    expectedDate: string | null;
    pipelineState: string | null;
};

type UseScannerExecutionOptions = {
    index: string;
    isIntraday: boolean;
    isPolling: boolean;
    selectedProfileId?: string;
    setData: (data: ScannerData | null) => void;
    setError: (error: string) => void;
    setErrorTitle: (title: string) => void;
    setIsPolling: (value: boolean) => void;
    setLoading: (value: boolean) => void;
    setProgress: (value: string) => void;
};

export function useScannerExecution({
    index,
    isIntraday,
    isPolling,
    selectedProfileId,
    setData,
    setError,
    setErrorTitle,
    setIsPolling,
    setLoading,
    setProgress,
}: UseScannerExecutionOptions) {
    const [staleMeta, setStaleMeta] = useState<StaleMeta | null>(null);

    const pollStatus = async () => {
        try {
            const statusRes = await apiFetch('/scanner/status');
            const status = await readJsonSafe<any>(statusRes);

            if (status.status === 'RUNNING') {
                setLoading(true);
                setProgress(`Scanning ${status.current_ticker || ''} [${status.progress || 0}/${status.total || '?'}]`);
            } else if (status.status === 'COMPLETED') {
                setIsPolling(false);
                setData(status.result);
                setLoading(false);
                setProgress('');
            } else if (status.status === 'ERROR' || status.status === 'error') {
                setIsPolling(false);
                setError(status.error || status.message || 'Scan Error');
                setLoading(false);
            }
        } catch (error) {
            console.error('Scanner Polling Error:', error);
            setIsPolling(false);
            setLoading(false);
            setError('Lost connection to API during scan.');
        }
    };

    usePolling(pollStatus, { intervalMs: 2000, enabled: isPolling, runImmediately: true, pauseWhenHidden: true });

    const runScan = async () => {
        setLoading(true);
        setError('');
        setErrorTitle('Connection Error');
        setProgress('Starting...');
        setData(null);
        setStaleMeta(null);

        try {
            const params = new URLSearchParams({
                index,
                intraday: String(isIntraday),
            });
            if (selectedProfileId) {
                params.set('profile_id', selectedProfileId);
            } else {
                params.set('use_active_profile', 'false');
            }
            const startRes = await apiFetch(`/scanner/start?${params.toString()}`, { method: 'POST' });
            if (!startRes.ok) {
                let errorMsg = 'Failed to start scan.';
                try {
                    const payload = await readJsonSafe<any>(startRes);
                    if (payload?.status === 'stale_mode') {
                        const pipe = payload?.pipeline_state ? ` (${payload.pipeline_state})` : '';
                        setErrorTitle('Read-Only Stale Mode');
                        errorMsg = `${payload?.message || 'Scanner is blocked in stale mode.'}${pipe}`;
                        setStaleMeta({
                            lastUpdated: payload?.last_updated ?? null,
                            expectedDate: payload?.expected_date ?? null,
                            pipelineState: payload?.pipeline_state ?? null,
                        });
                    } else {
                        errorMsg = payload?.message || payload?.detail || errorMsg;
                    }
                } catch {
                    // Keep default fallback when response body isn't JSON.
                }
                throw new Error(errorMsg);
            }

            setIsPolling(true);
        } catch (err) {
            console.error('Scanner Scan Trigger Error:', err);
            setError(err instanceof Error ? err.message : 'Failed to connect to Scanner API. Ensure Backend is running.');
            setLoading(false);
            setProgress('');
        }
    };

    const bypassStaleMode = async () => {
        try {
            setLoading(true);
            setError('');
            setStaleMeta(null);
            const res = await apiFetch('/system/stale-override', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ approve: true }),
            });
            if (!res.ok) {
                setError('Failed to bypass stale mode.');
                setLoading(false);
                return;
            }
            // Auto-retry the scan now that override is set
            await runScan();
        } catch (err) {
            console.error('Bypass Stale Error:', err);
            setError('Failed to apply stale bypass.');
            setLoading(false);
        }
    };
    const confirmHoliday = async () => {
        try {
            setLoading(true);
            setError('');
            // Prioritize the expected date for the holiday check
            const dateStr = staleMeta?.expectedDate || staleMeta?.lastUpdated?.split(' ')[0];
            
            const res = await apiFetch('/system/confirm-holiday', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    date: dateStr,
                    description: 'User confirmed market holiday' 
                }),
            });
            if (!res.ok) {
                const payload = await readJsonSafe<any>(res);
                setError(payload?.message || 'Failed to confirm holiday.');
                setLoading(false);
                return;
            }
            setStaleMeta(null);
            await runScan();
        } catch (err) {
            console.error('Confirm Holiday Error:', err);
            setError('Failed to confirm holiday.');
            setLoading(false);
        }
    };

    return {
        runScan,
        staleMeta,
        bypassStaleMode,
        confirmHoliday,
    };
}
