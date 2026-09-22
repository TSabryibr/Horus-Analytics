'use client';

import clsx from 'clsx';
import { InfoTooltip } from '@/components/InfoTooltip';

type MetricItemProps = {
    label: string;
    value: string | number;
    description: string;
    trend?: number;
    isLoading?: boolean;
};

function MetricItem({ label, value, description, trend, isLoading }: MetricItemProps) {
    return (
        <div className="group min-w-0 rounded-[0.85rem] border border-white/8 bg-black/20 px-4 py-3.5 cursor-default">
            <InfoTooltip content={description}>
                <span className="text-[9px] font-black text-slate-500 tracking-[0.24em] uppercase transition-colors group-hover:text-slate-400 underline decoration-white/5 underline-offset-4">
                    {label}
                </span>
            </InfoTooltip>
            <div className="mt-3 flex min-w-0 flex-wrap items-baseline gap-x-2 gap-y-1">
                {isLoading ? (
                    <div className="h-7 w-16 animate-pulse rounded-sm bg-white/5" />
                ) : (
                    <>
                        <span className="min-w-0 break-words font-mono text-[0.95rem] font-bold leading-6 tracking-[0.04em] tabular-nums text-white">
                            {value}
                        </span>
                        {trend !== undefined && (
                            <span
                                className={clsx(
                                    'font-mono text-[10px] font-black tracking-tight',
                                    trend >= 0 ? 'text-cyan-400' : 'text-amber-500'
                                )}
                            >
                                {trend > 0 ? '+' : ''}
                                {trend}%
                            </span>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

type HomeMetricsBarProps = {
    metrics: {
        total_pnl?: number;
        unrealized_pnl?: number;
        realized_pnl?: number;
        total_trades?: number;
        open_positions?: number;
        win_rate?: number;
        profit_factor?: number;
    } | null;
    health: { win_rate: number; avg_gain: number } | null;
    isSourceLoading: boolean;
};

export function HomeMetricsBar({ metrics, health, isSourceLoading }: HomeMetricsBarProps) {
    const hasPortfolioTelemetry = Boolean(
        metrics
        && (
            Number(metrics.total_trades || 0) > 0
            || Number(metrics.open_positions || 0) > 0
            || Number(metrics.total_pnl || 0) !== 0
            || Number(metrics.realized_pnl || 0) !== 0
            || Number(metrics.unrealized_pnl || 0) !== 0
        )
    );
    const precisionValue = hasPortfolioTelemetry && health ? `${health.win_rate}%` : '--';
    const precisionTrend = hasPortfolioTelemetry ? health?.avg_gain : undefined;

    return (
        <div className="rounded-[1.55rem] border border-white/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02))] p-5">
            <div className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Temple Telemetry</div>
            <div className="mt-4 grid min-w-0 gap-3 sm:grid-cols-2">
                <MetricItem
                    label="VALUATION"
                    value={`EGP ${metrics?.total_pnl?.toLocaleString() || 0}`}
                    description="Current equity value of all tracked positions in EGP."
                    isLoading={isSourceLoading}
                />
                <MetricItem
                    label="VARIANCE"
                    value={`${metrics?.win_rate || 0}%`}
                    description="The fluctuation in system win rate over the trailing period."
                    isLoading={isSourceLoading}
                />
                <MetricItem
                    label="ALPHA"
                    value={metrics?.profit_factor || 0}
                    description="Profit factor: the ratio of gross profit to gross loss."
                    isLoading={isSourceLoading}
                />
                <MetricItem
                    label="PRECISION"
                    value={precisionValue}
                    description="Trailing precision is shown after portfolio or trade telemetry exists."
                    trend={precisionTrend}
                    isLoading={isSourceLoading}
                />
            </div>
        </div>
    );
}
