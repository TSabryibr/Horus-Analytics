'use client';

import { TrendingUp } from 'lucide-react';
import { CartesianGrid, Line, LineChart, Tooltip, XAxis, YAxis } from 'recharts';

import type { RagnarokResult } from '../hooks/useRagnarokSimulation';
import { ErrorDisplay, GlassCard, MetricBox, SimulationControls } from './SimulationPrimitives';
import { MeasuredChartFrame } from '@/app/components/charts/MeasuredChartFrame';

type RagnarokSimulationPanelProps = {
    ragnarokLoading: boolean;
    ragnarokResult: RagnarokResult | null;
    ragnarokError: string | null;
    ragnarokIterations: string;
    setRagnarokIterations: (value: string) => void;
    ragnarokDays: string;
    setRagnarokDays: (value: string) => void;
    ragnarokStartingValue: string;
    setRagnarokStartingValue: (value: string) => void;
    ragnarokRuinThresholdPct: string;
    setRagnarokRuinThresholdPct: (value: string) => void;
    tickerInput: string;
    setTickerInput: (value: string) => void;
    ragnarokChartData: Array<Record<string, number>>;
    onSimulate: () => void | Promise<void>;
};

export function RagnarokSimulationPanel({
    ragnarokLoading,
    ragnarokResult,
    ragnarokError,
    ragnarokIterations,
    setRagnarokIterations,
    ragnarokDays,
    setRagnarokDays,
    ragnarokStartingValue,
    setRagnarokStartingValue,
    ragnarokRuinThresholdPct,
    setRagnarokRuinThresholdPct,
    tickerInput,
    setTickerInput,
    ragnarokChartData,
    onSimulate,
}: RagnarokSimulationPanelProps) {
    return (
        <div className="animate-in fade-in slide-in-from-bottom-6 duration-700">
            <SimulationControls onSimulate={onSimulate} loading={ragnarokLoading} accentColor="orange">
                <div className="lg:col-span-2">
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Universe Tickers</label>
                    <input
                        aria-label="Universe Tickers"
                        type="text"
                        value={tickerInput}
                        onChange={(e) => setTickerInput(e.target.value)}
                        placeholder="COMI, ETEL, CCAP..."
                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-orange-500/50"
                    />
                </div>
                <div>
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Cycles</label>
                    <input
                        aria-label="Cycles"
                        type="number"
                        value={ragnarokIterations}
                        onChange={(e) => setRagnarokIterations(e.target.value)}
                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-orange-500/50"
                    />
                </div>
                <div>
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Horizon (Days)</label>
                    <input
                        aria-label="Horizon (Days)"
                        type="number"
                        value={ragnarokDays}
                        onChange={(e) => setRagnarokDays(e.target.value)}
                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-orange-500/50"
                    />
                </div>
                <div>
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Starting Value (EGP)</label>
                    <input
                        aria-label="Starting Value (EGP)"
                        type="number"
                        value={ragnarokStartingValue}
                        onChange={(e) => setRagnarokStartingValue(e.target.value)}
                        placeholder="Auto from account"
                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-orange-500/50"
                    />
                </div>
                <div>
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Ruin Threshold (%)</label>
                    <input
                        aria-label="Ruin Threshold (%)"
                        type="number"
                        value={ragnarokRuinThresholdPct}
                        onChange={(e) => setRagnarokRuinThresholdPct(e.target.value)}
                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-orange-500/50"
                    />
                </div>
            </SimulationControls>

            {ragnarokError && <ErrorDisplay error={ragnarokError} />}

            {ragnarokResult && (
                <div className="mt-12 space-y-8 animate-in fade-in fill-mode-both duration-1000">
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                        <MetricBox label="Expected Value" value={`EGP ${ragnarokResult.expected_value.toLocaleString()}`} color="cyan" />
                        <MetricBox label="95% VaR Floor" value={`EGP ${ragnarokResult.var_95.toLocaleString()}`} color="yellow" />
                        <MetricBox label="Loss Probability" value={`${(ragnarokResult.loss_probability ?? 0).toFixed(2)}%`} color="orange" />
                        <MetricBox label={`${(ragnarokResult.ruin_threshold_pct ?? 50).toFixed(0)}% Ruin Risk`} value={`${ragnarokResult.ruin_probability.toFixed(2)}%`} color="red" />
                        <MetricBox label="Sample Size" value={`${ragnarokResult.iterations} Paths`} color="slate" />
                    </div>

                    <GlassCard title="Probabilistic Trajectories" icon={<TrendingUp className="text-orange-500" />}>
                        <MeasuredChartFrame className="mt-6 h-[400px] w-full" fallbackHeight={400}>
                            {({ width, height }) => (
                                <LineChart width={width} height={height} data={ragnarokChartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                    <XAxis dataKey="name" hide />
                                    <YAxis domain={['auto', 'auto']} tick={{ fill: '#4b5563', fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' }}
                                        labelStyle={{ color: '#94a3b8', marginBottom: '8px' }}
                                    />
                                    {ragnarokResult.plot_paths.map((_, idx) => (
                                        <Line
                                            key={idx}
                                            type="monotone"
                                            dataKey={`p${idx}`}
                                            stroke="#f97316"
                                            strokeWidth={idx === 0 ? 2 : 0.5}
                                            strokeOpacity={idx === 0 ? 1 : 0.15}
                                            dot={false}
                                            isAnimationActive={false}
                                        />
                                    ))}
                                </LineChart>
                            )}
                        </MeasuredChartFrame>
                    </GlassCard>
                </div>
            )}
        </div>
    );
}
