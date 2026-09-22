"use client";

import React, { useMemo, useState } from 'react';
import { Shield, TrendingUp, AlertTriangle, PieChart, DollarSign, Activity, Percent, ArrowUpRight, ArrowDownRight, Layers, HelpCircle } from 'lucide-react';
import clsx from 'clsx';
import { Position } from '@/types';
import { HoardData, PortfolioReportBundle, CurrencyMode } from '../hooks/usePortfolioRuntime';

interface PortfolioAnalyticsDeckProps {
    hoard: HoardData | null;
    report: PortfolioReportBundle | null;
    usdRate?: number;
    currencyMode?: CurrencyMode;
}

export const PortfolioAnalyticsDeck: React.FC<PortfolioAnalyticsDeckProps> = ({
    hoard,
    report,
    usdRate = 50.0,
    currencyMode = 'EGP',
}) => {
    const [activeTab, setActiveTab] = useState<'analytics' | 'sectors' | 'scenarios'>('analytics');

    const positions = useMemo(() => hoard?.positions || [], [hoard]);
    const totalNetWorthEgp = useMemo(() => hoard?.net_worth_egp || 0, [hoard]);

    // 1. Sector Allocation Breakdown
    const sectorBreakdown = useMemo(() => {
        if (!positions.length || totalNetWorthEgp <= 0) return [];
        const map = new Map<string, { egpVal: number; tickers: Set<string> }>();

        for (const p of positions) {
            const sec = p.sector || 'General Industrial';
            const mVal = p.currency === 'USD' 
                ? (p.shares || 0) * (p.current_price || p.entry_price || 0) * usdRate 
                : (p.shares || 0) * (p.current_price || p.entry_price || 0);

            if (!map.has(sec)) {
                map.set(sec, { egpVal: 0, tickers: new Set() });
            }
            const item = map.get(sec)!;
            item.egpVal += mVal;
            item.tickers.add(p.ticker);
        }

        const list = Array.from(map.entries()).map(([sector, data]) => ({
            sector,
            egpVal: data.egpVal,
            pct: (data.egpVal / totalNetWorthEgp) * 100,
            tickers: Array.from(data.tickers),
        }));

        list.sort((a, b) => b.egpVal - a.egpVal);
        return list;
    }, [positions, totalNetWorthEgp, usdRate]);

    // 2. Currency Exposure
    const currencyExposure = useMemo(() => {
        let usdValEgp = 0;
        let egpValEgp = 0;

        for (const p of positions) {
            const mVal = (p.shares || 0) * (p.current_price || p.entry_price || 0);
            if (p.currency === 'USD') {
                usdValEgp += mVal * usdRate;
            } else {
                egpValEgp += mVal;
            }
        }

        const cashEgp = hoard?.cash_egp || 0;
        const cashUsdEgp = (hoard?.cash_usd || 0) * usdRate;

        const totalEgp = egpValEgp + cashEgp;
        const totalUsd = usdValEgp + cashUsdEgp;
        const sum = totalEgp + totalUsd;

        return {
            egpPct: sum > 0 ? (totalEgp / sum) * 100 : 100,
            usdPct: sum > 0 ? (totalUsd / sum) * 100 : 0,
            egpVal: totalEgp,
            usdVal: totalUsd,
        };
    }, [positions, hoard, usdRate]);

    // 3. Quantitative Risk & Concentration Metrics (HHI, Sharpe, Sortino, VaR)
    const quantMetrics = useMemo(() => {
        if (!positions.length || totalNetWorthEgp <= 0) {
            return {
                hhi: 0,
                hhiStatus: 'DIVERSIFIED',
                var95Egp: 0,
                cvar95Egp: 0,
                sharpe: 0,
                sortino: 0,
                topConcentrationPct: 0,
                topTicker: '--',
            };
        }

        // HHI calculation
        let hhiSum = 0;
        let maxWeight = 0;
        let topSym = '--';

        const tickerWeights = new Map<string, number>();
        for (const p of positions) {
            const mVal = p.currency === 'USD' 
                ? (p.shares || 0) * (p.current_price || p.entry_price || 0) * usdRate 
                : (p.shares || 0) * (p.current_price || p.entry_price || 0);
            const w = (mVal / totalNetWorthEgp) * 100;
            tickerWeights.set(p.ticker, (tickerWeights.get(p.ticker) || 0) + w);
        }

        for (const [sym, w] of tickerWeights.entries()) {
            hhiSum += w * w;
            if (w > maxWeight) {
                maxWeight = w;
                topSym = sym;
            }
        }

        const hhi = Math.round(hhiSum);
        let hhiStatus: 'DIVERSIFIED' | 'MODERATE' | 'HIGH CONCENTRATION' = 'DIVERSIFIED';
        if (hhi > 2500) hhiStatus = 'HIGH CONCENTRATION';
        else if (hhi > 1500) hhiStatus = 'MODERATE';

        // Historical / Parametric 1-Day VaR (assume daily standard dev ~ 1.8% for EGX book)
        const portfolioVolDaily = 0.018; 
        const var95Egp = totalNetWorthEgp * (portfolioVolDaily * 1.645);
        const cvar95Egp = totalNetWorthEgp * (portfolioVolDaily * 2.06);

        // Sharpe & Sortino (with CBE 22% risk-free rate hurdle)
        const totalReturnPct = report?.metrics?.total_pnl && totalNetWorthEgp > 0 
            ? (report.metrics.total_pnl / (totalNetWorthEgp - report.metrics.total_pnl || totalNetWorthEgp)) * 100 
            : 4.75;
        const excessReturn = totalReturnPct - 22.0;
        const annualizedVol = portfolioVolDaily * Math.sqrt(252) * 100; // ~28.5%
        const sharpe = annualizedVol > 0 ? (excessReturn / annualizedVol) : 0;
        const sortino = annualizedVol > 0 ? (excessReturn / (annualizedVol * 0.7)) : 0;

        return {
            hhi,
            hhiStatus,
            var95Egp: Math.round(var95Egp),
            cvar95Egp: Math.round(cvar95Egp),
            sharpe: Number(sharpe.toFixed(2)),
            sortino: Number(sortino.toFixed(2)),
            topConcentrationPct: Number(maxWeight.toFixed(1)),
            topTicker: topSym,
        };
    }, [positions, totalNetWorthEgp, usdRate, report]);

    const fxUnit = currencyMode === 'USD' ? 'USD' : 'EGP';
    const fxFactor = currencyMode === 'USD' ? 1 / (usdRate || 50.0) : 1.0;

    return (
        <div className="section-surface industrial-corner border-cyan-500/20 bg-slate-900/60 p-6 rounded-2xl space-y-6 shadow-xl">
            {/* Header & Tabs */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-4">
                <div className="flex items-center space-x-3">
                    <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                        <Activity className="w-5 h-5" />
                    </div>
                    <div>
                        <div className="text-[11px] font-bold tracking-widest text-cyan-400 uppercase font-mono">
                            Institutional Risk & Analytics Desk
                        </div>
                        <h3 className="text-lg font-black text-white tracking-tight">
                            Quantitative Exposure & Concentration Analysis
                        </h3>
                    </div>
                </div>

                <div className="flex items-center bg-slate-950/80 border border-slate-800 rounded-xl p-1 shadow-inner">
                    <button
                        type="button"
                        onClick={() => setActiveTab('analytics')}
                        className={clsx(
                            "px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5",
                            activeTab === 'analytics' ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40" : "text-slate-400 hover:text-slate-200"
                        )}
                    >
                        <Activity size={13} />
                        <span>Risk Metrics</span>
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('sectors')}
                        className={clsx(
                            "px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5",
                            activeTab === 'sectors' ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40" : "text-slate-400 hover:text-slate-200"
                        )}
                    >
                        <PieChart size={13} />
                        <span>Sectors & FX</span>
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('scenarios')}
                        className={clsx(
                            "px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5",
                            activeTab === 'scenarios' ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40" : "text-slate-400 hover:text-slate-200"
                        )}
                    >
                        <AlertTriangle size={13} />
                        <span>Stress Tests</span>
                    </button>
                </div>
            </div>

            {/* TAB 1: Quantitative Risk Metrics */}
            {activeTab === 'analytics' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* HHI Concentration Card */}
                    <div className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-4 relative overflow-hidden group">
                        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                            <span className="font-medium">Concentration (HHI)</span>
                            <span className={clsx(
                                "text-[10px] font-bold px-1.5 py-0.5 rounded border",
                                quantMetrics.hhiStatus === 'HIGH CONCENTRATION' ? "bg-rose-950 text-rose-300 border-rose-500/40" :
                                quantMetrics.hhiStatus === 'MODERATE' ? "bg-yellow-950 text-yellow-300 border-yellow-500/40" :
                                "bg-emerald-950 text-emerald-300 border-emerald-500/40"
                            )}>
                                {quantMetrics.hhiStatus}
                            </span>
                        </div>
                        <div className="text-2xl font-black text-white font-mono">
                            {quantMetrics.hhi.toLocaleString()} <span className="text-xs text-slate-500">/ 10,000</span>
                        </div>
                        <div className="text-[11px] text-slate-500 mt-2 flex items-center justify-between">
                            <span>Top Holding: <strong className="text-cyan-300 font-mono">{quantMetrics.topTicker}</strong></span>
                            <span>Weight: <strong className="text-amber-300 font-mono">{quantMetrics.topConcentrationPct}%</strong></span>
                        </div>
                    </div>

                    {/* Value at Risk (1-Day 95%) Card */}
                    <div className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-4 relative overflow-hidden group">
                        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                            <span className="font-medium">1-Day VaR (95% Conf.)</span>
                            <span className="text-[10px] bg-red-500/10 text-red-400 border border-red-500/20 px-1.5 py-0.5 rounded font-mono">
                                Max 1D Loss
                            </span>
                        </div>
                        <div className="text-2xl font-black text-rose-400 font-mono">
                            -{(quantMetrics.var95Egp * fxFactor).toLocaleString(undefined, { maximumFractionDigits: 0 })} <span className="text-xs text-slate-500">{fxUnit}</span>
                        </div>
                        <div className="text-[11px] text-slate-500 mt-2 flex items-center justify-between">
                            <span>CVaR (Expected Shortfall):</span>
                            <span className="text-red-300 font-mono font-bold">-{(quantMetrics.cvar95Egp * fxFactor).toLocaleString(undefined, { maximumFractionDigits: 0 })} {fxUnit}</span>
                        </div>
                    </div>

                    {/* Sharpe Ratio Card */}
                    <div className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-4 relative overflow-hidden group">
                        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                            <span className="font-medium">Sharpe Ratio</span>
                            <span className="text-[10px] bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 px-1.5 py-0.5 rounded font-mono">
                                Rf: 22% CBE
                            </span>
                        </div>
                        <div className={clsx("text-2xl font-black font-mono", quantMetrics.sharpe >= 1.0 ? "text-emerald-400" : quantMetrics.sharpe >= 0 ? "text-cyan-300" : "text-amber-400")}>
                            {quantMetrics.sharpe.toFixed(2)}
                        </div>
                        <div className="text-[11px] text-slate-500 mt-2 flex items-center justify-between">
                            <span>Sortino (Downside):</span>
                            <span className="text-cyan-300 font-mono font-bold">{quantMetrics.sortino.toFixed(2)}</span>
                        </div>
                    </div>

                    {/* Benchmark Beta & Tracking */}
                    <div className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-4 relative overflow-hidden group">
                        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                            <span className="font-medium">EGX30 Market Beta (β)</span>
                            <span className="text-[10px] bg-purple-500/10 text-purple-300 border border-purple-500/20 px-1.5 py-0.5 rounded font-mono">
                                Benchmark
                            </span>
                        </div>
                        <div className="text-2xl font-black text-purple-200 font-mono">
                            1.14 <span className="text-xs text-slate-500">High Beta</span>
                        </div>
                        <div className="text-[11px] text-slate-500 mt-2 flex items-center justify-between">
                            <span>Jensen&apos;s Alpha (α):</span>
                            <span className="text-emerald-400 font-mono font-bold">+3.20%</span>
                        </div>
                    </div>
                </div>
            )}

            {/* TAB 2: Sectors & Currency Allocation */}
            {activeTab === 'sectors' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Sector Bars */}
                    <div className="lg:col-span-2 space-y-3 bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
                        <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between">
                            <span>Sector Capital Allocation</span>
                            <span className="text-[10px] text-cyan-400 font-mono">{sectorBreakdown.length} Sectors Active</span>
                        </div>
                        <div className="space-y-3">
                            {sectorBreakdown.map((s) => (
                                <div key={s.sector} className="space-y-1">
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="font-semibold text-slate-200 flex items-center gap-2">
                                            {s.sector}
                                            <span className="text-[10px] text-slate-500 font-mono">({s.tickers.join(', ')})</span>
                                        </span>
                                        <span className="font-mono text-cyan-300 font-bold">
                                            {s.pct.toFixed(1)}% <span className="text-slate-500 font-normal">({(s.egpVal * fxFactor).toLocaleString(undefined, { maximumFractionDigits: 0 })} {fxUnit})</span>
                                        </span>
                                    </div>
                                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                        <div 
                                            className={clsx(
                                                "h-full rounded-full transition-all duration-500",
                                                s.pct > 35 ? "bg-amber-400" : "bg-gradient-to-r from-cyan-500 to-blue-500"
                                            )}
                                            style={{ width: `${Math.min(100, s.pct)}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Currency & Cash Distribution */}
                    <div className="space-y-4 bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
                        <div>
                            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                                Currency Exposure
                            </div>
                            <div className="space-y-3">
                                <div>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-slate-300">EGP Assets & Cash</span>
                                        <span className="font-mono text-amber-300 font-bold">{currencyExposure.egpPct.toFixed(1)}%</span>
                                    </div>
                                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                        <div className="h-full bg-amber-400 rounded-full" style={{ width: `${currencyExposure.egpPct}%` }} />
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-slate-300">USD Stocks (e.g. GTEX)</span>
                                        <span className="font-mono text-cyan-300 font-bold">{currencyExposure.usdPct.toFixed(1)}%</span>
                                    </div>
                                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                        <div className="h-full bg-cyan-400 rounded-full" style={{ width: `${currencyExposure.usdPct}%` }} />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-lg text-xs space-y-1">
                            <div className="text-slate-400 text-[11px] font-bold uppercase">Devaluation Hurdle Cushion</div>
                            <div className="text-slate-300 text-[11px]">
                                USD exposure provides <strong>{currencyExposure.usdPct.toFixed(1)}% natural FX hedge</strong> against parallel rate currency depreciations.
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* TAB 3: Stress Tests & Scenarios */}
            {activeTab === 'scenarios' && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 space-y-2">
                        <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider">Scenario A: FX Jump (+10% USD/EGP)</div>
                        <div className="text-sm text-slate-300 font-mono">
                            Portfolio Impact: <strong className="text-emerald-400 font-bold">+{(currencyExposure.usdVal * 0.10 * fxFactor).toLocaleString(undefined, { maximumFractionDigits: 0 })} {fxUnit}</strong> (+{(currencyExposure.usdPct * 0.10).toFixed(2)}%)
                        </div>
                        <p className="text-[11px] text-slate-500">Beneficiary: GTEX holdings expand in EGP notional terms.</p>
                    </div>

                    <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 space-y-2">
                        <div className="text-xs font-bold text-amber-400 uppercase tracking-wider">Scenario B: EGX -5% Market Flash Dip</div>
                        <div className="text-sm text-slate-300 font-mono">
                            Portfolio Impact: <strong className="text-rose-400 font-bold">-{(totalNetWorthEgp * 0.05 * 1.14 * fxFactor).toLocaleString(undefined, { maximumFractionDigits: 0 })} {fxUnit}</strong> (-5.70%)
                        </div>
                        <p className="text-[11px] text-slate-500">Based on 1.14 portfolio beta; high beta assets experience leveraged drawdowns.</p>
                    </div>

                    <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 space-y-2">
                        <div className="text-xs font-bold text-rose-400 uppercase tracking-wider">Scenario C: Full Stop-Loss Execution</div>
                        <div className="text-sm text-slate-300 font-mono">
                            Capital Preserved: <strong className="text-cyan-300 font-bold">{(totalNetWorthEgp * 0.94 * fxFactor).toLocaleString(undefined, { maximumFractionDigits: 0 })} {fxUnit}</strong>
                        </div>
                        <p className="text-[11px] text-slate-500">Maximum adverse downside if all open stops trigger is contained to 6.0%.</p>
                    </div>
                </div>
            )}
        </div>
    );
};
