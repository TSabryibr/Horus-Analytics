'use client';

import type { ReactNode } from 'react';

import { clsx } from 'clsx';
import { BarChart3, CheckCircle2, RotateCw, Sparkles, TrendingUp } from 'lucide-react';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';

type OptimizationResultsPanelProps = {
    simResult: any;
    simParams: any;
    auditLoading: boolean;
    onRunAiAudit: () => void | Promise<void>;
    onPromptApply: (params: any) => void;
    chartContent: ReactNode;
};

function formatResearchMetric(value: unknown, decimals = 2) {
    if (value == null || value === '') {
        return '--';
    }

    const numericValue = Number(value);
    if (Number.isFinite(numericValue)) {
        return numericValue.toFixed(decimals);
    }

    const textValue = String(value).trim();
    return textValue || '--';
}

export function OptimizationResultsPanel({
    simResult,
    simParams,
    auditLoading,
    onRunAiAudit,
    onPromptApply,
    chartContent,
}: OptimizationResultsPanelProps) {
    const sourceMetadata = simResult?.source_metadata ?? {};
    const isPineProfileResult = sourceMetadata?.backtest_source === 'PINE_PROFILE';
    const pineReadiness = formatResearchMetric(simResult?.compatibility?.readiness, 0);
    const pineCompatibility = formatResearchMetric(simResult?.compatibility?.compatibility_score);
    const pinePerformance = formatResearchMetric(simResult?.rankings?.performance_score);
    const pineAlignment = formatResearchMetric(simResult?.alignment?.alignment_score);
    const pineCombined = formatResearchMetric(simResult?.rankings?.combined_score);

    return (
        <div className="lg:col-span-3 space-y-8">
            {simResult && simResult.metrics && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 animate-in fade-in slide-in-from-right-4 duration-700">
                    <IndustrialCard tone="secondary" className="relative overflow-hidden group" contentClassName="p-6">
                        <div className="absolute top-0 right-0 p-1 h-3 w-3 border-t border-r border-primary/20" />
                        <p className="text-[9px] font-black uppercase tracking-[0.3em] text-slate-500 mb-2">Total_Yield</p>
                        <p className={clsx('text-4xl font-black font-mono tracking-tighter  ', simResult.metrics.total_return >= 0 ? 'text-emerald-400' : 'text-rose-400')}>
                            {simResult.metrics.total_return > 0 ? '+' : ''}
                            {simResult.metrics.total_return.toFixed(2)}%
                        </p>
                        <div className="absolute bottom-0 left-0 h-[1px] bg-primary/20 w-8" />
                    </IndustrialCard>
                    <IndustrialCard tone="secondary" className="relative overflow-hidden group" contentClassName="p-6">
                        <div className="absolute top-0 right-0 p-1 h-3 w-3 border-t border-r border-primary/20" />
                        <p className="text-[9px] font-black uppercase tracking-[0.3em] text-slate-500 mb-2">Final_Equity</p>
                        <p className="text-4xl font-black font-mono tracking-tighter text-white">
                            EGP{simResult.metrics.final_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </p>
                        <div className="absolute bottom-0 left-0 h-[1px] bg-primary/20 w-8" />
                    </IndustrialCard>
                    <IndustrialCard tone="secondary" className="relative overflow-hidden group" contentClassName="p-6">
                        <div className="absolute top-0 right-0 p-1 h-3 w-3 border-t border-r border-primary/20" />
                        <p className="text-[9px] font-black uppercase tracking-[0.3em] text-slate-500 mb-2">Exec_Count</p>
                        <p className="text-4xl font-black font-mono tracking-tighter text-primary">
                            {simResult.metrics.trade_count}
                        </p>
                        <div className="absolute bottom-0 left-0 h-[1px] bg-primary/20 w-8" />
                    </IndustrialCard>
                    <IndustrialCard tone="secondary" className="relative overflow-hidden group" contentClassName="p-6">
                        <div className="absolute top-0 right-0 p-1 h-3 w-3 border-t border-r border-primary/20" />
                        <p className="text-[9px] font-black uppercase tracking-[0.3em] text-slate-500 mb-2">
                            {isPineProfileResult ? 'Research_Source' : 'AI_Verification'}
                        </p>
                        {isPineProfileResult ? (
                            <div className="space-y-2 text-sm text-slate-300">
                                <p className="font-black uppercase tracking-[0.18em] text-primary">Backtest Source: Pine Profile</p>
                                {sourceMetadata?.profile_name ? (
                                    <p className="text-[11px] font-black uppercase tracking-[0.16em] text-white">
                                        Profile: {String(sourceMetadata.profile_name)}
                                    </p>
                                ) : null}
                                {sourceMetadata?.profile_state ? (
                                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-300">
                                        Profile State: {String(sourceMetadata.profile_state)}
                                    </p>
                                ) : null}
                            </div>
                        ) : (
                            <IndustrialButton
                                type="button"
                                onClick={onRunAiAudit}
                                disabled={auditLoading}
                                variant={auditLoading ? 'secondary' : 'ghost'}
                                className={clsx('px-0 py-0 !border-0 !bg-transparent !shadow-none text-sm tracking-widest', auditLoading ? 'text-slate-600' : 'text-primary hover:text-white')}
                            >
                                {auditLoading ? 'Auditing...' : 'Run AI Audit'}
                                <Sparkles className={clsx('w-4 h-4', auditLoading && 'animate-spin')} />
                            </IndustrialButton>
                        )}
                        <div className="absolute bottom-0 left-0 h-[1px] bg-primary/20 w-8" />
                    </IndustrialCard>
                    {!isPineProfileResult ? (
                        <IndustrialButton
                            type="button"
                            onClick={() => onPromptApply(simParams)}
                            variant="primary"
                            className="h-auto items-start justify-start px-6 py-6 text-left text-[10px] tracking-[0.3em]"
                        >
                            <div className="flex flex-col items-start gap-2">
                                <span className="text-[9px] font-black uppercase tracking-[0.3em] text-cyan-100/70">Deployment</span>
                                <span className="flex items-center gap-3 text-xs font-black uppercase tracking-[0.2em] text-white">
                                    Apply_Config
                                    <CheckCircle2 size={16} className="text-primary" />
                                </span>
                            </div>
                        </IndustrialButton>
                    ) : (
                        <IndustrialCard tone="secondary" className="relative overflow-hidden group" contentClassName="p-6">
                            <div className="absolute top-0 right-0 p-1 h-3 w-3 border-t border-r border-primary/20" />
                            <p className="text-[9px] font-black uppercase tracking-[0.3em] text-slate-500 mb-3">Pine Research Summary</p>
                            <div className="space-y-2 text-[11px] font-black uppercase tracking-[0.16em] text-slate-300">
                                <p className="text-cyan-300">Readiness: {pineReadiness}</p>
                                <p>Compatibility: {pineCompatibility}</p>
                                <p>Performance: {pinePerformance}</p>
                                <p>Alignment: {pineAlignment}</p>
                                <p className="border-t border-white/10 pt-2 text-primary">Combined: {pineCombined}</p>
                            </div>
                            <div className="absolute bottom-0 left-0 h-[1px] bg-primary/20 w-8" />
                        </IndustrialCard>
                    )}
                </div>
            )}

            <IndustrialCard
                tone="primary"
                className="scan-line relative min-h-[550px] overflow-hidden group"
                contentClassName="flex min-h-[550px] flex-col p-10"
            >
                <div className="absolute top-0 left-0 flex h-12 w-full items-center justify-between border-b border-white/8 bg-white/[0.03] px-6">
                    <h3 className="font-heading font-black text-[9px] uppercase tracking-[0.4em] text-slate-400 flex items-center gap-4">
                        <div className="w-2 h-2 bg-emerald-500 industrial-corner" />
                        Equity_Projection_Matrix_FY{new Date().getFullYear()}
                    </h3>
                    <div className="flex gap-4">
                        <div className="w-16 h-1 bg-white/10 industrial-corner overflow-hidden">
                            <div className="h-full bg-primary/40 w-1/2" />
                        </div>
                        <TrendingUp size={12} className="text-emerald-500" />
                    </div>
                </div>

                <div className="mt-8 mb-8">
                    {simResult?.assumptions && (
                        <div className="text-[9px] uppercase tracking-[0.3em] text-slate-500 font-bold flex gap-8">
                            <div className="flex items-center gap-2">
                                <div className="w-1 h-1 bg-amber-500" />
                                <span>COMM_MODEL: {Number(simResult.assumptions.commission_pct ?? 0).toFixed(2)}%</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-1 h-1 bg-cyan-500" />
                                <span>SLIP_TARGET: {Number(simResult.assumptions.slippage_pct ?? 0).toFixed(2)}%</span>
                            </div>
                        </div>
                    )}
                </div>

                {simResult ? (
                    <div className="section-surface-muted industrial-corner flex-1 w-full border border-white/8 p-4">
                        {chartContent}
                    </div>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-slate-800 gap-8">
                        <div className="relative">
                            <BarChart3 size={120} className="stroke-[0.5]" />
                            <div className="absolute inset-0 flex items-center justify-center">
                                <RotateCw className="h-8 w-8 text-primary animate-spin opacity-20" />
                            </div>
                        </div>
                        <div className="flex flex-col items-center gap-2">
                            <p className="text-[10px] font-black uppercase tracking-[0.5em] font-mono">Waiting_For_Telemetry</p>
                            <div className="h-[1px] w-24 bg-white/[0.08]" />
                        </div>
                    </div>
                )}
            </IndustrialCard>
        </div>
    );
}
