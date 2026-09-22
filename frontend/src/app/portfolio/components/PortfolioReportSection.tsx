'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Printer, FileText } from 'lucide-react';

import EmptyState from '../../components/EmptyState';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';
import { PortfolioReportBundle } from '../hooks/usePortfolioRuntime';
import { SystemPerformance, ExecutionHistoryItem } from '../hooks/useSystemPerformance';
import { MeasuredChartFrame } from '@/app/components/charts/MeasuredChartFrame';

const truncatePrice = (val: number, decimals: number = 3): string => {
    if (!Number.isFinite(val)) return '0.000';
    const factor = Math.pow(10, decimals);
    const truncated = Math.trunc(val * factor) / factor;
    return truncated.toFixed(decimals);
};

interface PortfolioReportSectionProps {
    portfolioId: number;
    report?: PortfolioReportBundle | null;
    loading?: boolean;
    compact?: boolean;
    showPrint?: boolean;
    performance?: SystemPerformance | null;
    executionHistory?: ExecutionHistoryItem[];
}

export default function PortfolioReportSection({
    portfolioId,
    report = null,
    loading = false,
    compact = false,
    showPrint = false,
    performance = null,
    executionHistory = []
}: PortfolioReportSectionProps) {
    const safeMetrics = performance?.metrics ?? report?.metrics ?? {
        total_pnl: 0,
        win_rate: 0,
        profit_factor: 0,
        total_trades: 0,
    };
    
    // Performance metrics extensions
    const maxDrawdown = performance?.metrics.max_drawdown;
    const avgHoldingDays = performance?.metrics.avg_holding_days;
    const signalQuality = performance?.signal_quality;
    const isStrategyAttribution =
        String(performance?.scope || '').toUpperCase() === 'STRATEGY_ATTRIBUTION' ||
        String(performance?.portfolio?.type || '').toUpperCase() === 'STRATEGY';

    const curve = Array.isArray(report?.curve) ? report.curve : [];
    
    const hasData = safeMetrics.total_trades > 0 || safeMetrics.total_pnl !== 0;
    
    // Fallback to legacy trades if executionHistory is empty
    const legacyTrades = Array.isArray(report?.trades) ? report.trades.slice(0, 20) : [];
    const hasExecutionHistory = executionHistory && executionHistory.length > 0;

    const realizedExecutionRows = (executionHistory || [])
        .map((t) => {
            const entry = Number(t.actual_entry || t.planned_entry || 0);
            const exit = Number(t.details?.exit_price || 0);
            const realizedPnl = Number(t.details?.realized_pnl || 0);
            const date = t.updated_at || t.created_at || '';
            const reason = String(t.close_reason || t.state || '').toUpperCase();
            const isRealized = exit > 0 || realizedPnl !== 0 || reason.includes('TARGET') || reason.includes('STOP') || reason.includes('CLOSED');
            return {
                source: 'execution' as const,
                key: `exec-${t.id}`,
                date,
                ticker: String(t.ticker || '').toUpperCase(),
                reason: t.close_reason || t.state,
                entry,
                exit,
                pnl: realizedPnl,
                isRealized,
            };
        })
        .filter((row) => row.isRealized);
    const executionLaneByRowKey = new Map(
        (executionHistory || []).map((item) => [`exec-${item.id}`, String(item.lane || '').toUpperCase()])
    );

    const legacyTradeRows = legacyTrades.map((t, i) => ({
        source: 'trade' as const,
        key: `trade-${i}-${String(t.ticker || '').toUpperCase()}-${t.exit_date}`,
        date: t.exit_date || '',
        ticker: String(t.ticker || '').toUpperCase(),
        reason: t.reason || 'TRADE',
        entry: Number(t.entry_price || 0),
        exit: Number(t.exit_price || 0),
        pnl: Number(t.pnl || 0),
    }));

    const combinedRowsRaw = [...realizedExecutionRows, ...legacyTradeRows]
        .filter((row) => row.exit > 0 || row.pnl !== 0)
        .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

    const dedupMap = new Map<string, (typeof combinedRowsRaw)[number]>();
    for (const row of combinedRowsRaw) {
        const normalizedDate = (row.date || '').replace(' ', 'T').slice(0, 16);
        const dedupKey = [
            row.ticker,
            row.entry.toFixed(4),
            row.exit.toFixed(4),
            row.pnl.toFixed(2),
            normalizedDate,
        ].join('|');
        const existing = dedupMap.get(dedupKey);
        if (!existing) {
            dedupMap.set(dedupKey, row);
            continue;
        }
        // Prefer execution rows because they carry richer close labels (TARGET_1 / TARGET_2 / STOP).
        if (existing.source === 'trade' && row.source === 'execution') {
            dedupMap.set(dedupKey, row);
        }
    }

    const combinedRows = Array.from(dedupMap.values())
        .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
        .slice(0, 20);

    const formatDate = (dateStr: string) => {
        if (!dateStr || dateStr === 'Never') return '-';
        try {
            const date = new Date(dateStr);
            return date.toLocaleString('en-US', {
                month: 'short',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        } catch {
            return dateStr;
        }
    };

    if (!portfolioId) {
        return (
            <section className={compact ? "section-surface mt-10 p-6" : "section-surface mt-10 p-8"} aria-label="Treasury reporting">
                <EmptyState
                    icon="file"
                    title="No Active Portfolio"
                    message="Select an active portfolio to view reporting."
                />
            </section>
        );
    }

    if (loading && !report) {
        return (
            <div className="section-surface mt-10 p-6">
                <div className="flex flex-col gap-4">
                    <div className="h-5 bg-white/10 rounded w-56" />
                    <div className="h-40 bg-white/5 rounded" />
                </div>
            </div>
        );
    }

    return (
        <section className={compact ? "section-surface mt-10 p-6" : "section-surface mt-10 p-8"} aria-label="Treasury reporting">
            <div className="flex items-center justify-between gap-4 mb-6">
                <div className="flex items-center gap-4">
                    <FileText className="w-8 h-8 text-blue-400" />
                    <div>
                        <h3 className="text-xl font-black uppercase tracking-tighter text-white">
                            {isStrategyAttribution ? 'Strategy Attribution Report' : 'Investment Committee Report'}
                        </h3>
                        <p className="text-xs text-gray-400">
                            {isStrategyAttribution
                                ? 'Executed trades plus signal-quality attribution for the selected strategy profile.'
                                : 'Portfolio performance summary from Treasury data'}
                        </p>
                    </div>
                </div>
                {showPrint && (
                    <button
                        type="button"
                        onClick={() => window.print()}
                        className="action-secondary gap-2 !text-slate-200 print:hidden"
                    >
                        <Printer size={16} />
                        Print Report
                    </button>
                )}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
                <IndustrialCard tone="secondary" className="rounded-[1.25rem]" contentClassName="p-4">
                    <p className="text-[10px] uppercase font-black tracking-widest text-gray-500">Total PnL</p>
                    <p className={safeMetrics.total_pnl >= 0 ? "text-2xl font-black text-emerald-400" : "text-2xl font-black text-rose-400"}>
                        {safeMetrics.total_pnl.toLocaleString()} EGP
                    </p>
                </IndustrialCard>
                <IndustrialCard tone="secondary" className="rounded-[1.25rem]" contentClassName="p-4">
                    <p className="text-[10px] uppercase font-black tracking-widest text-gray-500">Win Rate</p>
                    <p className="text-2xl font-black text-blue-400">{safeMetrics.win_rate}%</p>
                </IndustrialCard>
                <IndustrialCard tone="secondary" className="rounded-[1.25rem]" contentClassName="p-4">
                    <p className="text-[10px] uppercase font-black tracking-widest text-gray-500">Profit Factor</p>
                    <p className="text-2xl font-black text-fuchsia-400">{safeMetrics.profit_factor}</p>
                </IndustrialCard>
                <IndustrialCard tone="secondary" className="rounded-[1.25rem]" contentClassName="p-4">
                    <p className="text-[10px] uppercase font-black tracking-widest text-gray-500">Total Trades</p>
                    <p className="text-2xl font-black text-white">{safeMetrics.total_trades}</p>
                </IndustrialCard>
                {maxDrawdown !== undefined && (
                    <IndustrialCard tone="secondary" className="rounded-[1.25rem]" contentClassName="p-4">
                        <p className="text-[10px] uppercase font-black tracking-widest text-gray-500">Max Drawdown</p>
                        <p className="text-2xl font-black text-amber-400">{maxDrawdown}%</p>
                    </IndustrialCard>
                )}
                {avgHoldingDays !== undefined && (
                    <IndustrialCard tone="secondary" className="rounded-[1.25rem]" contentClassName="p-4">
                        <p className="text-[10px] uppercase font-black tracking-widest text-gray-500">Avg Hold</p>
                        <p className="text-2xl font-black text-white">{avgHoldingDays}d</p>
                    </IndustrialCard>
                )}
                {isStrategyAttribution && (
                    <IndustrialCard tone="secondary" className="rounded-[1.25rem]" contentClassName="p-4">
                        <p className="text-[10px] uppercase font-black tracking-widest text-gray-500">Signals</p>
                        <p className="text-2xl font-black text-cyan-300">{signalQuality?.generated_count ?? 0}</p>
                    </IndustrialCard>
                )}
                {isStrategyAttribution && (
                    <IndustrialCard tone="secondary" className="rounded-[1.25rem]" contentClassName="p-4">
                        <p className="text-[10px] uppercase font-black tracking-widest text-gray-500">Fill Rate</p>
                        <p className="text-2xl font-black text-emerald-400">{signalQuality?.fill_rate ?? 0}%</p>
                    </IndustrialCard>
                )}
                {isStrategyAttribution && (
                    <IndustrialCard tone="secondary" className="rounded-[1.25rem]" contentClassName="p-4">
                        <p className="text-[10px] uppercase font-black tracking-widest text-gray-500">No-Fill</p>
                        <p className="text-2xl font-black text-amber-300">{signalQuality?.no_fill_count ?? 0}</p>
                    </IndustrialCard>
                )}
                {isStrategyAttribution && (
                    <IndustrialCard tone="secondary" className="rounded-[1.25rem]" contentClassName="p-4">
                        <p className="text-[10px] uppercase font-black tracking-widest text-gray-500">No-Trade</p>
                        <p className="text-2xl font-black text-fuchsia-300">{signalQuality?.no_trade_rate ?? 0}%</p>
                    </IndustrialCard>
                )}
            </div>

            {hasData ? (
                <>
                    <div className="mb-8">
                        <h4 className="text-sm font-black uppercase tracking-wide mb-3 border-l-4 border-blue-600 pl-3">Equity Growth</h4>
                        <IndustrialCard tone="secondary" className="rounded-[1.35rem]" contentClassName="h-[280px] p-4">
                            <MeasuredChartFrame className="h-full w-full" fallbackHeight={280}>
                                {({ width, height }) => (
                                    <AreaChart width={width} height={height} data={curve}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                        <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 10 }} minTickGap={30} />
                                        <YAxis stroke="#94a3b8" tick={{ fontSize: 10 }} />
                                        <Area type="monotone" dataKey="equity" stroke="#2563eb" fill="#1e3a8a" fillOpacity={0.3} strokeWidth={2} />
                                    </AreaChart>
                                )}
                            </MeasuredChartFrame>
                        </IndustrialCard>
                    </div>

                    <div>
                        <h4 className="text-sm font-black uppercase tracking-wide mb-3 border-l-4 border-blue-600 pl-3">Recent Executions</h4>
                        <IndustrialCard tone="secondary" className="rounded-[1.35rem] overflow-hidden" contentClassName="overflow-x-auto p-0 custom-scrollbar">
                            <table className="w-full text-sm text-left notranslate" translate="no">
                                <thead className="border-b border-white/8 bg-white/[0.02] text-gray-400 uppercase text-xs">
                                    <tr>
                                        <th className="px-4 py-2">Date</th>
                                        {isStrategyAttribution && <th className="px-4 py-2">Lane</th>}
                                        <th className="px-4 py-2">Ticker</th>
                                        <th className="px-4 py-2 text-right">Entry</th>
                                        <th className="px-4 py-2 text-right">Exit</th>
                                        <th className="px-4 py-2 text-right">PnL</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/10">
                                    {combinedRows.length > 0 ? (
                                        combinedRows.map((row) => (
                                            <tr key={row.key} className="bg-transparent hover:bg-white/5 transition">
                                                <td className="px-4 py-2 font-mono text-gray-300">{formatDate(row.date)}</td>
                                                {isStrategyAttribution && (
                                                    <td className="px-4 py-2 text-[10px] font-black uppercase tracking-widest text-cyan-300">
                                                        {executionLaneByRowKey.get(row.key) || '-'}
                                                    </td>
                                                )}
                                                <td className="px-4 py-2 font-bold text-white notranslate" translate="no">
                                                    {row.ticker}
                                                    <span className="ml-2 text-[9px] uppercase tracking-wider text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded">
                                                        {row.reason}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-2 text-right text-gray-300">{truncatePrice(row.entry)}</td>
                                                <td className="px-4 py-2 text-right text-gray-300">{truncatePrice(row.exit)}</td>
                                                <td className={row.pnl >= 0 ? "px-4 py-2 text-right font-bold text-emerald-400" : "px-4 py-2 text-right font-bold text-rose-400"}>
                                                    {Number(row.pnl).toLocaleString()}
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        legacyTrades.map((t, i) => (
                                            <tr key={`${t.ticker}-${t.exit_date}-${i}`} className={i % 2 === 0 ? 'bg-transparent' : 'bg-white/5'}>
                                                <td className="px-4 py-2 font-mono text-gray-300">{formatDate(t.exit_date)}</td>
                                                {isStrategyAttribution && <td className="px-4 py-2 text-[10px] font-black uppercase tracking-widest text-cyan-300">-</td>}
                                                <td className="px-4 py-2 font-bold text-white notranslate" translate="no">{String(t.ticker || '').toUpperCase()}</td>
                                                <td className="px-4 py-2 text-right text-gray-300">{truncatePrice(t.entry_price)}</td>
                                                <td className="px-4 py-2 text-right text-gray-300">{truncatePrice(t.exit_price)}</td>
                                                <td className={t.pnl >= 0 ? "px-4 py-2 text-right font-bold text-emerald-400" : "px-4 py-2 text-right font-bold text-rose-400"}>
                                                    {Number(t.pnl).toLocaleString()}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </IndustrialCard>
                    </div>
                </>
            ) : (
                <IndustrialCard tone="secondary" className="rounded-[1.35rem]">
                    <EmptyState
                        icon="chart"
                        title="No Report Data Yet"
                        message="No closed trades were found for this portfolio. Add or close trades in Treasury to populate this report."
                    />
                </IndustrialCard>
            )}
        </section>
    );
}
