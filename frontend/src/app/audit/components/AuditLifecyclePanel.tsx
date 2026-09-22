'use client';

import clsx from 'clsx';

import type { AuditLifecycleRecord } from '../hooks/useAuditRuntime';
import type { LifecycleSummary } from '@/types/domain';

type AuditLifecyclePanelProps = {
    rows: AuditLifecycleRecord[];
    summary?: LifecycleSummary | null;
    loading: boolean;
    onOverride: (lifecycleId: number, payload: Record<string, unknown>) => void | Promise<void> | Promise<boolean>;
};

export function AuditLifecyclePanel({ rows, summary, loading, onOverride }: AuditLifecyclePanelProps) {
    return (
        <section className="col-span-12 section-surface rounded-3xl p-6">
            <div className="flex flex-col gap-4 border-b border-white/8 pb-5 lg:flex-row lg:items-center lg:justify-between">
                <div>
                    <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Lifecycle Review Ledger</h3>
                    <p className="mt-2 text-sm text-slate-400">
                        Operator-facing published signal lifecycle queue with ambiguity and override controls.
                    </p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300">
                        {Number(summary?.active_count ?? 0)} Active
                    </span>
                    <span className="rounded-full border border-amber-400/20 bg-amber-500/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-amber-200">
                        {Number(summary?.ambiguous_count ?? 0)} Ambiguous
                    </span>
                </div>
            </div>

            <div className="mt-5 space-y-3">
                {rows.slice(0, 8).map((row) => {
                    const ambiguous = row.state === 'AMBIGUOUS';
                    const active = ['PUBLISHED', 'OPEN', 'TP1_HIT', 'AMBIGUOUS'].includes(row.state);
                    return (
                        <div key={row.id} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
                            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-lg font-black uppercase tracking-[0.12em] text-white">{row.ticker}</span>
                                        <span className={clsx(
                                            'rounded-full px-2 py-1 text-[9px] font-black uppercase tracking-[0.2em]',
                                            ambiguous
                                                ? 'bg-amber-500/10 text-amber-200'
                                                : active
                                                    ? 'bg-cyan-500/10 text-cyan-200'
                                                    : 'bg-emerald-500/10 text-emerald-200',
                                        )}>
                                            {row.state}
                                        </span>
                                    </div>
                                    <div className="mt-2 text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
                                        {row.lane} / {row.source_module || 'HORUS'} / {row.published_at || 'unpublished'}
                                    </div>
                                    {row.close_reason ? (
                                        <div className="mt-2 text-xs text-slate-400">Close reason: {row.close_reason}</div>
                                    ) : null}
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {ambiguous ? (
                                        <>
                                            <button
                                                type="button"
                                                onClick={() => void onOverride(row.id, { action: 'RECLASSIFY', target_state: 'OPEN', notes: 'Resolved ambiguous sequencing.' })}
                                                className="rounded-xl border border-cyan-400/20 bg-cyan-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-cyan-200"
                                            >
                                                Resolve Open
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => void onOverride(row.id, { action: 'RECLASSIFY', target_state: 'TP1_HIT', notes: 'Resolved to TP1 milestone.' })}
                                                className="rounded-xl border border-emerald-400/20 bg-emerald-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-emerald-200"
                                            >
                                                Resolve TP1
                                            </button>
                                        </>
                                    ) : null}
                                    {row.state === 'OPEN' ? (
                                        <>
                                            <button
                                                type="button"
                                                onClick={() => void onOverride(row.id, { action: 'MARK_TP1', notes: 'Operator marked TP1.' })}
                                                className="rounded-xl border border-emerald-400/20 bg-emerald-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-emerald-200"
                                            >
                                                Mark TP1
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => void onOverride(row.id, { action: 'MARK_STOP_LOSS', notes: 'Operator marked stop loss.' })}
                                                className="rounded-xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-rose-200"
                                            >
                                                Mark Stop
                                            </button>
                                        </>
                                    ) : null}
                                    {row.state === 'TP1_HIT' ? (
                                        <button
                                            type="button"
                                            onClick={() => void onOverride(row.id, { action: 'MARK_TP2', notes: 'Operator marked TP2.' })}
                                            className="rounded-xl border border-emerald-400/20 bg-emerald-500/10 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-emerald-200"
                                        >
                                            Mark TP2
                                        </button>
                                    ) : null}
                                </div>
                            </div>
                        </div>
                    );
                })}
                {!loading && rows.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-white/10 px-4 py-8 text-center text-sm text-slate-500">
                        No published lifecycle records available yet.
                    </div>
                ) : null}
            </div>
        </section>
    );
}
