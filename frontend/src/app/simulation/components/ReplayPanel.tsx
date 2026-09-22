'use client';

import clsx from 'clsx';
import { Play, Square, Radio, Signal, Send, FileText, FileSpreadsheet, ChevronRight, CheckCircle2, XCircle, Clock, Target, BriefcaseBusiness, CalendarDays, RotateCcw, CalendarOff } from 'lucide-react';
import type { ReplayMode, ReplayStatus } from '../hooks/useReplay';
import { GlassCard, MetricBox, ErrorDisplay } from './SimulationPrimitives';

type ReplayPanelProps = {
    replayDate: string;
    setReplayDate: (v: string) => void;
    replayMode: ReplayMode;
    setReplayMode: (v: ReplayMode) => void;
    replayStartDate: string;
    setReplayStartDate: (v: string) => void;
    replayEndDate: string;
    setReplayEndDate: (v: string) => void;
    replaySpeed: string;
    setReplaySpeed: (v: string) => void;
    replayNotify: boolean;
    setReplayNotify: (v: boolean) => void;
    replayReport: boolean;
    setReplayReport: (v: boolean) => void;
    replayResetPortfolio: boolean;
    setReplayResetPortfolio: (v: boolean) => void;
    replayCloseOpenPositionsEnd: boolean;
    setReplayCloseOpenPositionsEnd: (v: boolean) => void;
    replayTreatMissingDaysAsHolidays: boolean;
    setReplayTreatMissingDaysAsHolidays: (v: boolean) => void;
    replayLiveChannelRouting: boolean;
    setReplayLiveChannelRouting: (v: boolean) => void;
    replayLoading: boolean;
    replayStatus: ReplayStatus | null;
    replayError: string | null;
    selectedProfileLabel: string;
    onStart: () => void | Promise<void>;
    onStop: () => void | Promise<void>;
    onDownloadExcel?: () => void;
};

const SPEED_PRESETS = [
    { label: '5x', value: '5', desc: 'Detailed' },
    { label: '10x', value: '10', desc: 'Balanced' },
    { label: '20x', value: '20', desc: 'Fast' },
    { label: '50x', value: '50', desc: 'Rapid' },
    { label: '100x', value: '100', desc: 'Turbo' },
    { label: '150x', value: '150', desc: 'Ultra' },
];

const formatReplayPrice = (value?: number | null) => {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric.toFixed(2) : '-';
};

const formatReplayDateTime = (value?: string | null) => {
    if (!value) return '-';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleString(undefined, {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
};

type ReplayOutcome = 'OPEN' | 'STOP' | 'BE_STOP' | 'TP1' | 'TP2' | 'END_FLAT' | 'CLOSED';

const resolveTradeOutcome = (trade: NonNullable<ReplayStatus['active_trades']>[number]): ReplayOutcome => {
    const state = String(trade.state || '').toUpperCase();
    const reason = String(trade.exit_reason || '').toLowerCase();
    const tp1Hit = Boolean(trade.tp1_hit);

    if (state !== 'CLOSED') {
        if (state === 'TP1_HIT' || tp1Hit) return 'TP1';
        return 'OPEN';
    }

    if (reason.includes('target_2')) return 'TP2';
    if (reason.includes('stop')) {
        return reason.includes('breakeven') ? 'BE_STOP' : 'STOP';
    }
    if (reason.includes('replay_end')) return 'END_FLAT';
    if (tp1Hit) return 'TP1';
    return 'CLOSED';
};

const resolveOutcomePriceClasses = (outcome: ReplayOutcome) => {
    const muted = 'text-slate-400';

    if (outcome === 'STOP' || outcome === 'BE_STOP') {
        return {
            exit: 'text-rose-300 font-black',
            stop: 'text-rose-300 font-black',
            tp1: muted,
            tp2: muted,
        };
    }

    if (outcome === 'TP2') {
        return {
            exit: 'text-emerald-300 font-black',
            stop: muted,
            tp1: 'text-cyan-300',
            tp2: 'text-emerald-300 font-black',
        };
    }

    if (outcome === 'TP1') {
        return {
            exit: 'text-emerald-300 font-black',
            stop: muted,
            tp1: 'text-emerald-300 font-black',
            tp2: muted,
        };
    }

    if (outcome === 'OPEN') {
        return {
            exit: 'text-cyan-300',
            stop: muted,
            tp1: 'text-cyan-300',
            tp2: 'text-cyan-300',
        };
    }

    return {
        exit: 'text-slate-200',
        stop: muted,
        tp1: muted,
        tp2: muted,
    };
};

export function ReplayPanel({
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
    selectedProfileLabel,
    onStart,
    onStop,
    onDownloadExcel,
}: ReplayPanelProps) {
    const isActive = replayStatus?.status === 'RUNNING' || replayStatus?.status === 'STARTING' || replayStatus?.status === 'STOPPING';
    const isCompleted = replayStatus?.status === 'COMPLETED';
    const isError = replayStatus?.status === 'ERROR';
    const effectiveProfileLabel = replayStatus?.profile_name || selectedProfileLabel;
    const replayTrades = replayStatus?.active_trades || [];
    const statusMode = replayStatus?.mode || replayMode;
    const campaignProgress = replayStatus?.campaign_progress_pct ?? replayStatus?.progress_pct ?? 0;
    const launchDisabled = replayLoading || (replayMode === 'SINGLE_DAY' ? !replayDate : !replayStartDate || !replayEndDate);
    const campaignSummary = replayStatus?.campaign_summary;
    const pendingEntryCount = replayStatus?.pending_entries_count ?? replayStatus?.pending_entries?.length ?? 0;
    const canDownloadExcel = Boolean(
        replayStatus &&
        ((replayStatus.ticks_completed ?? 0) > 0 || (replayStatus.active_trades && replayStatus.active_trades.length > 0))
    );

    return (
        <div className="animate-in fade-in slide-in-from-bottom-6 duration-700 space-y-8">
            {/* ── Controls ──────────────────────────────────────────── */}
            <div className="group relative">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 rounded-3xl blur opacity-20 transition duration-1000 group-hover:opacity-40" />
                <div className="relative bg-white/[0.02] border border-white/10 rounded-3xl p-8 space-y-8">

                    <div className="flex flex-wrap gap-2">
                        {(['SINGLE_DAY', 'CAMPAIGN'] as ReplayMode[]).map((mode) => (
                            <button
                                key={mode}
                                onClick={() => setReplayMode(mode)}
                                disabled={isActive}
                                className={clsx(
                                    'inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-xs font-black uppercase tracking-widest transition-all disabled:opacity-40',
                                    replayMode === mode
                                        ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                                        : 'border-white/10 bg-white/[0.02] text-slate-500 hover:border-white/20'
                                )}
                            >
                                {mode === 'CAMPAIGN' ? <CalendarDays className="h-3.5 w-3.5" /> : <Clock className="h-3.5 w-3.5" />}
                                {mode === 'CAMPAIGN' ? 'Campaign' : 'Single Day'}
                            </button>
                        ))}
                    </div>

                    {/* Row 1: Date + Speed */}
                    <div className="flex flex-col md:flex-row gap-8">
                        <div className="flex-[1.2]">
                            {replayMode === 'CAMPAIGN' ? (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                                            Campaign Start
                                        </label>
                                        <input
                                            type="date"
                                            value={replayStartDate}
                                            onChange={(e) => setReplayStartDate(e.target.value)}
                                            disabled={isActive}
                                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all disabled:opacity-40"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                                            Campaign End
                                        </label>
                                        <input
                                            type="date"
                                            value={replayEndDate}
                                            onChange={(e) => setReplayEndDate(e.target.value)}
                                            disabled={isActive}
                                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all disabled:opacity-40"
                                        />
                                    </div>
                                </div>
                            ) : (
                                <div>
                                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                                        Replay Date
                                    </label>
                                    <input
                                        type="date"
                                        value={replayDate}
                                        onChange={(e) => setReplayDate(e.target.value)}
                                        disabled={isActive}
                                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all disabled:opacity-40"
                                    />
                                </div>
                            )}
                        </div>
                        <div className="flex-1">
                            <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                                Time Compression
                            </label>
                            <div className="flex gap-2">
                                {SPEED_PRESETS.map((preset) => (
                                    <button
                                        key={preset.value}
                                        onClick={() => setReplaySpeed(preset.value)}
                                        disabled={isActive}
                                        className={clsx(
                                            'flex-1 px-3 py-3 rounded-xl text-xs font-bold transition-all border leading-none flex flex-col items-center gap-1 disabled:opacity-40',
                                            replaySpeed === preset.value
                                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                                : 'bg-white/5 text-slate-500 border-transparent hover:border-white/10'
                                        )}
                                    >
                                        <span className="font-black text-sm">{preset.label}</span>
                                        <span className="text-[9px] opacity-60">{preset.desc}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Row 2: Toggles + Action */}
                    <div className="flex flex-col md:flex-row items-end gap-8">
                        <div className="flex-1 flex gap-6">
                            <ToggleSwitch
                                label="Telegram Alerts"
                                icon={<Send className="w-3.5 h-3.5" />}
                                enabled={replayNotify}
                                onChange={setReplayNotify}
                                disabled={isActive}
                                color="emerald"
                            />
                            <ToggleSwitch
                                label="AI Report"
                                icon={<FileText className="w-3.5 h-3.5" />}
                                enabled={replayReport}
                                onChange={setReplayReport}
                                disabled={isActive}
                                color="emerald"
                            />
                            <ToggleSwitch
                                label="Close Open At End"
                                icon={<BriefcaseBusiness className="w-3.5 h-3.5" />}
                                enabled={replayCloseOpenPositionsEnd}
                                onChange={setReplayCloseOpenPositionsEnd}
                                disabled={isActive}
                                color="orange"
                            />
                            <ToggleSwitch
                                label="Live Channel Routing"
                                icon={<Radio className="w-3.5 h-3.5" />}
                                enabled={replayLiveChannelRouting}
                                onChange={setReplayLiveChannelRouting}
                                disabled={isActive}
                                color="orange"
                            />
                            {replayMode === 'CAMPAIGN' && (
                                <>
                                    <ToggleSwitch
                                        label="Reset Portfolio"
                                        icon={<RotateCcw className="w-3.5 h-3.5" />}
                                        enabled={replayResetPortfolio}
                                        onChange={setReplayResetPortfolio}
                                        disabled={isActive}
                                        color="cyan"
                                    />
                                    <ToggleSwitch
                                        label="Missing Days = Holidays"
                                        icon={<CalendarOff className="w-3.5 h-3.5" />}
                                        enabled={replayTreatMissingDaysAsHolidays}
                                        onChange={setReplayTreatMissingDaysAsHolidays}
                                        disabled={isActive}
                                        color="orange"
                                    />
                                </>
                            )}
                        </div>

                        <div className="flex gap-3 w-full md:w-auto">
                            {onDownloadExcel && (
                                <button
                                    onClick={onDownloadExcel}
                                    disabled={!canDownloadExcel}
                                    className="w-full md:w-auto px-6 py-4 bg-white/5 border border-white/10 hover:border-emerald-500/40 text-emerald-300 font-bold tracking-wider rounded-2xl transition-all active:scale-95 disabled:opacity-30 disabled:pointer-events-none uppercase text-xs flex items-center justify-center gap-2 hover:bg-emerald-500/10"
                                    title="Export full session results, signals, and trades to Excel (.xlsx)"
                                >
                                    <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                                    EXPORT EXCEL
                                </button>
                            )}
                            {isActive ? (
                                <button
                                    onClick={onStop}
                                    className="w-full md:w-auto px-10 py-4 bg-red-500 text-white font-black tracking-widest rounded-2xl transition-all active:scale-95 uppercase text-xs flex items-center justify-center gap-3 hover:bg-red-400"
                                >
                                    <Square className="w-4 h-4 fill-current" />
                                    ABORT REPLAY
                                </button>
                            ) : (
                                <button
                                    onClick={onStart}
                                    disabled={launchDisabled}
                                    className="w-full md:w-auto px-10 py-4 bg-emerald-500 text-white font-black tracking-widest rounded-2xl transition-all active:scale-95 disabled:opacity-30 disabled:pointer-events-none uppercase text-xs flex items-center justify-center gap-3 hover:bg-emerald-400"
                                >
                                    <Play className="w-4 h-4 fill-current" />
                                    {replayMode === 'CAMPAIGN' ? 'LAUNCH CAMPAIGN' : 'LAUNCH REPLAY'}
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-xs text-amber-200">
                        Replay persists <span className="font-bold">REPLAY</span> signals and simulation portfolio positions. Telegram toggles send real test Telegram messages when enabled.
                    </div>
                    <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/5 px-4 py-3 text-xs text-cyan-200">
                        Intraday entries are risk-sized from simulation cash and stop distance; entries with invalid entry/stop geometry are skipped and logged.
                    </div>
                </div>
            </div>

            {replayError && <ErrorDisplay error={replayError} />}

            {/* ── Live Progress ──────────────────────────────────────── */}
            {(isActive || isCompleted || isError) && replayStatus && (
                <div className="space-y-8 animate-in fade-in fill-mode-both duration-700">
                    <div className="flex items-center gap-3 rounded-2xl border border-emerald-500/15 bg-emerald-500/5 px-5 py-4">
                        <Target className="h-4 w-4 text-emerald-400" />
                        <span className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">Profile In Use</span>
                        <span className="truncate text-sm font-bold text-emerald-300">{effectiveProfileLabel}</span>
                    </div>

                    {/* Progress Bar */}
                    {isActive && (
                        <div className="relative bg-white/[0.02] border border-emerald-500/20 rounded-2xl p-6 overflow-hidden">
                            <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 to-transparent pointer-events-none" />
                            <div className="relative flex items-center gap-6">
                                <div className="relative">
                                    <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                                        <Radio className="w-6 h-6 text-emerald-400 animate-pulse" />
                                    </div>
                                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-ping" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-baseline gap-3 mb-2">
                                        <span className="text-2xl font-black text-emerald-400 font-mono">
                                            {campaignProgress.toFixed(1)}%
                                        </span>
                                        <span className="text-xs text-slate-500 font-bold uppercase tracking-widest">
                                            {statusMode === 'CAMPAIGN'
                                                ? `Day ${replayStatus.current_day_index || 0}/${replayStatus.days_total || 0} | Tick ${replayStatus.ticks_completed}/${replayStatus.total_ticks}`
                                                : `Tick ${replayStatus.ticks_completed}/${replayStatus.total_ticks}`}
                                        </span>
                                    </div>
                                    <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full transition-all duration-1000 ease-out"
                                            style={{ width: `${campaignProgress}%` }}
                                        />
                                    </div>
                                    <div className="flex justify-between mt-2 text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                                        <span>SIM TIME: {replayStatus.current_time || '—'}</span>
                                        <span>{replayStatus.market_open} → {replayStatus.market_close}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        <MetricBox label={statusMode === 'CAMPAIGN' ? 'Current Day' : 'Date'} value={replayStatus.current_date || replayStatus.date || '—'} color="slate" />
                        <MetricBox label="Speed" value={`${replayStatus.speed}x`} color="cyan" />
                        <MetricBox label="Signals Found" value={String(replayStatus.signals_found)} color="orange" />
                        <MetricBox label="Pending Open" value={String(pendingEntryCount)} color="yellow" />
                        <MetricBox
                            label="Status"
                            value={replayStatus.status}
                            color={isCompleted ? 'cyan' : isError ? 'red' : 'orange'}
                        />
                    </div>

                    {statusMode === 'CAMPAIGN' && campaignSummary && (
                        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                            <MetricBox label="Open" value={String(campaignSummary.open_positions)} color="cyan" />
                            <MetricBox label="Closed" value={String(campaignSummary.closed_positions)} color="slate" />
                            <MetricBox label="TP1" value={String(campaignSummary.tp1_hits ?? 0)} color="orange" />
                            <MetricBox label="TP2" value={String(campaignSummary.tp2_exits ?? 0)} color="cyan" />
                            <MetricBox label="SL" value={String(campaignSummary.stop_loss_exits ?? 0)} color="red" />
                            <MetricBox label="BE" value={String(campaignSummary.breakeven_stop_exits ?? 0)} color="slate" />
                        </div>
                    )}

                    {statusMode === 'CAMPAIGN' && (replayStatus.day_results?.length || 0) > 0 && (
                        <GlassCard title="Campaign Day Results" icon={<CalendarDays className="text-emerald-500" />}>
                            <div className="max-h-[360px] overflow-auto rounded-xl border border-white/5">
                                <table className="w-full min-w-[760px] text-left">
                                    <thead>
                                        <tr className="border-b border-white/10 bg-white/[0.02] text-[10px] font-black uppercase tracking-[0.18em] text-slate-500">
                                            <th className="p-3">Date</th>
                                            <th className="p-3 text-right">Signals</th>
                                            <th className="p-3 text-right">Ticks</th>
                                            <th className="p-3 text-right">Open</th>
                                            <th className="p-3 text-right">Closed</th>
                                            <th className="p-3 text-right">TP1</th>
                                            <th className="p-3 text-right">TP2</th>
                                            <th className="p-3 text-right">SL</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                        {replayStatus.day_results?.map((day, index) => (
                                            <tr key={`${day.date}-${index}`} className="text-sm">
                                                <td className="p-3 font-mono text-slate-200">{day.date}</td>
                                                <td className="p-3 text-right font-mono text-orange-300">{day.signals_found}</td>
                                                <td className="p-3 text-right font-mono text-cyan-300">{day.ticks_completed}/{day.total_ticks}</td>
                                                <td className="p-3 text-right font-mono text-cyan-200">{day.open_positions}</td>
                                                <td className="p-3 text-right font-mono text-slate-200">{day.closed_positions}</td>
                                                <td className="p-3 text-right font-mono text-amber-300">{day.tp1_hits ?? 0}</td>
                                                <td className="p-3 text-right font-mono text-emerald-300">{day.tp2_exits ?? 0}</td>
                                                <td className="p-3 text-right font-mono text-rose-300">{day.stop_loss_exits ?? 0}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </GlassCard>
                    )}

                    {replayTrades.length > 0 && (
                        <GlassCard title="Replay Results" icon={<BriefcaseBusiness className="text-emerald-500" />}>
                            <div className="overflow-x-auto">
                                <table className="w-full min-w-[980px] text-left">
                                    <thead>
                                        <tr className="border-b border-white/10 text-[10px] font-black uppercase tracking-[0.18em] text-slate-500">
                                            <th className="pb-3">Ticker</th>
                                            <th className="pb-3">State</th>
                                            <th className="pb-3 text-right">Entry Time</th>
                                            <th className="pb-3 text-right">Exit Time</th>
                                            <th className="pb-3 text-right">Entry</th>
                                            <th className="pb-3 text-right">Exit</th>
                                            <th className="pb-3 text-right">Stop</th>
                                            <th className="pb-3 text-right">TP1</th>
                                            <th className="pb-3 text-right">TP2</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                        {replayTrades.map((trade) => {
                                            const outcome = resolveTradeOutcome(trade);
                                            const priceClasses = resolveOutcomePriceClasses(outcome);
                                            return (
                                            <tr key={`${trade.ticker}-${trade.entry_at || ''}`} className="text-sm">
                                                <td className="py-3 font-black text-emerald-300">{trade.ticker}</td>
                                                <td className="py-3">
                                                    <span className={clsx(
                                                        'rounded-lg border px-2 py-1 text-[10px] font-black uppercase tracking-widest',
                                                        trade.state === 'CLOSED'
                                                            ? 'border-slate-500/20 bg-slate-500/10 text-slate-300'
                                                            : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300'
                                                    )}>
                                                        {trade.state}
                                                    </span>
                                                </td>
                                                <td className="py-3 text-right font-mono text-slate-400">{formatReplayDateTime(trade.entry_at)}</td>
                                                <td className="py-3 text-right font-mono text-slate-400">{formatReplayDateTime(trade.exit_at)}</td>
                                                <td className="py-3 text-right font-mono text-slate-200">{formatReplayPrice(trade.entry_price)}</td>
                                                <td className={clsx('py-3 text-right font-mono', priceClasses.exit)}>{formatReplayPrice(trade.exit_price)}</td>
                                                <td className={clsx('py-3 text-right font-mono', priceClasses.stop)}>{formatReplayPrice(trade.stop_loss)}</td>
                                                <td className={clsx('py-3 text-right font-mono', priceClasses.tp1)}>{formatReplayPrice(trade.tp1)}</td>
                                                <td className={clsx('py-3 text-right font-mono', priceClasses.tp2)}>{formatReplayPrice(trade.tp2)}</td>
                                            </tr>
                                        )})}
                                    </tbody>
                                </table>
                            </div>
                        </GlassCard>
                    )}

                    {/* Tick Log */}
                    {replayStatus.scan_results.length > 0 && (
                        <GlassCard title="Scan Activity Log" icon={<Signal className="text-emerald-500" />}>
                            <div className="max-h-[400px] overflow-y-auto space-y-2 pr-2 scrollbar-thin">
                                {replayStatus.scan_results.map((tick, i) => (
                                    <div
                                        key={i}
                                        className={clsx(
                                            'flex items-center gap-4 px-4 py-3 rounded-xl border transition-all',
                                            tick.signals_count > 0
                                                ? 'bg-emerald-500/5 border-emerald-500/15'
                                                : tick.error
                                                    ? 'bg-red-500/5 border-red-500/15'
                                                    : 'bg-white/[0.01] border-white/5'
                                        )}
                                    >
                                        <div className="flex items-center gap-2 min-w-0">
                                            {tick.error ? (
                                                <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                                            ) : tick.signals_count > 0 ? (
                                                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                                            ) : (
                                                <Clock className="w-4 h-4 text-slate-600 shrink-0" />
                                            )}
                                            <span className="text-xs font-mono text-slate-400 shrink-0">
                                                {tick.simulated_time}
                                            </span>
                                            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest shrink-0">
                                                {tick.scan_label}
                                            </span>
                                        </div>
                                        <div className="ml-auto flex items-center gap-3">
                                            {tick.signals_count > 0 && (
                                                <span className="text-xs font-black text-emerald-400">
                                                    {tick.signals_count} signal{tick.signals_count !== 1 ? 's' : ''}
                                                </span>
                                            )}
                                            {tick.signals.map((s, j) => (
                                                <span
                                                    key={j}
                                                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-emerald-500/10 text-emerald-300 text-[10px] font-bold"
                                                >
                                                    {s.ticker}
                                                    <ChevronRight className="w-2.5 h-2.5 opacity-50" />
                                                    {s.score}/10
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </GlassCard>
                    )}
                </div>
            )}
        </div>
    );
}


/* ── Toggle Switch Primitive ────────────────────────────────────── */

function ToggleSwitch({
    label,
    icon,
    enabled,
    onChange,
    disabled,
    color = 'emerald',
}: {
    label: string;
    icon: React.ReactNode;
    enabled: boolean;
    onChange: (v: boolean) => void;
    disabled?: boolean;
    color?: 'emerald' | 'cyan' | 'orange';
}) {
    const colors = {
        emerald: {
            active: 'bg-emerald-500',
            enabledFrame: 'border-emerald-500/30 bg-emerald-500/5',
            iconBg: 'bg-emerald-500/20',
            text: 'text-emerald-400',
        },
        cyan: {
            active: 'bg-cyan-500',
            enabledFrame: 'border-cyan-500/30 bg-cyan-500/5',
            iconBg: 'bg-cyan-500/20',
            text: 'text-cyan-400',
        },
        orange: {
            active: 'bg-orange-500',
            enabledFrame: 'border-orange-500/30 bg-orange-500/5',
            iconBg: 'bg-orange-500/20',
            text: 'text-orange-400',
        },
    }[color];

    return (
        <button
            onClick={() => onChange(!enabled)}
            disabled={disabled}
            className={clsx(
                'flex items-center gap-3 px-4 py-3 rounded-xl border transition-all text-left disabled:opacity-40',
                enabled
                    ? colors.enabledFrame
                    : 'border-white/5 bg-white/[0.02]'
            )}
        >
            <div className={clsx('p-1.5 rounded-lg', enabled ? colors.iconBg : 'bg-white/5')}>
                {icon}
            </div>
            <div>
                <span className="block text-[10px] font-black text-slate-500 uppercase tracking-widest">{label}</span>
                <span className={clsx('text-xs font-bold', enabled ? colors.text : 'text-slate-600')}>
                    {enabled ? 'ON' : 'OFF'}
                </span>
            </div>
            {/* Toggle indicator */}
            <div className={clsx(
                'ml-auto w-9 h-5 rounded-full transition-all relative',
                enabled ? colors.active : 'bg-white/10'
            )}>
                <div className={clsx(
                    'absolute top-0.5 w-4 h-4 bg-white rounded-full shadow-lg transition-all',
                    enabled ? 'left-[18px]' : 'left-0.5'
                )} />
            </div>
        </button>
    );
}
