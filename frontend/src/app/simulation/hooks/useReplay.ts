'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export type ReplayStatus = {
    status: 'IDLE' | 'STARTING' | 'RUNNING' | 'STOPPING' | 'COMPLETED' | 'ERROR';
    mode?: 'SINGLE_DAY' | 'CAMPAIGN';
    date: string | null;
    start_date?: string | null;
    end_date?: string | null;
    current_date?: string | null;
    days_total?: number;
    days_completed?: number;
    current_day_index?: number;
    campaign_progress_pct?: number;
    reset_portfolio?: boolean;
    close_open_positions_end?: boolean;
    allow_missing_intraday_as_holidays?: boolean;
    skipped_holiday_dates?: string[];
    replay_dates?: string[];
    day_results?: Array<{
        date: string;
        ticks_completed: number;
        total_ticks: number;
        signals_found: number;
        open_positions: number;
        closed_positions: number;
        tp1_hits?: number;
        tp2_exits?: number;
        stop_loss_exits?: number;
        breakeven_stop_exits?: number;
        stopped?: boolean;
    }>;
    campaign_summary?: {
        days_completed: number;
        days_total: number;
        signals_found: number;
        open_positions: number;
        closed_positions: number;
        tp1_hits?: number;
        tp2_exits?: number;
        stop_loss_exits?: number;
        breakeven_stop_exits?: number;
    } | null;
    speed: number;
    notify: boolean;
    report: boolean;
    live_channel_routing?: boolean;
    profile_id?: number | null;
    profile_name?: string | null;
    profile_source_type?: string | null;
    profile_scope?: string | null;
    market?: string | null;
    started_at: string | null;
    completed_at: string | null;
    current_time: string | null;
    market_open: string | null;
    market_close: string | null;
    ticks_completed: number;
    total_ticks: number;
    progress_pct: number;
    signals_found: number;
    pending_entries_count?: number;
    pending_entries?: Array<{
        ticker: string;
        state?: string;
        trigger_source?: string;
        scan_label?: string;
        regime?: string | null;
        planned_entry_price?: number;
        queued_at?: string | null;
    }>;
    active_trades?: Array<{
        ticker: string;
        side?: string;
        state: string;
        shares?: number;
        entry_price: number;
        stop_loss: number;
        tp1: number;
        tp2: number;
        tp1_hit?: boolean;
        exit_reason?: string | null;
        entry_at?: string | null;
        exit_at?: string | null;
        exit_price?: number | null;
    }>;
    scan_results: Array<{
        tick: number;
        simulated_time: string;
        scan_label: string;
        signals_count: number;
        signals: Array<{ ticker: string; score: number; type: string; pending_action?: string; skip_reason?: string | null }>;
        pending_entries?: {
            queued: number;
            opened: number;
            skipped: number;
            failed: number;
            remaining: number;
            items?: Array<Record<string, unknown>>;
        };
        error: string | null;
    }>;
    error: string | null;
};

export type ReplayMode = 'SINGLE_DAY' | 'CAMPAIGN';

type UseReplayOptions = {
    apiBase: string;
    selectedProfileId?: number | null;
};

export function useReplay({ apiBase, selectedProfileId = null }: UseReplayOptions) {
    const [replayDate, setReplayDate] = useState('');
    const [replayMode, setReplayMode] = useState<ReplayMode>('SINGLE_DAY');
    const [replayStartDate, setReplayStartDate] = useState('');
    const [replayEndDate, setReplayEndDate] = useState('');
    const [replaySpeed, setReplaySpeed] = useState('10');
    const [replayNotify, setReplayNotify] = useState(false);
    const [replayReport, setReplayReport] = useState(false);
    const [replayResetPortfolio, setReplayResetPortfolio] = useState(true);
    const [replayCloseOpenPositionsEnd, setReplayCloseOpenPositionsEnd] = useState(false);
    const [replayTreatMissingDaysAsHolidays, setReplayTreatMissingDaysAsHolidays] = useState(false);
    const [replayLiveChannelRouting, setReplayLiveChannelRouting] = useState(false);
    const [replayLoading, setReplayLoading] = useState(false);
    const [replayStatus, setReplayStatus] = useState<ReplayStatus | null>(null);
    const [replayError, setReplayError] = useState<string | null>(null);
    const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const startInFlightRef = useRef(false);

    const fetchStatus = useCallback(async () => {
        try {
            const res = await fetch(`${apiBase}/api/v1/replay/status`);
            const json = await res.json();
            setReplayStatus(json);
            return json as ReplayStatus;
        } catch (e) {
            console.error('[Replay] Status fetch error:', e);
            return null;
        }
    }, [apiBase]);

    const startPolling = useCallback(() => {
        if (pollingRef.current) return;
        pollingRef.current = setInterval(async () => {
            const status = await fetchStatus();
            if (status && !['RUNNING', 'STARTING', 'STOPPING'].includes(status.status)) {
                if (pollingRef.current) {
                    clearInterval(pollingRef.current);
                    pollingRef.current = null;
                }
                startInFlightRef.current = false;
                setReplayLoading(false);
            }
        }, 3000);
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

    useEffect(() => {
        let active = true;
        const bootstrap = async () => {
            const status = await fetchStatus();
            if (!active || !status) return;
            if (['RUNNING', 'STARTING', 'STOPPING'].includes(status.status)) {
                startPolling();
            }
        };
        void bootstrap();
        return () => {
            active = false;
        };
    }, [fetchStatus, startPolling]);

    const startReplay = async () => {
        if (startInFlightRef.current) return;
        if (replayMode === 'SINGLE_DAY' && !replayDate) {
            setReplayError('Please select a date');
            return;
        }
        if (replayMode === 'CAMPAIGN' && (!replayStartDate || !replayEndDate)) {
            setReplayError('Please select campaign start and end dates');
            return;
        }
        startInFlightRef.current = true;
        setReplayLoading(true);
        setReplayError(null);
        try {
            const isCampaign = replayMode === 'CAMPAIGN';
            const res = await fetch(`${apiBase}${isCampaign ? '/api/v1/replay/campaign/start' : '/api/v1/replay/start'}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(isCampaign
                    ? {
                        start_date: replayStartDate,
                        end_date: replayEndDate,
                        speed: parseInt(replaySpeed, 10) || 10,
                        notify: replayNotify,
                        report: replayReport,
                        reset_portfolio: replayResetPortfolio,
                        close_open_positions_end: replayCloseOpenPositionsEnd,
                        allow_missing_intraday_as_holidays: replayTreatMissingDaysAsHolidays,
                        live_channel_routing: replayLiveChannelRouting,
                        profile_id: selectedProfileId,
                    }
                    : {
                        date: replayDate,
                        speed: parseInt(replaySpeed, 10) || 10,
                        notify: replayNotify,
                        report: replayReport,
                        close_open_positions_end: replayCloseOpenPositionsEnd,
                        live_channel_routing: replayLiveChannelRouting,
                        profile_id: selectedProfileId,
                    }),
            });
            const json = await res.json();
            if (json.status === 'error') {
                setReplayError(json.message);
                startInFlightRef.current = false;
                setReplayLoading(false);
            } else {
                startPolling();
            }
        } catch (e) {
            setReplayError('Failed to start replay');
            startInFlightRef.current = false;
            setReplayLoading(false);
        }
    };

    const stopReplay = async () => {
        try {
            await fetch(`${apiBase}/api/v1/replay/stop`, { method: 'POST' });
            await fetchStatus();
            startInFlightRef.current = false;
        } catch (e) {
            console.error('[Replay] Stop error:', e);
        }
    };

    const downloadExcelReport = useCallback(() => {
        if (typeof window !== 'undefined') {
            window.open(`${apiBase}/api/v1/replay/export/excel`, '_blank');
        }
    }, [apiBase]);

    return {
        replayDate,
        setReplayDate,
        replayMode,
        setReplayMode,
        replayStartDate,
        setReplayStartDate,
        replayEndDate,
        setReplayEndDate,
        replaySpeed,
        setReplaySpeed,
        replayNotify,
        setReplayNotify,
        replayReport,
        setReplayReport,
        replayResetPortfolio,
        setReplayResetPortfolio,
        replayCloseOpenPositionsEnd,
        setReplayCloseOpenPositionsEnd,
        replayTreatMissingDaysAsHolidays,
        setReplayTreatMissingDaysAsHolidays,
        replayLiveChannelRouting,
        setReplayLiveChannelRouting,
        replayLoading,
        replayStatus,
        replayError,
        startReplay,
        stopReplay,
        downloadExcelReport,
        fetchStatus,
    };
}
