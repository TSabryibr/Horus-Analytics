'use client';

import { useEffect } from 'react';

import clsx from 'clsx';
import { ExternalLink, X } from 'lucide-react';

import { deriveSupportedRuntimeFeatures } from './pineRuntimeFeatures';

export type PineProfileDetailsLike = {
    profile_id?: number;
    profile_name: string;
    source_type?: string;
    market?: string;
    timeframe?: string;
    profile_state?: string;
    is_active?: boolean;
    created_at?: string | null;
    ready_at?: string | null;
    activated_at?: string | null;
    activation_count?: number;
    backtest_summary?: {
        total_return?: number;
        trade_count?: number;
        win_rate?: number;
        max_drawdown?: number;
    };
    compatibility_summary?: {
        readiness?: string;
        compatibility_score?: number;
        messages?: string[];
        supported_nodes?: string[];
        plan?: Record<string, any>;
    };
    promotion_summary?: {
        profile_state?: string;
        failed_gates?: string[];
        thresholds?: Record<string, number>;
        actuals?: Record<string, string | number>;
    };
    ranking_summary?: {
        performance_score?: number;
        alignment_score?: number;
        combined_score?: number;
        recommended?: boolean;
    };
    activation_history?: Array<{
        event_type: string;
        activated_at: string;
        previous_state?: string | null;
        previous_active_profile_id?: number | null;
        previous_active_profile_name?: string | null;
    }>;
};

type PineProfileDetailsDialogProps = {
    isOpen: boolean;
    profile: PineProfileDetailsLike | null;
    onClose: () => void;
    primaryHref?: string | null;
    primaryLabel?: string;
};

function getProfileFamilyLabel(sourceType?: string) {
    const normalized = String(sourceType || '').trim().toUpperCase();
    if (normalized === 'PRICE_ACTION') {
        return 'Price Action';
    }
    if (normalized === 'PINE_LOGIC_IMPORT') {
        return 'Imported Logic';
    }
    return 'Pine';
}

function formatAuditStamp(value?: string | null) {
    if (!value) {
        return 'Pending';
    }
    return value.replace('T', ' ').slice(0, 16);
}

function formatMetric(value?: number, digits = 1) {
    if (typeof value !== 'number' || Number.isNaN(value)) {
        return 'N/A';
    }
    return value.toFixed(digits);
}

function formatPercent(value?: number, digits = 1) {
    if (typeof value !== 'number' || Number.isNaN(value)) {
        return 'N/A';
    }
    return `${value >= 0 ? '+' : ''}${value.toFixed(digits)}%`;
}

function formatReadiness(value?: string) {
    const normalized = String(value || 'UNKNOWN').replaceAll('_', ' ').toLowerCase();
    return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function formatGateLabel(gate: string) {
    const labels: Record<string, string> = {
        readiness: 'Preflight readiness',
        compatibility_score: 'Compatibility score',
        combined_score: 'Combined score',
        trade_count: 'Trade count',
        total_return: 'Total return',
        max_drawdown: 'Max drawdown',
    };
    return labels[gate] ?? gate.replaceAll('_', ' ');
}

export function PineProfileDetailsDialog({
    isOpen,
    profile,
    onClose,
    primaryHref,
    primaryLabel = 'Open in Pine Lab',
}: PineProfileDetailsDialogProps) {
    useEffect(() => {
        if (!isOpen) {
            return;
        }

        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                onClose();
            }
        };

        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [isOpen, onClose]);

    if (!isOpen || !profile) {
        return null;
    }

    const ranking = profile.ranking_summary;
    const compatibility = profile.compatibility_summary;
    const promotion = profile.promotion_summary;
    const backtest = profile.backtest_summary;
    const activationHistory = profile.activation_history ?? [];
    const supportedRuntimeFeatures = deriveSupportedRuntimeFeatures(compatibility);
    const failedGates = promotion?.failed_gates ?? [];
    const actuals = promotion?.actuals ?? {};
    const thresholds = promotion?.thresholds ?? {};
    const profileFamilyLabel = getProfileFamilyLabel(profile.source_type);

    return (
        <div
            className="fixed inset-0 z-[140] flex items-center justify-center bg-black/70 p-4"
            role="dialog"
            aria-modal="true"
            aria-label={`Strategy profile details - ${profileFamilyLabel} profile details`}
            onClick={(event) => {
                if (event.target === event.currentTarget) {
                    onClose();
                }
            }}
        >
            <div className="section-surface w-full max-w-5xl overflow-hidden border border-cyan-500/15 bg-[#081019]">
                <div className="flex items-start justify-between gap-4 border-b border-white/10 px-6 py-5">
                    <div>
                        <p className="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-300">{profileFamilyLabel} Profile Details</p>
                        <h2 className="mt-2 text-2xl font-black text-white">{profile.profile_name}</h2>
                        <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-400">
                            {(profile.market ?? 'EGX30')} / {(profile.timeframe ?? '1D')} / {String(profile.profile_state || 'UNKNOWN').toUpperCase()}
                        </p>
                    </div>

                    <div className="flex items-center gap-2">
                        {profile.is_active && (
                            <span className="rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-emerald-300">
                                Active Default
                            </span>
                        )}
                        <button
                            type="button"
                            aria-label="Dismiss Profile Details"
                            className="rounded-md border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
                            onClick={onClose}
                        >
                            <X className="h-4 w-4" />
                        </button>
                    </div>
                </div>

                <div className="max-h-[78vh] overflow-y-auto px-6 py-6">
                    <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
                        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-500">Ranking</p>
                            <div className="mt-3 space-y-2 text-sm text-slate-200">
                                <p>Combined Score: {formatMetric(ranking?.combined_score)}</p>
                                <p>Performance Score: {formatMetric(ranking?.performance_score)}</p>
                                <p>Alignment Score: {formatMetric(ranking?.alignment_score)}</p>
                                <p className={clsx('font-semibold', ranking?.recommended ? 'text-emerald-300' : 'text-slate-300')}>
                                    Recommendation: {ranking?.recommended ? 'Promote to scanner' : 'Needs more evidence'}
                                </p>
                            </div>
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-500">Backtest Snapshot</p>
                            <div className="mt-3 space-y-2 text-sm text-slate-200">
                                <p>Total Return: {formatPercent(backtest?.total_return, 2)}</p>
                                <p>Win Rate: {formatPercent(backtest?.win_rate)}</p>
                                <p>Trade Count: {typeof backtest?.trade_count === 'number' ? backtest.trade_count : 'N/A'}</p>
                                <p>Max Drawdown: {typeof backtest?.max_drawdown === 'number' ? `${backtest.max_drawdown.toFixed(1)}%` : 'N/A'}</p>
                            </div>
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-500">Compatibility Check</p>
                            <div className="mt-3 space-y-2 text-sm text-slate-200">
                                <p>Readiness: {formatReadiness(compatibility?.readiness)}</p>
                                <p>Compatibility Score: {formatMetric(compatibility?.compatibility_score)}</p>
                            </div>
                            <div className="mt-3 space-y-2 text-xs text-slate-300">
                                {(compatibility?.messages?.length ?? 0) > 0 ? compatibility?.messages?.map((message) => (
                                    <p key={message}>{message}</p>
                                )) : (
                                    <p>No compatibility notes captured yet.</p>
                                )}
                            </div>
                            {supportedRuntimeFeatures.length > 0 && (
                                <div className="mt-4 rounded-xl border border-emerald-500/15 bg-emerald-500/5 px-3 py-3 text-xs text-emerald-100">
                                    <p className="font-black uppercase tracking-[0.18em] text-emerald-300">Supported Runtime Features</p>
                                    <div className="mt-2 space-y-1 text-slate-200">
                                        {supportedRuntimeFeatures.map((feature) => (
                                            <p key={feature}>{feature}</p>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-500">Audit Trail</p>
                            <div className="mt-3 space-y-2 text-sm text-slate-200">
                                <p>Created: {formatAuditStamp(profile.created_at)}</p>
                                <p>Ready: {formatAuditStamp(profile.ready_at)}</p>
                                <p>Activated: {formatAuditStamp(profile.activated_at)}</p>
                                <p>Activation Count: {Number(profile.activation_count ?? 0)}</p>
                            </div>
                        </div>
                    </div>

                    <div className="mt-6 grid gap-4 xl:grid-cols-2">
                        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-500">Promotion Gates</p>
                            <div className="mt-3 space-y-2 text-sm text-slate-200">
                                <p>State: {String(profile.profile_state || promotion?.profile_state || 'UNKNOWN').toUpperCase()}</p>
                                {failedGates.length > 0 ? (
                                    failedGates.map((gate) => (
                                        <p key={gate} className="text-amber-200">
                                            Failed Gate: {formatGateLabel(gate)}
                                        </p>
                                    ))
                                ) : (
                                    <p className="text-emerald-300">All ready-state promotion gates are currently passing.</p>
                                )}
                            </div>

                            {Object.keys(actuals).length > 0 && (
                                <div className="mt-4 grid gap-2 md:grid-cols-2">
                                    {Object.entries(actuals).map(([key, value]) => (
                                        <div key={key} className="rounded-xl border border-white/5 bg-white/5 px-3 py-2 text-xs text-slate-300">
                                            Actual {formatGateLabel(key)}: {typeof value === 'number' ? formatMetric(value) : formatReadiness(String(value))}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {Object.keys(thresholds).length > 0 && (
                                <div className="mt-4 grid gap-2 md:grid-cols-2">
                                    {Object.entries(thresholds).map(([key, value]) => (
                                        <div key={key} className="rounded-xl border border-white/5 bg-white/5 px-3 py-2 text-xs text-slate-300">
                                            Threshold {formatGateLabel(key)}: {formatMetric(value)}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-500">Activation History</p>
                            <div className="mt-3 space-y-3 text-sm text-slate-200">
                                {activationHistory.length > 0 ? activationHistory.map((event, index) => (
                                    <div key={`${event.activated_at}-${index}`} className="rounded-xl border border-cyan-500/10 bg-cyan-500/5 px-3 py-3">
                                        <p>{formatAuditStamp(event.activated_at)} - {event.event_type}</p>
                                        <p className="mt-1 text-xs text-slate-300">
                                            {event.previous_active_profile_name
                                                ? `Replaced ${event.previous_active_profile_name}`
                                                : 'First activation'}
                                        </p>
                                    </div>
                                )) : (
                                    <p className="text-slate-400">No activation events have been recorded for this profile yet.</p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex flex-wrap items-center justify-end gap-3 border-t border-white/10 px-6 py-4">
                    {primaryHref && (
                        <a
                            href={primaryHref}
                            className="inline-flex items-center gap-2 rounded-md border border-cyan-400/20 bg-cyan-500/10 px-4 py-2 text-[11px] font-black uppercase tracking-[0.2em] text-cyan-200 transition hover:bg-cyan-500/15 hover:text-white"
                        >
                            <ExternalLink className="h-4 w-4" />
                            {primaryLabel}
                        </a>
                    )}
                    <button
                        type="button"
                        className="rounded-md border border-white/10 bg-white/5 px-4 py-2 text-[11px] font-black uppercase tracking-[0.2em] text-slate-200 transition hover:bg-white/10"
                        onClick={onClose}
                    >
                        Close Profile Details
                    </button>
                </div>
            </div>
        </div>
    );
}
