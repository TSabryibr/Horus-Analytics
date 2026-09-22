'use client';

import clsx from 'clsx';

import type { AuditFollowUpRecord } from '../hooks/useAuditRuntime';
import type { FollowUpSummary } from '@/types/domain';

type AuditFollowUpsPanelProps = {
    rows: AuditFollowUpRecord[];
    summary?: FollowUpSummary | null;
    loading: boolean;
    onAction: (
        followUpId: number,
        action: 'SEND_NOW' | 'RETRY' | 'SUPPRESS' | 'RESEND',
        reason?: string,
    ) => void | Promise<void> | Promise<boolean>;
};

function countLabel(counts?: unknown) {
    const entries = Object.entries((counts || {}) as Record<string, number>).filter(([, value]) => Number(value) > 0);
    if (!entries.length) return 'None';
    return entries.map(([key, value]) => `${key.replace(/_/g, ' ')} ${value}`).join(' | ');
}

function destinationLabel(row: AuditFollowUpRecord) {
    const type = String(row.destination_type || 'PORTFOLIO').replace(/_/g, ' ');
    const name = row.destination_name || 'Legacy destination';
    const tier = row.service_tier ? ` / ${row.service_tier}` : '';
    return `${type}: ${name}${tier}`;
}

export function AuditFollowUpsPanel({ rows, summary, loading, onAction }: AuditFollowUpsPanelProps) {
    return (
        <section className="col-span-12 section-surface rounded-3xl p-6">
            <div className="flex flex-col gap-4 border-b border-white/8 pb-5 lg:flex-row lg:items-center lg:justify-between">
                <div>
                    <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Follow-Up Delivery Ledger</h3>
                    <p className="mt-2 text-sm text-slate-400">
                        Queue health, failed sends, suppressions, and resend control for post-publish Horus Telegram updates.
                    </p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-slate-200">
                        {Number(summary?.pending_count ?? 0) + Number(summary?.ready_count ?? 0)} Queued
                    </span>
                    <span className="rounded-full border border-rose-400/20 bg-rose-500/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-rose-200">
                        {Number(summary?.failed_count ?? 0)} Failed
                    </span>
                    <span className="rounded-full border border-amber-400/20 bg-amber-500/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-amber-200">
                        {Number(summary?.suppressed_count ?? 0)} Suppressed
                    </span>
                </div>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-xs text-slate-400">
                    Destinations: {countLabel(summary?.destination_counts)}
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-xs text-slate-400">
                    Service tiers: {countLabel(summary?.service_tier_counts)}
                </div>
            </div>

            <div className="mt-5 space-y-3">
                {rows.slice(0, 8).map((row) => {
                    const queueState = String(row.queue_state || '').toUpperCase();
                    return (
                        <div key={row.id} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
                            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-lg font-black uppercase tracking-[0.12em] text-white">{row.ticker}</span>
                                        <span className={clsx(
                                            'rounded-full px-2 py-1 text-[9px] font-black uppercase tracking-[0.2em]',
                                            queueState === 'FAILED'
                                                ? 'bg-rose-500/10 text-rose-200'
                                                : queueState === 'SENT'
                                                    ? 'bg-emerald-500/10 text-emerald-200'
                                                    : queueState === 'SUPPRESSED'
                                                        ? 'bg-amber-500/10 text-amber-200'
                                                        : 'bg-cyan-500/10 text-cyan-200',
                                        )}>
                                            {queueState}
                                        </span>
                                        <span className="rounded-full bg-white/[0.04] px-2 py-1 text-[9px] font-black uppercase tracking-[0.2em] text-slate-300">
                                            {row.trigger_state}
                                        </span>
                                    </div>
                                    <div className="mt-2 text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
                                        {row.lane} / {row.source_module || 'HORUS'} / retries {Number(row.retry_count ?? 0)}
                                    </div>
                                    <div className="mt-2 text-[10px] font-mono uppercase tracking-[0.18em] text-cyan-300/80">
                                        {destinationLabel(row)}
                                    </div>
                                    {row.last_error ? (
                                        <div className="mt-2 text-xs text-rose-300">Last error: {row.last_error}</div>
                                    ) : null}
                                    {row.suppression_reason ? (
                                        <div className="mt-2 text-xs text-amber-300">Suppressed: {row.suppression_reason}</div>
                                    ) : null}
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {(queueState === 'PENDING' || queueState === 'READY') ? (
                                        <button
                                            type="button"
                                            onClick={() => void onAction(row.id, 'SEND_NOW')}
                                            className="rounded-xl border border-cyan-400/20 bg-cyan-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-cyan-200"
                                        >
                                            Send Now
                                        </button>
                                    ) : null}
                                    {queueState === 'FAILED' ? (
                                        <button
                                            type="button"
                                            onClick={() => void onAction(row.id, 'RETRY')}
                                            className="rounded-xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-rose-200"
                                        >
                                            Retry
                                        </button>
                                    ) : null}
                                    {(queueState === 'SUPPRESSED' || queueState === 'SENT') ? (
                                        <button
                                            type="button"
                                            onClick={() => void onAction(row.id, 'RESEND')}
                                            className="rounded-xl border border-emerald-400/20 bg-emerald-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-emerald-200"
                                        >
                                            Requeue
                                        </button>
                                    ) : null}
                                    {(queueState === 'PENDING' || queueState === 'READY' || queueState === 'FAILED') ? (
                                        <button
                                            type="button"
                                            onClick={() => void onAction(row.id, 'SUPPRESS', 'suppressed_from_audit_queue')}
                                            className="rounded-xl border border-amber-400/20 bg-amber-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-amber-200"
                                        >
                                            Suppress
                                        </button>
                                    ) : null}
                                </div>
                            </div>
                        </div>
                    );
                })}
                {!loading && rows.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-white/10 px-4 py-8 text-center text-sm text-slate-500">
                        No lifecycle follow-up jobs available yet.
                    </div>
                ) : null}
            </div>
        </section>
    );
}
