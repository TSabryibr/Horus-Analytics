import clsx from 'clsx';
import { Activity, ArrowRight, ShieldAlert } from 'lucide-react';

import EmptyState from './EmptyState';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';

type LaneCandidate = {
    id?: number;
    ticker: string;
    side: string;
    confidence: number;
    source_module?: string | null;
    strategy_profile_name?: string | null;
};

type LaneState = {
    count: number;
    candidates: LaneCandidate[];
};

type HomeSignalsPanelProps = {
    hasSignals: boolean;
    isSourceLoading: boolean;
    onOpenArchives: () => void;
    onOpenTelegram: () => void;
    operatingMode: 'MANUAL' | 'AI_ASSIST' | 'AUTOPILOT';
    autopilotArmed: boolean;
    failedDeliveryCount?: number;
    lifecycle?: {
        activeCount?: number;
        ambiguousCount?: number;
        openCount?: number;
        tp1Count?: number;
    };
    followUps?: {
        total?: number;
        pendingCount?: number;
        readyCount?: number;
        failedCount?: number;
        suppressedCount?: number;
        stalePendingCount?: number;
    };
    lanes: {
        intraday: LaneState;
        swing: LaneState;
        position: LaneState;
    };
};

const LANE_CONFIG: Array<{
    key: keyof HomeSignalsPanelProps['lanes'];
    label: string;
    subtitle: string;
    accent: string;
}> = [
    { key: 'intraday', label: 'Intraday Horizon', subtitle: 'Session-cycle dispatch queue', accent: 'text-amber-300' },
    { key: 'swing', label: 'Swing Horizon', subtitle: 'Multi-session batch pipeline', accent: 'text-cyan-300' },
    { key: 'position', label: 'Position Horizon', subtitle: 'Long-horizon conviction pipeline', accent: 'text-emerald-300' },
];

export function HomeSignalsPanel({
    hasSignals,
    isSourceLoading,
    onOpenArchives,
    onOpenTelegram,
    operatingMode,
    autopilotArmed,
    failedDeliveryCount = 0,
    lifecycle,
    followUps,
    lanes,
}: HomeSignalsPanelProps) {
    const queueTotal = lanes.intraday.count + lanes.swing.count + lanes.position.count;

    return (
        <IndustrialCard
            tone="secondary"
            className="scan-line relative flex flex-col"
            contentClassName="relative flex flex-1 flex-col p-8"
        >
            <div className="absolute top-4 right-4 text-white/5 font-black text-8xl pointer-events-none select-none">
                02
            </div>

            <div className="mb-8 flex flex-col gap-5 border-b border-white/8 pb-6 lg:flex-row lg:items-center lg:justify-between">
                <div>
                    <h3 className="meta-label mb-2 text-amber-200/70">Signal Desk</h3>
                    <p className="text-2xl heading-title text-white tracking-tighter">Daily Signal Desk</p>
                    <p className="mt-2 max-w-2xl text-sm text-slate-400">
                        Candidates organized by release horizon for dispatch prioritization.
                    </p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                    <span className="terminal-tag terminal-tag-primary">{operatingMode}</span>
                    {autopilotArmed ? (
                        <span className="terminal-tag terminal-tag-alert">AUTOPILOT ARMED</span>
                    ) : (
                        <span className="terminal-tag terminal-tag-muted">Manual Hold</span>
                    )}
                    <div className="relative">
                        <Activity className={clsx('h-5 w-5 text-primary/50 transition-all', isSourceLoading ? 'animate-spin' : '')} />
                    </div>
                </div>
            </div>

            {hasSignals ? (
                <div className="space-y-4">
                    <div className="grid gap-3 rounded-[1.35rem] border border-white/10 bg-black/20 p-4 md:grid-cols-4">
                        <div className="rounded-[1rem] border border-white/8 bg-white/[0.03] px-3 py-3">
                            <div className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Total Pipeline</div>
                            <div className="mt-2 text-2xl font-black text-cyan-300">{queueTotal}</div>
                        </div>
                        <div className="rounded-[1rem] border border-white/8 bg-white/[0.03] px-3 py-3">
                            <div className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Intraday</div>
                            <div className="mt-2 text-2xl font-black text-amber-300">{lanes.intraday.count}</div>
                        </div>
                        <div className="rounded-[1rem] border border-white/8 bg-white/[0.03] px-3 py-3">
                            <div className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Swing</div>
                            <div className="mt-2 text-2xl font-black text-cyan-300">{lanes.swing.count}</div>
                        </div>
                        <div className="rounded-[1rem] border border-white/8 bg-white/[0.03] px-3 py-3">
                            <div className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Position</div>
                            <div className="mt-2 text-2xl font-black text-emerald-300">{lanes.position.count}</div>
                        </div>
                    </div>
                    <div className="flex flex-wrap gap-3 rounded-[1.35rem] border border-white/10 bg-black/20 p-4">
                        <div className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-2 text-[10px] font-black uppercase tracking-[0.22em] text-slate-300">
                            {followUps?.pendingCount ?? 0} Pending Follow-Ups
                        </div>
                        <div className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.22em] text-cyan-200">
                            {followUps?.readyCount ?? 0} Ready for Dispatch
                        </div>
                        <div className="rounded-full border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.22em] text-rose-200">
                            {followUps?.failedCount ?? 0} Failed Dispatches
                        </div>
                        <div className="rounded-full border border-amber-400/20 bg-amber-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.22em] text-amber-200">
                            {followUps?.stalePendingCount ?? 0} Stale Pipeline
                        </div>
                    </div>
                    <div className="grid gap-3 rounded-[1.35rem] border border-white/10 bg-[linear-gradient(135deg,rgba(251,191,36,0.05),rgba(15,23,42,0.62))] p-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
                        <div>
                            <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Signal Horizon Matrix</div>
                            <div className="mt-2 text-lg font-black uppercase tracking-[0.16em] text-white">Candidate Concentration by Horizon</div>
                            <p className="mt-2 max-w-2xl text-xs leading-5 text-slate-400">
                                The three release horizons surface the highest-conviction candidates before dispatch.
                            </p>
                        </div>
                        <div className="rounded-[1rem] border border-white/8 bg-black/20 px-4 py-4">
                            <div className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Dispatch Status</div>
                            <div className="mt-2 text-sm font-semibold text-stone-100">
                                {Number(followUps?.pendingCount ?? 0) > 0
                                    ? `${followUps?.pendingCount ?? 0} update${Number(followUps?.pendingCount ?? 0) === 1 ? '' : 's'} pending in the dispatch pipeline`
                                    : 'All published signals are tracking without pending intervention'}
                            </div>
                            <div className="mt-3 text-xs text-slate-400">
                                {Number(lifecycle?.activeCount ?? 0)} active signal lifecycle{Number(lifecycle?.activeCount ?? 0) === 1 ? '' : 's'} under surveillance.
                            </div>
                        </div>
                    </div>
                    <div className="grid gap-4 lg:grid-cols-3">
                    {LANE_CONFIG.map((lane) => {
                        const state = lanes[lane.key];
                        return (
                            <section
                                key={lane.key}
                                className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-4 shadow-[0_18px_40px_rgba(2,6,23,0.16)]"
                            >
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <p className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">{lane.label}</p>
                                        <p className="mt-2 text-sm text-slate-400">{lane.subtitle}</p>
                                    </div>
                                    <div className={clsx('text-2xl font-black', lane.accent)}>{state.count}</div>
                                </div>

                                <div className="mt-4 space-y-3">
                                    {state.candidates.slice(0, 3).map((candidate) => (
                                        <div
                                            key={`${lane.key}-${candidate.id ?? candidate.ticker}`}
                                            className="rounded-[1rem] border border-white/8 bg-slate-950/60 px-3 py-3"
                                        >
                                            <div className="flex items-center justify-between gap-3">
                                                <div>
                                                    <div className="text-sm font-black uppercase tracking-[0.16em] text-white">{candidate.ticker}</div>
                                                    <div className="mt-1 text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
                                                        {candidate.side} / {candidate.source_module || 'DESK'}
                                                    </div>
                                                    {candidate.strategy_profile_name ? (
                                                        <div className="mt-1 text-[10px] font-semibold tracking-[0.12em] text-cyan-200">
                                                            {candidate.strategy_profile_name}
                                                        </div>
                                                    ) : null}
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Confidence</div>
                                                    <div className="mt-1 text-sm font-black text-cyan-300">{candidate.confidence}%</div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    {state.candidates.length === 0 ? (
                                        <div className="rounded-[1rem] border border-dashed border-white/10 px-3 py-5 text-center text-xs text-slate-500">
                                            No qualified candidates in this horizon.
                                        </div>
                                    ) : null}
                                </div>
                            </section>
                        );
                    })}
                    </div>
                </div>
            ) : (
                <EmptyState
                    title="Pipeline Clear"
                    message="All scanners active. No horizon has produced a qualified dispatch candidate."
                    icon="activity"
                />
            )}

            <div className="mt-8 flex flex-col gap-3 border-t border-white/8 pt-5 sm:flex-row sm:items-center sm:justify-between">
                <button
                    onClick={onOpenArchives}
                    className="text-left text-[10px] font-black uppercase tracking-[0.34em] text-slate-500 transition-all hover:text-primary"
                >
                    Signal Archive · 30 Days
                </button>
                <button
                    onClick={onOpenTelegram}
                    className="inline-flex items-center justify-center gap-2 rounded-[0.95rem] border border-primary/30 bg-primary/10 px-4 py-2 text-[10px] font-black uppercase tracking-[0.24em] text-primary transition hover:border-primary/50 hover:bg-primary/15"
                >
                    Open Dispatch Rail
                    <ArrowRight className="h-3.5 w-3.5" />
                </button>
            </div>

            {autopilotArmed ? (
                <div className="mt-4 flex items-center gap-2 rounded-[1rem] border border-amber-500/25 bg-amber-500/8 px-3 py-2 text-[10px] font-black uppercase tracking-[0.2em] text-amber-200">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    Dispatch authority delegated to autonomous mode under current operating policy.
                </div>
            ) : null}
            {failedDeliveryCount > 0 ? (
                <div className="mt-3 flex items-center gap-2 rounded-[1rem] border border-rose-500/25 bg-rose-500/8 px-3 py-2 text-[10px] font-black uppercase tracking-[0.2em] text-rose-200">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    {failedDeliveryCount} failed dispatch{failedDeliveryCount === 1 ? ' requires' : 'es require'} retry from the dispatch rail.
                </div>
            ) : null}
            {Number(followUps?.failedCount ?? 0) > 0 || Number(followUps?.pendingCount ?? 0) > 0 ? (
                <div className="mt-3 flex items-center gap-2 rounded-[1rem] border border-cyan-500/25 bg-cyan-500/8 px-3 py-2 text-[10px] font-black uppercase tracking-[0.2em] text-cyan-100">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    {Number(followUps?.pendingCount ?? 0)} follow-up update{Number(followUps?.pendingCount ?? 0) === 1 ? '' : 's'} pending · {Number(followUps?.failedCount ?? 0)} failed in dispatch pipeline.
                </div>
            ) : null}
        </IndustrialCard>
    );
}
