'use client';

import { useState, useEffect } from 'react';
import { AlertCircle, Shield, TrendingUp, X, Activity, Flame, ShieldAlert, Zap, RefreshCw, BarChart2 } from 'lucide-react';
import clsx from 'clsx';
import { apiFetch, readJsonSafe } from '@/lib/api';
import { PortfolioAnalysisReport } from '../hooks/usePortfolioRuntime';

export interface StressScenario {
    id: string;
    name: string;
    description: string;
    loss_pct: number;
    loss_egp: number;
    remaining_net_worth: number;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'POSITIVE' | 'INFO';
}

export interface StressTestData {
    portfolio_id: number;
    net_worth_egp: number;
    invested_market_val_egp: number;
    cash_reserve_egp: number;
    portfolio_beta: number;
    daily_volatility_pct: number;
    horizon_days: number;
    simulations_count: number;
    var_95_egp: number;
    var_95_pct: number;
    var_99_egp: number;
    var_99_pct: number;
    cvar_95_egp: number;
    cvar_95_pct: number;
    monte_carlo_distribution: {
        p5_loss_pct: number;
        p25_pct: number;
        median_pct: number;
        p75_pct: number;
        p95_gain_pct: number;
    };
    scenarios: StressScenario[];
}

interface PortfolioAnalysisModalProps {
    analysis: PortfolioAnalysisReport;
    activePortfolioId?: number | null;
    onClose: () => void;
}

export function PortfolioAnalysisModal({ analysis, activePortfolioId, onClose }: PortfolioAnalysisModalProps) {
    const [activeTab, setActiveTab] = useState<'DIAGNOSTICS' | 'STRESS_TEST'>('DIAGNOSTICS');
    const [stressData, setStressData] = useState<StressTestData | null>(null);
    const [stressLoading, setStressLoading] = useState(false);

    useEffect(() => {
        if (activeTab === 'STRESS_TEST' && activePortfolioId && !stressData) {
            setStressLoading(true);
            apiFetch(`/api/v1/portfolio/stress-test?portfolio_id=${activePortfolioId}&simulations=1000&days=30`)
                .then((res) => readJsonSafe<StressTestData>(res))
                .then((data) => {
                    if (data && data.net_worth_egp !== undefined) {
                        setStressData(data);
                    }
                })
                .catch((err) => console.error('Failed to fetch stress test data:', err))
                .finally(() => setStressLoading(false));
        }
    }, [activeTab, activePortfolioId, stressData]);

    const runSimulation = () => {
        if (!activePortfolioId) return;
        setStressLoading(true);
        apiFetch(`/api/v1/portfolio/stress-test?portfolio_id=${activePortfolioId}&simulations=1000&days=30`)
            .then((res) => readJsonSafe<StressTestData>(res))
            .then((data) => {
                if (data && data.net_worth_egp !== undefined) {
                    setStressData(data);
                }
            })
            .catch((err) => console.error('Failed to run simulation:', err))
            .finally(() => setStressLoading(false));
    };

    return (
        <div className="fixed inset-0 bg-black/75 z-[110] flex items-center justify-center p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-label="Portfolio diagnostics">
            <div className="section-surface w-full max-w-4xl overflow-hidden rounded-[2rem] border border-slate-700/60 animate-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col bg-slate-900 shadow-2xl">
                {/* Header */}
                <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/80 flex-shrink-0">
                    <div>
                        <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                            Institutional Portfolio Risk Terminal
                        </h3>
                        <p className="text-xs text-slate-400 font-mono">
                            Diagnostic Health Audit & Predictive Monte Carlo Engine
                        </p>
                    </div>
                    <button type="button" onClick={onClose} aria-label="Close" className="text-slate-400 hover:text-slate-100 p-2 rounded-lg hover:bg-slate-800 transition">
                        <X size={20} />
                    </button>
                </div>

                {/* Tab Pill Switcher */}
                <div className="px-6 py-3 bg-slate-950/60 border-b border-slate-800/80 flex items-center gap-2 flex-shrink-0">
                    <button
                        onClick={() => setActiveTab('DIAGNOSTICS')}
                        className={clsx(
                            "flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all",
                            activeTab === 'DIAGNOSTICS'
                                ? "bg-cyan-950/80 text-cyan-300 border border-cyan-500/50 shadow-md shadow-cyan-950/50"
                                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                        )}
                    >
                        <Shield size={14} />
                        <span>Health Diagnostics & Heat</span>
                    </button>

                    <button
                        onClick={() => setActiveTab('STRESS_TEST')}
                        className={clsx(
                            "flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all",
                            activeTab === 'STRESS_TEST'
                                ? "bg-rose-950/80 text-rose-300 border border-rose-500/50 shadow-md shadow-rose-950/50"
                                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                        )}
                    >
                        <Activity size={14} />
                        <span>1,000-Path Monte Carlo & Stress Test</span>
                    </button>
                </div>

                {/* Body Content */}
                <div className="overflow-y-auto flex-1 p-6 space-y-6 custom-scrollbar">
                    {activeTab === 'DIAGNOSTICS' ? (
                        <>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-slate-950/40 rounded-xl p-5 border border-slate-800 text-center">
                                    <h4 className="text-xs text-slate-400 uppercase tracking-widest mb-1 font-mono">Health Score</h4>
                                    <div className={clsx('text-4xl font-black font-mono', analysis.health_score > 80 ? 'text-emerald-400' : analysis.health_score > 50 ? 'text-amber-400' : 'text-rose-400')}>
                                        {analysis.health_score} / 100
                                    </div>
                                </div>
                                <div className="bg-slate-950/40 rounded-xl p-5 border border-slate-800 text-center">
                                    <h4 className="text-xs text-slate-400 uppercase tracking-widest mb-1 font-mono">Portfolio Heat</h4>
                                    <div className={clsx('text-4xl font-black font-mono', analysis.heat < 2 ? 'text-emerald-400' : analysis.heat < 5 ? 'text-amber-400' : 'text-rose-400')}>
                                        {analysis.heat}%
                                    </div>
                                    <p className="text-[10px] text-slate-500 mt-1 font-mono">Stop-Loss Capital at Risk</p>
                                </div>
                            </div>

                            <div>
                                <h4 className="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2 uppercase tracking-wider font-mono">
                                    <Shield className="w-4 h-4 text-cyan-400" /> Guardian Risk Audit
                                </h4>
                                <div className="space-y-2.5">
                                    {!analysis.recommendations || analysis.recommendations.length === 0 ? (
                                        <div className="p-4 bg-emerald-950/30 border border-emerald-500/30 rounded-xl text-emerald-300 text-xs flex items-center gap-3">
                                            <TrendingUp size={18} />
                                            <span>No critical issues detected. Your portfolio structure is healthy.</span>
                                        </div>
                                    ) : (
                                        analysis.recommendations.map((rec, index) => (
                                            <div
                                                key={index}
                                                className={clsx(
                                                    'p-3.5 rounded-xl border flex gap-3 text-xs',
                                                    rec.severity === 'HIGH' ? 'bg-rose-950/30 border-rose-500/30' : 'bg-amber-950/30 border-amber-500/30'
                                                )}
                                            >
                                                <div className={clsx('mt-0.5', rec.severity === 'HIGH' ? 'text-rose-400' : 'text-amber-400')}>
                                                    <AlertCircle size={16} />
                                                </div>
                                                <div>
                                                    <h5 className={clsx('font-bold font-mono', rec.severity === 'HIGH' ? 'text-rose-300' : 'text-amber-300')}>
                                                        {rec.title}
                                                    </h5>
                                                    <p className="text-slate-300 text-[11px] mt-0.5">{rec.message}</p>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>

                            <div>
                                <h4 className="text-sm font-bold text-slate-200 mb-3 uppercase tracking-wider font-mono">
                                    Sector Exposure Breakdown
                                </h4>
                                <div className="grid grid-cols-2 lg:grid-cols-3 gap-2.5">
                                    {analysis.sector_breakdown && Object.keys(analysis.sector_breakdown).length > 0 ? (
                                        Object.entries(analysis.sector_breakdown).map(([sector, count]) => (
                                            <div key={sector} className="bg-slate-950/40 border border-slate-800 rounded-lg p-2.5 flex justify-between items-center text-xs">
                                                <span className="text-slate-300">{sector}</span>
                                                <span className="bg-cyan-950 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded text-[10px] font-mono font-bold">{count}</span>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="col-span-full text-center py-4 text-slate-500 text-xs italic">
                                            No sector data available.
                                        </div>
                                    )}
                                </div>
                            </div>
                        </>
                    ) : (
                        /* Monte Carlo & Crisis Stress-Testing Tab */
                        <div className="space-y-6">
                            <div className="flex justify-between items-center bg-slate-950/40 p-4 rounded-xl border border-slate-800">
                                <div>
                                    <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                                        <Activity size={16} className="text-rose-400" />
                                        1,000-Path Monte Carlo Simulation (30-Day Horizon)
                                    </h4>
                                    <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                                        Calculates tail risk loss distributions and systemic crash resilience
                                    </p>
                                </div>
                                <button
                                    onClick={runSimulation}
                                    disabled={stressLoading}
                                    className="flex items-center gap-2 px-3 py-1.5 bg-rose-950/70 hover:bg-rose-900 border border-rose-500/50 text-rose-200 text-xs font-semibold rounded-lg transition-all"
                                >
                                    <RefreshCw size={13} className={clsx(stressLoading && "animate-spin text-rose-300")} />
                                    <span>Rerun Simulation</span>
                                </button>
                            </div>

                            {stressLoading && !stressData ? (
                                <div className="p-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
                                    <RefreshCw size={24} className="animate-spin text-rose-400" />
                                    <p className="text-xs font-mono">Generating 1,000 Brownian motion asset trajectories...</p>
                                </div>
                            ) : stressData ? (
                                <div className="space-y-6">
                                    {/* VaR and CVaR KPI Cards */}
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                        <div className="bg-slate-950/50 p-4 rounded-xl border border-rose-500/30">
                                            <div className="text-[10px] uppercase font-mono text-rose-400 font-bold tracking-wider">
                                                Value at Risk (VaR 95%)
                                            </div>
                                            <div className="text-2xl font-black text-rose-300 font-mono mt-1">
                                                -{stressData.var_95_pct.toFixed(1)}%
                                            </div>
                                            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                                                -{(stressData.var_95_egp || 0).toLocaleString()} EGP (30D)
                                            </div>
                                        </div>

                                        <div className="bg-slate-950/50 p-4 rounded-xl border border-rose-600/40">
                                            <div className="text-[10px] uppercase font-mono text-rose-400 font-bold tracking-wider">
                                                Extreme VaR (99%)
                                            </div>
                                            <div className="text-2xl font-black text-rose-200 font-mono mt-1">
                                                -{stressData.var_99_pct.toFixed(1)}%
                                            </div>
                                            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                                                -{(stressData.var_99_egp || 0).toLocaleString()} EGP (30D)
                                            </div>
                                        </div>

                                        <div className="bg-slate-950/50 p-4 rounded-xl border border-amber-500/30">
                                            <div className="text-[10px] uppercase font-mono text-amber-400 font-bold tracking-wider">
                                                Expected Shortfall (CVaR)
                                            </div>
                                            <div className="text-2xl font-black text-amber-300 font-mono mt-1">
                                                -{stressData.cvar_95_pct.toFixed(1)}%
                                            </div>
                                            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                                                -{(stressData.cvar_95_egp || 0).toLocaleString()} EGP (tail avg)
                                            </div>
                                        </div>
                                    </div>

                                    {/* Monte Carlo Quantile Distribution */}
                                    <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-3">
                                        <div className="flex justify-between items-center">
                                            <h5 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">
                                                Monte Carlo 30-Day Return Distribution
                                            </h5>
                                            <span className="text-[10px] font-mono text-slate-500">1,000 Iterations</span>
                                        </div>

                                        <div className="grid grid-cols-5 gap-2 text-center text-xs font-mono">
                                            <div className="p-2 rounded bg-rose-950/40 border border-rose-500/30">
                                                <div className="text-[9px] text-rose-400">5th %ile (Worst)</div>
                                                <div className="font-bold text-rose-300 mt-1">{stressData.monte_carlo_distribution.p5_loss_pct}%</div>
                                            </div>
                                            <div className="p-2 rounded bg-amber-950/30 border border-amber-500/30">
                                                <div className="text-[9px] text-amber-400">25th %ile</div>
                                                <div className="font-bold text-amber-300 mt-1">{stressData.monte_carlo_distribution.p25_pct}%</div>
                                            </div>
                                            <div className="p-2 rounded bg-slate-800 border border-slate-700">
                                                <div className="text-[9px] text-slate-400">Median (50th)</div>
                                                <div className="font-bold text-slate-100 mt-1">{stressData.monte_carlo_distribution.median_pct}%</div>
                                            </div>
                                            <div className="p-2 rounded bg-emerald-950/30 border border-emerald-500/30">
                                                <div className="text-[9px] text-emerald-400">75th %ile</div>
                                                <div className="font-bold text-emerald-300 mt-1">+{stressData.monte_carlo_distribution.p75_pct}%</div>
                                            </div>
                                            <div className="p-2 rounded bg-emerald-950/50 border border-emerald-500/40">
                                                <div className="text-[9px] text-emerald-300">95th %ile (Best)</div>
                                                <div className="font-bold text-emerald-200 mt-1">+{stressData.monte_carlo_distribution.p95_gain_pct}%</div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Macro Crisis Scenarios */}
                                    <div className="space-y-3">
                                        <h5 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-2">
                                            <ShieldAlert size={14} className="text-amber-400" />
                                            Macro & Crisis Shock Stress Scenarios
                                        </h5>

                                        <div className="grid grid-cols-1 gap-2.5">
                                            {stressData.scenarios.map((sc) => (
                                                <div
                                                    key={sc.id}
                                                    className="p-3.5 bg-slate-950/40 border border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-3 text-xs"
                                                >
                                                    <div className="space-y-0.5 max-w-md">
                                                        <div className="font-bold text-slate-200 flex items-center gap-2">
                                                            <span>{sc.name}</span>
                                                            <span className={clsx(
                                                                "text-[9px] px-1.5 py-0.5 rounded font-mono font-bold border",
                                                                sc.severity === 'CRITICAL' && "bg-rose-950 text-rose-300 border-rose-500/50",
                                                                sc.severity === 'HIGH' && "bg-rose-950/60 text-rose-400 border-rose-500/30",
                                                                sc.severity === 'MEDIUM' && "bg-amber-950/60 text-amber-300 border-amber-500/30",
                                                                sc.severity === 'LOW' && "bg-slate-800 text-slate-300 border-slate-700",
                                                                sc.severity === 'POSITIVE' && "bg-emerald-950 text-emerald-300 border-emerald-500/30"
                                                            )}>
                                                                {sc.severity}
                                                            </span>
                                                        </div>
                                                        <p className="text-[11px] text-slate-400">{sc.description}</p>
                                                    </div>

                                                    <div className="text-right font-mono">
                                                        <div className={clsx(
                                                            "font-bold text-sm",
                                                            sc.loss_pct > 0 ? "text-rose-400" : "text-emerald-400"
                                                        )}>
                                                            {sc.loss_pct > 0 ? '-' : '+'}{Math.abs(sc.loss_pct).toFixed(1)}%
                                                        </div>
                                                        <div className="text-[10px] text-slate-500">
                                                            Remaining: {sc.remaining_net_worth.toLocaleString()} EGP
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            ) : null}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
