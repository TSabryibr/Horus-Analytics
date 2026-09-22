'use client';

import { Activity } from 'lucide-react';
import { CartesianGrid, Line, LineChart, Tooltip, XAxis, YAxis } from 'recharts';

import type { MonteCarloResult } from '../hooks/useStrategyMonteCarlo';
import { DistributionRow, ErrorDisplay, GlassCard, MetricBox, SimulationControls } from './SimulationPrimitives';
import { MeasuredChartFrame } from '@/app/components/charts/MeasuredChartFrame';

type StrategyMonteCarloPanelProps = {
    mcLoading: boolean;
    mcResult: MonteCarloResult | null;
    mcError: string | null;
    mcCapital: string;
    setMcCapital: (value: string) => void;
    mcSims: string;
    setMcSims: (value: string) => void;
    mcRuinThreshold: string;
    setMcRuinThreshold: (value: string) => void;
    mcChartData: Array<Record<string, number>>;
    onSimulate: () => void | Promise<void>;
};

export function StrategyMonteCarloPanel({
    mcLoading,
    mcResult,
    mcError,
    mcCapital,
    setMcCapital,
    mcSims,
    setMcSims,
    mcRuinThreshold,
    setMcRuinThreshold,
    mcChartData,
    onSimulate,
}: StrategyMonteCarloPanelProps) {
    return (
        <div className="animate-in fade-in slide-in-from-bottom-6 duration-700">
            <SimulationControls onSimulate={onSimulate} loading={mcLoading} accentColor="cyan">
                <div className="flex-1">
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Strategy Capital</label>
                    <input
                        aria-label="Strategy Capital"
                        type="number"
                        value={mcCapital}
                        onChange={(e) => setMcCapital(e.target.value)}
                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                    />
                </div>
                <div className="flex-1">
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Sim Cycles</label>
                    <input
                        aria-label="Sim Cycles"
                        type="number"
                        value={mcSims}
                        onChange={(e) => setMcSims(e.target.value)}
                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                    />
                </div>
                <div className="flex-1">
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Ruin Threshold (%)</label>
                    <input
                        aria-label="Ruin Threshold (%)"
                        type="number"
                        value={mcRuinThreshold}
                        onChange={(e) => setMcRuinThreshold(e.target.value)}
                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                    />
                </div>
            </SimulationControls>

            {mcError && <ErrorDisplay error={mcError} />}

            {mcResult && (
                <div className="mt-12 space-y-8 animate-in fade-in fill-mode-both duration-1000">
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                        <MetricBox label="Median Outcome" value={`EGP ${mcResult.median_equity.toLocaleString()}`} color="cyan" tooltip="The 50th percentile final equity value across all simulated path runs." />
                        <MetricBox label="Loss Probability" value={`${(mcResult.loss_probability ?? 0).toFixed(2)}%`} color="orange" tooltip="The percentage of simulated paths that ended below the starting capital." />
                        <MetricBox label={`${(mcResult.ruin_threshold_pct ?? 50).toFixed(0)}% Ruin Risk`} value={`${mcResult.ruin_probability.toFixed(2)}%`} color="red" tooltip="The probability that capital drops below the specified ruin threshold percentage at any point." />
                        <MetricBox label="Worst Drawdown" value={`${mcResult.worst_max_drawdown.toFixed(1)}%`} color="orange" tooltip="The maximum peak-to-trough decline observed in the worst performing simulated path." />
                        <MetricBox label="20% DD Prob" value={`${mcResult.drawdown_probability_20.toFixed(1)}%`} color="yellow" tooltip="The probability of experiencing at least a 20% drawdown during the strategy lifecycle." />
                    </div>

                    <GlassCard title="Monte Carlo Strategy Paths" icon={<Activity className="text-cyan-500" />}>
                        <MeasuredChartFrame className="mt-6 h-[400px] w-full" fallbackHeight={400}>
                            {({ width, height }) => (
                                <LineChart width={width} height={height} data={mcChartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                    <XAxis dataKey="name" hide />
                                    <YAxis domain={['auto', 'auto']} tick={{ fill: '#4b5563', fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' }} />
                                    {mcResult.plot_paths.map((_, idx) => (
                                        <Line
                                            key={idx}
                                            type="monotone"
                                            dataKey={`p${idx}`}
                                            stroke="#06b6d4"
                                            strokeWidth={0.5}
                                            strokeOpacity={0.1}
                                            dot={false}
                                            isAnimationActive={false}
                                        />
                                    ))}
                                    <Line type="monotone" dataKey="p0" stroke="#06b6d4" strokeWidth={2} dot={false} />
                                </LineChart>
                            )}
                        </MeasuredChartFrame>
                    </GlassCard>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-6">
                            <h4 className="text-xs font-black text-slate-500 uppercase tracking-widest mb-6 border-b border-white/5 pb-4">Statistical Distributions</h4>
                            <div className="space-y-6">
                                <DistributionRow label="50% Drawdown Prob" value={mcResult.drawdown_probability_50} color="red" />
                                <DistributionRow label="20% Drawdown Prob" value={mcResult.drawdown_probability_20} color="orange" />
                                <DistributionRow label={`${(mcResult.ruin_threshold_pct ?? 50).toFixed(0)}% Ruin Risk`} value={mcResult.ruin_probability} color="rose" />
                            </div>
                        </div>
                        <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-6">
                            <h4 className="text-xs font-black text-slate-500 uppercase tracking-widest mb-6 border-b border-white/5 pb-4">Simulation Metadata</h4>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                    <span className="block text-[8px] font-bold text-slate-500 uppercase mb-1">Total Cycles</span>
                                    <span className="text-xl font-mono text-slate-100">{mcResult.simulations}</span>
                                </div>
                                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                    <span className="block text-[8px] font-bold text-slate-500 uppercase mb-1">Median DD</span>
                                    <span className="text-xl font-mono text-slate-100">{mcResult.median_max_drawdown.toFixed(1)}%</span>
                                </div>
                                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                    <span className="block text-[8px] font-bold text-slate-500 uppercase mb-1">Ruin Floor</span>
                                    <span className="text-xl font-mono text-slate-100">EGP {(mcResult.ruin_floor ?? 0).toLocaleString()}</span>
                                </div>
                                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                    <span className="block text-[8px] font-bold text-slate-500 uppercase mb-1">Worst Equity</span>
                                    <span className="text-xl font-mono text-cyan-400">EGP {mcResult.worst_case_equity.toLocaleString()}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
