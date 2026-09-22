import { BarChart3 } from 'lucide-react';

type BreakdownItem = {
    avg_realized_pnl_pct?: number;
    fill_rate_pct?: number;
    full_win_rate_pct?: number;
    key?: string;
    published_count?: number;
    stop_loss_rate_pct?: number;
    tp1_hit_rate_pct?: number;
};

type WeeklyReportSummaryPanelProps = {
    failed: string[];
    keyShifts: string[];
    market: {
        volatility_context?: string;
    };
    recommendations: string[];
    review: {
        avg_pnl_pct?: number;
        avg_time_to_open_hours?: number;
        avg_time_to_resolution_hours?: number;
        closed_outcomes?: number;
        expectancy_pct?: number;
        expiry_rate_pct?: number;
        fill_rate_pct?: number;
        followup_avg_retry_count?: number;
        followup_failure_rate_pct?: number;
        followup_pending_count?: number;
        followup_sent_rate_pct?: number;
        followup_suppressed_count?: number;
        followup_total?: number;
        full_win_rate_pct?: number;
        no_trade_outcomes?: number;
        open_outcomes?: number;
        published_signals?: number;
        review_source?: string;
        stop_loss_rate_pct?: number;
        tp1_hit_rate_pct?: number;
        win_rate_pct?: number;
        lane_breakdown?: BreakdownItem[];
        source_module_breakdown?: BreakdownItem[];
        operating_mode_breakdown?: BreakdownItem[];
    };
    worked: string[];
};

function fmt(value: number | undefined, decimals = 2): string {
    return value != null ? value.toFixed(decimals) : '\u2014';
}

function BreakdownTable({ items, title }: { items: BreakdownItem[]; title: string }) {
    if (!items || items.length === 0) return null;
    return (
        <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
            <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400 mb-3">{title}</p>
            <div className="overflow-x-auto">
                <table className="w-full text-[11px] text-slate-300">
                    <thead>
                        <tr className="border-b border-slate-800 text-slate-500">
                            <th className="text-left py-1 pr-3 font-medium">Lane</th>
                            <th className="text-right py-1 px-2 font-medium">Published</th>
                            <th className="text-right py-1 px-2 font-medium">TP1</th>
                            <th className="text-right py-1 px-2 font-medium">Full Win</th>
                            <th className="text-right py-1 px-2 font-medium">Stop</th>
                            <th className="text-right py-1 pl-2 font-medium">Avg PnL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.map((item, idx) => (
                            <tr key={idx} className="border-b border-slate-800/50">
                                <td className="py-1 pr-3 text-slate-200 font-medium">{item.key ?? '\u2014'}</td>
                                <td className="py-1 px-2 text-right">{item.published_count ?? '\u2014'}</td>
                                <td className="py-1 px-2 text-right">{fmt(item.tp1_hit_rate_pct)}%</td>
                                <td className="py-1 px-2 text-right">{fmt(item.full_win_rate_pct)}%</td>
                                <td className="py-1 px-2 text-right">{fmt(item.stop_loss_rate_pct)}%</td>
                                <td className="py-1 pl-2 text-right">{fmt(item.avg_realized_pnl_pct, 4)}%</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export function WeeklyReportSummaryPanel({
    failed,
    keyShifts,
    market,
    recommendations,
    review,
    worked,
}: WeeklyReportSummaryPanelProps) {
    const isLifecycleReview = String(review.review_source || '').toUpperCase() === 'PUBLISHED_LIFECYCLE';

    return (
        <div className="grid gap-6 md:grid-cols-2">
            <div className="section-surface p-6 rounded-2xl">
                <h3 className="text-sm font-bold uppercase tracking-widest text-blue-300 mb-4 flex items-center">
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Market Summary
                </h3>
                <p className="text-sm text-slate-300">{market.volatility_context || 'No volatility context available.'}</p>
                <div className="mt-4 space-y-2">
                    {keyShifts.length === 0 && <p className="text-xs text-slate-500">No key shifts detected.</p>}
                    {keyShifts.map((line, idx) => (
                        <p key={idx} className="text-xs text-slate-300">- {line}</p>
                    ))}
                </div>
            </div>
            <div className="section-surface p-6 rounded-2xl">
                <div className="mb-4 flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-bold uppercase tracking-widest text-blue-300">Signal Review</h3>
                    <span className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] ${
                        isLifecycleReview
                            ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                            : 'border-slate-700 bg-slate-900/70 text-slate-300'
                    }`}>
                        {isLifecycleReview ? 'Published Lifecycle' : 'Legacy Summary'}
                    </span>
                </div>
                <div className="space-y-2 text-xs text-slate-300">
                    <p>
                        Closed/Open/NoTrade: {review.closed_outcomes ?? '\u2014'}/{review.open_outcomes ?? '\u2014'}/
                        {review.no_trade_outcomes ?? '\u2014'}
                    </p>
                    {isLifecycleReview && (
                        <>
                            <p>Published/Fill: {review.published_signals ?? '\u2014'}/{fmt(review.fill_rate_pct)}%</p>
                            <p>TP1/Full Win/Stop: {fmt(review.tp1_hit_rate_pct)}%/{fmt(review.full_win_rate_pct)}%/{fmt(review.stop_loss_rate_pct)}%</p>
                            <p>Expiry rate: {fmt(review.expiry_rate_pct)}%</p>
                            <p>Avg time open/resolution: {fmt(review.avg_time_to_open_hours)}h/{fmt(review.avg_time_to_resolution_hours)}h</p>
                        </>
                    )}
                    <p>Win rate: {fmt(review.win_rate_pct)}%</p>
                    <p>Avg PnL: {fmt(review.avg_pnl_pct, 4)}%</p>
                    <p>Expectancy: {fmt(review.expectancy_pct, 4)}%</p>
                </div>
                {isLifecycleReview && (
                    <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                        <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">Delivery Performance</p>
                        <div className="mt-3 space-y-2 text-xs text-slate-300">
                            <p>Follow-ups: {review.followup_total ?? '\u2014'}</p>
                            <p>Sent/Failed: {fmt(review.followup_sent_rate_pct)}%/{fmt(review.followup_failure_rate_pct)}%</p>
                            <p>Pending/Suppressed: {review.followup_pending_count ?? '\u2014'}/{review.followup_suppressed_count ?? '\u2014'}</p>
                            <p>Avg retry count: {fmt(review.followup_avg_retry_count)}</p>
                        </div>
                    </div>
                )}
                {isLifecycleReview && review.lane_breakdown && review.lane_breakdown.length > 0 && (
                    <BreakdownTable items={review.lane_breakdown} title="Lane Breakdown" />
                )}
                {isLifecycleReview && Boolean(review.source_module_breakdown) && (
                    <BreakdownTable
                        items={review.source_module_breakdown as BreakdownItem[]}
                        title="Source Module Breakdown"
                    />
                )}
                {isLifecycleReview && Boolean(review.operating_mode_breakdown) && (
                    <BreakdownTable
                        items={review.operating_mode_breakdown as BreakdownItem[]}
                        title="Operating Mode Breakdown"
                    />
                )}
                {recommendations.length > 0 && (
                    <div className="mt-4">
                        <p className="text-xs uppercase tracking-wider text-blue-400 mb-1">Recommendations</p>
                        {recommendations.map((line, idx) => (
                            <p key={idx} className="text-xs text-slate-300">- {line}</p>
                        ))}
                    </div>
                )}
                <div className="mt-4">
                    <div className="flex items-center gap-2 mb-1">
                        <p className="text-xs uppercase tracking-wider text-emerald-400">What Worked</p>
                        <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 tracking-wider">
                            WORKED ⚡
                        </span>
                    </div>
                    {(worked.length ? worked : ['No strong positive pattern yet.']).map((line, idx) => (
                        <p key={idx} className="text-xs text-slate-300">- {line}</p>
                    ))}
                </div>
                <div className="mt-4">
                    <p className="text-xs uppercase tracking-wider text-rose-400 mb-1">What Failed</p>
                    {(failed.length ? failed : ['No major failure pattern flagged.']).map((line, idx) => (
                        <p key={idx} className="text-xs text-slate-300">- {line}</p>
                    ))}
                </div>
            </div>
        </div>
    );
}
