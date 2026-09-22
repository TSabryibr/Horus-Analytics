'use client';

import clsx from 'clsx';
import { AlertTriangle, ShieldCheck } from 'lucide-react';
import { Bar, BarChart, Cell, Tooltip, XAxis, YAxis } from 'recharts';

import type { StressResult } from '../hooks/useCrashSimulation';
import { GlassCard, MetricBox, SimulationControls } from './SimulationPrimitives';
import { MeasuredChartFrame } from '@/app/components/charts/MeasuredChartFrame';

type CrashSimulationPanelProps = {
    stressLoading: boolean;
    stressResult: StressResult | null;
    indexChoice: string;
    setIndexChoice: (value: string) => void;
    startDate: string;
    setStartDate: (value: string) => void;
    initialCapital: string;
    setInitialCapital: (value: string) => void;
    onSimulate: () => void | Promise<void>;
};

export function CrashSimulationPanel({
    stressLoading,
    stressResult,
    indexChoice,
    setIndexChoice,
    startDate,
    setStartDate,
    initialCapital,
    setInitialCapital,
    onSimulate,
}: CrashSimulationPanelProps) {
    return (
        <div className="animate-in fade-in slide-in-from-bottom-6 duration-700">
            <SimulationControls onSimulate={onSimulate} loading={stressLoading} accentColor="red">
                <div className="flex-1">
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Target Index</label>
                    <div className="flex gap-2">
                        {['EGX30', 'EGX70', 'FINANCIALS'].map((idx) => (
                            <button
                                key={idx}
                                onClick={() => setIndexChoice(idx)}
                                className={clsx(
                                    'px-4 py-2 rounded-lg text-xs font-bold transition-all border leading-none',
                                    indexChoice === idx
                                        ? 'bg-red-500/10 text-red-400 border-red-500/30'
                                        : 'bg-white/5 text-slate-500 border-transparent hover:border-white/10'
                                )}
                            >
                                {idx}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="flex-1">
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Ref Date</label>
                    <input
                        aria-label="Ref Date"
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-red-500/50 transition-all"
                    />
                </div>
                <div className="flex-1">
                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Base Capital (EGP)</label>
                    <input
                        aria-label="Base Capital (EGP)"
                        type="number"
                        value={initialCapital}
                        onChange={(e) => setInitialCapital(e.target.value)}
                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-red-500/50 transition-all"
                    />
                </div>
            </SimulationControls>

            {stressResult && (
                <div className="mt-12 space-y-8 animate-in fade-in fill-mode-both duration-1000">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <MetricBox label="Worst Historical Date" value={stressResult.crash_date} color="slate" />
                        <MetricBox label="Market Shock Impact" value={`${stressResult.market_impact}%`} color="red" />
                        <MetricBox label="Base Capital" value={`EGP ${((stressResult.initial_capital ?? Number(initialCapital)) || 0).toLocaleString()}`} color="orange" />
                        <MetricBox label="Projected Ending Capital" value={`EGP ${(stressResult.ending_capital ?? 0).toLocaleString()}`} color="cyan" />
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        <GlassCard title="Vulnerability Spectrum" icon={<AlertTriangle className="text-red-500" />}>
                            <MeasuredChartFrame className="mt-4 h-[350px] w-full" fallbackHeight={350}>
                                {({ width, height }) => (
                                    <BarChart width={width} height={height} data={stressResult.worst_affected} layout="vertical" margin={{ left: 20 }}>
                                        <XAxis type="number" hide />
                                        <YAxis type="category" dataKey="Ticker" width={60} tick={{ fill: '#64748b', fontSize: 10, fontWeight: 700 }} />
                                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' }} />
                                        <Bar dataKey="Total_Drop_%" fill="#ef4444" radius={[0, 8, 8, 0]}>
                                            {stressResult.worst_affected.map((_, index: number) => (
                                                <Cell key={`cell-${index}`} fillOpacity={1 - index * 0.08} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                )}
                            </MeasuredChartFrame>
                        </GlassCard>

                        <GlassCard title="Defensive Outliers" icon={<ShieldCheck className="text-emerald-500" />}>
                            <div className="overflow-hidden rounded-2xl border border-white/5 mt-4">
                                <table className="w-full text-left text-xs border-collapse">
                                    <thead>
                                        <tr className="bg-white/5 text-slate-500 font-black uppercase tracking-widest">
                                            <th className="p-4">Ticker</th>
                                            <th className="p-4">Current</th>
                                            <th className="p-4">Simulated</th>
                                            <th className="p-4 text-right">Delta</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {stressResult.least_affected.map((item: any, idx: number) => (
                                            <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition">
                                                <td className="p-4 font-black text-emerald-400">{item.Ticker}</td>
                                                <td className="p-4 text-slate-400 font-mono">{item.Current_Price}</td>
                                                <td className="p-4 text-slate-200 font-mono">{Number(item.Final_Price).toFixed(2)}</td>
                                                <td className="p-4 text-right font-black text-emerald-500/80">{item['Total_Drop_%']}%</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </GlassCard>
                    </div>
                </div>
            )}
        </div>
    );
}
