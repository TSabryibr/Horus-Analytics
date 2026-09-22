'use client';

import React, { useState } from 'react';
import { Activity, Target, TrendingUp, AlertTriangle, Copy } from 'lucide-react';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';
import { SystemComparisonResult } from '../hooks/useSystemPerformance';

interface SystemComparisonSectionProps {
    comparison: SystemComparisonResult | null;
    loading: boolean;
    activePortfolioId: number | null;
    onReplicatePortfolio?: (sourcePortfolioId: number) => Promise<void> | void;
}

export function SystemComparisonSection({ comparison, loading, activePortfolioId, onReplicatePortfolio }: SystemComparisonSectionProps) {
    const [replicatingId, setReplicatingId] = useState<number | null>(null);
    const portfolios = Array.isArray(comparison?.portfolios) ? comparison.portfolios : [];

    const handleReplicate = async (portfolioId: number) => {
        if (!onReplicatePortfolio || replicatingId !== null || !activePortfolioId) return;
        try {
            setReplicatingId(portfolioId);
            await onReplicatePortfolio(portfolioId);
        } finally {
            setReplicatingId(null);
        }
    };

    if (loading && !comparison) {
        return (
            <section className="section-surface mt-10 p-8" aria-label="System Comparison">
                <div className="flex flex-col gap-4">
                    <div className="h-5 bg-white/10 rounded w-56" />
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="h-48 bg-white/5 rounded" />
                        <div className="h-48 bg-white/5 rounded" />
                        <div className="h-48 bg-white/5 rounded" />
                    </div>
                </div>
            </section>
        );
    }

    if (!comparison || portfolios.length === 0) {
        return null;
    }

    return (
        <section className="section-surface mt-10 p-8" aria-label="System Comparison">
            <div className="flex items-center gap-4 mb-6">
                <Activity className="w-8 h-8 text-cyan-400" />
                <div>
                    <h3 className="text-xl font-black uppercase tracking-tighter text-white">System Fleet Comparison</h3>
                    <p className="text-xs text-gray-400">Live performance telemetry & 1-Click Fleet Book Replication</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {portfolios.map((perf) => {
                    const isActive = perf.portfolio.id === activePortfolioId;
                    const isProfitable = perf.metrics.total_pnl >= 0;
                    const isReplicating = replicatingId === perf.portfolio.id;

                    return (
                        <IndustrialCard
                            key={perf.portfolio.id}
                            tone={isActive ? 'primary' : 'secondary'}
                            className={`rounded-[1.25rem] relative overflow-hidden transition-all duration-300 ${isActive ? 'ring-2 ring-cyan-500/50' : 'hover:border-cyan-500/30'}`}
                        >
                            <div className="p-5">
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h4 className="text-lg font-black text-white">{perf.portfolio.name}</h4>
                                        <span className="text-[10px] uppercase tracking-widest text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded">
                                            {perf.portfolio.type}
                                        </span>
                                    </div>
                                    {isActive ? (
                                        <div className="animate-pulse flex items-center gap-1 text-[10px] text-cyan-400 font-bold uppercase tracking-wider bg-cyan-500/10 px-2 py-1 rounded">
                                            <Target className="w-4 h-4 text-cyan-400" /> Active
                                        </div>
                                    ) : onReplicatePortfolio && (
                                        <button
                                            type="button"
                                            onClick={() => handleReplicate(perf.portfolio.id)}
                                            disabled={isReplicating || replicatingId !== null || !activePortfolioId}
                                            className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-amber-300 bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/20 px-2.5 py-1 rounded transition disabled:opacity-50"
                                            title={!activePortfolioId ? "Select an active target portfolio first" : "Replicate this System Fleet holdings into active portfolio"}
                                        >
                                            {isReplicating ? (
                                                <Activity className="w-3 h-3 animate-spin text-amber-300" />
                                            ) : (
                                                <>
                                                    <Copy className="w-3 h-3" /> Replicate Fleet
                                                </>
                                            )}
                                        </button>
                                    )}
                                </div>

                                <div className="grid grid-cols-2 gap-y-4 gap-x-2 mt-4">
                                    <div>
                                        <p className="text-[10px] uppercase font-black tracking-widest text-gray-500 mb-1">Win Rate</p>
                                        <p className="text-xl font-bold text-white">{perf.metrics.win_rate}%</p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] uppercase font-black tracking-widest text-gray-500 mb-1">Total PnL</p>
                                        <p className={`text-xl font-bold ${isProfitable ? 'text-emerald-400' : 'text-rose-400'}`}>
                                            {perf.metrics.total_pnl > 0 ? '+' : ''}{perf.metrics.total_pnl.toLocaleString()} EGP
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] uppercase font-black tracking-widest text-gray-500 mb-1">Profit Factor</p>
                                        <p className="text-lg font-bold text-fuchsia-400">{perf.metrics.profit_factor}</p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] uppercase font-black tracking-widest text-gray-500 mb-1 flex items-center gap-1">
                                            Drawdown <AlertTriangle className="w-3 h-3 text-amber-500" />
                                        </p>
                                        <p className="text-lg font-bold text-amber-400">{perf.metrics.max_drawdown}%</p>
                                    </div>
                                </div>

                                <div className="mt-5 pt-4 border-t border-white/5 flex justify-between items-center text-xs text-gray-400">
                                    <span className="flex items-center gap-1">
                                        <TrendingUp className="w-3 h-3" /> {perf.metrics.total_trades} Trades
                                    </span>
                                    <span>{perf.summary.open_positions} Active</span>
                                </div>
                            </div>
                        </IndustrialCard>
                    );
                })}
            </div>
        </section>
    );
}
