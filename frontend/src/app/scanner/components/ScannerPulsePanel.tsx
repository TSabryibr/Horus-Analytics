'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ScannerData } from '@/types';
import { ShieldAlert } from 'lucide-react';
import { IndustrialCard } from '../../components/custom/IndustrialCard';
import { getScannerBreadthBarClass, getScannerRegimeClass } from '../lib/scannerTransforms';
import { cn } from '@/lib/utils';

type ScannerPulsePanelProps = {
    data: ScannerData | null;
};

const NumberTicker = ({ value, prefix = '', suffix = '', decimal = 0 }: { value: number, prefix?: string, suffix?: string, decimal?: number }) => {
    return (
        <motion.span
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            key={value}
            transition={{ type: 'spring', stiffness: 100, damping: 15 }}
            className="tabular-nums"
        >
            {prefix}{value.toFixed(decimal)}{suffix}
        </motion.span>
    );
};

function formatAuditStamp(value?: string | null) {
    if (!value) {
        return 'Pending';
    }

    return value.replace('T', ' ').slice(0, 16);
}

function formatMetric(value?: number) {
    if (typeof value !== 'number' || Number.isNaN(value)) {
        return 'N/A';
    }

    return value.toFixed(1);
}

function formatReadiness(value?: string) {
    const normalized = String(value || 'UNKNOWN').replaceAll('_', ' ').toLowerCase();
    return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function getPromotionMarginLines(profile?: ScannerData['strategy_profile']) {
    const actuals = profile?.promotion_summary?.actuals;
    const thresholds = profile?.promotion_summary?.thresholds;

    if (!actuals || !thresholds) {
        return [];
    }

    const lines: string[] = [];
    const compatibilityActual = Number(actuals.compatibility_score);
    const compatibilityThreshold = Number(thresholds.compatibility_score);
    const combinedActual = Number(actuals.combined_score);
    const combinedThreshold = Number(thresholds.combined_score);
    const drawdownActual = Number(actuals.max_drawdown);
    const drawdownThreshold = Number(thresholds.max_drawdown);

    if (Number.isFinite(compatibilityActual) && Number.isFinite(compatibilityThreshold) && compatibilityActual - compatibilityThreshold <= 5) {
        lines.push(`Compatibility margin: ${formatMetric(compatibilityActual)} vs ready floor ${formatMetric(compatibilityThreshold)}`);
    }

    if (Number.isFinite(combinedActual) && Number.isFinite(combinedThreshold) && combinedActual - combinedThreshold <= 5) {
        lines.push(`Combined score margin: ${formatMetric(combinedActual)} vs ready floor ${formatMetric(combinedThreshold)}`);
    }

    if (Number.isFinite(drawdownActual) && Number.isFinite(drawdownThreshold) && drawdownThreshold - drawdownActual <= 5) {
        lines.push(`Drawdown headroom: ${formatMetric(drawdownActual)}% vs ${formatMetric(drawdownThreshold)}% max`);
    }

    return lines;
}

export function ScannerPulsePanel({ data }: ScannerPulsePanelProps) {
    if (!data) return null;

    const diagnostics = data.whale_trap_diagnostics;
    const supportiveWhales = Number(diagnostics?.supportive_whale_alignments || 0);
    const conflicts = Number(diagnostics?.whale_conflicts || 0);
    const highTrap = Number(diagnostics?.high_trap_risk_count || 0);
    const severeTrap = Number(diagnostics?.severe_trap_risk_count || 0);
    const thresholdAnalysis = diagnostics?.threshold_analysis;
    const enforcement = data.enforcement_diagnostics;
    const topEnforcementReason = enforcement?.counts_by_reason ? Object.keys(enforcement.counts_by_reason)[0]?.replaceAll('_', ' ') : null;
    const calibrationSegment = data.calibration_diagnostics?.market_segments
        ? Object.values(data.calibration_diagnostics.market_segments)[0]
        : null;
    const calibrationCandidateKey = calibrationSegment?.candidate_calibration_profiles?.[0]
        || (calibrationSegment?.calibration_summary?.candidates ? Object.keys(calibrationSegment.calibration_summary.candidates)[0] : null);
    const calibrationCandidate = calibrationCandidateKey
        ? calibrationSegment?.calibration_summary?.candidates?.[calibrationCandidateKey]
        : null;
    const strategyProfile = data.strategy_profile;
    const isPineProfile = String(strategyProfile?.source_type || '').toUpperCase() === 'PINE';
    const lastActivation = strategyProfile?.activation_history?.[0];
    const promotionMarginLines = getPromotionMarginLines(strategyProfile);

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <IndustrialCard title="Market Regime" subtitle="Current Volatility Context">
                    <div className="flex items-center justify-between">
                        <div className={cn(
                            "text-xl font-black uppercase tracking-tighter",
                            getScannerRegimeClass(data.regime)
                        )}>
                            {data.regime || 'UNKNOWN'}
                        </div>
                        <div className={cn(
                            "size-2 rounded-full animate-pulse",
                            String(data.regime).toUpperCase() === 'BULLISH' ? "bg-primary shadow-[0_0_10px_#25d1f4]" : "bg-destructive shadow-[0_0_10px_#ff7f50]"
                        )} />
                    </div>
                </IndustrialCard>

                <IndustrialCard title="Market Breadth" subtitle="Sector Participation %">
                    <div className="flex flex-col gap-2">
                        <div className="text-2xl font-black text-white">
                            <NumberTicker value={Number(data.breadth)} suffix="%" decimal={1} />
                        </div>
                        <div className="w-full bg-white/5 h-1.5 rounded-none overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${data.breadth}%` }}
                                transition={{ duration: 1, ease: "easeOut" }}
                                className={cn("h-full", getScannerBreadthBarClass(data.breadth))}
                            />
                        </div>
                    </div>
                </IndustrialCard>

                <IndustrialCard title="Signals Found" subtitle="Validated Tactical Alerts">
                    <div className="flex items-end justify-between">
                        <div className="text-3xl font-black text-primary">
                            <NumberTicker value={data.signals_count || 0} />
                        </div>
                        <span className="terminal-tag terminal-tag-primary">LIVE_FEED</span>
                    </div>
                </IndustrialCard>

                <IndustrialCard title="Shadow Observability" subtitle="Whale Alignment Logic">
                     <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                        <div className="flex items-center justify-between">
                            <span className="text-[9px] uppercase font-bold text-slate-500">Support</span>
                            <span className="text-[10px] font-mono font-bold text-emerald-400">{supportiveWhales} supportive</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-[9px] uppercase font-bold text-slate-500">Conflict</span>
                            <span className="text-[10px] font-mono font-bold text-rose-400">{conflicts} conflict</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-[9px] uppercase font-bold text-slate-500">High Risk</span>
                            <span className="text-[10px] font-mono font-bold text-amber-400">{highTrap} high</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-[9px] uppercase font-bold text-slate-500">Severe</span>
                            <span className="text-[10px] font-mono font-bold text-destructive">{severeTrap} severe</span>
                        </div>
                     </div>
                </IndustrialCard>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <IndustrialCard title="Shadow Legend" subtitle="Volume Flow & Institutional Positioning">
                    <div className="space-y-4">
                        <p className="text-[11px] text-slate-400 leading-relaxed font-mono">
                           <span className="text-primary mr-2 font-bold">[PROT_ALPHA]</span>
                           <span>Whale Support favors long setups with accumulation.</span>{' '}
                           <span>
                               Alignment confidence is <NumberTicker value={String(data.regime).toUpperCase() === 'BULLISH' ? 88.4 : 42.1} suffix="%" decimal={1} />.
                           </span>
                        </p>
                        <div className="flex gap-4">
                            <div className="flex-1 industrial-border border p-3 flex flex-col gap-1 bg-white/[0.02]">
                                <span className="text-[8px] uppercase font-black text-slate-600">Enforcement Blocked</span>
                                <span className="text-sm font-black text-destructive">{data.enforcement_diagnostics?.block_count || 0} Assets</span>
                            </div>
                            <div className="flex-1 industrial-border border p-3 flex flex-col gap-1 bg-white/[0.02]">
                                <span className="text-[8px] uppercase font-black text-slate-600">Watch-Only Protocols</span>
                                <span className="text-sm font-black text-amber-500">{data.enforcement_diagnostics?.watch_only_count || 0} Assets</span>
                            </div>
                        </div>
                        <p className="text-[10px] uppercase tracking-[0.18em] text-slate-400">
                            Future gates: {thresholdAnalysis?.would_review_count || 0} review / {thresholdAnalysis?.would_block_count || 0} block
                        </p>
                    </div>
                </IndustrialCard>

                <IndustrialCard title="Enforcement Rollup" subtitle="System Enforcement Summary">
                    <div className="space-y-3">
                         <div className="p-3 bg-slate-950 industrial-border border border-white/5 flex items-center justify-between">
                             <div className="flex flex-col">
                                 <span className="text-[10px] font-black uppercase text-slate-400">Primary Breach Reason</span>
                                 <span className="text-xs font-mono text-slate-200 mt-1 uppercase">
                                     {topEnforcementReason || 'NO_BREACH'}
                                 </span>
                             </div>
                             <ShieldAlert className="size-5 text-slate-700" />
                         </div>
                         <div className="grid grid-cols-3 gap-3">
                             <div className="text-[9px] uppercase font-bold text-slate-500">
                                <span className="text-white font-mono">{enforcement?.allow_count || 0} allow</span>
                             </div>
                             <div className="text-[9px] uppercase font-bold text-slate-500 text-center">
                                <span className="text-amber-400 font-mono">{enforcement?.watch_only_count || 0} watch-only</span>
                             </div>
                             <div className="text-[9px] uppercase font-bold text-slate-500 text-right">
                                <span className="text-rose-400 font-mono">{enforcement?.block_count || 0} blocked</span>
                             </div>
                         </div>
                         <div className="pt-2 border-t border-white/5">
                             <p className="text-[9px] text-slate-600 italic">
                                Top enforcement reason: {topEnforcementReason || 'none'}
                             </p>
                         </div>
                    </div>
                </IndustrialCard>
            </div>

            {calibrationSegment && calibrationCandidate ? (
                <IndustrialCard title="Calibration Compare" subtitle="Promotion fallback diagnostics">
                    <div className="space-y-3 text-xs text-slate-300">
                        <p>{calibrationSegment.active_enforcement_profile} -&gt; {calibrationCandidateKey}</p>
                        <p>Rollback: {calibrationSegment.rollback_profile || 'None'}</p>
                        <p>
                            Delta: {calibrationCandidate.deltas.allow_delta >= 0 ? '+' : ''}{calibrationCandidate.deltas.allow_delta} allow / {calibrationCandidate.deltas.watch_only_delta >= 0 ? '+' : ''}{calibrationCandidate.deltas.watch_only_delta} watch / {calibrationCandidate.deltas.block_delta >= 0 ? '+' : ''}{calibrationCandidate.deltas.block_delta} block
                        </p>
                    </div>
                </IndustrialCard>
            ) : null}

            {strategyProfile ? (
                <IndustrialCard title="Scanner Profile" subtitle="Persisted Pine audit + ranking telemetry">
                    <div className="space-y-5">
                        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                            <div className="space-y-2">
                                <h3 className="text-lg font-black text-white">{strategyProfile.profile_name}</h3>
                                <div className="flex flex-wrap gap-2 text-[10px] uppercase tracking-[0.18em] text-slate-400">
                                    <span>{strategyProfile.market}</span>
                                    <span>/</span>
                                    <span>{strategyProfile.timeframe}</span>
                                    {strategyProfile.activated_at ? (
                                        <span>Activated {formatAuditStamp(strategyProfile.activated_at)}</span>
                                    ) : null}
                                    <span>Activations: {Number(strategyProfile.activation_count ?? 0)}</span>
                                </div>
                                {lastActivation?.previous_active_profile_name ? (
                                    <p className="text-xs text-slate-400">
                                        Last activation replaced {lastActivation.previous_active_profile_name}
                                    </p>
                                ) : null}
                            </div>

                            {isPineProfile ? (
                                <a
                                    href={strategyProfile.profile_id ? `/optimization?mode=PINE_LAB&profileId=${strategyProfile.profile_id}` : '/optimization?mode=PINE_LAB'}
                                    className="inline-flex items-center justify-center rounded-[0.95rem] border border-cyan-500/20 bg-cyan-500/10 px-3 py-2 text-[11px] font-black uppercase tracking-[0.2em] text-cyan-200 transition hover:bg-cyan-500/15 hover:text-white"
                                >
                                    Open in Pine Lab
                                </a>
                            ) : null}
                        </div>

                        {isPineProfile ? (
                            <div className="grid gap-4 lg:grid-cols-3">
                                <div className="section-surface-muted rounded-[1rem] p-4">
                                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-slate-500">Profile Ranking</p>
                                    <div className="mt-3 space-y-2 text-xs text-slate-300">
                                        <p>Combined Score</p>
                                        <p className="text-lg font-black text-white">{formatMetric(strategyProfile.ranking_summary?.combined_score)}</p>
                                        <p>Performance</p>
                                        <p className="text-lg font-black text-white">{formatMetric(strategyProfile.ranking_summary?.performance_score)}</p>
                                        <p>Alignment</p>
                                        <p className="text-lg font-black text-white">{formatMetric(strategyProfile.ranking_summary?.alignment_score)}</p>
                                        {strategyProfile.ranking_summary?.recommended ? (
                                            <p className="text-emerald-300">Recommended for scanner promotion</p>
                                        ) : null}
                                    </div>
                                </div>

                                <div className="section-surface-muted rounded-[1rem] p-4">
                                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-slate-500">Backtest Snapshot</p>
                                    <div className="mt-3 space-y-2 text-xs text-slate-300">
                                        <p>Return</p>
                                        <p className="text-lg font-black text-white">{formatMetric(strategyProfile.backtest_summary?.total_return)}%</p>
                                        <p>Win Rate</p>
                                        <p className="text-lg font-black text-white">{formatMetric(strategyProfile.backtest_summary?.win_rate)}%</p>
                                        <p>Trades</p>
                                        <p className="text-lg font-black text-white">{strategyProfile.backtest_summary?.trade_count ?? 'N/A'}</p>
                                        <p>Max DD</p>
                                        <p className="text-lg font-black text-white">{formatMetric(strategyProfile.backtest_summary?.max_drawdown)}%</p>
                                    </div>
                                </div>

                                <div className="section-surface-muted rounded-[1rem] p-4">
                                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-slate-500">Compatibility Check</p>
                                    <div className="mt-3 space-y-2 text-xs text-slate-300">
                                        <p>{formatReadiness(strategyProfile.compatibility_summary?.readiness)}</p>
                                        <p>Score</p>
                                        <p className="text-lg font-black text-white">{formatMetric(strategyProfile.compatibility_summary?.compatibility_score)}</p>
                                        {(strategyProfile.compatibility_summary?.messages || []).map((message) => (
                                            <p key={message}>{message}</p>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="grid gap-4 lg:grid-cols-3">
                                <div className="section-surface-muted rounded-[1rem] p-4">
                                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-slate-500">Native Engine</p>
                                    <div className="mt-3 space-y-2 text-xs text-slate-300">
                                        <p>Signal Model</p>
                                        <p className="text-lg font-black text-white">Horus Core Engine</p>
                                        <p>Market Scope</p>
                                        <p className="text-lg font-black text-white">{strategyProfile.market || 'ALL'}</p>
                                        <p>Timeframe</p>
                                        <p className="text-lg font-black text-white">{strategyProfile.timeframe || '1D'}</p>
                                    </div>
                                </div>

                                <div className="section-surface-muted rounded-[1rem] p-4">
                                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-slate-500">Scan Snapshot</p>
                                    <div className="mt-3 space-y-2 text-xs text-slate-300">
                                        <p>Regime</p>
                                        <p className="text-lg font-black text-white">{data.regime || 'UNKNOWN'}</p>
                                        <p>Breadth</p>
                                        <p className="text-lg font-black text-white">{formatMetric(Number(data.breadth))}%</p>
                                        <p>Signals</p>
                                        <p className="text-lg font-black text-white">{Number(data.signals_count || 0)}</p>
                                    </div>
                                </div>

                                <div className="section-surface-muted rounded-[1rem] p-4">
                                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-slate-500">Native Execution</p>
                                    <div className="mt-3 space-y-2 text-xs text-slate-300">
                                        <p>Ready</p>
                                        <p className="text-lg font-black text-white">Ready</p>
                                        <p>Telemetry</p>
                                        <p>Activate a Pine scanner profile to unlock ranking, backtest, and compatibility telemetry.</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {isPineProfile && promotionMarginLines.length > 0 ? (
                            <div className="rounded-[1rem] border border-amber-500/20 bg-amber-500/10 p-4">
                                <p className="text-[10px] font-black uppercase tracking-[0.22em] text-amber-200">Borderline Promotion Margin</p>
                                <p className="mt-2 text-xs text-amber-100/90">
                                    Scanner is active, but this Pine profile is running close to one or more promotion thresholds.
                                </p>
                                <div className="mt-2 space-y-1 text-xs text-amber-100/90">
                                    {promotionMarginLines.map((line) => (
                                        <p key={line}>{line}</p>
                                    ))}
                                </div>
                            </div>
                        ) : null}
                    </div>
                </IndustrialCard>
            ) : null}
        </div>
    );
}
