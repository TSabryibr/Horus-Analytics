'use client';

import clsx from 'clsx';

type TelegramStatusCardProps = {
    configured: boolean;
    operatingMode?: string;
    autopilotArmed?: boolean;
    autopilotStatus?: string;
    readyCount?: number;
    failedDeliveryCount?: number;
    activeLifecycleCount?: number;
    ambiguousCount?: number;
    pendingFollowUpCount?: number;
    readyFollowUpCount?: number;
    failedFollowUpCount?: number;
};

export function TelegramStatusCard({
    configured,
    operatingMode,
    autopilotArmed,
    autopilotStatus,
    readyCount = 0,
    failedDeliveryCount = 0,
    activeLifecycleCount = 0,
    ambiguousCount = 0,
    pendingFollowUpCount = 0,
    readyFollowUpCount = 0,
    failedFollowUpCount = 0,
}: TelegramStatusCardProps) {
    return (
        <div
            className={clsx(
                'flex flex-wrap items-center gap-2.5 rounded-[1.2rem] border px-3 py-2.5 transition-all',
                configured
                    ? 'border-emerald-500/20 bg-[linear-gradient(135deg,rgba(16,185,129,0.12),rgba(255,255,255,0.02))]'
                    : 'border-rose-500/20 bg-[linear-gradient(135deg,rgba(244,63,94,0.12),rgba(255,255,255,0.02))]',
            )}
        >
            <div className="flex items-center gap-2.5 rounded-full border border-white/8 bg-black/20 px-3 py-1.5">
                <span className="relative flex h-2 w-2">
                    {configured ? <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" /> : null}
                    <span className={clsx('relative inline-flex h-2 w-2 rounded-full', configured ? 'bg-emerald-500' : 'bg-rose-500')} />
                </span>
                <span className={clsx('text-[10px] font-black uppercase tracking-[0.26em]', configured ? 'text-emerald-300' : 'text-rose-300')}>
                    {configured ? 'CHANNEL ONLINE' : 'OFFLINE'}
                </span>
            </div>

            {operatingMode ? (
                <span className="rounded-full border border-white/10 bg-black/20 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.22em] text-slate-200">
                    {operatingMode}
                </span>
            ) : null}

            <span className="rounded-full border border-white/8 bg-black/20 px-2.5 py-1 text-[9px] font-mono uppercase tracking-[0.18em] text-slate-300">
                {readyCount} ready
            </span>
            <span className="rounded-full border border-white/8 bg-black/20 px-2.5 py-1 text-[9px] font-mono uppercase tracking-[0.18em] text-slate-300">
                {activeLifecycleCount} active
            </span>
            <span className="rounded-full border border-white/8 bg-black/20 px-2.5 py-1 text-[9px] font-mono uppercase tracking-[0.18em] text-slate-300">
                {pendingFollowUpCount + readyFollowUpCount} queued updates
            </span>

            {autopilotArmed ? (
                <span className="rounded-full border border-amber-400/20 bg-amber-500/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.2em] text-amber-200">
                    Autopilot Armed
                </span>
            ) : null}
            {autopilotStatus ? (
                <span className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.2em] text-cyan-200">
                    Auto {autopilotStatus}
                </span>
            ) : null}
            {failedDeliveryCount > 0 ? (
                <span className="rounded-full border border-rose-400/20 bg-rose-500/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.2em] text-rose-200">
                    {failedDeliveryCount} Retry Needed
                </span>
            ) : null}
            {failedFollowUpCount > 0 ? (
                <span className="rounded-full border border-rose-400/20 bg-rose-500/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.2em] text-rose-200">
                    {failedFollowUpCount} Update Failed
                </span>
            ) : null}
            {ambiguousCount > 0 ? (
                <span className="rounded-full border border-amber-400/20 bg-amber-500/10 px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.2em] text-amber-200">
                    {ambiguousCount} Ambiguous
                </span>
            ) : null}
        </div>
    );
}
