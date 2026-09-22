'use client';

import clsx from 'clsx';
import { BarChart3, Calendar, Layers3, ShieldAlert, ShieldCheck } from 'lucide-react';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';

interface StatusDiagnosticsPanelProps {
    status: any;
    lastRefresh: Date | null;
}

export function StatusDiagnosticsPanel({ status, lastRefresh }: StatusDiagnosticsPanelProps) {
    const provisioningStatus = String(status?.provisioning_status || '').toUpperCase();
    const provisioningError = String(status?.provisioning_error || '').trim();
    const lastBackfillStatus = String(status?.last_backfill_status || '').toUpperCase();
    const lastBackfillMode = String(status?.last_backfill_mode || '').toUpperCase();
    const lastBackfillCompleted = Number(status?.last_backfill_completed_trading_days || 0);
    const lastBackfillTarget = Number(status?.last_backfill_target_trading_days || 0);
    const lastBackfillUniverseChoice = String(status?.last_backfill_universe_choice || 'EGX30').toUpperCase();
    const hasHistoricalBackfillSnapshot = status?.system_ready
        && ['COMPLETED', 'COMPLETED_WITH_WARNINGS'].includes(lastBackfillStatus)
        && lastBackfillTarget > 0;
    const lastBackfillLine = hasHistoricalBackfillSnapshot
        ? `> Last ${lastBackfillMode === 'MANUAL' ? 'manual' : lastBackfillMode === 'AUTOMATIC' ? 'automatic' : 'historical'} backfill completed (${lastBackfillUniverseChoice}): ${lastBackfillCompleted} / ${lastBackfillTarget} trading days.`
        : null;
    const lastRefreshDisplay = lastRefresh ? lastRefresh.toLocaleTimeString() : '--:--:--';
    const coreState = status?.system_ready
        ? 'READY'
        : provisioningStatus === 'RUNNING'
            ? 'PROVISIONING'
            : provisioningStatus === 'ERROR'
                ? 'PROVISIONING_ERROR'
                : 'INIT';
    const statusLine = status?.system_ready
        ? '> System readiness check passed.'
        : provisioningStatus === 'RUNNING'
            ? '> Historical provisioning still in progress.'
            : provisioningStatus === 'ERROR'
                ? '> System readiness blocked by provisioning failure.'
                : '> System readiness still initializing.';
    const runtimeUniverse = status?.runtime_universe || null;
    const runtimeSummary = runtimeUniverse?.summary || {};
    const runtimeSourceContext = runtimeUniverse?.source_context || {};
    const overlayBackedArchiveLag = Boolean(runtimeSourceContext.archive_intraday_stale && runtimeSourceContext.realtime_overlay_active);
    const runtimeQuarantined = Array.isArray(runtimeUniverse?.runtime_quarantined)
        ? runtimeUniverse.runtime_quarantined
        : [];
    const reviewCandidates = Array.isArray(runtimeUniverse?.review_candidates)
        ? runtimeUniverse.review_candidates
        : [];
    const hasRuntimeUniverse = runtimeUniverse && (
        runtimeSummary?.tracked_count !== undefined
        || runtimeQuarantined.length > 0
        || reviewCandidates.length > 0
    );

    return (
        <div className="min-w-0 space-y-8">
            <IndustrialCard tone="primary" className="rounded-3xl" contentClassName="p-8">
                <div className="flex items-center gap-3 mb-6">
                    <BarChart3 className="w-6 h-6 text-primary" />
                    <h2 className="text-xl font-bold text-white tracking-tight uppercase">Engine Stats</h2>
                </div>
                <div className="space-y-6">
                    <div>
                        <p className="text-[10px] text-slate-400 font-black uppercase mb-1">Signals Processed (Total)</p>
                        <p className="text-4xl font-black text-white">{status?.metrics?.total_signals?.toLocaleString() || 0}</p>
                    </div>
                    <div>
                        <p className="text-[10px] text-slate-400 font-black uppercase mb-1">Last Scan Integrity</p>
                        <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4 text-slate-500" />
                            <span className="text-sm text-slate-300 font-bold">{status?.metrics?.last_signal_date || 'N/A'}</span>
                        </div>
                    </div>
                </div>
                <div className="mt-8 pt-6 border-t border-primary/10">
                    <div className="flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-emerald-500" />
                        <span className="text-[10px] font-bold text-emerald-500 uppercase">Integrity Score: 100%</span>
                    </div>
                </div>
            </IndustrialCard>

            <IndustrialCard tone="secondary" className="rounded-3xl" contentClassName="p-8">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Diagnostics Console</h3>
                <div className="space-y-2 rounded-xl bg-black/40 p-4 font-mono text-[10px] leading-relaxed text-slate-400 break-words">
                    <p className="text-emerald-500">[{lastRefreshDisplay}] System Status Poll...</p>
                    <p className="text-slate-500">&gt; Core State: {coreState}</p>
                    <p className="text-slate-500">&gt; Message: {status?.message || 'Running...'}</p>
                    {provisioningStatus === 'ERROR' && provisioningError ? (
                        <p className="text-rose-500">&gt; Provisioning Error: {provisioningError}</p>
                    ) : null}
                    <p className={status?.system_ready ? 'text-cyan-500' : provisioningStatus === 'ERROR' ? 'text-rose-500' : 'text-amber-400'}>
                        {statusLine}
                    </p>
                    {lastBackfillLine ? (
                        <p className={lastBackfillStatus === 'COMPLETED_WITH_WARNINGS' ? 'text-amber-400' : 'text-slate-500'}>
                            {lastBackfillLine}
                        </p>
                    ) : null}
                </div>
            </IndustrialCard>

            {hasRuntimeUniverse ? (
                <IndustrialCard tone="secondary" className="rounded-3xl" contentClassName="p-8">
                    <div className="flex items-center gap-3 mb-6">
                        <Layers3 className="w-5 h-5 text-primary" />
                        <h3 className="text-xl font-bold text-white tracking-tight uppercase">Runtime Universe</h3>
                    </div>

                    <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
                        <RuntimeMetric label="Tracked" value={runtimeSummary?.tracked_count ?? 0} tone="neutral" />
                        <RuntimeMetric label="Quarantined" value={runtimeSummary?.runtime_quarantined_count ?? 0} tone="warning" />
                        <RuntimeMetric label="Review" value={runtimeSummary?.review_candidate_count ?? 0} tone="info" />
                    </div>

                    {overlayBackedArchiveLag ? (
                        <div className="mb-5 rounded-2xl border border-cyan-400/20 bg-cyan-500/10 px-4 py-3">
                            <p className="font-mono text-[10px] font-black uppercase tracking-[0.2em] text-cyan-200">
                                Archive stale / realtime overlay live
                            </p>
                            <p className="mt-2 text-xs leading-5 text-slate-300">
                                {runtimeSourceContext.runtime_review_note}
                            </p>
                        </div>
                    ) : runtimeSourceContext.runtime_review_note ? (
                        <div className="mb-5 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-xs leading-5 text-slate-400">
                            {runtimeSourceContext.runtime_review_note}
                        </div>
                    ) : null}

                    <RuntimeTickerBucket
                        title="Runtime Quarantined"
                        tone="warning"
                        emptyLabel="No runtime quarantines"
                        items={runtimeQuarantined}
                    />

                    <RuntimeTickerBucket
                        title="Review Candidates"
                        tone="info"
                        emptyLabel="No review candidates"
                        items={reviewCandidates}
                    />
                </IndustrialCard>
            ) : null}
        </div>
    );
}

function RuntimeMetric({
    label,
    value,
    tone,
}: {
    label: string;
    value: number;
    tone: 'neutral' | 'warning' | 'info';
}) {
    return (
        <div className="section-surface-muted industrial-corner rounded-2xl border border-white/10 px-4 py-3">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">{label}</p>
            <p
                className={clsx(
                    'mt-2 text-2xl font-black tracking-tight',
                    tone === 'neutral' && 'text-white',
                    tone === 'warning' && 'text-amber-400',
                    tone === 'info' && 'text-cyan-400',
                )}
            >
                {value}
            </p>
        </div>
    );
}

function RuntimeTickerBucket({
    title,
    tone,
    emptyLabel,
    items,
}: {
    title: string;
    tone: 'warning' | 'info';
    emptyLabel: string;
    items: Array<{ ticker?: string; reason?: string }>;
}) {
    return (
        <div className="mb-5 last:mb-0">
            <div className="mb-3 flex items-center gap-2">
                {tone === 'warning' ? (
                    <ShieldAlert className="h-4 w-4 text-amber-400" />
                ) : (
                    <BarChart3 className="h-4 w-4 text-cyan-400" />
                )}
                <h4 className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">{title}</h4>
            </div>

            {items.length ? (
                <div className="flex flex-wrap gap-2">
                    {items.map((item) => (
                        <div
                            key={`${item.ticker}-${item.reason}`}
                            className={clsx(
                                'rounded-full border px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em]',
                                tone === 'warning'
                                    ? 'border-amber-500/20 bg-amber-500/10 text-amber-300'
                                    : 'border-cyan-500/20 bg-cyan-500/10 text-cyan-300',
                            )}
                        >
                            {item.ticker}
                        </div>
                    ))}
                </div>
            ) : (
                <p className="text-xs text-slate-500">{emptyLabel}</p>
            )}
        </div>
    );
}
