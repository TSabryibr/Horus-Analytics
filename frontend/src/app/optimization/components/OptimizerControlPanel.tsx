'use client';

import { clsx } from 'clsx';
import { Activity, Cpu, Play, RotateCw, Settings2, TrendingUp } from 'lucide-react';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';

type OptimizerControlPanelProps = {
    optIndex: string;
    setOptIndex: (value: string) => void;
    optLoading: boolean;
    optimizerStatus: string;
    optimizerIsActive: boolean;
    optimizerHasResults: boolean;
    optStatus: any;
    onRunOptimizer: () => void | Promise<void>;
    onTestMatrix: (params: any) => void;
};

export function OptimizerControlPanel({
    optIndex,
    setOptIndex,
    optLoading,
    optimizerStatus,
    optimizerIsActive,
    optimizerHasResults,
    optStatus,
    onRunOptimizer,
    onTestMatrix,
}: OptimizerControlPanelProps) {
    return (
        <div className="space-y-12 animate-in fade-in zoom-in-95 duration-700">
            <IndustrialCard
                tone="secondary"
                className="group relative overflow-hidden p-0 text-center"
                contentClassName="relative p-10 md:p-16"
            >
                <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
                <div className="absolute top-0 left-0 w-full h-1 bg-white/5 overflow-hidden">
                    <div className="h-full bg-primary/40 animate-progress w-1/4" />
                </div>

                <div className="relative z-10 max-w-2xl mx-auto">
                    <div className="relative mb-12 flex justify-center">
                        <Settings2 size={100} className="text-primary stroke-[0.5] animate-spin-slow" />
                        <div className="absolute inset-0 flex items-center justify-center">
                            <Cpu className="h-10 w-10 text-primary" />
                        </div>
                    </div>
                    <h2 className="text-4xl font-black text-white mb-6 tracking-widest uppercase italic">
                        Matrix_Convergence_Node
                    </h2>
                    <p className="text-slate-500 max-w-xl mx-auto mb-12 text-[11px] font-bold uppercase tracking-[0.2em] leading-relaxed">
                        Engaging evolutionary algorithms to simulate over <span className="text-primary">1,000 algorithmic combinations</span> against historical datasets.
                        Identifying mathematical convergence for maximum alpha generation.
                    </p>

                    <div className="flex flex-col md:flex-row justify-center items-center gap-8">
                        <div className="relative min-w-[280px]">
                            <div className="absolute -top-6 left-1 flex items-center gap-2">
                                <div className="h-1 w-1 bg-primary/40 rounded-full" />
                                <span className="text-[8px] font-black uppercase text-slate-600 tracking-[0.3em]">Target_Vector</span>
                            </div>
                            <select
                                aria-label="Optimizer Index"
                                value={optIndex}
                                onChange={(e) => setOptIndex(e.target.value)}
                                className="section-surface-muted industrial-corner w-full appearance-none border border-white/10 p-4 text-[11px] font-black uppercase tracking-[0.3em] text-slate-300 transition-all hover:border-white/16 focus:border-primary focus:outline-none"
                            >
                                <option value="EGX30" className="bg-slate-950">EGX 30 Blue Chips</option>
                                <option value="EGX70" className="bg-slate-950">EGX 70 Mid-Cap</option>
                                <option value="EGX100" className="bg-slate-950">EGX 100 Index</option>
                                <option value="ALL" className="bg-slate-950">Full Market Matrix</option>
                            </select>
                            <Activity className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-primary pointer-events-none opacity-40" />
                        </div>
                        <IndustrialButton
                            type="button"
                            onClick={onRunOptimizer}
                            disabled={optLoading}
                            variant={optLoading ? 'secondary' : 'primary'}
                            size="lg"
                            className="group/opt min-w-[300px] overflow-hidden py-4 text-[11px] tracking-[0.4em]"
                        >
                            <div className="absolute inset-0 bg-white/20 -translate-x-full group-hover/opt:translate-x-full transition-transform duration-1000 skew-x-12" />
                            {optLoading ? <RotateCw className="animate-spin h-4 w-4" /> : <Play size={16} fill="currentColor" />}
                            {optLoading ? 'Converging_Strategy' : 'Execute_Optimization'}
                        </IndustrialButton>
                    </div>

                    {(optimizerIsActive || optimizerStatus === 'COMPLETED') && (
                        <div className="mt-16 max-w-xl mx-auto animate-in slide-in-from-bottom-8 duration-1000">
                            <div className="flex justify-between text-[9px] font-black uppercase tracking-[0.4em] mb-4 text-primary">
                                <span>Convergence_Progress</span>
                                <span className="font-mono tabular-nums">{optStatus.progress ?? 0}%</span>
                            </div>
                            <div className="w-full bg-black/40 h-2 industrial-corner overflow-hidden mb-10 border border-white/5 relative">
                                <div className="absolute inset-0 scan-line opacity-20" />
                                <div className="bg-primary h-full transition-all duration-1000 ease-out" style={{ width: `${optStatus.progress ?? 0}%` }} />
                            </div>
                            {optimizerStatus === 'COMPLETED' && (
                                <div className="bg-emerald-500/5 border border-emerald-500/20 p-6 industrial-corner text-emerald-400 text-[9px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-5">
                                    <div className="h-2 w-2 rounded-full bg-emerald-500" />
                                    Optimization complete. Strategies cached in Matrix_Memory.
                                    <span className="text-[9px] font-black tracking-wider border border-emerald-400/30 bg-emerald-500/15 rounded px-1.5 py-0.5">CONVERGED ⚡</span>
                                </div>
                            )}
                        </div>
                    )}
                    {optimizerStatus === 'ERROR' && (
                        <div className="mt-10 industrial-corner border border-rose-500/30 bg-rose-500/5 p-5 text-rose-400 text-[9px] font-black uppercase tracking-[0.3em]">
                            Node_Failure: {String(optStatus.error || 'Unknown failure')}
                        </div>
                    )}
                </div>
            </IndustrialCard>

            {optimizerHasResults && (
                <IndustrialCard
                    tone="secondary"
                    className="relative overflow-hidden animate-in slide-in-from-bottom-12 duration-1000"
                    contentClassName="overflow-x-auto p-0"
                >
                    <div className="absolute inset-0 pointer-events-none border-b border-primary/5" />
                    <div className="p-10 flex items-center justify-between relative">
                        <div className="flex items-center gap-6">
                            <div className="h-8 w-1 bg-primary industrial-corner" />
                            <h2 className="text-2xl font-black uppercase tracking-widest text-white italic">Optimization_Log</h2>
                        </div>
                        <span className="text-[10px] font-black text-primary uppercase tracking-[0.4em] bg-primary/10 px-4 py-2 border border-primary/20 industrial-corner">
                            Top_Efficiency_Variants
                        </span>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-white/5 text-slate-500 text-[9px] font-black uppercase tracking-[0.4em]">
                                <tr>
                                    <th className="p-8">ID</th>
                                    <th className="p-8">Efficiency</th>
                                    <th className="p-8">Success_Rate</th>
                                    <th className="p-8">Mean_Return</th>
                                    <th className="p-8">Ops_Count</th>
                                    <th className="p-8">Vector_Config</th>
                                    <th className="p-8 text-right">Node_Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {optStatus.result.slice(0, 20).map((res: any, i: number) => (
                                    <tr key={i} className="hover:bg-primary/5 transition-all group">
                                        <td className="p-8 font-mono font-bold text-slate-600 text-xs tracking-tighter">NODE_{String(i + 1).padStart(3, '0')}</td>
                                        <td className="p-8">
                                            <div className="flex items-center gap-3">
                                                <span className="text-2xl font-black text-primary font-mono tracking-tighter">{res.score.toFixed(1)}</span>
                                                {i === 0 && <div className="p-1.5 bg-primary/20 industrial-corner"><TrendingUp size={12} className="text-primary" /></div>}
                                            </div>
                                        </td>
                                        <td className="p-8">
                                            <div className="flex flex-col gap-2">
                                                <span className="text-emerald-400 font-black font-mono text-sm tracking-tighter">{res.win_rate.toFixed(1)}%</span>
                                                <div className="w-20 h-1 bg-white/5 industrial-corner overflow-hidden">
                                                    <div className="h-full bg-emerald-500/40" style={{ width: `${res.win_rate}%` }} />
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-8 font-black font-mono tracking-tighter text-white text-lg">{res.avg_return.toFixed(2)}%</td>
                                        <td className="p-8 text-slate-500 font-mono text-xs font-bold">{res.trades} <span className="opacity-40">ops</span></td>
                                        <td className="p-8">
                                            <div className="flex flex-wrap gap-2.5">
                                                <span className="px-2.5 py-1.5 bg-black/40 text-[9px] font-black uppercase tracking-[0.2em] text-slate-400 border border-white/5 industrial-corner" title="RSI Bracket">RSI {res.params.RSI_MIN}-{res.params.RSI_MAX}</span>
                                                <span className="px-2.5 py-1.5 bg-black/40 text-[9px] font-black uppercase tracking-[0.2em] text-slate-400 border border-white/5 industrial-corner" title="Volume Spike">VOL {res.params.VOL_SPIKE}X</span>
                                                <span className="px-2.5 py-1.5 bg-rose-500/5 text-[9px] font-black uppercase tracking-[0.2em] text-rose-400/80 border border-rose-500/20 industrial-corner" title="Stop Loss">SL {res.params.SL_PCT}%</span>
                                                <span className="px-2.5 py-1.5 bg-emerald-500/5 text-[9px] font-black uppercase tracking-[0.2em] text-emerald-400/80 border border-emerald-500/20 industrial-corner" title="Take Profit 1">TP {res.params.TP1_PCT}%</span>
                                                <span className="px-2.5 py-1.5 bg-primary/5 text-[9px] font-black uppercase tracking-[0.2em] text-primary/80 border border-primary/20 industrial-corner" title="Momentum">MOM {res.params.MOMENTUM}%</span>
                                            </div>
                                        </td>
                                        <td className="p-8 text-right">
                                            <IndustrialButton
                                                type="button"
                                                onClick={() => onTestMatrix(res.params)}
                                                variant="secondary"
                                                className="px-6 py-3 text-[10px] tracking-[0.3em]"
                                            >
                                                Test_Matrix
                                            </IndustrialButton>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </IndustrialCard>
            )}
        </div>
    );
}
