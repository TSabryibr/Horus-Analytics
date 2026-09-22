import Image from 'next/image';
import clsx from 'clsx';
import { Activity, LayoutGrid, LineChart, Zap } from 'lucide-react';

import { HomeMetricsBar } from './HomeMetricsBar';
import { OPEN_SYSTEM_BOOT_EVENT } from './systemBootModel';
import { InfoTooltip } from '@/components/InfoTooltip';

type HomeShellProps = {
    children: React.ReactNode;
    dataSource: 'LIVE' | 'FALLBACK' | 'LOADING';
    error: string | null;
    deskMode: 'MANUAL' | 'AI_ASSIST' | 'AUTOPILOT';
    autopilotArmed: boolean;
    failedDeliveryCount: number;
    laneSummary: { intraday: number; swing: number; position: number };
    publishReadinessLabel: string;
    initializeLoading: boolean;
    marketStatus: React.ReactNode;
    metrics: { total_pnl?: number; win_rate?: number; profit_factor?: number } | null;
    health: { win_rate: number; avg_gain: number } | null;
    isSourceLoading: boolean;
    focusMode: 'FULL' | 'CHART' | 'FEED';
    onSetFocusMode: (mode: 'FULL' | 'CHART' | 'FEED') => void;
    onInitializeRun: () => void;
};

function getTemplePosture(laneSummary: HomeShellProps['laneSummary'], failedDeliveryCount: number) {
    const total = laneSummary.intraday + laneSummary.swing + laneSummary.position;

    if (failedDeliveryCount > 0) {
        return {
            title: 'Intervention Required',
            technicalSubTitle: `TECHNICAL ALERT: ${failedDeliveryCount} FAILED DISPATCH(ES) — INTERVENTION NEEDED`,
            tone: 'Failed deliveries require operator resolution before the next dispatch window.',
            accentClass: 'text-rose-200',
            haloClass: 'from-rose-400/20 via-amber-300/10 to-transparent',
            horizonBadge: 'DISPATCH PIPELINE BLOCKED',
            riskGuardLabel: 'Action Required',
        };
    }

    if (total === 0) {
        return {
            title: 'Surveillance Active',
            technicalSubTitle: 'SCANNERS ACTIVE: NO QUALIFIED CANDIDATES STAGED',
            tone: 'All scanners active. No qualified dispatch candidates at this time.',
            accentClass: 'text-amber-100',
            haloClass: 'from-amber-300/20 via-transparent to-transparent',
            horizonBadge: 'MONITORING MODE',
            riskGuardLabel: 'Standby',
        };
    }

    if (laneSummary.swing >= laneSummary.intraday && laneSummary.swing >= laneSummary.position) {
        return {
            title: 'Swing Conviction Leading',
            technicalSubTitle: `SWING CONVICTION: ${laneSummary.swing} CANDIDATE(S) STAGED | RISK GUARD: ATR ACTIVE`,
            tone: 'Swing-horizon candidates are leading the desk with the highest conviction concentration.',
            accentClass: 'text-amber-100',
            haloClass: 'from-amber-200/20 via-cyan-300/10 to-transparent',
            horizonBadge: `SWING HORIZON LEAD (${laneSummary.swing} SETUPS • 5-20 DAYS)`,
            riskGuardLabel: 'ATR Trailing Stop Active • Kelly Cap 2.5%',
        };
    }

    if (laneSummary.intraday > laneSummary.swing && laneSummary.intraday >= laneSummary.position) {
        return {
            title: 'Intraday Opportunity Dense',
            technicalSubTitle: `INTRADAY DENSITY: ${laneSummary.intraday} CANDIDATE(S) STAGED | TACTICAL 1-3 DAY`,
            tone: 'Intraday-horizon opportunity is concentrated in the active dispatch queue.',
            accentClass: 'text-cyan-100',
            haloClass: 'from-cyan-300/20 via-amber-200/10 to-transparent',
            horizonBadge: `INTRADAY DENSE (${laneSummary.intraday} SETUPS • 1-3 DAYS)`,
            riskGuardLabel: 'Tight Stop Guard Active',
        };
    }

    return {
        title: 'Position Conviction Leading',
        technicalSubTitle: `POSITION CONVICTION: ${laneSummary.position} CANDIDATE(S) STAGED | MACRO ACCUMULATION`,
        tone: 'Position-horizon conviction is setting the cadence for the next dispatch decision.',
        accentClass: 'text-emerald-100',
        haloClass: 'from-emerald-300/20 via-amber-200/10 to-transparent',
        horizonBadge: `POSITION LEAD (${laneSummary.position} SETUPS • MULTI-WEEK)`,
        riskGuardLabel: 'Macro Trend Guard Active',
    };
}

function getTempleDirective(totalCandidates: number, autopilotArmed: boolean, failedDeliveryCount: number) {
    if (failedDeliveryCount > 0) {
        return 'Resolve Failed Dispatches';
    }

    if (autopilotArmed && totalCandidates > 0) {
        return 'Autonomous Mode Active';
    }

    if (totalCandidates > 0) {
        return 'Dispatch Candidates';
    }

    return 'Review Pipeline';
}

export function HomeShell({
    children,
    dataSource,
    error,
    deskMode,
    autopilotArmed,
    failedDeliveryCount,
    laneSummary,
    publishReadinessLabel,
    initializeLoading,
    marketStatus,
    metrics,
    health,
    isSourceLoading,
    focusMode,
    onSetFocusMode,
    onInitializeRun,
}: HomeShellProps) {
    const openSystemCheck = () => {
        if (typeof window === 'undefined') {
            return;
        }

        window.dispatchEvent(new Event(OPEN_SYSTEM_BOOT_EVENT));
    };

    const totalCandidates = laneSummary.intraday + laneSummary.swing + laneSummary.position;
    const templePosture = getTemplePosture(laneSummary, failedDeliveryCount);
    const templeDirective = getTempleDirective(totalCandidates, autopilotArmed, failedDeliveryCount);

    return (
        <div className="page-shell page-shell-wide stagger-in flex flex-col gap-8 text-white/90 xl:gap-10">
            <div className="relative overflow-hidden rounded-[1.75rem] border border-white/8 bg-[linear-gradient(180deg,rgba(20,16,10,0.98),rgba(8,10,14,0.98))] px-5 py-5 shadow-[0_32px_120px_rgba(2,6,23,0.34)] md:px-6 md:py-6 xl:px-7 xl:py-7">
                <div className={clsx(
                    'pointer-events-none absolute inset-x-[10%] top-[-10rem] h-[28rem] rounded-full bg-gradient-to-b blur-3xl',
                    templePosture.haloClass
                )} />
                <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(245,158,11,0.08),transparent_40%),linear-gradient(135deg,rgba(251,191,36,0.04),transparent_28%),linear-gradient(transparent_95%,rgba(255,255,255,0.03)_96%,transparent_97%)]" />
                <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-amber-200/20 to-transparent" />

                <div className="relative grid gap-5 xl:grid-cols-[minmax(0,1.3fr)_minmax(21rem,0.7fr)]">
                    <div className="min-w-0 rounded-[1.55rem] border border-amber-200/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.02))] p-5 md:p-6 xl:p-7">
                        <div className="flex flex-wrap items-start justify-between gap-5">
                            <div className="flex min-w-0 items-start gap-4">
                                <div className="relative mt-1 h-14 w-14 shrink-0 md:h-15 md:w-15">
                                    <div className="absolute inset-0 rounded-full bg-amber-200/15" />
                                    <div className="absolute -inset-1 rounded-full border border-amber-200/20" />
                                    <Image
                                        src="/android-chrome-192x192.png"
                                        alt="Horus Logo"
                                        width={56}
                                        height={58}
                                        className="relative h-auto w-full object-contain horus-logo-float"
                                        style={{ height: 'auto' }}
                                    />
                                </div>
                                <div className="min-w-0">
                                    <div className="text-[10px] font-black uppercase tracking-[0.42em] text-amber-200/70">
                                        Horus Analytics
                                    </div>
                                    <h1 className="mt-3 max-w-3xl text-[clamp(2.35rem,5vw,4.6rem)] font-heading font-black uppercase leading-[0.92] tracking-[0.07em] text-white">
                                        {templePosture.title}
                                    </h1>
                                    <div className="mt-2 text-[11px] font-mono font-bold tracking-[0.18em] text-amber-200/90">
                                        {templePosture.technicalSubTitle}
                                    </div>
                                    <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-300/90 md:text-[15px]">
                                        {templePosture.tone}
                                    </p>

                                    {/* Conviction & Risk Telemetry Box */}
                                    <div className="mt-4 inline-flex flex-wrap items-center gap-3 rounded-[1rem] border border-amber-300/20 bg-black/40 px-3.5 py-2 font-mono text-xs">
                                        <span className="rounded-full border border-amber-300/20 bg-amber-400/10 px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-amber-200">
                                            {templePosture.horizonBadge}
                                        </span>
                                        <span className="text-[10px] text-stone-300">
                                            Risk Telemetry: <strong className="text-emerald-300">{templePosture.riskGuardLabel}</strong>
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex flex-wrap items-center gap-2">
                                <div
                                    className={clsx(
                                        'rounded-full border px-4 py-1.5 text-[9px] font-black uppercase tracking-[0.3em]',
                                        dataSource === 'LIVE'
                                            ? 'border-emerald-400/30 bg-emerald-500/10 text-emerald-200'
                                            : dataSource === 'FALLBACK'
                                                ? 'border-amber-300/30 bg-amber-500/10 text-amber-100'
                                                : 'border-cyan-300/30 bg-cyan-500/10 text-cyan-100',
                                    )}
                                >
                                    {dataSource === 'LIVE' ? 'System Online' : dataSource === 'FALLBACK' ? 'Archive Mode' : 'Synchronizing'}
                                </div>
                                <div
                                    className={clsx(
                                        'rounded-full border px-4 py-1.5 text-[9px] font-black uppercase tracking-[0.3em]',
                                        isSourceLoading
                                            ? 'border-amber-400/30 bg-amber-500/10 text-amber-200'
                                            : error
                                                ? 'border-rose-400/30 bg-rose-500/10 text-rose-200'
                                                : 'border-cyan-400/30 bg-cyan-500/10 text-cyan-200'
                                    )}
                                >
                                    DATA STREAM: {isSourceLoading ? 'SYNCING' : error ? 'DEGRADED' : 'ONLINE / FRESH'}
                                </div>
                                <span className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-1.5 text-[9px] font-black uppercase tracking-[0.3em] text-stone-300">
                                    {deskMode === 'AI_ASSIST' ? 'AI Assist' : deskMode}
                                </span>
                            </div>
                        </div>

                        <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
                            <div className="rounded-[1.35rem] border border-white/8 bg-black/20 px-4 py-4 md:px-5 md:py-5">
                                <div className="flex flex-wrap items-center justify-between gap-3">
                                    <div>
                                        <div className="text-[10px] font-black uppercase tracking-[0.32em] text-slate-500">
                                            Command Desk
                                        </div>
                                        <div className={clsx('mt-2 text-xl font-black uppercase tracking-[0.16em]', templePosture.accentClass)}>
                                            {templeDirective}
                                        </div>
                                    </div>
                                    <span className={clsx(
                                        'rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-[0.24em]',
                                        autopilotArmed ? 'bg-amber-500/10 text-amber-100' : 'bg-white/[0.05] text-stone-300'
                                    )}>
                                        {autopilotArmed ? 'Autonomous Armed' : 'Operator Hold'}
                                    </span>
                                </div>
                                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                                    <div>
                                        <div className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Qualified Signals</div>
                                        <div className="mt-2 text-3xl font-black text-white">{totalCandidates}</div>
                                    </div>
                                    <div>
                                        <div className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Dispatch Readiness</div>
                                        <div className="mt-2 text-sm font-semibold text-stone-200">{publishReadinessLabel}</div>
                                    </div>
                                    <div>
                                        <div className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Delivery Status</div>
                                        <div className="mt-2 text-sm font-semibold text-stone-200">
                                            {failedDeliveryCount > 0 ? `${failedDeliveryCount} dispatch failure${failedDeliveryCount === 1 ? '' : 's'}` : 'Dispatch pipeline clear'}
                                        </div>
                                    </div>
                                </div>
                                <div className="mt-4 flex flex-wrap items-center gap-2">
                                    <span className="rounded-full border border-amber-200/15 bg-amber-300/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.22em] text-amber-100">
                                        Intraday {laneSummary.intraday}
                                    </span>
                                    <span className="rounded-full border border-cyan-200/15 bg-cyan-300/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.22em] text-cyan-100">
                                        Swing {laneSummary.swing}
                                    </span>
                                    <span className="rounded-full border border-emerald-200/15 bg-emerald-300/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.22em] text-emerald-100">
                                        Position {laneSummary.position}
                                    </span>
                                </div>
                            </div>

                            <div className="grid gap-3">
                                <div className="rounded-[1.25rem] border border-white/8 bg-white/[0.03] p-4">
                                    <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Desk Controls</div>
                                    <div className="mt-4 flex items-center gap-2 rounded-[1rem] border border-white/10 bg-white/[0.03] p-1">
                                        <InfoTooltip content="Full Dashboard · All Telemetry Channels">
                                            <button
                                                onClick={() => onSetFocusMode('FULL')}
                                                className={clsx(
                                                    'p-2 transition-all transition-colors',
                                                    focusMode === 'FULL' ? 'bg-primary text-primary-foreground' : 'text-slate-500 hover:text-white'
                                                )}
                                            >
                                                <LayoutGrid size={16} />
                                            </button>
                                        </InfoTooltip>
                                        <InfoTooltip content="Equity Focus · Minimize Subsidiary Feeds">
                                            <button
                                                onClick={() => onSetFocusMode('CHART')}
                                                className={clsx(
                                                    'p-2 transition-all transition-colors',
                                                    focusMode === 'CHART' ? 'bg-primary text-primary-foreground' : 'text-slate-500 hover:text-white'
                                                )}
                                            >
                                                <LineChart size={16} />
                                            </button>
                                        </InfoTooltip>
                                        <InfoTooltip content="Signal Feed Focus · Minimize Analytical Panels">
                                            <button
                                                onClick={() => onSetFocusMode('FEED')}
                                                className={clsx(
                                                    'p-2 transition-all transition-colors',
                                                    focusMode === 'FEED' ? 'bg-primary text-primary-foreground' : 'text-slate-500 hover:text-white'
                                                )}
                                            >
                                                <Zap size={16} />
                                            </button>
                                        </InfoTooltip>
                                    </div>
                                    <div className="mt-4">{marketStatus}</div>
                                </div>
                                <div className="grid gap-3 sm:grid-cols-2">
                                    <button
                                        type="button"
                                        onClick={openSystemCheck}
                                        className="rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-5 py-4 text-left text-[10px] font-black uppercase tracking-[0.3em] text-slate-300 transition hover:border-primary/30 hover:bg-primary/10 hover:text-white"
                                    >
                                        <div className="text-slate-500">Diagnostics</div>
                                        <div className="mt-2 text-white">System Check</div>
                                    </button>
                                    <button
                                        disabled={initializeLoading}
                                        onClick={onInitializeRun}
                                        className="group relative overflow-hidden rounded-[1.2rem] border border-amber-300/25 bg-[linear-gradient(135deg,rgba(251,191,36,0.18),rgba(120,53,15,0.18))] px-5 py-4 text-left text-[10px] font-black uppercase tracking-[0.3em] text-amber-50 transition hover:scale-[1.01] active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-70"
                                    >
                                        <div className="absolute inset-0 translate-x-[-100%] bg-white/15 transition-transform duration-700 group-hover:translate-x-[100%] pointer-events-none" />
                                        <div className="relative flex items-center gap-2 text-amber-100/80">
                                            <Activity className="h-4 w-4" />
                                            Execute
                                        </div>
                                        <div className="relative mt-2 text-white">Initialize Pipeline</div>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="grid gap-4">
                        <div className="rounded-[1.35rem] border border-white/8 bg-white/[0.03] p-4 md:p-5">
                            <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Dispatch Readiness</div>
                            <div className="mt-3 text-2xl font-black text-white">{publishReadinessLabel}</div>
                            <div className="mt-2 text-sm text-stone-300/80">
                                {autopilotArmed ? 'Autonomous dispatch enabled under current operating policy.' : 'Manual operator approval required before dispatch.'}
                            </div>
                        </div>
                        <div className="rounded-[1.35rem] border border-white/8 bg-white/[0.03] p-4 md:p-5">
                            <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Horizon Distribution</div>
                            <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                                <div>
                                    <div className="text-[10px] font-black uppercase tracking-[0.22em] text-amber-300">Intraday</div>
                                    <div className="mt-2 text-3xl font-black text-white">{laneSummary.intraday}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] font-black uppercase tracking-[0.22em] text-cyan-300">Swing</div>
                                    <div className="mt-2 text-3xl font-black text-white">{laneSummary.swing}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] font-black uppercase tracking-[0.22em] text-emerald-300">Position</div>
                                    <div className="mt-2 text-3xl font-black text-white">{laneSummary.position}</div>
                                </div>
                            </div>
                        </div>
                        <HomeMetricsBar
                            metrics={metrics}
                            health={health}
                            isSourceLoading={isSourceLoading}
                        />
                    </div>
                </div>
            </div>

            {error && (
                <div className="bg-[#0A0D14] border border-white/10 industrial-corner px-6 py-4 border-rose-500/30 text-rose-300 text-[10px] uppercase tracking-[0.3em] font-black scan-line">
                    ERROR DETECTED: {error}
                </div>
            )}

            {children}
        </div>
    );
}
