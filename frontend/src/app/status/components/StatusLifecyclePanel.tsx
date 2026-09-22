'use client';

type StatusLifecyclePanelProps = {
    signalDesk?: {
        queued_candidate_count?: number;
        lanes?: {
            intraday?: number;
            swing?: number;
            position?: number;
        };
    } | null;
    lifecycle?: {
        configured?: boolean;
        total?: number;
        active_count?: number;
        ambiguous_count?: number;
        stale_active_count?: number;
        monitor_status?: string;
        latest_published_at?: string | null;
    } | null;
    followups?: {
        configured?: boolean;
        total?: number;
        pending_count?: number;
        ready_count?: number;
        failed_count?: number;
        suppressed_count?: number;
        stale_pending_count?: number;
        destination_counts?: Record<string, number>;
        service_tier_counts?: Record<string, number>;
        latest_created_at?: string | null;
    } | null;
};

function countLabel(counts?: Record<string, number>) {
    const entries = Object.entries(counts || {}).filter(([, value]) => Number(value) > 0);
    if (!entries.length) return 'None';
    return entries.map(([key, value]) => `${key.replace(/_/g, ' ')} ${value}`).join(' | ');
}

export function StatusLifecyclePanel({ signalDesk, lifecycle, followups }: StatusLifecyclePanelProps) {
    const deskSummary = signalDesk ?? {};
    const summary = lifecycle ?? {};
    const followupSummary = followups ?? {};
    const queuedCandidateCount = Number(deskSummary.queued_candidate_count ?? 0);
    const lanes = deskSummary.lanes ?? {};
    const followupsConfigured = followupSummary.configured !== false;
    const followupTag = followupsConfigured ? `${Number(followupSummary.total ?? 0)} Jobs` : 'FOLLOWUPS_DISABLED';

    return (
        <div className="section-surface rounded-3xl p-6">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Signal Lifecycle + Queue</h3>
                    <p className="mt-2 text-sm text-slate-400">
                        Monitor queued desk candidates and unresolved published lifecycle load across the active Horus signal book.
                    </p>
                </div>
                <div className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300">
                    {summary.monitor_status ?? 'READY'}
                </div>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-4">
                <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/10 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-cyan-200">Candidate Queue</div>
                    <div className="mt-2 text-2xl font-black text-cyan-100">{queuedCandidateCount}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Published</div>
                    <div className="mt-2 text-2xl font-black text-white">{Number(summary.total ?? 0)}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Active Published</div>
                    <div className="mt-2 text-2xl font-black text-cyan-300">{Number(summary.active_count ?? 0)}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Ambiguous</div>
                    <div className="mt-2 text-2xl font-black text-amber-300">{Number(summary.ambiguous_count ?? 0)}</div>
                </div>
            </div>

            <div className="mt-4 grid gap-3 text-xs text-slate-400 md:grid-cols-[minmax(0,1fr)_auto]">
                <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                    Latest published: {summary.latest_published_at ?? 'No published lifecycle records yet.'}
                    <span className="ml-3 text-rose-300">Stale active: {Number(summary.stale_active_count ?? 0)}</span>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 font-mono text-[10px] uppercase tracking-[0.16em] text-slate-300">
                    Intraday {Number(lanes.intraday ?? 0)} / Swing {Number(lanes.swing ?? 0)} / Position {Number(lanes.position ?? 0)}
                </div>
            </div>

            <div className="mt-5 border-t border-white/8 pt-5">
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <h4 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Follow-Up Queue</h4>
                        <p className="mt-2 text-sm text-slate-400">
                            Operational status for Telegram lifecycle updates after TP1, TP2, stop, expiry, and cancellation events.
                        </p>
                    </div>
                    <div className={followupsConfigured
                        ? 'rounded-full border border-white/10 bg-black/20 px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-cyan-300'
                        : 'rounded-full border border-orange-400/30 bg-orange-500/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-orange-200'}
                    >
                        {followupTag}
                    </div>
                </div>

                {!followupsConfigured ? (
                    <div className="mt-4 rounded-2xl border border-orange-400/20 bg-orange-500/10 px-4 py-3 text-xs leading-5 text-orange-100">
                        Follow-up processing is not configured. Lifecycle updates will not be queued until the follow-up worker is enabled.
                    </div>
                ) : null}

                <div className="mt-5 grid gap-3 md:grid-cols-5">
                    <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                        <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Pending</div>
                        <div className="mt-2 text-2xl font-black text-white">{Number(followupSummary.pending_count ?? 0)}</div>
                    </div>
                    <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/10 px-4 py-3">
                        <div className="text-[10px] uppercase tracking-[0.2em] text-cyan-200">Ready</div>
                        <div className="mt-2 text-2xl font-black text-cyan-100">{Number(followupSummary.ready_count ?? 0)}</div>
                    </div>
                    <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3">
                        <div className="text-[10px] uppercase tracking-[0.2em] text-rose-200">Failed</div>
                        <div className="mt-2 text-2xl font-black text-rose-100">{Number(followupSummary.failed_count ?? 0)}</div>
                    </div>
                    <div className="rounded-2xl border border-amber-400/20 bg-amber-500/10 px-4 py-3">
                        <div className="text-[10px] uppercase tracking-[0.2em] text-amber-200">Suppressed</div>
                        <div className="mt-2 text-2xl font-black text-amber-100">{Number(followupSummary.suppressed_count ?? 0)}</div>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                        <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Stale Queue</div>
                        <div className="mt-2 text-2xl font-black text-white">{Number(followupSummary.stale_pending_count ?? 0)}</div>
                    </div>
                </div>

                <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-xs text-slate-400">
                    Latest queued update: {followupSummary.latest_created_at ?? 'No follow-up jobs queued yet.'}
                </div>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                    <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-xs text-slate-400">
                        Destinations: {countLabel(followupSummary.destination_counts)}
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-xs text-slate-400">
                        Service tiers: {countLabel(followupSummary.service_tier_counts)}
                    </div>
                </div>
            </div>
        </div>
    );
}
