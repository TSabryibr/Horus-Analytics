'use client';

import { useState } from 'react';
import clsx from 'clsx';
import { Crown, ScrollText, ShieldCheck, Sparkles } from 'lucide-react';

import { getApiBase } from '@/lib/api';
import { TelegramActivityLog } from './components/TelegramActivityLog';
import { TelegramBroadcastPanel } from './components/TelegramBroadcastPanel';
import { TelegramConfigModal } from './components/TelegramConfigModal';
import { TelegramFollowUpsPanel } from './components/TelegramFollowUpsPanel';
import { TelegramSignalPanel } from './components/TelegramSignalPanel';
import { TelegramShell } from './components/TelegramShell';
import { TelegramStatusCard } from './components/TelegramStatusCard';
import { useTelegramBroadcasts } from './hooks/useTelegramBroadcasts';
import { useTelegramConfig } from './hooks/useTelegramConfig';
import { useTelegramRuntime } from './hooks/useTelegramRuntime';
import { useSignalDeskData } from '../context/GlobalDataContext';

function getReleasePosture({
    readyCount,
    failedDeliveryCount,
    readyFollowUpCount,
    pendingFollowUpCount,
    activeRunId,
    autopilotReady,
    isAuthorityHeld,
}: {
    readyCount: number;
    failedDeliveryCount: number;
    readyFollowUpCount: number;
    pendingFollowUpCount: number;
    activeRunId: number | null;
    autopilotReady: boolean;
    isAuthorityHeld?: boolean;
}) {
    if (isAuthorityHeld) {
        return {
            title: 'Authority Suspended',
            technicalSubTitle: 'EMERGENCY HOLD: OPERATOR RELEASE FREEZE ACTIVE',
            tone: 'Outbound signal dispatches have been manually paused by operator decree.',
            accentClass: 'text-rose-200',
        };
    }

    if (failedDeliveryCount > 0) {
        return {
            title: 'Recovery Decree',
            technicalSubTitle: `TECHNICAL ALERT: ${failedDeliveryCount} FAILED DELIVERIES — PIPELINE BLOCKED`,
            tone: 'Failed outbound items need intervention before the next clean release window.',
            accentClass: 'text-rose-100',
        };
    }

    if (readyFollowUpCount > 0 || pendingFollowUpCount > 0) {
        return {
            title: 'Follow-Up Pressure',
            technicalSubTitle: `LIFECYCLE QUEUE: ${readyFollowUpCount} READY / ${pendingFollowUpCount} PENDING UPDATES`,
            tone: 'Lifecycle updates are waiting in the chamber and should be governed before the next issue cycle.',
            accentClass: 'text-amber-100',
        };
    }

    if (autopilotReady && activeRunId) {
        return {
            title: 'Autopilot Authorized',
            technicalSubTitle: `AUTOPILOT ARMED: RUN #${activeRunId} DISPATCH AUTHORIZED`,
            tone: 'Horus can issue from the active desk run under the current release policy.',
            accentClass: 'text-amber-100',
        };
    }

    if (activeRunId && readyCount > 0) {
        return {
            title: 'Release Window Open',
            technicalSubTitle: `STAGE READY: RUN #${activeRunId} POSITIONED (${readyCount} SIGNALS)`,
            tone: 'The active desk run is staged for outbound issue and awaiting final chamber action.',
            accentClass: 'text-amber-100',
        };
    }

    return {
        title: 'Authority Held',
        technicalSubTitle: 'STANDBY: NO QUALIFIED RELEASE STAGED (PIPE ONLINE)',
        tone: 'The chamber is standing by with no qualified release yet authorized for issue.',
        accentClass: 'text-stone-100',
    };
}

function getPrimaryActionLabel({
    failedDeliveryCount,
    readyFollowUpCount,
    autopilotReady,
    activeRunId,
    isAuthorityHeld,
}: {
    failedDeliveryCount: number;
    readyFollowUpCount: number;
    autopilotReady: boolean;
    activeRunId: number | null;
    isAuthorityHeld?: boolean;
}) {
    if (isAuthorityHeld) {
        return 'Authority Suspended (Hold Active)';
    }

    if (failedDeliveryCount > 0) {
        return 'Retry Failed Deliveries';
    }

    if (readyFollowUpCount > 0) {
        return 'Process Ready Follow-Ups';
    }

    if (autopilotReady && activeRunId) {
        return 'Run Autopilot Dispatch';
    }

    if (activeRunId) {
        return 'Dispatch Latest Run';
    }

    return 'Authority Held';
}

export default function TelegramPage() {
    const API_BASE = getApiBase();
    const [isAuthorityHeld, setIsAuthorityHeldState] = useState(() => {
        if (typeof window !== 'undefined') {
            return window.sessionStorage.getItem('horus_telegram_authority_held') === 'true';
        }
        return false;
    });

    const setIsAuthorityHeld = (val: boolean | ((prev: boolean) => boolean)) => {
        setIsAuthorityHeldState((prev) => {
            const next = typeof val === 'function' ? val(prev) : val;
            if (typeof window !== 'undefined') {
                window.sessionStorage.setItem('horus_telegram_authority_held', String(next));
            }
            return next;
        });
    };
    const {
        desk,
        lifecycleSummary,
        followUpSummary,
        followUpRecords,
        followUpLoading,
        runAutopilot,
        processFollowUps,
        actOnFollowUp,
    } = useSignalDeskData();
    const {
        config,
        sending,
        setSending,
        log,
        addToLog,
        clearLog,
        isConfigModalOpen,
        openConfigModal,
        closeConfigModal,
        buildHeaders,
        refreshConfig,
        logEndRef,
    } = useTelegramRuntime();
    const {
        message,
        setMessage,
        image,
        setImage,
        signalForm,
        setSignalForm,
        handleDeskRelease,
        handleRetryFailedDeliveries,
        handleBroadcast,
        handleSignalBroadcast,
        handleAiDailyReportBroadcast,
        handleAnalysisReportBroadcast,
        triggerScan,
    } = useTelegramBroadcasts({
        apiBase: API_BASE,
        buildHeaders,
        addToLog,
        setSending,
        activeRunId: Number((desk?.active_run as any)?.id || 0) || null,
        failedDeliveryCount: Number(desk?.failed_delivery_count ?? 0),
    });
    const { configForm, setConfigForm, hydrateConfigForm, handleUpdateConfig } = useTelegramConfig({
        apiBase: API_BASE,
        buildHeaders,
        addToLog,
        setSending,
        closeConfigModal,
        refreshConfig,
    });

    const readyCount = (desk?.lanes?.intraday?.count ?? 0) + (desk?.lanes?.swing?.count ?? 0) + (desk?.lanes?.position?.count ?? 0);
    const activeRunId = Number((desk?.active_run as any)?.id || 0) || null;
    const autopilotStatus = desk?.autopilot?.status;
    const autopilotReady = desk?.operating_mode === 'AUTOPILOT' && Boolean(desk?.autopilot_armed);
    const failedDeliveryCount = Number(desk?.failed_delivery_count ?? 0);
    const activeLifecycleCount = Number(lifecycleSummary?.active_count ?? 0);
    const ambiguousCount = Number(lifecycleSummary?.ambiguous_count ?? 0);
    const pendingFollowUpCount = Number(followUpSummary?.pending_count ?? 0);
    const readyFollowUpCount = Number(followUpSummary?.ready_count ?? 0);
    const failedFollowUpCount = Number(followUpSummary?.failed_count ?? 0);
    const releasePosture = getReleasePosture({
        readyCount,
        failedDeliveryCount,
        readyFollowUpCount,
        pendingFollowUpCount,
        activeRunId,
        autopilotReady,
        isAuthorityHeld,
    });
    const primaryActionLabel = getPrimaryActionLabel({
        failedDeliveryCount,
        readyFollowUpCount,
        autopilotReady,
        activeRunId,
        isAuthorityHeld,
    });

    const handleAutopilotDispatch = async () => {
        if (isAuthorityHeld) return;
        setSending(true);
        addToLog('Evaluating desk policy and running Horus autopilot...');
        try {
            const completed = await runAutopilot();
            addToLog(completed ? 'Horus autopilot completed Telegram dispatch.' : 'Horus autopilot stopped before dispatch or failed policy checks.');
        } finally {
            setSending(false);
        }
    };

    const handleProcessFollowUpQueue = async () => {
        if (isAuthorityHeld) return;
        setSending(true);
        addToLog('Processing ready lifecycle follow-up updates...');
        try {
            const ok = await processFollowUps();
            addToLog(ok ? 'Lifecycle follow-up queue processed.' : 'Lifecycle follow-up queue processing failed.');
        } finally {
            setSending(false);
        }
    };

    const handleFollowUpAction = async (
        followUpId: number,
        action: 'SEND_NOW' | 'RETRY' | 'SUPPRESS' | 'RESEND',
        reason?: string,
    ) => {
        setSending(true);
        addToLog(`Executing follow-up action ${action} on queue item ${followUpId}...`);
        try {
            const ok = await actOnFollowUp(followUpId, action, reason);
            addToLog(ok ? `Follow-up action ${action} completed.` : `Follow-up action ${action} failed.`);
        } finally {
            setSending(false);
        }
    };

    const handlePrimaryReleaseAction = async () => {
        if (isAuthorityHeld) return;
        if (failedDeliveryCount > 0) {
            await handleRetryFailedDeliveries();
            return;
        }

        if (readyFollowUpCount > 0) {
            await handleProcessFollowUpQueue();
            return;
        }

        if (autopilotReady && activeRunId) {
            await handleAutopilotDispatch();
            return;
        }

        if (activeRunId) {
            await handleDeskRelease();
        }
    };

    const getPayloadPreview = () => {
        if (isAuthorityHeld) {
            return {
                label: 'AUTHORITY FREEZE',
                badge: 'HOLD ACTIVE',
                content: '[PAUSED] Outbound dispatches are currently frozen by operator emergency hold.',
            };
        }
        if (failedDeliveryCount > 0) {
            return {
                label: 'RECOVERY RETRY PAYLOAD',
                badge: 'RECOVERY BLOCK',
                content: `[RETRY QUEUE] Prepared to re-dispatch ${failedDeliveryCount} failed message(s) through Telegram pipe.`,
            };
        }
        if (readyFollowUpCount > 0) {
            const topFollowUp = followUpRecords[0];
            return {
                label: 'LIFECYCLE UPDATE PAYLOAD',
                badge: 'FOLLOW-UP QUEUE',
                content: topFollowUp
                    ? `[UPDATE] Ticker ${topFollowUp.ticker || 'POSITION'} (${topFollowUp.lane || 'Swing'}) -> Event: ${topFollowUp.trigger_state || 'UPDATE'}`
                    : `[UPDATE] ${readyFollowUpCount} lifecycle update(s) prepared for dispatch.`,
            };
        }
        if (activeRunId) {
            return {
                label: 'DESK RUN DISPATCH PAYLOAD',
                badge: 'SIGNAL DISPATCH',
                content: `[DESK RUN #${activeRunId}] Staged Candidates: ${readyCount} total (${desk?.lanes?.intraday?.count ?? 0} Intraday, ${desk?.lanes?.swing?.count ?? 0} Swing, ${desk?.lanes?.position?.count ?? 0} Position)`,
            };
        }
        if (message) {
            return {
                label: 'CUSTOM BROADCAST DRAFT',
                badge: 'MANUAL BROADCAST',
                content: `[BROADCAST] "${message.substring(0, 140)}${message.length > 140 ? '...' : ''}"`,
            };
        }
        return {
            label: 'OUTBOUND PIPE STANDBY',
            badge: 'STANDBY MODE',
            content: '[STANDBY] No outbound signal payload currently staged for release.',
        };
    };

    const payloadPreview = getPayloadPreview();

    return (
        <TelegramShell
            onOpenConfig={() => {
                hydrateConfigForm(config);
                openConfigModal();
            }}
            statusNode={
                <TelegramStatusCard
                    configured={Boolean(config?.configured)}
                    operatingMode={desk?.operating_mode}
                    autopilotArmed={Boolean(desk?.autopilot_armed)}
                    autopilotStatus={autopilotStatus}
                    readyCount={readyCount}
                    failedDeliveryCount={failedDeliveryCount}
                    activeLifecycleCount={activeLifecycleCount}
                    ambiguousCount={ambiguousCount}
                    pendingFollowUpCount={pendingFollowUpCount}
                    readyFollowUpCount={readyFollowUpCount}
                    failedFollowUpCount={failedFollowUpCount}
                />
            }
        >
            <section className="relative overflow-hidden rounded-[1.85rem] border border-white/8 bg-[linear-gradient(180deg,rgba(26,20,10,0.96),rgba(8,10,14,0.98))] px-5 py-5 shadow-[0_28px_110px_rgba(2,6,23,0.3)] md:px-6 md:py-6 xl:px-7 xl:py-7">
                <div className="pointer-events-none absolute inset-x-[18%] top-[-8rem] h-[22rem] rounded-full bg-[radial-gradient(circle,rgba(251,191,36,0.18),transparent_60%)] blur-3xl" />
                <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(135deg,rgba(251,191,36,0.05),transparent_28%),radial-gradient(circle_at_top_right,rgba(245,158,11,0.08),transparent_24%)]" />

                <div className="relative grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(22rem,0.85fr)]">
                    <div className="min-w-0 rounded-[1.55rem] border border-amber-200/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.02))] p-5 md:p-6">
                        <div className="flex flex-wrap items-start justify-between gap-5">
                            <div className="min-w-0 max-w-3xl">
                                <div className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.36em] text-amber-200/70">
                                    <span className="inline-flex h-10 w-10 items-center justify-center rounded-[1rem] border border-amber-200/20 bg-amber-300/10 text-amber-100">
                                        <Crown className="h-4 w-4" />
                                    </span>
                                    Release Throne
                                </div>
                                <h2 className={clsx('mt-4 font-heading text-[clamp(2.2rem,4.5vw,4.4rem)] font-black uppercase tracking-[0.08em]', releasePosture.accentClass)}>
                                    {releasePosture.title}
                                </h2>
                                <div className="mt-2 text-[11px] font-mono font-bold tracking-[0.18em] text-amber-200/90">
                                    {releasePosture.technicalSubTitle}
                                </div>
                                <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-300/85 md:text-[15px]">
                                    {releasePosture.tone}
                                </p>
                            </div>

                            <div className="flex flex-wrap items-center gap-2">
                                <button
                                    type="button"
                                    onClick={() => setIsAuthorityHeld(!isAuthorityHeld)}
                                    className={clsx(
                                        'rounded-full border px-4 py-1.5 text-[9px] font-black uppercase tracking-[0.3em] transition-all',
                                        isAuthorityHeld
                                            ? 'border-rose-400/40 bg-rose-500/20 text-rose-200 hover:bg-rose-500/30'
                                            : 'border-white/10 bg-white/[0.04] text-stone-300 hover:border-amber-300/30 hover:text-amber-200',
                                    )}
                                >
                                    {isAuthorityHeld ? 'Unfreeze Release' : 'Emergency Hold'}
                                </button>

                                <span className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-1.5 text-[9px] font-black uppercase tracking-[0.3em] text-stone-300">
                                    {desk?.operating_mode === 'AI_ASSIST' ? 'AI Assist' : desk?.operating_mode ?? 'Manual'}
                                </span>
                                <span className={clsx(
                                    'rounded-full border px-4 py-1.5 text-[9px] font-black uppercase tracking-[0.3em]',
                                    Boolean(config?.configured)
                                        ? 'border-emerald-400/25 bg-emerald-500/10 text-emerald-200'
                                        : 'border-rose-400/25 bg-rose-500/10 text-rose-200',
                                )}>
                                    {config?.configured ? 'Channel Online' : 'Channel Offline'}
                                </span>
                            </div>
                        </div>

                        {/* Live Outbound Payload Preview Box */}
                        <div className="mt-5 rounded-[1.35rem] border border-amber-300/20 bg-black/40 p-4">
                            <div className="flex items-center justify-between gap-3">
                                <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.28em] text-amber-200/80">
                                    <Sparkles className="h-3.5 w-3.5 text-amber-300" />
                                    Outbound Payload Preview
                                </div>
                                <span className="rounded-full border border-amber-300/20 bg-amber-400/10 px-2.5 py-0.5 text-[9px] font-mono font-bold uppercase tracking-wider text-amber-200">
                                    {payloadPreview.badge}
                                </span>
                            </div>
                            <div className="mt-2 font-mono text-xs text-amber-100/90 leading-relaxed bg-black/30 p-3 rounded-[0.85rem] border border-white/5">
                                {payloadPreview.content}
                            </div>
                            <div className="mt-2 flex flex-wrap items-center justify-between text-[9px] font-mono text-stone-400">
                                <span>Target: {config?.chat_id ? `Channel (${config.chat_id})` : 'Not set'}</span>
                                <span>Format: MarkdownV2 • Rate Limit: Safe</span>
                            </div>
                        </div>

                        <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)]">
                            <div className="rounded-[1.35rem] border border-white/8 bg-black/20 px-4 py-4 md:px-5 md:py-5">
                                <div className="flex flex-wrap items-center justify-between gap-3">
                                    <div>
                                        <div className="text-[10px] font-black uppercase tracking-[0.32em] text-slate-500">
                                            Chamber Authority
                                        </div>
                                        <div className="mt-2 text-xl font-black uppercase tracking-[0.14em] text-white">
                                            {primaryActionLabel}
                                        </div>
                                    </div>
                                    <span className={clsx(
                                        'rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-[0.24em]',
                                        isAuthorityHeld
                                            ? 'bg-rose-500/20 text-rose-200 border border-rose-500/30'
                                            : autopilotReady
                                                ? 'bg-amber-500/10 text-amber-100'
                                                : 'bg-white/[0.05] text-stone-300',
                                    )}>
                                        {isAuthorityHeld ? 'Authority Frozen' : autopilotReady ? 'Autopilot Clear' : 'Operator Gate'}
                                    </span>
                                </div>

                                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                                    <div>
                                        <div className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Desk Ready</div>
                                        <div className="mt-2 text-3xl font-black text-white">{readyCount}</div>
                                    </div>
                                    <div>
                                        <div className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Active Run</div>
                                        <div className="mt-2 text-sm font-semibold text-stone-200">{activeRunId ? `Run #${activeRunId}` : 'No active run'}</div>
                                    </div>
                                    <div>
                                        <div className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Queue Pressure</div>
                                        <div className="mt-2 text-sm font-semibold text-stone-200">
                                            {failedDeliveryCount > 0
                                                ? `${failedDeliveryCount} delivery blockers`
                                                : readyFollowUpCount > 0
                                                    ? `${readyFollowUpCount} updates ready`
                                                    : 'Outbound clear'}
                                        </div>
                                    </div>
                                </div>

                                <div className="mt-4 flex flex-wrap items-center gap-2">
                                    <span className="rounded-full border border-amber-200/15 bg-amber-300/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.22em] text-amber-100">
                                        Intraday {desk?.lanes?.intraday?.count ?? 0}
                                    </span>
                                    <span className="rounded-full border border-cyan-200/15 bg-cyan-300/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.22em] text-cyan-100">
                                        Swing {desk?.lanes?.swing?.count ?? 0}
                                    </span>
                                    <span className="rounded-full border border-emerald-200/15 bg-emerald-300/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.22em] text-emerald-100">
                                        Position {desk?.lanes?.position?.count ?? 0}
                                    </span>
                                </div>
                            </div>

                            <div className="grid gap-3">
                                <div className="rounded-[1.25rem] border border-white/8 bg-white/[0.03] p-4">
                                    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
                                        <ShieldCheck className="h-3.5 w-3.5 text-amber-200/70" />
                                        Authority State
                                    </div>
                                    <div className="mt-3 space-y-3 text-sm text-slate-300">
                                        <div className="flex items-center justify-between rounded-[1rem] border border-white/8 bg-black/20 px-3 py-2.5">
                                            <span>Autopilot</span>
                                            <span className={clsx('font-black uppercase tracking-[0.12em]', autopilotReady ? 'text-amber-200' : 'text-slate-400')}>
                                                {autopilotReady ? 'Authorized' : 'Held'}
                                            </span>
                                        </div>
                                        <div className="flex items-center justify-between rounded-[1rem] border border-white/8 bg-black/20 px-3 py-2.5">
                                            <span>Lifecycle</span>
                                            <span className="font-black text-cyan-200">{activeLifecycleCount} active</span>
                                        </div>
                                        <div className="flex items-center justify-between rounded-[1rem] border border-white/8 bg-black/20 px-3 py-2.5">
                                            <span>Ambiguous</span>
                                            <span className={clsx('font-black', ambiguousCount > 0 ? 'text-amber-200' : 'text-slate-300')}>
                                                {ambiguousCount}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <div className="grid gap-3 sm:grid-cols-2">
                                    <button
                                        type="button"
                                        onClick={() => {
                                            void handlePrimaryReleaseAction();
                                        }}
                                        disabled={sending || isAuthorityHeld || (!activeRunId && readyFollowUpCount < 1 && failedDeliveryCount < 1)}
                                        className="group relative overflow-hidden rounded-[1.2rem] border border-amber-300/25 bg-[linear-gradient(135deg,rgba(251,191,36,0.18),rgba(120,53,15,0.18))] px-5 py-4 text-left text-[10px] font-black uppercase tracking-[0.3em] text-amber-50 transition hover:scale-[1.01] active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
                                    >
                                        <div className="absolute inset-0 translate-x-[-100%] bg-white/15 transition-transform duration-700 group-hover:translate-x-[100%] pointer-events-none" />
                                        <div className="relative flex items-center gap-2 text-amber-100/80">
                                            <Sparkles className="h-4 w-4" />
                                            Throne Action
                                        </div>
                                        <div className="relative mt-2 text-white">{primaryActionLabel}</div>
                                    </button>

                                    <div className="rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-5 py-4 text-left">
                                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
                                            <ScrollText className="h-4 w-4 text-amber-200/60" />
                                            Chamber Notes
                                        </div>
                                        <div className="mt-2 text-sm text-stone-300/85">
                                            {isAuthorityHeld
                                                ? 'Release freeze is active. Unfreeze to permit outbound dispatches.'
                                                : readyFollowUpCount > 0
                                                    ? 'Ready lifecycle updates are waiting in the lower chamber.'
                                                    : activeRunId
                                                        ? 'The latest desk run is positioned for outbound issue.'
                                                        : 'No active run is staged for Telegram release.'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="grid gap-4">
                        <div className="rounded-[1.35rem] border border-white/8 bg-white/[0.03] p-4 md:p-5">
                            <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Market Edge + Pipe Telemetry</div>
                            <div className="mt-3 text-2xl font-black text-white">{readyCount} issue candidates</div>
                            <div className="mt-2 space-y-2 text-xs text-stone-300/85">
                                <div className="flex items-center justify-between rounded-lg bg-black/20 px-3 py-1.5 border border-white/5 font-mono">
                                    <span>Signal Edge:</span>
                                    <span className="text-amber-200 font-bold">{activeRunId ? `Run #${activeRunId}` : 'Standby'}</span>
                                </div>
                                <div className="flex items-center justify-between rounded-lg bg-black/20 px-3 py-1.5 border border-white/5 font-mono">
                                    <span>Delivery Pipe:</span>
                                    <span className={clsx('font-bold', config?.configured ? 'text-emerald-300' : 'text-rose-300')}>
                                        {config?.configured ? 'Telegram API OK' : 'Pipe Offline'}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="rounded-[1.35rem] border border-white/8 bg-white/[0.03] p-4 md:p-5">
                            <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Follow-Up Pressure</div>
                            <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                                <div>
                                    <div className="text-[10px] font-black uppercase tracking-[0.22em] text-amber-300">Pending</div>
                                    <div className="mt-2 text-2xl font-black text-white">{pendingFollowUpCount}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] font-black uppercase tracking-[0.22em] text-cyan-300">Ready</div>
                                    <div className="mt-2 text-2xl font-black text-white">{readyFollowUpCount}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] font-black uppercase tracking-[0.22em] text-rose-300">Failed</div>
                                    <div className="mt-2 text-2xl font-black text-white">{failedFollowUpCount}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.12fr)_minmax(21rem,0.88fr)]">
                <TelegramSignalPanel
                    signalForm={signalForm}
                    sending={sending}
                    activeRunId={activeRunId}
                    autopilotReady={autopilotReady}
                    failedDeliveryCount={failedDeliveryCount}
                    setSignalForm={setSignalForm}
                    onDeskRelease={handleDeskRelease}
                    onAutopilotRun={handleAutopilotDispatch}
                    onRetryFailedDeliveries={handleRetryFailedDeliveries}
                    onSignalBroadcast={handleSignalBroadcast}
                    onAiDailyReport={handleAiDailyReportBroadcast}
                    onAnalysisReport={handleAnalysisReportBroadcast}
                    onScan={triggerScan}
                />

                <div className="grid gap-6">
                    <div className="section-surface rounded-[1.6rem] p-5">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Operator Ledger</div>
                                <div className="mt-2 text-lg font-black uppercase tracking-[0.14em] text-white">Automation Summary</div>
                            </div>
                            <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[9px] font-black uppercase tracking-[0.22em] text-stone-300">
                                {config?.configured ? 'Configured' : 'Awaiting Setup'}
                            </span>
                        </div>

                        {config ? (
                            <div className="mt-4 grid gap-3">
                                {[
                                    ['Intraday Scans', config?.auto_intraday],
                                    ['Daily Close Scans', config?.auto_daily],
                                    ['Horus Eye', config?.auto_horus_eye],
                                    ['AI Daily Dispatch', config?.auto_ai_daily_report],
                                    ['Weekly Report', config?.auto_weekly_report],
                                    ['Monthly Report', config?.auto_monthly_report],
                                ].map(([label, enabled]) => (
                                    <div key={String(label)} className="flex items-center justify-between rounded-[1rem] border border-white/8 bg-black/20 px-3 py-2.5">
                                        <span className="text-[11px] text-slate-300">{label}</span>
                                        <span className={clsx(
                                            'text-[10px] font-black uppercase tracking-[0.2em]',
                                            enabled ? 'text-emerald-300' : 'text-rose-300',
                                        )}>
                                            {enabled ? 'On' : 'Off'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="mt-4 grid gap-3">
                                <div className="h-12 rounded-[1rem] bg-white/[0.03]" />
                                <div className="h-12 rounded-[1rem] bg-white/[0.03]" />
                                <div className="h-12 rounded-[1rem] bg-white/[0.03]" />
                            </div>
                        )}
                    </div>

                    <TelegramBroadcastPanel
                        message={message}
                        image={image}
                        sending={sending}
                        setMessage={setMessage}
                        setImage={setImage}
                        onBroadcast={handleBroadcast}
                    />

                    <TelegramActivityLog log={log} onClear={clearLog} logEndRef={logEndRef} />
                </div>
            </div>

            <TelegramFollowUpsPanel
                summary={followUpSummary}
                records={followUpRecords}
                loading={followUpLoading}
                disabled={sending}
                onProcessReady={handleProcessFollowUpQueue}
                onAction={handleFollowUpAction}
            />

            <TelegramConfigModal
                isOpen={isConfigModalOpen}
                sending={sending}
                configForm={configForm}
                setConfigForm={setConfigForm}
                onClose={closeConfigModal}
                onSubmit={handleUpdateConfig}
            />
        </TelegramShell>
    );
}
