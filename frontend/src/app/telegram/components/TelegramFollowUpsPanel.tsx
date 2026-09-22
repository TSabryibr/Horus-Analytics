'use client';

import clsx from 'clsx';
import { RefreshCcw, Send, ShieldOff } from 'lucide-react';

import type { SignalFollowUpRecord, SignalFollowUpSummary } from '@/app/context/SignalFollowUpContext';

type TelegramFollowUpsPanelProps = {
    summary?: SignalFollowUpSummary | null;
    records: SignalFollowUpRecord[];
    loading: boolean;
    disabled?: boolean;
    onProcessReady: () => void | Promise<void>;
    onAction: (
        followUpId: number,
        action: 'SEND_NOW' | 'RETRY' | 'SUPPRESS' | 'RESEND',
        reason?: string,
    ) => void | Promise<void>;
};

function queueTone(queueState: string) {
    switch (String(queueState || '').toUpperCase()) {
        case 'SENT':
            return 'border-emerald-400/20 bg-emerald-500/10 text-emerald-200';
        case 'FAILED':
            return 'border-rose-400/20 bg-rose-500/10 text-rose-200';
        case 'SUPPRESSED':
            return 'border-amber-400/20 bg-amber-500/10 text-amber-200';
        case 'READY':
            return 'border-cyan-400/20 bg-cyan-500/10 text-cyan-200';
        default:
            return 'border-white/10 bg-black/20 text-slate-300';
    }
}

function summarizeDraft(draftMessage?: string | null) {
    const normalized = String(draftMessage || '').replace(/\s+/g, ' ').trim();
    if (!normalized) {
        return 'Draft will be generated from lifecycle state.';
    }
    return normalized.length > 140 ? `${normalized.slice(0, 137)}...` : normalized;
}

function queuePriority(queueState: string) {
    switch (String(queueState || '').toUpperCase()) {
        case 'FAILED':
            return 0;
        case 'READY':
            return 1;
        case 'PENDING':
            return 2;
        case 'SUPPRESSED':
            return 3;
        case 'SENT':
            return 4;
        default:
            return 5;
    }
}

function destinationLabel(record: SignalFollowUpRecord) {
    const destinationType = String(record.destination_type || 'PORTFOLIO').replace(/_/g, ' ');
    const destinationName = record.destination_name || record.portfolio_name || 'Legacy destination';
    const tier = record.service_tier ? ` / ${record.service_tier}` : '';
    return `${destinationType}: ${destinationName}${tier}`;
}

function countLabel(counts?: Record<string, number>) {
    const entries = Object.entries(counts || {}).filter(([, value]) => Number(value) > 0);
    if (!entries.length) return 'None';
    return entries
        .map(([key, value]) => `${key.replace(/_/g, ' ')} ${value}`)
        .join(' | ');
}

export function TelegramFollowUpsPanel({
    summary,
    records,
    loading,
    disabled = false,
    onProcessReady,
    onAction,
}: TelegramFollowUpsPanelProps) {
    const prioritizedRecords = [...records]
        .sort((left, right) => queuePriority(left.queue_state) - queuePriority(right.queue_state))
        .slice(0, 8);

    return (
        <div className="section-surface rounded-[1.75rem] p-5 md:p-6">
            <div className="flex flex-col gap-4 border-b border-white/8 pb-5 lg:flex-row lg:items-center lg:justify-between">
                <div>
                    <h3 className="text-[10px] font-bold uppercase tracking-[0.28em] text-slate-500">Lower Chamber</h3>
                    <div className="mt-2 font-heading text-xl font-black uppercase tracking-[0.12em] text-white">Lifecycle Follow-Ups</div>
                    <p className="mt-2 max-w-2xl text-sm text-slate-400">
                        Client-facing Horus updates queued from lifecycle milestones, with direct send, retry, suppression, and requeue control.
                    </p>
                </div>
                <button
                    type="button"
                    onClick={onProcessReady}
                    disabled={disabled || loading || Number(summary?.ready_count ?? 0) < 1}
                    className="action-secondary inline-flex items-center justify-center gap-2 px-4 py-3 text-[10px] tracking-[0.2em] disabled:opacity-50"
                >
                    <RefreshCcw className="h-3.5 w-3.5" />
                    Process Ready Queue
                </button>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-5">
                <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Pending</div>
                    <div className="mt-2 text-2xl font-black text-white">{Number(summary?.pending_count ?? 0)}</div>
                </div>
                <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/10 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-cyan-200">Ready</div>
                    <div className="mt-2 text-2xl font-black text-cyan-100">{Number(summary?.ready_count ?? 0)}</div>
                </div>
                <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-emerald-200">Sent</div>
                    <div className="mt-2 text-2xl font-black text-emerald-100">{Number(summary?.sent_count ?? 0)}</div>
                </div>
                <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-rose-200">Failed</div>
                    <div className="mt-2 text-2xl font-black text-rose-100">{Number(summary?.failed_count ?? 0)}</div>
                </div>
                <div className="rounded-2xl border border-amber-400/20 bg-amber-500/10 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-amber-200">Suppressed</div>
                    <div className="mt-2 text-2xl font-black text-amber-100">{Number(summary?.suppressed_count ?? 0)}</div>
                </div>
            </div>

            <div className="mt-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-xs text-slate-400">
                Stale queue: {Number(summary?.stale_pending_count ?? 0)} | Latest queued: {summary?.latest_created_at ?? 'No follow-up jobs yet.'}
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-xs text-slate-400">
                    Destinations: {countLabel(summary?.destination_counts)}
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-xs text-slate-400">
                    Service tiers: {countLabel(summary?.service_tier_counts)}
                </div>
            </div>

            <div className="mt-5 space-y-3">
                {prioritizedRecords.map((record) => {
                    const queueState = String(record.queue_state || '').toUpperCase();
                    const canSuppress = queueState !== 'SUPPRESSED' && queueState !== 'SENT';
                    return (
                        <div key={record.id} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
                            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                                <div className="min-w-0 flex-1">
                                    <div className="flex flex-wrap items-center gap-2">
                                        <span className="text-lg font-black uppercase tracking-[0.12em] text-white">{record.ticker}</span>
                                        <span className={clsx('rounded-full border px-2 py-1 text-[9px] font-black uppercase tracking-[0.2em]', queueTone(queueState))}>
                                            {queueState}
                                        </span>
                                        <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-1 text-[9px] font-black uppercase tracking-[0.2em] text-slate-300">
                                            {record.trigger_state}
                                        </span>
                                        <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-1 text-[9px] font-black uppercase tracking-[0.2em] text-slate-300">
                                            {record.message_type}
                                        </span>
                                    </div>
                                    <div className="mt-2 text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
                                        {record.lane} / {record.source_module || 'HORUS'} / retries {record.retry_count}
                                    </div>
                                    <div className="mt-2 text-[10px] font-mono uppercase tracking-[0.18em] text-cyan-300/80">
                                        {destinationLabel(record)}
                                    </div>
                                    <p className="mt-3 text-xs leading-6 text-slate-300">{summarizeDraft(record.draft_message)}</p>
                                    {record.last_error ? (
                                        <p className="mt-2 text-xs text-rose-300">Last error: {record.last_error}</p>
                                    ) : null}
                                </div>
                                <div className="flex flex-wrap gap-2 xl:max-w-[18rem] xl:justify-end">
                                    {(queueState === 'PENDING' || queueState === 'READY') ? (
                                        <button
                                            type="button"
                                            onClick={() => void onAction(record.id, 'SEND_NOW')}
                                            disabled={disabled || loading}
                                            className="rounded-xl border border-cyan-400/20 bg-cyan-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-cyan-100 disabled:opacity-50"
                                        >
                                            <Send className="mr-1 inline h-3 w-3" />
                                            Send Now
                                        </button>
                                    ) : null}
                                    {queueState === 'FAILED' ? (
                                        <button
                                            type="button"
                                            onClick={() => void onAction(record.id, 'RETRY')}
                                            disabled={disabled || loading}
                                            className="rounded-xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-rose-100 disabled:opacity-50"
                                        >
                                            <RefreshCcw className="mr-1 inline h-3 w-3" />
                                            Retry
                                        </button>
                                    ) : null}
                                    {(queueState === 'SUPPRESSED' || queueState === 'SENT') ? (
                                        <button
                                            type="button"
                                            onClick={() => void onAction(record.id, 'RESEND')}
                                            disabled={disabled || loading}
                                            className="rounded-xl border border-emerald-400/20 bg-emerald-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-emerald-100 disabled:opacity-50"
                                        >
                                            <RefreshCcw className="mr-1 inline h-3 w-3" />
                                            Requeue
                                        </button>
                                    ) : null}
                                    {canSuppress ? (
                                        <button
                                            type="button"
                                            onClick={() => void onAction(record.id, 'SUPPRESS', 'suppressed_from_telegram_rail')}
                                            disabled={disabled || loading}
                                            className="rounded-xl border border-amber-400/20 bg-amber-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-amber-100 disabled:opacity-50"
                                        >
                                            <ShieldOff className="mr-1 inline h-3 w-3" />
                                            Suppress
                                        </button>
                                    ) : null}
                                </div>
                            </div>
                        </div>
                    );
                })}
                {!loading && records.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-white/10 px-4 py-8 text-center text-sm text-slate-500">
                        No lifecycle follow-up jobs are queued yet.
                    </div>
                ) : null}
            </div>
        </div>
    );
}
