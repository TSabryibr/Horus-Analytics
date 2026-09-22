'use client';

import { LineChart, Line, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Activity } from 'lucide-react';

import type { PriceActionCatalogItem, SimulationBacktestResult } from '../hooks/useSimulationBacktest';
import { ErrorDisplay, GlassCard, MetricBox, SimulationControls } from './SimulationPrimitives';
import { MeasuredChartFrame } from '@/app/components/charts/MeasuredChartFrame';

type StrategyBacktestPanelProps = {
    loading: boolean;
    error: string | null;
    result: SimulationBacktestResult | null;
    strategyCatalog: PriceActionCatalogItem[];
    strategyId: string;
    setStrategyId: (value: string) => void;
    market: string;
    setMarket: (value: string) => void;
    startDate: string;
    setStartDate: (value: string) => void;
    endDate: string;
    setEndDate: (value: string) => void;
    capital: string;
    setCapital: (value: string) => void;
    commission: string;
    setCommission: (value: string) => void;
    slippage: string;
    setSlippage: (value: string) => void;
    onRun: () => void | Promise<void>;
};

const MARKET_OPTIONS = ['EGX30', 'EGX70', 'EGX100', 'ALL'];

export function StrategyBacktestPanel({
    loading,
    error,
    result,
    strategyCatalog,
    strategyId,
    setStrategyId,
    market,
    setMarket,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    capital,
    setCapital,
    commission,
    setCommission,
    slippage,
    setSlippage,
    onRun,
}: StrategyBacktestPanelProps) {
    const equityChartData = (result?.equity_curve || []).map((value, index) => ({
        step: index,
        equity: value,
    }));

    return (
        <div className="space-y-8">
            <SimulationControls onSimulate={onRun} loading={loading} accentColor="cyan">
                <div className="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-4">
                    <div>
                        <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Strategy</label>
                        <select
                            value={strategyId}
                            onChange={(e) => setStrategyId(e.target.value)}
                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                        >
                            {strategyCatalog.length > 0 ? (
                                strategyCatalog.map((item) => (
                                    <option key={item.strategy_id} value={item.strategy_id}>
                                        {item.display_name || item.strategy_id}
                                    </option>
                                ))
                            ) : (
                                <option value={strategyId}>{strategyId}</option>
                            )}
                        </select>
                    </div>
                    <div>
                        <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Market</label>
                        <select
                            value={market}
                            onChange={(e) => setMarket(e.target.value)}
                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                        >
                            {MARKET_OPTIONS.map((value) => (
                                <option key={value} value={value}>{value}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Start Date</label>
                        <input
                            aria-label="Backtest Start Date"
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                        />
                    </div>
                    <div>
                        <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">End Date</label>
                        <input
                            aria-label="Backtest End Date"
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                        />
                    </div>
                    <div>
                        <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Capital</label>
                        <input
                            aria-label="Backtest Capital"
                            type="number"
                            value={capital}
                            onChange={(e) => setCapital(e.target.value)}
                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                        />
                    </div>
                    <div>
                        <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Commission (%)</label>
                        <input
                            aria-label="Commission (%)"
                            type="number"
                            value={commission}
                            onChange={(e) => setCommission(e.target.value)}
                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                        />
                    </div>
                    <div>
                        <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Slippage (%)</label>
                        <input
                            aria-label="Slippage (%)"
                            type="number"
                            value={slippage}
                            onChange={(e) => setSlippage(e.target.value)}
                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                        />
                    </div>
                </div>
            </SimulationControls>

            {error && <ErrorDisplay error={error} />}

            {result && (
                <div className="space-y-8 animate-in fade-in fill-mode-both duration-1000">
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                        <MetricBox label="Total Return" value={`${result.total_return.toFixed(2)}%`} color="cyan" tooltip="The cumulative net profit or loss generated by the strategy relative to starting capital." />
                        <MetricBox label="Max Drawdown" value={`${result.max_drawdown.toFixed(2)}%`} color="red" tooltip="The largest peak-to-trough decline in portfolio equity during the backtest timeframe." />
                        <MetricBox label="Profit Factor" value={result.profit_factor.toFixed(2)} color="orange" tooltip="Gross profits divided by gross losses. A value above 1.0 indicates a profitable system." />
                        <MetricBox label="Win Rate" value={`${result.win_rate.toFixed(2)}%`} color="yellow" tooltip="The percentage of closed trades that resulted in a positive return." />
                    </div>

                    <GlassCard title="Equity Curve" icon={<Activity className="text-cyan-500" />}>
                        <MeasuredChartFrame className="mt-6 h-[340px] w-full" fallbackHeight={340}>
                            {({ width, height }) => (
                                <LineChart width={width} height={height} data={equityChartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                    <XAxis dataKey="step" hide />
                                    <YAxis tick={{ fill: '#4b5563', fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' }} />
                                    <Line type="monotone" dataKey="equity" stroke="#06b6d4" strokeWidth={2} dot={false} />
                                </LineChart>
                            )}
                        </MeasuredChartFrame>
                    </GlassCard>
                </div>
            )}
        </div>
    );
}
