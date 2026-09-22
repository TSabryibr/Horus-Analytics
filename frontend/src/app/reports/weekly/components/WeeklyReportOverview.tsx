import clsx from 'clsx';

type WeeklyReportOverviewProps = {
    data: {
        generated_at?: string;
        period_end?: string;
        period_start?: string;
        status?: string;
    } | null;
    market: {
        breadth_change_pct?: number;
        period_return_pct?: number;
        regime_end?: string;
        regime_start?: string;
    };
    review: {
        avg_pnl_pct?: number;
        run_count?: number;
        signals_generated?: number;
        win_rate_pct?: number;
    };
};

function fmt(value: number | undefined, decimals = 2): string {
    return value != null ? value.toFixed(decimals) : '\u2014';
}

export function WeeklyReportOverview({
    data,
    market,
    review,
}: WeeklyReportOverviewProps) {
    return (
        <div className="grid gap-6 md:grid-cols-3">
            <div className="section-surface p-6 rounded-2xl">
                <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Window</p>
                <p className="text-sm font-semibold text-white">
                    {data?.period_start ?? '\u2014'} to {data?.period_end ?? '\u2014'}
                </p>
                <p className="text-xs text-slate-400 mt-2">Generated: {data?.generated_at ?? '\u2014'}</p>
                <p className="text-xs text-slate-400 mt-1">Status: {(data?.status ?? 'unknown').toUpperCase()}</p>
            </div>
            <div className="section-surface p-6 rounded-2xl">
                <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Regime Shift</p>
                <p className="text-sm font-semibold text-white">
                    {(market.regime_start ?? 'NEUTRAL').toUpperCase()} to {(market.regime_end ?? 'NEUTRAL').toUpperCase()}
                </p>
                <p
                    className={clsx(
                        'text-xl font-black mt-3',
                        (market.period_return_pct ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400',
                    )}
                >
                    {fmt(market.period_return_pct)}%
                </p>
                <p className="text-xs text-slate-400 mt-1">Breadth: {fmt(market.breadth_change_pct)}pp</p>
            </div>
            <div className="section-surface p-6 rounded-2xl">
                <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Signal Quality</p>
                <p className="text-sm text-white">Runs: {review.run_count ?? '\u2014'}</p>
                <p className="text-sm text-white">Signals: {review.signals_generated ?? '\u2014'}</p>
                <p className="text-sm text-white">Win Rate: {fmt(review.win_rate_pct)}%</p>
                <p className="text-sm text-white">Avg PnL: {fmt(review.avg_pnl_pct, 4)}%</p>
            </div>
        </div>
    );
}
