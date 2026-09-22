'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ChevronRight, Activity } from 'lucide-react';
import { ScannerData, ScannerSignal } from '@/types';
import { 
    describeScannerEnforcementState,
    describeScannerTrapRiskBand,
    describeScannerWhaleAlignment,
    formatScannerEnforcementReason,
    formatScannerEnforcementState, 
    formatScannerRouteProfile,
    formatScannerSectorRs,
    formatScannerVsaLabel,
    formatScannerWhaleAlignment, 
    formatScannerTrapRiskBand,
    truncateScannerPrice 
} from '../lib/scannerTransforms';
import { cn } from '@/lib/utils';
import { IndustrialButton } from '../../components/custom/IndustrialButton';

type ScannerResultsTableProps = {
    data: ScannerData | null;
    loading: boolean;
    onPromoteCandidate?: (candidate: Record<string, unknown>) => void | Promise<unknown>;
};

export function ScannerResultsTable({ data, loading, onPromoteCandidate }: ScannerResultsTableProps) {
    const [promotingKey, setPromotingKey] = React.useState<string | null>(null);

    const handlePromote = async (lane: 'INTRADAY' | 'SWING' | 'POSITION', signal: ScannerSignal) => {
        const key = `${signal.Ticker}-${lane}`;
        if (promotingKey === key) return;
        setPromotingKey(key);
        try {
            await onPromoteCandidate?.({
                lane,
                ticker: signal.Ticker,
                side: signal.Signal_Type,
                entry_price: signal.Entry_Price,
                stop_loss: signal.Stop_Loss,
                target_price: signal.Target_Price,
                confidence: Math.min(100, Math.max(0, Number(signal.Score || 0) * 20)),
                score: Number(signal.Score || 0),
                source_module: 'SCANNER',
                rationale: {
                    signal_setup: signal.Signal_Setup,
                    route_profile: signal.Route_Profile,
                    whale_alignment: signal.Whale_Alignment,
                    trap_risk_band: signal.Trap_Risk_Band,
                },
            });
        } finally {
            setPromotingKey(null);
        }
    };

    return (
        <div className="industrial-border border bg-slate-950 overflow-hidden">
            <div className="overflow-x-auto custom-scrollbar">
                <table className="w-full text-left border-collapse min-w-[1000px]">
                    <thead>
                        <tr className="border-b border-white/5 bg-white/[0.01]">
                            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-widest text-slate-500">Asset Telemetry</th>
                            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-widest text-slate-500">Tactical Setup</th>
                            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-widest text-slate-500 font-mono">Entry</th>
                            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-widest text-slate-500 font-mono text-center">Stop // TP</th>
                            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-widest text-slate-500 text-center">Confidence</th>
                            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-widest text-slate-500 text-right">Directives</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {!data && !loading && (
                            <tr>
                                <td colSpan={6} className="py-24 text-center">
                                    <div className="flex flex-col items-center gap-4 opacity-40">
                                        <div className="size-12 industrial-border border flex items-center justify-center">
                                            <Activity className="size-6" />
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-sm font-black uppercase tracking-[0.26em] text-white">Ready for Mission Control</p>
                                            <p className="text-[10px] uppercase tracking-[0.24em] text-slate-500">Initialize a scan to begin market telemetry.</p>
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        )}

                        {data?.signals?.map((signal: ScannerSignal, i: number) => {
                            const isPromotingIntra = promotingKey === `${signal.Ticker}-INTRADAY`;
                            const isPromotingSwing = promotingKey === `${signal.Ticker}-SWING`;
                            const isPromotingPos = promotingKey === `${signal.Ticker}-POSITION`;
                            const isRowPromoting = isPromotingIntra || isPromotingSwing || isPromotingPos;

                            return (
                                <motion.tr
                                    key={i}
                                    initial={{ opacity: 0, x: -5 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.03, duration: 0.3 }}
                                    className={cn(
                                        "group hover:bg-white/[0.03] transition-colors relative cursor-default",
                                        signal.Enforcement_State === 'BLOCK_EXECUTION' && "opacity-40 grayscale pointer-events-none"
                                    )}
                                >
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-3">
                                            <div className="size-8 industrial-border border border-white/10 flex items-center justify-center font-black text-[10px] group-hover:border-primary/40 group-hover:bg-primary/[0.05] transition-all">
                                                {signal.Ticker}
                                            </div>
                                            <div>
                                                <p className="text-xs font-black text-white group-hover:text-primary transition-colors tracking-tight">{signal.Ticker}</p>
                                                <p className="text-[8px] font-mono text-slate-600 uppercase tracking-tighter">ID_SQ: {i.toString().padStart(3, '0')}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="space-y-2">
                                            <div className="flex flex-wrap gap-1.5">
                                                <span className={cn(
                                                    "terminal-tag",
                                                    signal.Signal_Type === 'BUY' ? "terminal-tag-primary" : "terminal-tag-alert"
                                                )}>
                                                    {signal.Signal_Type}
                                                </span>
                                                <span className="terminal-tag terminal-tag-muted">
                                                    {signal.Signal_Setup || 'BREAKOUT'}
                                                </span>
                                                <span className="terminal-tag terminal-tag-muted">
                                                    {formatScannerRouteProfile(signal.Route_Profile)}
                                                </span>
                                                {signal.Liquidity_Tier ? (
                                                    <span className="terminal-tag terminal-tag-muted">
                                                        {signal.Liquidity_Tier}
                                                    </span>
                                                ) : null}
                                            </div>

                                            <div className="flex flex-wrap gap-1.5 text-[9px]">
                                                {signal.Volume_x ? (
                                                    <span className="rounded-sm border border-white/8 bg-white/[0.03] px-2 py-1 text-slate-300">
                                                        {signal.Volume_x}x
                                                    </span>
                                                ) : null}
                                                <span className="rounded-sm border border-white/8 bg-white/[0.03] px-2 py-1 text-slate-300">
                                                    {formatScannerVsaLabel(signal.VSA_Valid)}
                                                </span>
                                                <span className="rounded-sm border border-white/8 bg-white/[0.03] px-2 py-1 text-slate-300">
                                                    {formatScannerSectorRs(signal.Sector_RS_14)}
                                                </span>
                                                <span
                                                    className="rounded-sm border border-cyan-500/15 bg-cyan-500/[0.06] px-2 py-1 text-cyan-300"
                                                    title={describeScannerWhaleAlignment(signal.Whale_Alignment)}
                                                >
                                                    {formatScannerWhaleAlignment(signal.Whale_Alignment)}
                                                </span>
                                                <span
                                                    className="rounded-sm border border-amber-500/15 bg-amber-500/[0.06] px-2 py-1 text-amber-300"
                                                    title={describeScannerTrapRiskBand(signal.Trap_Risk_Band)}
                                                >
                                                    {formatScannerTrapRiskBand(signal.Trap_Risk_Band)}
                                                </span>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 font-mono text-[11px] font-bold text-slate-300">
                                        {truncateScannerPrice(signal.Entry_Price)}
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center justify-center gap-4 font-mono text-[10px]">
                                            <span className="text-rose-400/80">{truncateScannerPrice(signal.Stop_Loss)}</span>
                                            <span className="text-slate-700">|</span>
                                            <span className="text-emerald-400/80">{truncateScannerPrice(signal.Target_Price)}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center justify-center gap-3">
                                            <div className="w-12 h-1 bg-white/5 rounded-none overflow-hidden">
                                                <div className="h-full bg-primary" style={{ width: `${(signal.Score / 5) * 100}%` }} />
                                            </div>
                                            <span className="text-[10px] font-black text-cyan-400 w-8 text-right">{(signal.Score || 0).toFixed(1)}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            {signal.Enforcement_State && (
                                                <span className={cn(
                                                    "text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-sm border",
                                                    signal.Enforcement_State === 'BLOCK_EXECUTION' ? "bg-destructive/10 border-destructive/30 text-destructive" :
                                                    signal.Enforcement_State === 'WATCH_ONLY' ? "bg-amber-500/10 border-amber-500/30 text-amber-500" :
                                                    "bg-emerald-500/10 border-emerald-500/30 text-emerald-500"
                                                )} title={describeScannerEnforcementState(signal.Enforcement_State)}>
                                                    {formatScannerEnforcementState(signal.Enforcement_State)}
                                                </span>
                                            )}
                                            <IndustrialButton
                                                variant="ghost"
                                                size="sm"
                                                className="px-2 py-1 text-[9px]"
                                                disabled={isRowPromoting}
                                                onClick={() => { void handlePromote('INTRADAY', signal); }}
                                                aria-label={`Promote ${signal.Ticker} to intraday lane`}
                                            >
                                                {isPromotingIntra ? 'Promoting...' : 'Intra'}
                                            </IndustrialButton>
                                            <IndustrialButton
                                                variant="ghost"
                                                size="sm"
                                                className="px-2 py-1 text-[9px]"
                                                disabled={isRowPromoting}
                                                onClick={() => { void handlePromote('SWING', signal); }}
                                                aria-label={`Promote ${signal.Ticker} to swing lane`}
                                            >
                                                {isPromotingSwing ? 'Promoting...' : 'Swing'}
                                            </IndustrialButton>
                                            <IndustrialButton
                                                variant="ghost"
                                                size="sm"
                                                className="px-2 py-1 text-[9px]"
                                                disabled={isRowPromoting}
                                                onClick={() => { void handlePromote('POSITION', signal); }}
                                                aria-label={`Promote ${signal.Ticker} to position lane`}
                                            >
                                                {isPromotingPos ? 'Promoting...' : 'Position'}
                                            </IndustrialButton>
                                            <IndustrialButton variant="ghost" size="sm" className="size-6 p-0 border-white/5">
                                                <ChevronRight className="size-3" />
                                            </IndustrialButton>
                                        </div>
                                        {signal.Enforcement_Reason ? (
                                            <div className="mt-1 text-[9px] uppercase tracking-[0.18em] text-slate-500">
                                                {formatScannerEnforcementReason(signal.Enforcement_Reason)}
                                            </div>
                                        ) : null}
                                    </td>
                                </motion.tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
