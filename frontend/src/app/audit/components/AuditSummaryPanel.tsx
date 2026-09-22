'use client';

import { ShieldAlert, TrendingUp } from 'lucide-react';

import { Strategy } from '@/types/domain';

import { StrategyCard } from './StrategyCard';

interface AuditSummaryPanelProps {
    strategies: Strategy[];
    colors: string[];
}

export function AuditSummaryPanel({ strategies, colors }: AuditSummaryPanelProps) {
    const averageWinRate = Math.round(
        strategies.reduce((acc, cur) => acc + (cur.win_rate || 0), 0) / (strategies.length || 1)
    );
    const averageConversion = Math.round(
        strategies.reduce((acc, cur) => acc + (cur.conversion_rate || 0), 0) / (strategies.length || 1)
    );
    const averageExpectedValue =
        strategies.reduce((acc, cur) => acc + (cur.expected_value || 0), 0) / (strategies.length || 1);

    return (
        <>
            <div className="col-span-12 lg:col-span-4 space-y-6">
                <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-[2rem] p-8 text-white relative overflow-hidden group">
                    <div className="relative z-10">
                        <ShieldAlert className="w-10 h-10 mb-6 text-blue-200 opacity-50" />
                        <h3 className="text-sm font-black uppercase tracking-[0.2em] mb-1 opacity-70 italic">Global Precision</h3>
                        <div className="text-5xl font-black tracking-tighter mb-4">{averageWinRate}%</div>
                        <div className="grid grid-cols-2 gap-4 pt-6 border-t border-white/10">
                            <div>
                                <div className="text-[10px] font-black uppercase tracking-widest opacity-60">Converted</div>
                                <div className="text-xl font-bold">{averageConversion}%</div>
                            </div>
                            <div>
                                <div className="text-[10px] font-black uppercase tracking-widest opacity-60">EV/Signal</div>
                                <div className="text-xl font-bold">+{averageExpectedValue.toFixed(2)}%</div>
                            </div>
                        </div>
                    </div>
                    <TrendingUp className="absolute -bottom-10 -right-10 w-64 h-64 text-white/5 rotate-[-15deg] pointer-events-none group-hover:scale-110 transition-transform duration-1000" />
                </div>

                <div className="bg-slate-900/40 border border-white/5 rounded-[2rem] p-8">
                    <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-6">Strategy Health Radar</h4>
                    <div className="space-y-6">
                        {strategies.slice(0, 3).map((strat, index) => (
                            <div key={strat.name} className="flex items-center justify-between group">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-xl bg-slate-800 flex items-center justify-center text-[10px] font-black text-slate-400 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                                        {index + 1}
                                    </div>
                                    <div>
                                        <div className="text-xs font-black text-white uppercase">{strat.name}</div>
                                        <div className="text-[10px] text-slate-500">{strat.count} Audits</div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span className="text-gray-400 text-xs">EV: +{(strat.expected_value || 0).toFixed(2)}%</span>
                                    <div className="w-20 h-1 bg-slate-800 rounded-full mt-1.5 overflow-hidden">
                                        <div
                                            className="h-full bg-emerald-500 transition-all duration-1000"
                                            style={{ width: `${Math.min(100, ((strat.expected_value || 0) / 5) * 100)}%` }}
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                    <button
                        onClick={() => document.getElementById('intelligence-log')?.scrollIntoView({ behavior: 'smooth' })}
                        className="w-full mt-8 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest hover:text-white transition-colors border-t border-white/5"
                    >
                        View Full Intelligence →
                    </button>
                </div>
            </div>

            <div className="col-span-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {strategies.map((strat, idx) => (
                    <StrategyCard key={strat.name} strat={strat} colors={colors} idx={idx} />
                ))}
            </div>
        </>
    );
}
