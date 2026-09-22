'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
    Scale,
    RefreshCw,
    CheckCircle2,
    AlertTriangle,
    ArrowRight,
    Shield,
    Zap,
    ArrowDownRight,
    ArrowUpRight,
    FileText,
    ChevronLeft,
    Check,
    Info,
    Coins,
    AlertCircle,
} from 'lucide-react';
import clsx from 'clsx';
import { apiFetch, readJsonSafe } from '@/lib/api';

export interface RebalanceRecommendation {
    ticker: string;
    currency?: string;
    is_usd?: boolean;
    action: 'TRIM' | 'ADD' | 'HOLD';
    current_pct: number;
    target_pct: number;
    drift_pct: number;
    current_shares: number;
    target_shares: number;
    shares_delta: number;
    delta_value_native?: number;
    delta_value_egp: number;
    current_price: number;
    current_price_egp?: number;
    usd_rate?: number;
    reason: string;
    model: string;
}

interface PortfolioRebalanceModalProps {
    isOpen: boolean;
    onClose: () => void;
    activePortfolioId: number | null;
    onApplyRebalance: (model: string, callbacks?: { onSuccess?: () => void }) => Promise<void>;
    actionLoading?: boolean;
}

type ViewMode = 'DESK' | 'REPORT' | 'RECEIPT';

export function PortfolioRebalanceModal({
    isOpen,
    onClose,
    activePortfolioId,
    onApplyRebalance,
    actionLoading = false,
}: PortfolioRebalanceModalProps) {
    const [selectedModel, setSelectedModel] = useState<'EQUAL_WEIGHT' | 'RISK_PARITY' | 'KELLY_WEIGHTED'>('EQUAL_WEIGHT');
    const [recommendations, setRecommendations] = useState<RebalanceRecommendation[]>([]);
    const [loading, setLoading] = useState(false);
    const [fetchError, setFetchError] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<ViewMode>('DESK');
    const [confirmedAcknowledged, setConfirmedAcknowledged] = useState(false);

    const fetchRecommendations = useCallback(async () => {
        if (!activePortfolioId || !isOpen) return;

        setLoading(true);
        setFetchError(null);
        try {
            const res = await apiFetch(`/api/v1/portfolio/rebalance?portfolio_id=${activePortfolioId}&model=${selectedModel}`);
            const data = await readJsonSafe<any>(res);
            if (res.ok && Array.isArray(data)) {
                setRecommendations(data);
            } else {
                setFetchError('Failed to fetch rebalance recommendations.');
            }
        } catch (_err) {
            setFetchError('Network error loading rebalance recommendations.');
        } finally {
            setLoading(false);
        }
    }, [activePortfolioId, isOpen, selectedModel]);

    useEffect(() => {
        if (isOpen) {
            setViewMode('DESK');
            setConfirmedAcknowledged(false);
            void fetchRecommendations();
        }
    }, [isOpen, fetchRecommendations]);

    if (!isOpen) return null;

    // Sells (TRIM) and Buys (ADD)
    const sellOrders = recommendations.filter((r) => r.action === 'TRIM' && r.shares_delta > 0);
    const buyOrders = recommendations.filter((r) => r.action === 'ADD' && r.shares_delta > 0);
    const hasUsdHoldings = recommendations.some((r) => r.is_usd || r.currency === 'USD');

    // EGP Book Totals
    const egpSells = sellOrders.filter((r) => !r.is_usd && r.currency !== 'USD');
    const egpBuys = buyOrders.filter((r) => !r.is_usd && r.currency !== 'USD');
    const totalSellValueEgp = egpSells.reduce((sum, r) => sum + Math.abs(r.delta_value_egp), 0);
    const totalBuyValueEgp = egpBuys.reduce((sum, r) => sum + Math.abs(r.delta_value_egp), 0);
    const netCashFlowEgp = totalSellValueEgp - totalBuyValueEgp;

    // USD Book Totals
    const usdSells = sellOrders.filter((r) => r.is_usd || r.currency === 'USD');
    const usdBuys = buyOrders.filter((r) => r.is_usd || r.currency === 'USD');
    const totalSellValueUsd = usdSells.reduce((sum, r) => sum + Math.abs(r.delta_value_native ?? (r.delta_value_egp / (r.usd_rate || 50))), 0);
    const totalBuyValueUsd = usdBuys.reduce((sum, r) => sum + Math.abs(r.delta_value_native ?? (r.delta_value_egp / (r.usd_rate || 50))), 0);
    const netCashFlowUsd = totalSellValueUsd - totalBuyValueUsd;

    const hasActions = sellOrders.length > 0 || buyOrders.length > 0;

    const handleExecute = async () => {
        await onApplyRebalance(selectedModel, {
            onSuccess: () => {
                setViewMode('RECEIPT');
            },
        });
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fade-in">
            <div className="bg-slate-900 border border-slate-700/60 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden ring-1 ring-cyan-500/20">
                {/* Modal Header */}
                <div className="p-5 sm:p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/80">
                    <div className="flex items-center space-x-3">
                        <div className="p-2.5 bg-cyan-950/70 text-cyan-400 border border-cyan-500/30 rounded-xl">
                            {viewMode === 'REPORT' ? <FileText size={22} /> : <Scale size={22} />}
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <h2 className="text-lg sm:text-xl font-bold text-slate-100">
                                    {viewMode === 'REPORT'
                                        ? 'Rebalance Execution Report & Staging Ticket'
                                        : viewMode === 'RECEIPT'
                                        ? 'Rebalance Execution Confirmation'
                                        : 'Institutional Rebalancing Desk'}
                                </h2>
                                {viewMode === 'REPORT' && (
                                    <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-amber-950/60 text-amber-300 border border-amber-500/40 rounded">
                                        Staging Preview
                                    </span>
                                )}
                            </div>
                            <p className="text-xs text-slate-400 font-mono mt-0.5">
                                {viewMode === 'REPORT'
                                    ? 'Review currency-segmented order sequence and cash requirements prior to execution'
                                    : 'Optimize portfolio weights and eliminate idiosyncratic drift'}
                            </p>
                        </div>
                    </div>

                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-200 p-2 hover:bg-slate-800 rounded-lg transition-colors"
                        aria-label="Close modal"
                    >
                        ✕
                    </button>
                </div>

                {/* STAGE 1: DESK VIEW */}
                {viewMode === 'DESK' && (
                    <>
                        {/* Model Selector Bar */}
                        <div className="px-6 py-4 bg-slate-950/40 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
                            <div className="flex items-center space-x-2">
                                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mr-1">
                                    Allocation Model:
                                </span>
                                {[
                                    { id: 'EQUAL_WEIGHT', label: 'Equal Weight', icon: Scale, desc: 'Even % across all holdings' },
                                    { id: 'RISK_PARITY', label: 'Risk Parity', icon: Shield, desc: 'Inverse volatility & stop distance' },
                                    { id: 'KELLY_WEIGHTED', label: 'Kelly Weighted', icon: Zap, desc: 'Signal conviction & R/R' },
                                ].map((m) => {
                                    const Icon = m.icon;
                                    const active = selectedModel === m.id;
                                    return (
                                        <button
                                            key={m.id}
                                            onClick={() => setSelectedModel(m.id as any)}
                                            className={clsx(
                                                "flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold border transition-all",
                                                active
                                                    ? "bg-cyan-950/70 border-cyan-500/60 text-cyan-300 shadow-md shadow-cyan-950/50"
                                                    : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                                            )}
                                            title={m.desc}
                                        >
                                            <Icon size={14} className={active ? "text-cyan-400" : "text-slate-500"} />
                                            <span>{m.label}</span>
                                        </button>
                                    );
                                })}
                            </div>

                            <button
                                onClick={fetchRecommendations}
                                disabled={loading}
                                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-cyan-400 px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 transition-colors"
                            >
                                <RefreshCw size={13} className={clsx(loading && "animate-spin text-cyan-400")} />
                                <span>Recalculate</span>
                            </button>
                        </div>

                        {/* Content Body */}
                        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
                            {fetchError && (
                                <div className="p-4 bg-rose-950/30 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center gap-2">
                                    <AlertTriangle size={16} />
                                    <span>{fetchError}</span>
                                </div>
                            )}

                            {loading ? (
                                <div className="p-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
                                    <RefreshCw size={24} className="animate-spin text-cyan-400" />
                                    <p className="text-xs font-mono">Simulating consolidated allocation targets...</p>
                                </div>
                            ) : recommendations.length === 0 ? (
                                <div className="p-12 text-center text-slate-500 italic border border-slate-800/80 rounded-xl bg-slate-900/20">
                                    No open positions found to rebalance.
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {/* Consolidated Allocations Table */}
                                    <div className="rounded-xl border border-slate-800 overflow-hidden">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-slate-950/60 text-[10px] uppercase font-mono text-slate-400 border-b border-slate-800">
                                                    <th className="p-3 pl-4">Ticker</th>
                                                    <th className="p-3 text-center">Curr</th>
                                                    <th className="p-3 text-right">Current %</th>
                                                    <th className="p-3 text-right">Target %</th>
                                                    <th className="p-3 text-right">Drift</th>
                                                    <th className="p-3 text-center">Action</th>
                                                    <th className="p-3 text-right">Delta Shares</th>
                                                    <th className="p-3 text-right pr-4">Delta Value</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-800/60 text-xs font-mono">
                                                {recommendations.map((r) => {
                                                    const isTrim = r.action === 'TRIM';
                                                    const isAdd = r.action === 'ADD';
                                                    const isUsd = r.is_usd || r.currency === 'USD';
                                                    return (
                                                        <tr key={r.ticker} className="hover:bg-slate-800/30 transition-colors">
                                                            <td className="p-3 pl-4 font-bold text-slate-200">
                                                                {r.ticker}
                                                            </td>
                                                            <td className="p-3 text-center">
                                                                <span className={clsx(
                                                                    "px-1.5 py-0.5 rounded text-[10px] font-bold border",
                                                                    isUsd
                                                                        ? "bg-amber-950/40 text-amber-300 border-amber-500/40"
                                                                        : "bg-slate-800 text-slate-400 border-slate-700"
                                                                )}>
                                                                    {isUsd ? 'USD' : 'EGP'}
                                                                </span>
                                                            </td>
                                                            <td className="p-3 text-right text-slate-300">
                                                                {r.current_pct.toFixed(1)}%
                                                            </td>
                                                            <td className="p-3 text-right text-cyan-300 font-semibold">
                                                                {r.target_pct.toFixed(1)}%
                                                            </td>
                                                            <td className="p-3 text-right">
                                                                <span className={clsx(
                                                                    "font-semibold",
                                                                    r.drift_pct > 2 ? "text-amber-400" : r.drift_pct < -2 ? "text-cyan-400" : "text-slate-400"
                                                                )}>
                                                                    {r.drift_pct > 0 ? '+' : ''}{r.drift_pct.toFixed(1)}%
                                                                </span>
                                                            </td>
                                                            <td className="p-3 text-center">
                                                                <span className={clsx(
                                                                    "px-2 py-0.5 rounded text-[10px] font-bold border tracking-wider",
                                                                    isTrim && "bg-rose-950/40 text-rose-300 border-rose-500/40",
                                                                    isAdd && "bg-emerald-950/40 text-emerald-300 border-emerald-500/40",
                                                                    !isTrim && !isAdd && "bg-slate-800 text-slate-400 border-slate-700"
                                                                )}>
                                                                    {r.action}
                                                                </span>
                                                            </td>
                                                            <td className="p-3 text-right text-slate-300">
                                                                {r.shares_delta > 0 ? (
                                                                    <span>
                                                                        {isTrim ? '-' : '+'}
                                                                        {r.shares_delta.toLocaleString()}
                                                                    </span>
                                                                ) : (
                                                                    <span className="text-slate-500">0</span>
                                                                )}
                                                            </td>
                                                            <td className="p-3 text-right pr-4 font-semibold text-slate-200">
                                                                {isUsd && r.delta_value_native !== undefined ? (
                                                                    <div>
                                                                        <span>
                                                                            {r.delta_value_native > 0 ? '+$' : '-$'}
                                                                            {Math.abs(r.delta_value_native).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
                                                                        </span>
                                                                        <span className="text-[10px] text-slate-500 block font-normal">
                                                                            ≈ {r.delta_value_egp > 0 ? '+' : ''}{r.delta_value_egp.toLocaleString(undefined, { maximumFractionDigits: 0 })} EGP
                                                                        </span>
                                                                    </div>
                                                                ) : r.delta_value_egp !== 0 ? (
                                                                    <span>
                                                                        {r.delta_value_egp > 0 ? '+' : ''}
                                                                        {r.delta_value_egp.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} EGP
                                                                    </span>
                                                                ) : (
                                                                    <span className="text-slate-500">0.00</span>
                                                                )}
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>

                                    {/* Weight visual distribution preview */}
                                    <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-3">
                                        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                            Allocation Drift Visualizer
                                        </h4>
                                        <div className="space-y-2">
                                            {recommendations.map((r) => (
                                                <div key={`bar-${r.ticker}`} className="space-y-1">
                                                    <div className="flex justify-between text-[11px] font-mono text-slate-400">
                                                        <div className="flex items-center gap-1.5">
                                                            <span className="text-slate-200 font-semibold">{r.ticker}</span>
                                                            {(r.is_usd || r.currency === 'USD') && (
                                                                <span className="px-1 text-[9px] bg-amber-950/60 text-amber-300 border border-amber-500/30 rounded font-bold">
                                                                    USD
                                                                </span>
                                                            )}
                                                        </div>
                                                        <span>
                                                            Current {r.current_pct.toFixed(1)}% <ArrowRight size={10} className="inline mx-1 text-slate-500" /> Target {r.target_pct.toFixed(1)}%
                                                        </span>
                                                    </div>
                                                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden flex">
                                                        <div
                                                            className="bg-slate-500 h-full"
                                                            style={{ width: `${Math.min(r.current_pct, 100)}%` }}
                                                        />
                                                        <div
                                                            className={clsx("h-full", r.drift_pct < 0 ? "bg-emerald-500" : "bg-rose-500")}
                                                            style={{ width: `${Math.min(Math.abs(r.drift_pct), 100)}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Footer Controls */}
                        <div className="p-5 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
                            <div className="text-xs text-slate-400 font-mono">
                                {hasActions ? (
                                    <span className="text-cyan-300">
                                        Ready to stage {sellOrders.length + buyOrders.length} order(s) across {recommendations.length} consolidated security(ies).
                                    </span>
                                ) : (
                                    <span className="text-emerald-400 flex items-center gap-1.5">
                                        <CheckCircle2 size={14} />
                                        Portfolio is currently balanced within ±2% drift.
                                    </span>
                                )}
                            </div>

                            <div className="flex items-center space-x-3">
                                <button
                                    onClick={onClose}
                                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl transition-colors"
                                >
                                    Cancel
                                </button>

                                <button
                                    onClick={() => setViewMode('REPORT')}
                                    disabled={!hasActions || loading}
                                    className={clsx(
                                        "flex items-center gap-2 px-5 py-2 text-xs font-bold rounded-xl transition-all shadow-lg",
                                        !hasActions || loading
                                            ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                                            : "bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-cyan-500/25 cursor-pointer"
                                    )}
                                >
                                    <FileText size={14} />
                                    <span>Review Execution Instructions</span>
                                </button>
                            </div>
                        </div>
                    </>
                )}

                {/* STAGE 2: EXECUTION REPORT & STAGING TICKET */}
                {viewMode === 'REPORT' && (
                    <>
                        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
                            {/* Summary Metrics Cards Segmented by Currency */}
                            <div className="space-y-3">
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                    <div className="p-3.5 bg-rose-950/20 border border-rose-500/30 rounded-xl">
                                        <span className="text-[10px] font-mono text-rose-300 uppercase tracking-wider block">
                                            🇪🇬 EGP Cash Generated (Sell)
                                        </span>
                                        <span className="text-sm font-bold text-rose-400 font-mono mt-1 block">
                                            +{totalSellValueEgp.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} EGP
                                        </span>
                                    </div>

                                    <div className="p-3.5 bg-emerald-950/20 border border-emerald-500/30 rounded-xl">
                                        <span className="text-[10px] font-mono text-emerald-300 uppercase tracking-wider block">
                                            🇪🇬 EGP Cash Required (Buy)
                                        </span>
                                        <span className="text-sm font-bold text-emerald-400 font-mono mt-1 block">
                                            -{totalBuyValueEgp.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} EGP
                                        </span>
                                    </div>

                                    <div className="p-3.5 bg-cyan-950/30 border border-cyan-500/30 rounded-xl">
                                        <span className="text-[10px] font-mono text-cyan-300 uppercase tracking-wider block">
                                            🇪🇬 Net EGP Cash Flow
                                        </span>
                                        <span className={clsx(
                                            "text-sm font-bold font-mono mt-1 block",
                                            netCashFlowEgp >= 0 ? "text-emerald-400" : "text-amber-400"
                                        )}>
                                            {netCashFlowEgp >= 0 ? '+' : ''}
                                            {netCashFlowEgp.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} EGP
                                        </span>
                                    </div>
                                </div>

                                {/* USD Currency Book Summary (if present) */}
                                {hasUsdHoldings && (
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                        <div className="p-3.5 bg-amber-950/20 border border-amber-500/30 rounded-xl">
                                            <span className="text-[10px] font-mono text-amber-300 uppercase tracking-wider block">
                                                🇺🇸 USD Cash Generated (Sell)
                                            </span>
                                            <span className="text-sm font-bold text-amber-400 font-mono mt-1 block">
                                                +${totalSellValueUsd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
                                            </span>
                                        </div>

                                        <div className="p-3.5 bg-emerald-950/20 border border-emerald-500/30 rounded-xl">
                                            <span className="text-[10px] font-mono text-emerald-300 uppercase tracking-wider block">
                                                🇺🇸 USD Cash Required (Buy)
                                            </span>
                                            <span className="text-sm font-bold text-emerald-400 font-mono mt-1 block">
                                                -${totalBuyValueUsd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
                                            </span>
                                        </div>

                                        <div className="p-3.5 bg-cyan-950/30 border border-cyan-500/30 rounded-xl">
                                            <span className="text-[10px] font-mono text-cyan-300 uppercase tracking-wider block">
                                                🇺🇸 Net USD Cash Flow
                                            </span>
                                            <span className={clsx(
                                                "text-sm font-bold font-mono mt-1 block",
                                                netCashFlowUsd >= 0 ? "text-emerald-400" : "text-amber-400"
                                            )}>
                                                {netCashFlowUsd >= 0 ? '+$' : '-$'}
                                                {Math.abs(netCashFlowUsd).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Standard Operating Procedure & Currency Protocol Notice */}
                            <div className="p-4 bg-slate-950/80 border border-cyan-500/30 rounded-xl space-y-2.5">
                                <div className="flex items-center gap-2 text-cyan-300 text-xs font-bold uppercase tracking-wider">
                                    <Info size={15} />
                                    <span>Pre-Flight Execution Protocol (Follow in Sequential Order)</span>
                                </div>
                                <ol className="text-xs text-slate-300 space-y-1.5 pl-5 list-decimal font-mono">
                                    <li>
                                        <strong className="text-rose-400">Step 1 — Execute TRIM / SELL Orders First:</strong> Submit sell orders on your broker workstation to unlock cash liquidity before purchasing.
                                    </li>
                                    <li>
                                        <strong className="text-emerald-400">Step 2 — Execute ADD / BUY Orders Second:</strong> Utilize freed proceeds to fund underweight allocations.
                                    </li>
                                    <li>
                                        <strong className="text-cyan-300">Step 3 — System Synchronization:</strong> Click <em>&quot;Confirm &amp; Execute System Rebalance&quot;</em> below only after filling orders to update internal ledger state.
                                    </li>
                                </ol>

                                {/* Currency Restriction Callout */}
                                {hasUsdHoldings && (
                                    <div className="mt-2 p-3 bg-amber-950/30 border border-amber-500/30 rounded-lg flex items-start gap-2 text-amber-300 text-xs font-mono">
                                        <AlertCircle size={16} className="text-amber-400 shrink-0 mt-0.5" />
                                        <div>
                                            <strong>EGX Multi-Currency Notice:</strong> USD-denominated stocks (e.g. <em>GTEX, EGBE</em>) trade against your broker&apos;s USD cash balance. You <u>cannot</u> buy USD stocks with EGP cash. Ensure sufficient USD liquidity before placing USD orders.
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Section 1: SELL / TRIM ORDERS */}
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                                        <ArrowDownRight size={16} />
                                        <span>Phase 1: Sell Orders (Trim Overweight Positions)</span>
                                    </h3>
                                    <span className="text-[11px] font-mono text-slate-400">
                                        {sellOrders.length} Order(s)
                                    </span>
                                </div>

                                {sellOrders.length === 0 ? (
                                    <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl text-center text-xs font-mono text-slate-500">
                                        No sell orders required. All positions are below target limits.
                                    </div>
                                ) : (
                                    <div className="rounded-xl border border-rose-500/30 overflow-hidden bg-rose-950/10">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-rose-950/40 text-[10px] uppercase font-mono text-rose-300 border-b border-rose-500/20">
                                                    <th className="p-3 pl-4">Ticker</th>
                                                    <th className="p-3 text-center">Curr</th>
                                                    <th className="p-3 text-right">Shares to Sell</th>
                                                    <th className="p-3 text-right">Market Price</th>
                                                    <th className="p-3 text-right">Cash Freed</th>
                                                    <th className="p-3 text-right">Current %</th>
                                                    <th className="p-3 text-right pr-4">Post-Sell Target %</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-rose-500/10 text-xs font-mono">
                                                {sellOrders.map((r) => {
                                                    const isUsd = r.is_usd || r.currency === 'USD';
                                                    return (
                                                        <tr key={`sell-${r.ticker}`} className="hover:bg-rose-950/20 transition-colors">
                                                            <td className="p-3 pl-4 font-bold text-rose-200">
                                                                {r.ticker}
                                                            </td>
                                                            <td className="p-3 text-center">
                                                                <span className={clsx(
                                                                    "px-1.5 py-0.5 rounded text-[10px] font-bold border",
                                                                    isUsd
                                                                        ? "bg-amber-950/60 text-amber-300 border-amber-500/40"
                                                                        : "bg-slate-800 text-slate-400 border-slate-700"
                                                                )}>
                                                                    {isUsd ? 'USD' : 'EGP'}
                                                                </span>
                                                            </td>
                                                            <td className="p-3 text-right font-bold text-rose-300">
                                                                SELL {r.shares_delta.toLocaleString()} shs
                                                            </td>
                                                            <td className="p-3 text-right text-slate-300">
                                                                {isUsd ? `$${r.current_price.toFixed(4)} USD` : `${r.current_price.toFixed(2)} EGP`}
                                                            </td>
                                                            <td className="p-3 text-right font-semibold text-emerald-400">
                                                                {isUsd && r.delta_value_native !== undefined ? (
                                                                    <div>
                                                                        <span>
                                                                            +${Math.abs(r.delta_value_native).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
                                                                        </span>
                                                                        <span className="text-[10px] text-slate-500 block font-normal">
                                                                            ≈ +{Math.abs(r.delta_value_egp).toLocaleString(undefined, { maximumFractionDigits: 0 })} EGP
                                                                        </span>
                                                                    </div>
                                                                ) : (
                                                                    <span>
                                                                        +{Math.abs(r.delta_value_egp).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} EGP
                                                                    </span>
                                                                )}
                                                            </td>
                                                            <td className="p-3 text-right text-slate-400">
                                                                {r.current_pct.toFixed(1)}%
                                                            </td>
                                                            <td className="p-3 text-right pr-4 font-semibold text-cyan-300">
                                                                {r.target_pct.toFixed(1)}%
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>

                            {/* Section 2: BUY / ADD ORDERS */}
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                                        <ArrowUpRight size={16} />
                                        <span>Phase 2: Buy Orders (Fund Underweight Positions)</span>
                                    </h3>
                                    <span className="text-[11px] font-mono text-slate-400">
                                        {buyOrders.length} Order(s)
                                    </span>
                                </div>

                                {buyOrders.length === 0 ? (
                                    <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl text-center text-xs font-mono text-slate-500">
                                        No buy orders required. All allocations meet model minimums.
                                    </div>
                                ) : (
                                    <div className="rounded-xl border border-emerald-500/30 overflow-hidden bg-emerald-950/10">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-emerald-950/40 text-[10px] uppercase font-mono text-emerald-300 border-b border-emerald-500/20">
                                                    <th className="p-3 pl-4">Ticker</th>
                                                    <th className="p-3 text-center">Curr</th>
                                                    <th className="p-3 text-right">Shares to Buy</th>
                                                    <th className="p-3 text-right">Market Price</th>
                                                    <th className="p-3 text-right">Cash Required</th>
                                                    <th className="p-3 text-right">Current %</th>
                                                    <th className="p-3 text-right pr-4">Post-Buy Target %</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-emerald-500/10 text-xs font-mono">
                                                {buyOrders.map((r) => {
                                                    const isUsd = r.is_usd || r.currency === 'USD';
                                                    return (
                                                        <tr key={`buy-${r.ticker}`} className="hover:bg-emerald-950/20 transition-colors">
                                                            <td className="p-3 pl-4 font-bold text-emerald-200">
                                                                {r.ticker}
                                                            </td>
                                                            <td className="p-3 text-center">
                                                                <span className={clsx(
                                                                    "px-1.5 py-0.5 rounded text-[10px] font-bold border",
                                                                    isUsd
                                                                        ? "bg-amber-950/60 text-amber-300 border-amber-500/40"
                                                                        : "bg-slate-800 text-slate-400 border-slate-700"
                                                                )}>
                                                                    {isUsd ? 'USD' : 'EGP'}
                                                                </span>
                                                            </td>
                                                            <td className="p-3 text-right font-bold text-emerald-300">
                                                                BUY +{r.shares_delta.toLocaleString()} shs
                                                            </td>
                                                            <td className="p-3 text-right text-slate-300">
                                                                {isUsd ? `$${r.current_price.toFixed(4)} USD` : `${r.current_price.toFixed(2)} EGP`}
                                                            </td>
                                                            <td className="p-3 text-right font-semibold text-rose-400">
                                                                {isUsd && r.delta_value_native !== undefined ? (
                                                                    <div>
                                                                        <span>
                                                                            -${Math.abs(r.delta_value_native).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
                                                                        </span>
                                                                        <span className="text-[10px] text-slate-500 block font-normal">
                                                                            ≈ -{Math.abs(r.delta_value_egp).toLocaleString(undefined, { maximumFractionDigits: 0 })} EGP
                                                                        </span>
                                                                    </div>
                                                                ) : (
                                                                    <span>
                                                                        -{Math.abs(r.delta_value_egp).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} EGP
                                                                    </span>
                                                                )}
                                                            </td>
                                                            <td className="p-3 text-right text-slate-400">
                                                                {r.current_pct.toFixed(1)}%
                                                            </td>
                                                            <td className="p-3 text-right pr-4 font-semibold text-cyan-300">
                                                                {r.target_pct.toFixed(1)}%
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>

                            {/* Safety Verification Checkbox */}
                            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl flex items-start space-x-3">
                                <input
                                    type="checkbox"
                                    id="rebalance-ack-check"
                                    checked={confirmedAcknowledged}
                                    onChange={(e) => setConfirmedAcknowledged(e.target.checked)}
                                    className="mt-0.5 h-4 w-4 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500 cursor-pointer"
                                />
                                <label htmlFor="rebalance-ack-check" className="text-xs text-slate-300 cursor-pointer select-none leading-relaxed">
                                    <strong>Admin Confirmation:</strong> I have reviewed the order quantities, currency denominations (EGP / USD), and broker liquidity requirements. I confirm that clicking the button below will record these trade adjustments into the Horus system ledger.
                                </label>
                            </div>
                        </div>

                        {/* Footer Controls for Report */}
                        <div className="p-5 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
                            <button
                                onClick={() => setViewMode('DESK')}
                                className="flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl transition-colors"
                            >
                                <ChevronLeft size={14} />
                                <span>Back to Allocation Model</span>
                            </button>

                            <div className="flex items-center space-x-3">
                                <button
                                    onClick={onClose}
                                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs font-semibold rounded-xl transition-colors"
                                >
                                    Cancel
                                </button>

                                <button
                                    onClick={handleExecute}
                                    disabled={actionLoading || !confirmedAcknowledged}
                                    className={clsx(
                                        "flex items-center gap-2 px-5 py-2 text-xs font-bold rounded-xl transition-all shadow-lg",
                                        !confirmedAcknowledged || actionLoading
                                            ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                                            : "bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/25 cursor-pointer"
                                    )}
                                >
                                    {actionLoading ? (
                                        <>
                                            <RefreshCw size={14} className="animate-spin" />
                                            <span>Recording Rebalance Trades...</span>
                                        </>
                                    ) : (
                                        <>
                                            <Check size={14} />
                                            <span>Confirm & Execute Rebalance</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </>
                )}

                {/* STAGE 3: RECEIPT / CONFIRMATION */}
                {viewMode === 'RECEIPT' && (
                    <div className="p-10 flex flex-col items-center justify-center text-center space-y-4 my-auto">
                        <div className="p-4 bg-emerald-950/60 border border-emerald-500/40 text-emerald-400 rounded-2xl shadow-xl shadow-emerald-950/40 animate-bounce">
                            <CheckCircle2 size={40} />
                        </div>
                        <div className="space-y-1">
                            <h3 className="text-xl font-bold text-slate-100">
                                Portfolio Rebalance Executed Successfully
                            </h3>
                            <p className="text-xs text-slate-400 font-mono max-w-md">
                                All {sellOrders.length + buyOrders.length} rebalancing trade adjustments have been committed to the portfolio ledger under the <strong>{selectedModel.replace('_', ' ')}</strong> model.
                            </p>
                        </div>
                        <div className="pt-4">
                            <button
                                onClick={onClose}
                                className="px-6 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold rounded-xl shadow-lg shadow-cyan-500/20 transition-all"
                            >
                                Return to Portfolio
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
