"use client";

import { Shield, AlertCircle, Edit2, Trash2, ArrowUpRight, ArrowDownRight, CheckSquare, Square, ShieldCheck, Scissors, AlertOctagon, X, ChevronDown, ChevronRight, Layers, ListFilter } from 'lucide-react';
import clsx from 'clsx';
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Position, PortfolioHealth, HealthDiagnosis } from '../types';

export interface PriceTick {
    ticker: string;
    price: number;
    change?: number;
    direction: 'up' | 'down' | 'neutral';
    timestamp: number;
}

interface PortfolioTableProps {
    positions: Position[];
    health: PortfolioHealth | null;
    onEdit: (position: Position) => void;
    onClose: (ticker: string) => void;
    livePrices?: Record<string, PriceTick>;
    feeMode?: 'GROSS' | 'NET';
    currencyMode?: 'EGP' | 'USD';
    usdRate?: number;
    onBatchMoveBreakeven?: (tickers: string[]) => void;
    onBatchScaleOut50?: (tickers: string[]) => void;
    onBatchFlatten?: (tickers: string[]) => void;
}

interface ConsolidatedGroup {
    ticker: string;
    currency: string;
    totalShares: number;
    weightedEntryPrice: number;
    weightedStopLoss: number;
    weightedTargetPrice: number;
    weightedTargetPrice2?: number;
    livePrice: number;
    totalCost: number;
    totalMarketVal: number;
    effectivePnl: number;
    effectivePnlPct: number;
    riskStatus: string;
    lots: Position[];
    tp1HitCount: number;
}

const truncatePrice = (val: number, decimals: number = 3): string => {
    if (!Number.isFinite(val)) return '0.000';
    const factor = Math.pow(10, decimals);
    const truncated = Math.trunc(val * factor) / factor;
    return truncated.toFixed(decimals);
};

const formatDateTime = (value?: string | null): string => {
    if (!value) return '--';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleString(undefined, {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
};

const getHealthColor = (status?: string) => {
    if (status === 'SAFE') return 'text-emerald-400';
    if (status === 'WARNING') return 'text-yellow-400';
    if (status === 'DANGER') return 'text-red-500';
    if (status === 'DEVALUATION_LOSS') return 'text-orange-400 font-bold';
    return 'text-slate-400';
};

export const PortfolioTable = React.memo(({
    positions = [],
    health,
    onEdit,
    onClose,
    livePrices = {},
    feeMode = 'GROSS',
    currencyMode = 'EGP',
    usdRate = 50.0,
    onBatchMoveBreakeven,
    onBatchScaleOut50,
    onBatchFlatten,
}: PortfolioTableProps) => {
    const [viewMode, setViewMode] = useState<'consolidated' | 'lots'>('consolidated');
    const [selectedTickers, setSelectedTickers] = useState<Set<string>>(new Set());
    const [expandedTickers, setExpandedTickers] = useState<Set<string>>(new Set());
    const [filterStatus, setFilterStatus] = useState<string>('ALL');

    // Consolidated grouping
    const consolidatedGroups = useMemo<ConsolidatedGroup[]>(() => {
        const map = new Map<string, Position[]>();
        for (const p of positions) {
            const sym = (p.ticker || '').toUpperCase();
            if (!map.has(sym)) {
                map.set(sym, []);
            }
            map.get(sym)!.push(p);
        }

        const groups: ConsolidatedGroup[] = [];
        for (const [sym, lots] of map.entries()) {
            let totalShares = 0;
            let sumCost = 0;
            let sumSl = 0;
            let sumTp1 = 0;
            let sumTp2 = 0;
            let tp1HitCount = 0;

            const tick = livePrices[sym];
            const livePrice = tick?.price || lots[0]?.current_price || lots[0]?.entry_price || 0;
            const curr = lots[0]?.currency || 'EGP';

            let worstRisk = 'SAFE';
            for (const lot of lots) {
                const sh = lot.shares || 0;
                const ep = lot.entry_price || 0;
                totalShares += sh;
                sumCost += sh * ep;
                if (lot.stop_loss) sumSl += sh * lot.stop_loss;
                if (lot.target_price) sumTp1 += sh * lot.target_price;
                if (lot.target_price_2) sumTp2 += sh * lot.target_price_2;
                if (lot.tp1_hit) tp1HitCount++;

                if (lot.risk_status === 'DANGER') worstRisk = 'DANGER';
                else if (lot.risk_status === 'WARNING' && worstRisk !== 'DANGER') worstRisk = 'WARNING';
                else if (lot.risk_status === 'DEVALUATION_LOSS' && worstRisk === 'SAFE') worstRisk = 'DEVALUATION_LOSS';
            }

            const weightedEntryPrice = totalShares > 0 ? sumCost / totalShares : (lots[0]?.entry_price || 0);
            const weightedStopLoss = totalShares > 0 ? sumSl / totalShares : 0;
            const weightedTargetPrice = totalShares > 0 ? sumTp1 / totalShares : 0;
            const weightedTargetPrice2 = totalShares > 0 && sumTp2 > 0 ? sumTp2 / totalShares : undefined;

            const totalMarketVal = totalShares * livePrice;
            const grossPnl = totalMarketVal - sumCost;
            const feeDeduction = feeMode === 'NET' ? (sumCost * 0.0015 + totalMarketVal * 0.0015) : 0;
            const effectivePnl = grossPnl - feeDeduction;
            const effectivePnlPct = sumCost > 0 ? (effectivePnl / sumCost) * 100 : 0;

            groups.push({
                ticker: sym,
                currency: curr,
                totalShares,
                weightedEntryPrice,
                weightedStopLoss,
                weightedTargetPrice,
                weightedTargetPrice2,
                livePrice,
                totalCost: sumCost,
                totalMarketVal,
                effectivePnl,
                effectivePnlPct,
                riskStatus: worstRisk,
                lots,
                tp1HitCount,
            });
        }

        return groups;
    }, [positions, livePrices, feeMode]);

    // Filtered lists
    const filteredConsolidated = useMemo(() => {
        if (filterStatus === 'ALL') return consolidatedGroups;
        if (filterStatus === 'MULTI-LOT') return consolidatedGroups.filter(g => g.lots.length > 1);
        return consolidatedGroups.filter(g => g.riskStatus === filterStatus);
    }, [consolidatedGroups, filterStatus]);

    const filteredPositions = useMemo(() => {
        if (filterStatus === 'ALL') return positions;
        return positions.filter(p => p.risk_status === filterStatus);
    }, [positions, filterStatus]);

    const allTickers = useMemo(() => Array.from(new Set(positions.map((p) => p.ticker))), [positions]);
    const isAllSelected = allTickers.length > 0 && selectedTickers.size === allTickers.length;

    const toggleSelectAll = () => {
        if (isAllSelected) {
            setSelectedTickers(new Set());
        } else {
            setSelectedTickers(new Set(allTickers));
        }
    };

    const toggleSelectTicker = (ticker: string) => {
        setSelectedTickers((prev) => {
            const next = new Set(prev);
            if (next.has(ticker)) {
                next.delete(ticker);
            } else {
                next.add(ticker);
            }
            return next;
        });
    };

    const toggleExpand = (ticker: string) => {
        setExpandedTickers(prev => {
            const next = new Set(prev);
            if (next.has(ticker)) next.delete(ticker);
            else next.add(ticker);
            return next;
        });
    };

    // Danger & Breakeven quick stats
    const dangerPositions = useMemo(() => positions.filter(p => p.risk_status === 'DANGER'), [positions]);
    const beEligiblePositions = useMemo(() => {
        return positions.filter(p => {
            const tick = livePrices[p.ticker.toUpperCase()];
            const curr = tick?.price || p.current_price || p.entry_price || 0;
            const profitPct = p.entry_price && p.entry_price > 0 ? ((curr - p.entry_price) / p.entry_price) * 100 : 0;
            return profitPct >= 10 && (!p.stop_loss || p.stop_loss < p.entry_price);
        });
    }, [positions, livePrices]);

    const container = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: {
                staggerChildren: 0.03,
            },
        },
    };

    const item = {
        hidden: { opacity: 0, y: 6 },
        show: { opacity: 1, y: 0 },
    };

    const fxRate = currencyMode === 'USD' ? (usdRate || 50.0) : 1.0;

    return (
        <div className="relative glass-technical rounded-2xl overflow-hidden border border-slate-800/80 shadow-2xl" data-testid="portfolio-table">
            {/* Header & Mode Controls */}
            <div className="p-5 border-b border-slate-700/50 flex flex-wrap gap-4 justify-between items-center bg-slate-950/60 backdrop-blur-md">
                <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center space-x-2.5">
                        <h3 className="heading-title text-xl text-slate-100 font-black tracking-tight">Portfolio Holdings</h3>
                        <span className="bg-slate-800 text-cyan-300 text-xs px-2.5 py-0.5 rounded-full font-mono border border-cyan-500/30">
                            {viewMode === 'consolidated' ? `${consolidatedGroups.length} Assets` : `${positions.length} Lots`}
                        </span>
                    </div>

                    {/* View Mode Toggle */}
                    <div className="flex items-center bg-slate-900/90 border border-slate-700/60 rounded-xl p-1 shadow-inner">
                        <button
                            type="button"
                            onClick={() => setViewMode('consolidated')}
                            className={clsx(
                                "flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg transition-all",
                                viewMode === 'consolidated'
                                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                                    : "text-slate-400 hover:text-slate-200"
                            )}
                        >
                            <Layers size={13} />
                            <span>Consolidated Book</span>
                        </button>
                        <button
                            type="button"
                            onClick={() => setViewMode('lots')}
                            className={clsx(
                                "flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg transition-all",
                                viewMode === 'lots'
                                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                                    : "text-slate-400 hover:text-slate-200"
                            )}
                        >
                            <ListFilter size={13} />
                            <span>Individual Lots</span>
                        </button>
                    </div>

                    {feeMode === 'NET' && (
                        <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
                            Net PnL (EGX 0.30% Fee Deducted)
                        </span>
                    )}
                </div>

                {/* Filter Chips */}
                <div className="flex items-center space-x-2">
                    <button
                        type="button"
                        onClick={() => setFilterStatus('ALL')}
                        className={clsx(
                            "text-[10px] font-bold px-2.5 py-1 rounded-lg border transition-all",
                            filterStatus === 'ALL' ? "bg-slate-700 text-white border-slate-500" : "text-slate-400 border-slate-800 hover:bg-slate-800"
                        )}
                    >
                        ALL ({positions.length})
                    </button>
                    {['SAFE', 'WARNING', 'DANGER'].map((status) => {
                        const count = positions.filter(p => p.risk_status === status).length;
                        return (
                            <button
                                key={status}
                                type="button"
                                onClick={() => setFilterStatus(filterStatus === status ? 'ALL' : status)}
                                className={clsx(
                                    "flex items-center gap-1 text-[10px] font-bold px-2.5 py-1 rounded-lg border tracking-wider transition-all",
                                    status === 'SAFE' && (filterStatus === 'SAFE' ? "text-emerald-300 bg-emerald-950/80 border-emerald-500 shadow-sm" : "text-emerald-400 bg-emerald-950/30 border-emerald-900/50 hover:bg-emerald-950/50"),
                                    status === 'WARNING' && (filterStatus === 'WARNING' ? "text-yellow-300 bg-yellow-950/80 border-yellow-500 shadow-sm" : "text-yellow-400 bg-yellow-950/30 border-yellow-900/50 hover:bg-yellow-950/50"),
                                    status === 'DANGER' && (filterStatus === 'DANGER' ? "text-red-300 bg-red-950/80 border-red-500 shadow-sm animate-pulse" : "text-red-400 bg-red-950/30 border-red-900/50 hover:bg-red-950/50")
                                )}
                            >
                                <span>{status}</span>
                                <span className="opacity-75 font-mono">({count})</span>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Emergency Guardian Quick Action Notice Banner */}
            {dangerPositions.length > 0 && onBatchFlatten && (
                <div className="bg-gradient-to-r from-red-950/80 via-red-900/40 to-slate-950 border-b border-red-500/40 p-3 px-5 flex flex-wrap items-center justify-between gap-3 text-xs text-red-200">
                    <div className="flex items-center gap-2.5">
                        <AlertOctagon className="w-4 h-4 text-red-400 shrink-0 animate-bounce" />
                        <span>
                            <strong>GUARDIAN STOP ALERT:</strong> {dangerPositions.length} position(s) are currently violating Stop Loss limits ({dangerPositions.map(p => p.ticker).join(', ')}).
                        </span>
                    </div>
                    <button
                        type="button"
                        onClick={() => onBatchFlatten(dangerPositions.map(p => p.ticker))}
                        className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white font-bold rounded-lg shadow-md transition text-[11px] flex items-center gap-1.5 cursor-pointer"
                    >
                        <Trash2 size={12} />
                        <span>Enforce Stop Discipline (Close All Danger)</span>
                    </button>
                </div>
            )}

            {/* Positive Breakeven Trailing Banner */}
            {beEligiblePositions.length > 0 && onBatchMoveBreakeven && dangerPositions.length === 0 && (
                <div className="bg-gradient-to-r from-emerald-950/70 via-emerald-900/30 to-slate-950 border-b border-emerald-500/30 p-2.5 px-5 flex flex-wrap items-center justify-between gap-3 text-xs text-emerald-200">
                    <div className="flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span>
                            <strong>PROFIT PROTECTION:</strong> {beEligiblePositions.length} position(s) have $+10\%$ gains with stops below cost. Raise stops to breakeven to lock in downside.
                        </span>
                    </div>
                    <button
                        type="button"
                        onClick={() => onBatchMoveBreakeven(beEligiblePositions.map(p => p.ticker))}
                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg shadow-md transition text-[11px] flex items-center gap-1.5 cursor-pointer"
                    >
                        <ShieldCheck size={12} />
                        <span>Raise Stops to Breakeven</span>
                    </button>
                </div>
            )}

            {/* Table Area */}
            <div className="overflow-x-auto custom-scrollbar">
                <table className="w-full min-w-[1160px] text-left border-collapse">
                    <thead>
                        <tr className="text-[10px] text-slate-500 uppercase tracking-widest font-sans border-b border-slate-700/50 bg-slate-950/40">
                            <th className="p-4 pl-5 w-10">
                                <button
                                    onClick={toggleSelectAll}
                                    className="text-slate-400 hover:text-cyan-400 transition-colors"
                                    title={isAllSelected ? "Deselect All" : "Select All"}
                                >
                                    {isAllSelected ? <CheckSquare size={16} className="text-cyan-400" /> : <Square size={16} />}
                                </button>
                            </th>
                            <th className="p-4 font-medium">{viewMode === 'consolidated' ? 'Asset & Lots' : 'Ticker'}</th>
                            <th className="p-4 font-medium text-right">Shares</th>
                            <th className="p-4 font-medium text-right">{viewMode === 'consolidated' ? 'Earliest Entry' : 'Entry Time'}</th>
                            <th className="p-4 font-medium text-right">{viewMode === 'consolidated' ? 'Notional Cost' : 'Exit Time'}</th>
                            <th className="p-4 font-medium text-right">{viewMode === 'consolidated' ? 'Weighted Entry' : 'Avg Entry'}</th>
                            <th className="p-4 font-medium text-right">Live Price</th>
                            <th className="p-4 font-medium text-right">{viewMode === 'consolidated' ? 'Blended Exits' : 'Exits'}</th>
                            <th className="p-4 font-medium text-right">PnL %</th>
                            <th className="p-4 font-medium">Health (Guardian)</th>
                            <th className="p-4 font-medium text-right pr-6">Actions</th>
                        </tr>
                    </thead>

                    {viewMode === 'consolidated' ? (
                        <motion.tbody
                            variants={container}
                            initial="hidden"
                            animate="show"
                            className="divide-y divide-slate-800/50"
                        >
                            {(!filteredConsolidated || filteredConsolidated.length === 0) ? (
                                <tr>
                                    <td colSpan={11} className="p-12 text-center text-slate-500 italic">
                                        No open positions found.
                                    </td>
                                </tr>
                            ) : filteredConsolidated.map((g: ConsolidatedGroup) => {
                                const isSelected = selectedTickers.has(g.ticker);
                                const isExpanded = expandedTickers.has(g.ticker);
                                const hasMultiLot = g.lots.length > 1;

                                const tick = livePrices[g.ticker];
                                const isRecentTick = tick && (Date.now() - tick.timestamp < 3500);

                                const isProfit = g.effectivePnl >= 0;
                                const displayPnl = currencyMode === 'USD' ? (g.effectivePnl / fxRate) : g.effectivePnl;
                                const displayCost = currencyMode === 'USD' ? (g.totalCost / fxRate) : g.totalCost;
                                const currSymbol = currencyMode === 'USD' ? 'USD' : g.currency;

                                return (
                                    <React.Fragment key={g.ticker}>
                                        <motion.tr
                                            variants={item}
                                            className={clsx(
                                                "transition-colors duration-200 group cursor-pointer",
                                                isSelected ? "bg-cyan-950/20 hover:bg-cyan-900/30" : "hover:bg-slate-800/40",
                                                isExpanded && "bg-slate-900/40"
                                            )}
                                            data-testid={`row-${g.ticker}`}
                                            onClick={() => hasMultiLot && toggleExpand(g.ticker)}
                                        >
                                            <td className="p-4 pl-5" onClick={(e) => e.stopPropagation()}>
                                                <button
                                                    onClick={() => toggleSelectTicker(g.ticker)}
                                                    className="text-slate-400 hover:text-cyan-400 transition-colors"
                                                >
                                                    {isSelected ? <CheckSquare size={16} className="text-cyan-400" /> : <Square size={16} />}
                                                </button>
                                            </td>

                                            <td className="p-4">
                                                <div className="flex items-center gap-2.5">
                                                    {hasMultiLot && (
                                                        <div className="text-slate-400 group-hover:text-cyan-300 transition-colors">
                                                            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                                        </div>
                                                    )}
                                                    <div>
                                                        <div className="font-bold text-slate-200 group-hover:text-cyan-400 transition-colors font-mono tracking-tight text-sm flex items-center gap-2">
                                                            {g.ticker}
                                                            {hasMultiLot && (
                                                                <span className="text-[10px] bg-cyan-950/60 text-cyan-300 font-bold px-1.5 py-0.5 rounded border border-cyan-500/40">
                                                                    {g.lots.length} LOTS
                                                                </span>
                                                            )}
                                                            {g.tp1HitCount > 0 && (
                                                                <span className="text-[10px] bg-amber-500/20 text-amber-500 px-1.5 py-0.5 rounded border border-amber-500/30">
                                                                    TP1 HIT
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="text-[9px] text-slate-500 font-bold tracking-widest mt-0.5">{g.currency}</div>
                                                    </div>
                                                </div>
                                            </td>

                                            <td className="p-4 text-right">
                                                <span className="data-value text-slate-200 font-bold text-sm">{(g.totalShares || 0).toLocaleString()}</span>
                                            </td>

                                            <td className="p-4 text-right">
                                                <span className="font-mono text-xs text-slate-400">
                                                    {formatDateTime(g.lots[0]?.entry_date)}
                                                </span>
                                            </td>

                                            <td className="p-4 text-right">
                                                <span className="font-mono text-xs text-slate-300">
                                                    {displayCost.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} <span className="text-[10px] text-slate-500">{currSymbol}</span>
                                                </span>
                                            </td>

                                            <td className="p-4 text-right">
                                                <span className="data-value text-slate-300 text-sm font-mono">
                                                    {truncatePrice(g.weightedEntryPrice)}
                                                </span>
                                            </td>

                                            <td className="p-4 text-right">
                                                <span className={clsx(
                                                    "data-value font-bold text-sm px-2 py-1 rounded border transition-all duration-500",
                                                    isRecentTick && tick?.direction === 'up' && "bg-emerald-500/30 text-emerald-300 border-emerald-400/60 ring-1 ring-emerald-400/40",
                                                    isRecentTick && tick?.direction === 'down' && "bg-rose-500/30 text-rose-300 border-rose-400/60 ring-1 ring-rose-400/40",
                                                    (!isRecentTick || tick?.direction === 'neutral') && "bg-slate-800/50 text-slate-100 border-slate-700/50"
                                                )}>
                                                    {truncatePrice(g.livePrice)}
                                                </span>
                                            </td>

                                            <td className="p-4 text-right">
                                                <div className="flex flex-col items-end text-[10px] font-mono text-slate-400 space-y-0.5 min-w-[70px]">
                                                    {g.weightedTargetPrice > 0 && (
                                                        <span className="px-1 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                                                            TP1: {truncatePrice(g.weightedTargetPrice)}
                                                        </span>
                                                    )}
                                                    {g.weightedTargetPrice2 && (
                                                        <span className="px-1 rounded bg-fuchsia-500/10 text-fuchsia-400 border border-fuchsia-500/20">
                                                            TP2: {truncatePrice(g.weightedTargetPrice2)}
                                                        </span>
                                                    )}
                                                    {g.weightedStopLoss > 0 && (
                                                        <span className="px-1 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                                                            SL: {truncatePrice(g.weightedStopLoss)}
                                                        </span>
                                                    )}
                                                </div>
                                            </td>

                                            <td className="p-4 text-right">
                                                <div className={clsx("flex items-center justify-end font-bold text-sm font-mono tracking-tight", isProfit ? "text-emerald-400" : "text-red-400")}>
                                                    {isProfit ? <ArrowUpRight size={12} className="mr-1" /> : <ArrowDownRight size={12} className="mr-1" />}
                                                    {Math.abs(g.effectivePnlPct).toFixed(2)}%
                                                </div>
                                                <div className={clsx("text-[10px] text-right mt-0.5 opacity-80 font-mono", isProfit ? "text-emerald-500" : "text-red-500")}>
                                                    {displayPnl >= 0 ? '+' : ''}{displayPnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {currSymbol}
                                                </div>
                                            </td>

                                            <td className="p-4">
                                                <div className={clsx("flex items-center space-x-2 text-xs font-bold transition-all duration-300", getHealthColor(g.riskStatus))}>
                                                    <Shield className="w-3.5 h-3.5" />
                                                    <span className="tracking-wide font-sans text-[10px] opacity-90">{g.riskStatus}</span>
                                                </div>
                                            </td>

                                            <td className="p-4 pr-6 text-right" onClick={(e) => e.stopPropagation()}>
                                                <div className="flex items-center justify-end gap-2 opacity-70 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        onClick={() => onEdit(g.lots[0])}
                                                        className="p-1.5 hover:bg-cyan-500/10 border border-transparent hover:border-cyan-500/30 rounded text-slate-400 hover:text-cyan-400 transition-all duration-200"
                                                        title="Update Risk"
                                                        aria-label={`Edit ${g.ticker}`}
                                                    >
                                                        <Edit2 size={13} />
                                                    </button>
                                                    <button
                                                        onClick={() => onClose(g.ticker)}
                                                        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 hover:bg-red-500/10 border border-transparent hover:border-red-500/30 rounded text-slate-400 hover:text-red-400 transition-all duration-200"
                                                        title="Close Position"
                                                        aria-label={`Sell ${g.ticker} (${(g.totalShares || 0).toLocaleString()} shares)`}
                                                    >
                                                        <Trash2 size={13} />
                                                        <span className="text-[10px] font-semibold tracking-wide">
                                                            Sell {(g.totalShares || 0).toLocaleString()}
                                                        </span>
                                                    </button>
                                                </div>
                                            </td>
                                        </motion.tr>

                                        {/* Multi-Lot Accordion Breakdown */}
                                        <AnimatePresence>
                                            {isExpanded && hasMultiLot && (
                                                <motion.tr
                                                    initial={{ opacity: 0, height: 0 }}
                                                    animate={{ opacity: 1, height: 'auto' }}
                                                    exit={{ opacity: 0, height: 0 }}
                                                    className="bg-slate-950/80 border-b border-cyan-500/20"
                                                >
                                                    <td colSpan={11} className="p-4 pl-12 pr-6">
                                                        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 shadow-inner">
                                                            <div className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 mb-2 flex items-center gap-1.5">
                                                                <Layers size={13} />
                                                                <span>Execution Tranches / Lots for {g.ticker}</span>
                                                            </div>
                                                            <div className="space-y-1.5">
                                                                {g.lots.map((lot, idx) => {
                                                                    const lotCost = (lot.entry_price || 0) * (lot.shares || 0);
                                                                    const lotVal = g.livePrice * (lot.shares || 0);
                                                                    const lotPnl = lotVal - lotCost;
                                                                    const lotPnlPct = lotCost > 0 ? (lotPnl / lotCost) * 100 : 0;
                                                                    return (
                                                                        <div
                                                                            key={lot.id || idx}
                                                                            className="flex flex-wrap items-center justify-between gap-3 text-xs bg-slate-950/70 border border-slate-800/80 rounded-lg p-2 px-3 font-mono"
                                                                        >
                                                                            <div className="flex items-center gap-3">
                                                                                <span className="text-slate-500 text-[10px]">Lot #{idx + 1}</span>
                                                                                <span className="text-slate-300 font-bold">{(lot.shares || 0).toLocaleString()} sh</span>
                                                                                <span className="text-slate-400">@ {truncatePrice(lot.entry_price || 0)} {lot.currency}</span>
                                                                                <span className="text-slate-500 text-[11px]">{formatDateTime(lot.entry_date)}</span>
                                                                            </div>
                                                                            <div className="flex items-center gap-4">
                                                                                <div className="flex items-center gap-2 text-[11px]">
                                                                                    {lot.stop_loss && <span className="text-red-400/80">SL: {truncatePrice(lot.stop_loss)}</span>}
                                                                                    {lot.target_price && <span className="text-cyan-400/80">TP: {truncatePrice(lot.target_price)}</span>}
                                                                                </div>
                                                                                <div className={clsx("font-bold text-xs", lotPnl >= 0 ? "text-emerald-400" : "text-rose-400")}>
                                                                                    {lotPnl >= 0 ? '+' : ''}{lotPnlPct.toFixed(2)}% ({lotPnl.toLocaleString(undefined, { maximumFractionDigits: 0 })} {lot.currency})
                                                                                </div>
                                                                                <div className={clsx("text-[10px] font-sans font-bold px-1.5 py-0.5 rounded", getHealthColor(lot.risk_status))}>
                                                                                    {lot.risk_status}
                                                                                </div>
                                                                                <button
                                                                                    onClick={() => onEdit(lot)}
                                                                                    className="p-1 text-slate-400 hover:text-cyan-400 transition"
                                                                                    title="Edit this Lot"
                                                                                >
                                                                                    <Edit2 size={12} />
                                                                                </button>
                                                                            </div>
                                                                        </div>
                                                                    );
                                                                })}
                                                            </div>
                                                        </div>
                                                    </td>
                                                </motion.tr>
                                            )}
                                        </AnimatePresence>
                                    </React.Fragment>
                                );
                            })}
                        </motion.tbody>
                    ) : (
                        /* Individual Lots View */
                        <motion.tbody
                            variants={container}
                            initial="hidden"
                            animate="show"
                            className="divide-y divide-slate-800/50"
                        >
                            {(!filteredPositions || filteredPositions.length === 0) ? (
                                <tr>
                                    <td colSpan={11} className="p-12 text-center text-slate-500 italic">
                                        No open positions found.
                                    </td>
                                </tr>
                            ) : filteredPositions.map((p: Position) => {
                                const diag = health?.diagnoses?.find((d: HealthDiagnosis) => d.ticker === p.ticker);
                                const isSelected = selectedTickers.has(p.ticker);

                                const tick = livePrices[p.ticker.toUpperCase()];
                                const livePrice = tick?.price || p.current_price || p.entry_price || 0;
                                const isRecentTick = tick && (Date.now() - tick.timestamp < 3500);

                                const entryCost = (p.entry_price || 0) * (p.shares || 0);
                                const marketVal = livePrice * (p.shares || 0);
                                const grossPnl = marketVal - entryCost;
                                const feeDeduction = feeMode === 'NET' ? (entryCost * 0.0015 + marketVal * 0.0015) : 0;
                                const effectivePnl = grossPnl - feeDeduction;
                                const effectivePnlPct = entryCost > 0 ? (effectivePnl / entryCost) * 100 : (p.pnl_pct || 0);
                                const isProfit = effectivePnl >= 0;

                                const displayPnl = currencyMode === 'USD' ? (effectivePnl / fxRate) : effectivePnl;
                                const currSymbol = currencyMode === 'USD' ? 'USD' : (p.currency || 'EGP');

                                return (
                                    <motion.tr
                                        key={p.id || p.ticker}
                                        variants={item}
                                        className={clsx(
                                            "transition-colors duration-200 group",
                                            isSelected ? "bg-cyan-950/20 hover:bg-cyan-900/30" : "hover:bg-slate-800/40"
                                        )}
                                        data-testid={`row-${p.ticker}`}
                                    >
                                        <td className="p-4 pl-5">
                                            <button
                                                onClick={() => toggleSelectTicker(p.ticker)}
                                                className="text-slate-400 hover:text-cyan-400 transition-colors"
                                            >
                                                {isSelected ? <CheckSquare size={16} className="text-cyan-400" /> : <Square size={16} />}
                                            </button>
                                        </td>
                                        <td className="p-4">
                                            <div className="flex items-center">
                                                <div>
                                                    <div className="font-bold text-slate-200 group-hover:text-cyan-400 transition-colors font-mono tracking-tight text-sm flex items-center">
                                                        {p.ticker}
                                                        {p.tp1_hit && <span className="ml-2 text-[10px] bg-amber-500/20 text-amber-500 px-1.5 py-0.5 rounded border border-amber-500/30">TP1 HIT</span>}
                                                    </div>
                                                    <div className="text-[9px] text-slate-500 font-bold tracking-widest mt-0.5">{p.currency || 'EGP'}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-4 text-right">
                                            <span className="data-value text-slate-300 text-sm">{(p.shares || 0).toLocaleString()}</span>
                                        </td>
                                        <td className="p-4 text-right">
                                            <span className="font-mono text-xs text-slate-400">{formatDateTime(p.entry_date)}</span>
                                        </td>
                                        <td className="p-4 text-right">
                                            <span className="font-mono text-xs text-slate-500">{formatDateTime(p.exit_date)}</span>
                                        </td>
                                        <td className="p-4 text-right">
                                            <span className="data-value text-slate-400 text-sm">{truncatePrice(p.entry_price || 0)}</span>
                                        </td>
                                        <td className="p-4 text-right">
                                            <span className={clsx(
                                                "data-value font-bold text-sm px-2 py-1 rounded border transition-all duration-500",
                                                isRecentTick && tick?.direction === 'up' && "bg-emerald-500/30 text-emerald-300 border-emerald-400/60 ring-1 ring-emerald-400/40",
                                                isRecentTick && tick?.direction === 'down' && "bg-rose-500/30 text-rose-300 border-rose-400/60 ring-1 ring-rose-400/40",
                                                (!isRecentTick || tick?.direction === 'neutral') && "bg-slate-800/50 text-slate-100 border-slate-700/50"
                                            )}>
                                                {truncatePrice(livePrice)}
                                            </span>
                                        </td>
                                        <td className="p-4 text-right">
                                            <div className="flex flex-col items-end text-[10px] font-mono text-slate-400 space-y-0.5 min-w-[70px]">
                                                {p.target_price ? (
                                                    <span className={clsx("px-1 rounded border", p.tp1_hit ? "bg-amber-500/10 text-amber-500 border-amber-500/20 line-through opacity-70" : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20")}>
                                                        TP1: {truncatePrice(p.target_price)}
                                                    </span>
                                                ) : null}
                                                {p.target_price_2 ? (
                                                    <span className="px-1 rounded bg-fuchsia-500/10 text-fuchsia-400 border border-fuchsia-500/20">
                                                        TP2: {truncatePrice(p.target_price_2)}
                                                    </span>
                                                ) : null}
                                                {p.stop_loss ? (
                                                    <span className="px-1 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                                                        SL: {truncatePrice(p.stop_loss)}
                                                    </span>
                                                ) : null}
                                                {!p.target_price && !p.target_price_2 && !p.stop_loss && (
                                                    <span className="opacity-50">--</span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="p-4 text-right">
                                            <div className={clsx("flex items-center justify-end font-bold text-sm font-mono tracking-tight", isProfit ? "text-emerald-400" : "text-red-400")}>
                                                {isProfit ? <ArrowUpRight size={12} className="mr-1" /> : <ArrowDownRight size={12} className="mr-1" />}
                                                {Math.abs(effectivePnlPct).toFixed(2)}%
                                            </div>
                                            <div className={clsx("text-[10px] text-right mt-0.5 opacity-80 font-mono", isProfit ? "text-emerald-500" : "text-red-500")}>
                                                {displayPnl >= 0 ? '+' : ''}{displayPnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {currSymbol}
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <div className={clsx("flex items-center space-x-2 text-xs font-bold transition-all duration-300", getHealthColor(p.risk_status))}>
                                                <Shield className="w-3.5 h-3.5" />
                                                <span className="tracking-wide font-sans text-[10px] opacity-90">{p.risk_status || 'UNKNOWN'}</span>
                                            </div>
                                            {diag && diag.signals && diag.signals.length > 0 && (
                                                <div className="mt-1.5 flex items-start space-x-1.5">
                                                    <AlertCircle className="w-3 h-3 text-amber-500 shrink-0 mt-0.5" />
                                                    <span className="text-[9px] text-amber-500/80 font-mono leading-tight max-w-[120px] block">
                                                        {diag.signals[0]}
                                                    </span>
                                                </div>
                                            )}
                                        </td>
                                        <td className="p-4 pr-6 text-right">
                                            <div className="flex items-center justify-end gap-2 opacity-60 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => onEdit(p)}
                                                    className="p-1.5 hover:bg-cyan-500/10 border border-transparent hover:border-cyan-500/30 rounded text-slate-400 hover:text-cyan-400 transition-all duration-200"
                                                    title="Update Risk"
                                                    aria-label={`Edit ${p.ticker}`}
                                                >
                                                    <Edit2 size={13} />
                                                </button>
                                                <button
                                                    onClick={() => onClose(p.ticker)}
                                                    className="inline-flex items-center gap-1.5 px-2.5 py-1.5 hover:bg-red-500/10 border border-transparent hover:border-red-500/30 rounded text-slate-400 hover:text-red-400 transition-all duration-200"
                                                    title="Close Position"
                                                    aria-label={`Sell ${p.ticker} (${(p.shares || 0).toLocaleString()} shares)`}
                                                >
                                                    <Trash2 size={13} />
                                                    <span className="text-[10px] font-semibold tracking-wide">
                                                        Sell {(p.shares || 0).toLocaleString()}
                                                    </span>
                                                </button>
                                            </div>
                                        </td>
                                    </motion.tr>
                                );
                            })}
                        </motion.tbody>
                    )}
                </table>
            </div>

            {/* Sticky Floating Multi-Position Batch Operations Bar */}
            <AnimatePresence>
                {selectedTickers.size > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        className="sticky bottom-4 mx-4 my-2 p-3 bg-slate-900/95 backdrop-blur-md border border-cyan-500/40 rounded-xl shadow-2xl flex flex-wrap items-center justify-between gap-3 z-30 ring-1 ring-cyan-500/20"
                    >
                        <div className="flex items-center space-x-3">
                            <span className="flex h-2.5 w-2.5 rounded-full bg-cyan-400 animate-pulse" />
                            <span className="text-xs font-mono text-cyan-200 font-semibold">
                                {selectedTickers.size} position(s) selected
                            </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                            {onBatchMoveBreakeven && (
                                <button
                                    onClick={() => onBatchMoveBreakeven(Array.from(selectedTickers))}
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-950/60 hover:bg-emerald-900/80 border border-emerald-500/50 text-emerald-300 text-xs font-semibold rounded-lg transition-all shadow-sm"
                                    title="Move Stop Loss to Entry Price for all selected positions"
                                >
                                    <ShieldCheck size={14} />
                                    <span>Move Stops to BE</span>
                                </button>
                            )}

                            {onBatchScaleOut50 && (
                                <button
                                    onClick={() => onBatchScaleOut50(Array.from(selectedTickers))}
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-950/60 hover:bg-amber-900/80 border border-amber-500/50 text-amber-300 text-xs font-semibold rounded-lg transition-all shadow-sm"
                                    title="Close 50% shares for all selected positions"
                                >
                                    <Scissors size={14} />
                                    <span>Scale Out 50%</span>
                                </button>
                            )}

                            {onBatchFlatten && (
                                <button
                                    onClick={() => onBatchFlatten(Array.from(selectedTickers))}
                                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-950/70 hover:bg-rose-900 border border-rose-500/60 text-rose-300 text-xs font-semibold rounded-lg transition-all shadow-sm"
                                    title="Emergency Close 100% of all selected positions"
                                >
                                    <AlertOctagon size={14} />
                                    <span>Emergency Flatten</span>
                                </button>
                            )}

                            <button
                                onClick={() => setSelectedTickers(new Set())}
                                className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition-colors ml-2"
                                title="Clear Selection"
                            >
                                <X size={14} />
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
});

PortfolioTable.displayName = 'PortfolioTable';
