'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export type DryRunStep = {
    step: string;
    status: 'running' | 'completed' | 'error';
    started_at: string;
    duration_sec: number;
    result: any;
    error: string | null;
};

export type DryRunStatus = {
    status: 'IDLE' | 'RUNNING' | 'COMPLETED' | 'ERROR';
    date: string | null;
    notify: boolean;
    report: boolean;
    ai_report: boolean;
    profile_id?: number | null;
    profile_name?: string | null;
    profile_source_type?: string | null;
    profile_scope?: string | null;
    market?: string | null;
    started_at: string | null;
    completed_at: string | null;
    duration_sec: number;
    steps: DryRunStep[];
    signals_found: number;
    signals: Array<{
        ticker: string;
        score: number;
        type: string;
        entry: number;
        stop_loss: number;
        target: number;
    }>;
    regime: string | null;
    breadth: number;
    report_generated: boolean;
    ai_report_generated: boolean;
    telegram_messages_sent: number;
    error: string | null;
};

type UseDryRunOptions = {
    apiBase: string;
    selectedProfileId?: number | null;
};

export function useDryRun({ apiBase, selectedProfileId = null }: UseDryRunOptions) {
    const [dryrunDate, setDryrunDate] = useState('');
    const [dryrunNotify, setDryrunNotify] = useState(false);
    const [dryrunReport, setDryrunReport] = useState(true);
    const [dryrunAiReport, setDryrunAiReport] = useState(false);
    const [dryrunLoading, setDryrunLoading] = useState(false);
    const [dryrunStatus, setDryrunStatus] = useState<DryRunStatus | null>(null);
    const [dryrunError, setDryrunError] = useState<string | null>(null);
    const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const fetchStatus = useCallback(async () => {
        try {
            const res = await fetch(`${apiBase}/api/v1/dryrun/status`);
            const json = await res.json();
            setDryrunStatus(json);
            return json as DryRunStatus;
        } catch (e) {
            console.error('[DryRun] Status fetch error:', e);
            return null;
        }
    }, [apiBase]);

    const startPolling = useCallback(() => {
        if (pollingRef.current) return;
        pollingRef.current = setInterval(async () => {
            const status = await fetchStatus();
            if (status && !['RUNNING'].includes(status.status)) {
                if (pollingRef.current) {
                    clearInterval(pollingRef.current);
                    pollingRef.current = null;
                }
                setDryrunLoading(false);
            }
        }, 2000);
    }, [fetchStatus]);

    const stopPolling = useCallback(() => {
        if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
    }, []);

    useEffect(() => {
        return () => stopPolling();
    }, [stopPolling]);

    const startDryRun = async () => {
        setDryrunLoading(true);
        setDryrunError(null);
        try {
            const res = await fetch(`${apiBase}/api/v1/dryrun/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: dryrunDate || null,
                    notify: dryrunNotify,
                    report: dryrunReport,
                    ai_report: dryrunAiReport,
                    profile_id: selectedProfileId,
                }),
            });
            const json = await res.json();
            if (json.status === 'error') {
                setDryrunError(json.message);
                setDryrunLoading(false);
            } else {
                startPolling();
            }
        } catch (e) {
            setDryrunError('Failed to start dry run');
            setDryrunLoading(false);
        }
    };

    return {
        dryrunDate,
        setDryrunDate,
        dryrunNotify,
        setDryrunNotify,
        dryrunReport,
        setDryrunReport,
        dryrunAiReport,
        setDryrunAiReport,
        dryrunLoading,
        dryrunStatus,
        dryrunError,
        startDryRun,
        fetchStatus,
    };
}
