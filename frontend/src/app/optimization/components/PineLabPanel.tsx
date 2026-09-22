'use client';

import { type ReactNode, useMemo, useState } from 'react';

import { clsx } from 'clsx';
import { Activity, FileCode2, Radar, RefreshCw, Rocket, ShieldCheck } from 'lucide-react';

import { PineProfileDetailsDialog } from '@/app/components/PineProfileDetailsDialog';
import { deriveSupportedRuntimeFeatures } from '@/app/components/pineRuntimeFeatures';

import type { PineLabForm } from '../hooks/usePineBacktest';
import type { PineProfileRecord } from '../hooks/usePineProfilePromotion';

type PineLabPanelProps = {
    pineForm: PineLabForm;
    onChangeForm: (nextForm: PineLabForm) => void;
    preflightResult: any;
    preflightLoading: boolean;
    onRunPreflight: () => void | Promise<void>;
    importPreviewResult?: any;
    importPreviewLoading?: boolean;
    onRunImportPreview?: () => void | Promise<void>;
    signalOverrides?: Record<string, string>;
    onChangeSignalOverride?: (role: string, nextValue: string) => void;
    operatorApproved?: boolean;
    onSetOperatorApproved?: (nextApproved: boolean) => void;
    importBacktestResult?: any;
    importBacktestLoading?: boolean;
    onRunImportBacktest?: () => void | Promise<void>;
    backtestResult: any;
    backtestLoading: boolean;
    onRunBacktest: () => void | Promise<void>;
    promotionLoading: boolean;
    importProfileLoading?: boolean;
    activationLoading: boolean;
    createdProfile: PineProfileRecord | null;
    profileRegistry: PineProfileRecord[];
    profileRegistryLoading: boolean;
    focusedProfileId?: string | null;
    onCreateProfile: () => void | Promise<void>;
    onSaveImportedProfile?: () => void | Promise<void>;
    onActivateProfile: (profile?: PineProfileRecord | null) => void | Promise<void>;
    importTranslationProvider?: string | null;
    chartContent: ReactNode;
};

const IMPORT_SIGNAL_ROLES = ['long_entry', 'short_entry', 'long_exit', 'short_exit'] as const;

const PROFILE_FILTERS = ['ALL', 'DRAFT', 'READY', 'ACTIVE'] as const;
type ProfileFilter = typeof PROFILE_FILTERS[number];
type ProfileSort = 'ACTIVE_FIRST' | 'HIGHEST_SCORE' | 'RECENT_ACTIVATION';
const PROFILE_SORT_OPTIONS: Array<{ value: ProfileSort; label: string }> = [
    { value: 'ACTIVE_FIRST', label: 'Active First' },
    { value: 'HIGHEST_SCORE', label: 'Highest Score' },
    { value: 'RECENT_ACTIVATION', label: 'Recent Activation' },
];

const secondaryToggleClass =
    'section-surface-muted industrial-corner border border-white/10 px-4 py-3 text-[10px] font-black uppercase tracking-[0.22em] text-slate-300 transition-all hover:border-white/16 hover:text-white';

const formFieldClass =
    'section-surface-muted industrial-corner w-full border border-white/10 px-4 py-3 text-[11px] font-black tracking-widest text-slate-200 outline-none transition hover:border-white/16 focus:border-primary/50';

const actionButtonClass =
    'section-surface-muted industrial-corner flex items-center justify-center gap-3 border border-white/10 py-4 text-[11px] font-black uppercase tracking-[0.3em] text-slate-100 transition-all hover:border-white/16 hover:text-white';

const diagnosticsPanelClass =
    'section-surface-muted industrial-corner border border-white/8 p-6';

const diagnosticsInsetClass =
    'rounded-md border border-white/8 bg-slate-950/45 px-3 py-3 text-sm text-slate-200';

const GATE_LABELS: Record<string, string> = {
    readiness: 'Preflight readiness is not ready',
    compatibility_score: 'Compatibility score below ready threshold',
    combined_score: 'Combined score below ready threshold',
    trade_count: 'Trade count below ready minimum',
    total_return: 'Total return must stay positive',
    max_drawdown: 'Drawdown is above the safety ceiling',
};

function formatGateLabel(gate: string) {
    return GATE_LABELS[gate] ?? gate.replaceAll('_', ' ');
}

function formatAuditStamp(value?: string | null) {
    if (!value) {
        return 'Pending';
    }
    return value.replace('T', ' ').slice(0, 16);
}

function formatImportReviewStatus(value?: string | null) {
    return String(value || 'PENDING').replaceAll('_', ' ');
}

function formatGateMetricValue(gate: string, value?: string | number) {
    if (value == null) {
        return '--';
    }
    if (gate === 'readiness') {
        return String(value).toUpperCase();
    }
    const numericValue = Number(value);
    if (Number.isNaN(numericValue)) {
        return String(value);
    }
    if (gate === 'trade_count') {
        return String(Math.round(numericValue));
    }
    return numericValue.toFixed(2);
}

function formatGateRequirement(gate: string, value?: string | number) {
    if (gate === 'readiness') {
        return `Required: ${formatGateMetricValue(gate, value ?? 'READY')}`;
    }
    const comparator = gate === 'max_drawdown'
        ? '<='
        : gate === 'total_return'
            ? '>'
            : '>=';
    return `Required: ${comparator} ${formatGateMetricValue(gate, value)}`;
}

function formatSignalRole(role: string) {
    return role.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatProfileSourceType(sourceType?: string | null) {
    return String(sourceType || 'PINE').toUpperCase() === 'PINE_LOGIC_IMPORT' ? 'Logic Import' : 'Native Runtime';
}

function formatImportTranslatorProvider(provider?: string | null) {
    return String(provider || 'LOCAL').toUpperCase() === 'OLLAMA'
        ? 'Ollama-assisted translation'
        : 'Local deterministic draft';
}

function formatConfidencePercent(value?: number | string | null) {
    const numericValue = Number(value);
    if (Number.isNaN(numericValue) || numericValue <= 0) {
        return '0.0%';
    }
    return `${(numericValue * 100).toFixed(1)}%`;
}

export function PineLabPanel({
    pineForm,
    onChangeForm,
    preflightResult,
    preflightLoading,
    onRunPreflight,
    importPreviewResult,
    importPreviewLoading,
    onRunImportPreview,
    signalOverrides = {},
    onChangeSignalOverride,
    operatorApproved = false,
    onSetOperatorApproved,
    importBacktestResult,
    importBacktestLoading,
    onRunImportBacktest,
    backtestResult,
    backtestLoading,
    onRunBacktest,
    promotionLoading,
    importProfileLoading = false,
    activationLoading,
    createdProfile,
    profileRegistry,
    profileRegistryLoading,
    focusedProfileId,
    onCreateProfile,
    onSaveImportedProfile,
    onActivateProfile,
    importTranslationProvider,
    chartContent,
}: PineLabPanelProps) {
    const [runtimeMode, setRuntimeMode] = useState<'NATIVE_RUNTIME' | 'LOGIC_IMPORT'>('NATIVE_RUNTIME');
    const [profileFilter, setProfileFilter] = useState<ProfileFilter>('ALL');
    const [profileSort, setProfileSort] = useState<ProfileSort>('ACTIVE_FIRST');
    const [detailsProfile, setDetailsProfile] = useState<PineProfileRecord | null>(null);
    const preflightIssues = Array.isArray(preflightResult?.unsupported_features) ? preflightResult.unsupported_features : [];
    const preflightMessages = Array.isArray(preflightResult?.messages) ? preflightResult.messages : [];
    const supportedRuntimeFeatures = useMemo(() => deriveSupportedRuntimeFeatures(preflightResult), [preflightResult]);
    const canRunBacktest = !backtestLoading && (!preflightResult || preflightResult.readiness === 'READY');
    const importWarnings = Array.isArray(importPreviewResult?.rule_spec?.warnings) ? importPreviewResult.rule_spec.warnings : [];
    const importIgnoredSections = Array.isArray(importPreviewResult?.ignored_sections) ? importPreviewResult.ignored_sections : [];
    const importUnresolvedReferences = Array.isArray(importPreviewResult?.reduced_source_pack?.unresolved_references)
        ? importPreviewResult.reduced_source_pack.unresolved_references
        : [];
    const importTraceability = Array.isArray(importPreviewResult?.rule_spec?.traceability) ? importPreviewResult.rule_spec.traceability : [];
    const importSummary = importPreviewResult?.rule_spec?.human_summary ?? {};
    const importSignals = importPreviewResult?.rule_spec?.signals ?? {};
    const importConfidence = importPreviewResult?.rule_spec?.confidence ?? {};
    const importExecutionPlan = importPreviewResult?.rule_spec?.execution_plan ?? null;
    const importMissingSignals = useMemo(
        () => IMPORT_SIGNAL_ROLES.filter((role) => String(importSignals?.[role]?.status || 'missing') !== 'mapped'),
        [importSignals]
    );
    const importDefinitionOptions = useMemo<string[]>(() => {
        const definitions: any[] = Array.isArray(importPreviewResult?.reduced_source_pack?.definitions)
            ? importPreviewResult.reduced_source_pack.definitions
            : [];
        return definitions
            .map((definition: any) => String(definition?.name || '').trim())
            .filter((name: string) => Boolean(name))
            .filter((name: string, index: number, all: string[]) => all.indexOf(name) === index)
            .sort((left: string, right: string) => left.localeCompare(right));
    }, [importPreviewResult]);
    const importComparison = importBacktestResult?.comparison ?? {};
    const importCoreMetrics = importComparison?.horus_core?.metrics ?? null;
    const importTranslation = importPreviewResult?.translation ?? null;
    const canRunImportBacktest = Boolean(importExecutionPlan) && Boolean(operatorApproved) && !importBacktestLoading;
    const canSaveImportedProfile = Boolean(importBacktestResult) && Boolean(operatorApproved) && !importProfileLoading;
    const importBacktestGateReason = importBacktestLoading
        ? 'Import backtest is already running.'
        : !importExecutionPlan
            ? 'No executable Horus plan was generated from this draft yet.'
            : !operatorApproved
                ? 'Approve the imported rule spec to unlock import backtest.'
                : 'Import backtest is ready to run.';
    const failedGates = createdProfile?.promotion_summary?.failed_gates ?? [];
    const failedGateBreakdown = useMemo(() => {
        const thresholds = createdProfile?.promotion_summary?.thresholds ?? {};
        const actuals = createdProfile?.promotion_summary?.actuals ?? {};

        return failedGates.map((gate) => ({
            gate,
            label: formatGateLabel(gate),
            actual: formatGateMetricValue(gate, actuals[gate]),
            required: formatGateRequirement(gate, thresholds[gate]),
        }));
    }, [createdProfile, failedGates]);
    const filteredProfiles = useMemo(() => {
        if (profileFilter === 'ALL') {
            return profileRegistry;
        }
        return profileRegistry.filter((profile) => profile.profile_state === profileFilter);
    }, [profileFilter, profileRegistry]);
    const sortedProfiles = useMemo(() => {
        const profiles = [...filteredProfiles];
        const stateRank = (state?: string) => {
            switch (String(state || '').toUpperCase()) {
                case 'ACTIVE':
                    return 0;
                case 'READY':
                    return 1;
                case 'DRAFT':
                    return 2;
                default:
                    return 3;
            }
        };
        const auditRank = (value?: string | null) => {
            if (!value) {
                return 0;
            }
            const ts = Date.parse(value);
            return Number.isNaN(ts) ? 0 : ts;
        };

        profiles.sort((left, right) => {
            if (profileSort === 'HIGHEST_SCORE') {
                const scoreDiff = Number(right.ranking_summary?.combined_score ?? 0) - Number(left.ranking_summary?.combined_score ?? 0);
                if (scoreDiff !== 0) {
                    return scoreDiff;
                }
                const returnDiff = Number(right.backtest_summary?.total_return ?? 0) - Number(left.backtest_summary?.total_return ?? 0);
                if (returnDiff !== 0) {
                    return returnDiff;
                }
            }

            if (profileSort === 'RECENT_ACTIVATION') {
                const activationDiff = auditRank(right.activated_at) - auditRank(left.activated_at);
                if (activationDiff !== 0) {
                    return activationDiff;
                }
                const readyDiff = auditRank(right.ready_at) - auditRank(left.ready_at);
                if (readyDiff !== 0) {
                    return readyDiff;
                }
            }

            const stateDiff = stateRank(left.profile_state) - stateRank(right.profile_state);
            if (stateDiff !== 0) {
                return stateDiff;
            }
            return String(left.profile_name || '').localeCompare(String(right.profile_name || ''));
        });

        return profiles;
    }, [filteredProfiles, profileSort]);

    return (
        <div className="grid grid-cols-1 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500 lg:grid-cols-4">
            <div className="section-surface-muted industrial-corner group relative h-fit overflow-hidden border border-white/10 p-8 lg:col-span-1">
                <div className="absolute right-0 top-0 p-2 opacity-20">
                    <FileCode2 size={40} className="text-primary transition-transform duration-700 group-hover:rotate-6" />
                </div>

                <div className="mb-10 flex items-center gap-4">
                    <div className="h-1 w-1 bg-primary" />
                    <h2 className="font-heading text-xs font-black uppercase tracking-[0.3em] text-white">Pine_Import_Runtime</h2>
                </div>

                <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-3">
                        <button
                            type="button"
                            aria-pressed={runtimeMode === 'NATIVE_RUNTIME'}
                            onClick={() => setRuntimeMode('NATIVE_RUNTIME')}
                            className={clsx(
                                'industrial-corner px-4 py-3 text-[10px] font-black uppercase tracking-[0.22em] transition-all',
                                runtimeMode === 'NATIVE_RUNTIME'
                                    ? 'bg-primary text-primary-foreground'
                                    : secondaryToggleClass
                            )}
                        >
                            Native Runtime
                        </button>
                        <button
                            type="button"
                            aria-pressed={runtimeMode === 'LOGIC_IMPORT'}
                            onClick={() => setRuntimeMode('LOGIC_IMPORT')}
                            className={clsx(
                                'industrial-corner px-4 py-3 text-[10px] font-black uppercase tracking-[0.22em] transition-all',
                                runtimeMode === 'LOGIC_IMPORT'
                                    ? 'bg-primary text-primary-foreground'
                                    : secondaryToggleClass
                            )}
                        >
                            Logic Import
                        </button>
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="pine-script-source" className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                            Pine Script Source
                        </label>
                        <textarea
                            id="pine-script-source"
                            aria-label="Pine Script Source"
                            value={pineForm.scriptSource}
                            onChange={(event) => onChangeForm({ ...pineForm, scriptSource: event.target.value })}
                            rows={12}
                            className="industrial-corner w-full border border-white/10 bg-slate-950/60 px-4 py-3 text-xs text-slate-200 outline-none transition hover:border-white/16 focus:border-primary/50"
                            placeholder="// Paste Pine strategy or indicator source here"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label htmlFor="pine-market" className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                                Market
                            </label>
                            <select
                                id="pine-market"
                                value={pineForm.market}
                                onChange={(event) => onChangeForm({ ...pineForm, market: event.target.value })}
                                className={formFieldClass}
                            >
                                <option value="EGX30">EGX30</option>
                                <option value="EGX70">EGX70</option>
                                <option value="EGX100">EGX100</option>
                                <option value="ALL">ALL</option>
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="pine-timeframe" className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                                Timeframe
                            </label>
                            <select
                                id="pine-timeframe"
                                value={pineForm.timeframe}
                                onChange={(event) => onChangeForm({ ...pineForm, timeframe: event.target.value })}
                                className={formFieldClass}
                            >
                                <option value="1D">1D</option>
                                <option value="1W">1W</option>
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label htmlFor="pine-date-from" className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                                Date From
                            </label>
                            <input
                                id="pine-date-from"
                                type="date"
                                value={pineForm.dateFrom}
                                onChange={(event) => onChangeForm({ ...pineForm, dateFrom: event.target.value })}
                                className={formFieldClass}
                            />
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="pine-date-to" className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                                Date To
                            </label>
                            <input
                                id="pine-date-to"
                                type="date"
                                value={pineForm.dateTo}
                                onChange={(event) => onChangeForm({ ...pineForm, dateTo: event.target.value })}
                                className={formFieldClass}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                            <label htmlFor="pine-capital" className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                                Capital
                            </label>
                            <input
                                id="pine-capital"
                                type="number"
                                value={pineForm.capital}
                                onChange={(event) => onChangeForm({ ...pineForm, capital: Number(event.target.value) })}
                                className={formFieldClass}
                            />
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="pine-commission" className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                                Commission %
                            </label>
                            <input
                                id="pine-commission"
                                type="number"
                                step="0.01"
                                value={pineForm.commissionPct}
                                onChange={(event) => onChangeForm({ ...pineForm, commissionPct: Number(event.target.value) })}
                                className={formFieldClass}
                            />
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="pine-slippage" className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                                Slippage %
                            </label>
                            <input
                                id="pine-slippage"
                                type="number"
                                step="0.01"
                                value={pineForm.slippagePct}
                                onChange={(event) => onChangeForm({ ...pineForm, slippagePct: Number(event.target.value) })}
                                className={formFieldClass}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="pine-profile-name" className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                            Profile Name
                        </label>
                        <input
                            id="pine-profile-name"
                            type="text"
                            value={pineForm.profileName}
                            onChange={(event) => onChangeForm({ ...pineForm, profileName: event.target.value })}
                            className={formFieldClass}
                            placeholder="EGX Breakout Pine"
                        />
                    </div>

                    <div className="grid grid-cols-1 gap-3">
                                {runtimeMode === 'LOGIC_IMPORT' ? (
                            <>
                                <div className="rounded-md border border-cyan-500/20 bg-cyan-500/10 px-3 py-3 text-xs text-cyan-100">
                                    <div className="font-black uppercase tracking-[0.18em] text-cyan-300">Next Draft Engine: {formatImportTranslatorProvider(importTranslationProvider)}</div>
                                    <div className="mt-2 text-slate-300">
                                        Current translator setting comes from Settings &gt; Delivery &amp; AI. Extracted drafts still pass through Horus validation before review.
                                    </div>
                                </div>
                                <button
                                    type="button"
                                    onClick={onRunImportPreview}
                                    disabled={importPreviewLoading}
                                    className={clsx(
                                        actionButtonClass,
                                        importPreviewLoading && 'border-white/6 text-slate-500 hover:border-white/6 hover:text-slate-500'
                                    )}
                                >
                                    {importPreviewLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                                    {importPreviewLoading ? 'Extracting Rule Spec' : importPreviewResult ? 'Re-Extract Rule Spec' : 'Extract Rule Spec'}
                                </button>
                                {importPreviewResult?.rule_spec && (
                                    <>
                                        <button
                                            type="button"
                                            onClick={onRunImportPreview}
                                            disabled={importPreviewLoading}
                                            className={clsx(
                                                actionButtonClass,
                                                importPreviewLoading && 'border-white/6 text-slate-500 hover:border-white/6 hover:text-slate-500'
                                            )}
                                        >
                                            {importPreviewLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                                            {importPreviewLoading ? 'Applying Review Edits' : 'Apply Review Edits'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => onSetOperatorApproved?.(!operatorApproved)}
                                            className={clsx(
                                                'industrial-corner flex items-center justify-center gap-3 py-4 text-[11px] font-black uppercase tracking-[0.3em] transition-all',
                                                operatorApproved
                                                    ? 'bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/20'
                                                    : 'bg-cyan-500/15 text-cyan-200 hover:bg-cyan-500/20'
                                            )}
                                        >
                                            <ShieldCheck className="h-4 w-4" />
                                            {operatorApproved ? 'Rule Spec Approved' : 'Approve Rule Spec'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={onRunImportBacktest}
                                            disabled={!canRunImportBacktest}
                                            className={clsx(
                                                actionButtonClass,
                                                !canRunImportBacktest
                                                    ? 'border-white/6 text-slate-500 hover:border-white/6 hover:text-slate-500'
                                                    : 'border-primary/40 bg-primary text-primary-foreground hover:scale-[1.01] hover:border-primary/50'
                                            )}
                                        >
                                            {importBacktestLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Radar className="h-4 w-4" />}
                                            {importBacktestLoading ? 'Running Import Backtest' : 'Run Import Backtest'}
                                        </button>
                                        <div
                                            className={clsx(
                                                'rounded-md border px-3 py-3 text-xs',
                                                canRunImportBacktest
                                                    ? 'border-emerald-500/15 bg-emerald-500/5 text-emerald-100'
                                                    : 'border-amber-500/15 bg-amber-500/5 text-amber-100'
                                            )}
                                        >
                                            {importBacktestGateReason}
                                        </div>
                                        <button
                                            type="button"
                                            onClick={onSaveImportedProfile}
                                            disabled={!canSaveImportedProfile}
                                            className={clsx(
                                                actionButtonClass,
                                                !canSaveImportedProfile
                                                    ? 'border-white/6 text-slate-500 hover:border-white/6 hover:text-slate-500'
                                                    : 'border-emerald-500/25 bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/20'
                                            )}
                                        >
                                            {importProfileLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
                                            {importProfileLoading ? 'Saving Imported Profile' : 'Save Imported Profile'}
                                        </button>
                                    </>
                                )}
                                <div className="rounded-md border border-cyan-500/20 bg-cyan-500/5 px-3 py-3 text-xs text-cyan-100">
                                    Logic Import is review-gated. Extract the rule spec, approve it explicitly, then run import backtest on the structured Horus plan.
                                </div>
                            </>
                        ) : (
                            <>
                                <button
                                    type="button"
                                    onClick={onRunPreflight}
                                    disabled={preflightLoading}
                                    className={clsx(
                                        actionButtonClass,
                                        preflightLoading && 'border-white/6 text-slate-500 hover:border-white/6 hover:text-slate-500'
                                    )}
                                >
                                    {preflightLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                                    {preflightLoading ? 'Running Preflight' : 'Run Preflight'}
                                </button>

                                <button
                                    type="button"
                                    onClick={onRunBacktest}
                                    disabled={!canRunBacktest}
                                    className={clsx(
                                        actionButtonClass,
                                        !canRunBacktest
                                            ? 'border-white/6 text-slate-500 hover:border-white/6 hover:text-slate-500'
                                            : 'border-primary/40 bg-primary text-primary-foreground hover:scale-[1.01] hover:border-primary/50'
                                    )}
                                >
                                    {backtestLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Radar className="h-4 w-4" />}
                                    {backtestLoading ? 'Running Pine Backtest' : 'Run Pine Backtest'}
                                </button>
                                {preflightResult?.readiness === 'BLOCKED' && (
                                    <p className="text-[11px] text-amber-300">
                                        Fix the blocked preflight items below before running a Pine backtest.
                                    </p>
                                )}

                                <button
                                    type="button"
                                    onClick={onCreateProfile}
                                    disabled={promotionLoading}
                                    className={clsx(
                                        actionButtonClass,
                                        promotionLoading
                                            ? 'border-white/6 text-slate-500 hover:border-white/6 hover:text-slate-500'
                                            : 'border-emerald-500/25 bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/20'
                                    )}
                                >
                                    {promotionLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
                                    {promotionLoading ? 'Creating Scanner Profile' : 'Create Scanner Profile'}
                                </button>

                                <button
                                    type="button"
                                    onClick={() => onActivateProfile(createdProfile)}
                                    disabled={activationLoading || !createdProfile || createdProfile.profile_state === 'DRAFT' || createdProfile.profile_state === 'ACTIVE'}
                                    className={clsx(
                                        actionButtonClass,
                                        activationLoading || !createdProfile || createdProfile.profile_state === 'DRAFT' || createdProfile.profile_state === 'ACTIVE'
                                            ? 'border-white/6 text-slate-500 hover:border-white/6 hover:text-slate-500'
                                            : 'border-cyan-500/25 bg-cyan-500/15 text-cyan-300 hover:bg-cyan-500/20'
                                    )}
                                >
                                    {activationLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
                                    {createdProfile?.profile_state === 'ACTIVE'
                                        ? 'Profile Active'
                                        : activationLoading
                                            ? 'Activating Profile'
                                            : 'Activate Scanner Profile'}
                                </button>
                            </>
                        )}
                    </div>
                </div>
            </div>

            <div className="lg:col-span-3 space-y-8">
                <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                    <div className={diagnosticsPanelClass}>
                        <div className="mb-2 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
                            <Activity className="h-3.5 w-3.5 text-primary" />
                            {runtimeMode === 'LOGIC_IMPORT' ? 'Import Review' : 'Preflight'}
                        </div>
                        <p className="text-sm font-black text-white">
                            {runtimeMode === 'LOGIC_IMPORT'
                                ? importBacktestResult
                                    ? 'Execution Stage: IMPORT BACKTEST'
                                    : `Preview Stage: ${formatImportReviewStatus(importPreviewResult?.review_status)}`
                                : `Readiness: ${preflightResult?.readiness ?? 'PENDING'}`}
                        </p>
                        <p className="mt-2 text-xs text-slate-400">
                            {runtimeMode === 'LOGIC_IMPORT'
                                ? importBacktestResult
                                    ? `Approval: ${operatorApproved ? 'APPROVED' : 'PENDING'}`
                                    : `Translation Mode: ${importPreviewResult?.translation?.mode ?? 'PENDING'}`
                                : `Compatibility Score: ${preflightResult?.compatibility_score ?? 0}`}
                        </p>
                    </div>

                    <div className={diagnosticsPanelClass}>
                        <div className="mb-2 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
                            <Radar className="h-3.5 w-3.5 text-primary" />
                            {runtimeMode === 'LOGIC_IMPORT' ? 'Signal Coverage' : 'Pine Return'}
                        </div>
                        <p className={clsx(
                            'text-3xl font-black font-mono',
                            runtimeMode === 'LOGIC_IMPORT'
                                ? importBacktestResult
                                    ? (importBacktestResult?.metrics?.total_return ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                                    : 'text-cyan-300'
                                : (backtestResult?.metrics?.total_return ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                        )}>
                            {runtimeMode === 'LOGIC_IMPORT'
                                ? importBacktestResult?.metrics?.total_return != null
                                    ? `${importBacktestResult.metrics.total_return > 0 ? '+' : ''}${Number(importBacktestResult.metrics.total_return).toFixed(2)}%`
                                    : String((importPreviewResult?.reduced_source_pack?.candidate_signals ?? []).length || '--')
                                : backtestResult?.metrics?.total_return != null
                                    ? `${backtestResult.metrics.total_return > 0 ? '+' : ''}${Number(backtestResult.metrics.total_return).toFixed(2)}%`
                                    : '--'}
                        </p>
                        <p className="mt-2 text-xs text-slate-400">
                            {runtimeMode === 'LOGIC_IMPORT'
                                ? importBacktestResult
                                    ? `Trades: ${importBacktestResult?.metrics?.trade_count ?? 0}`
                                    : `Ignored Sections: ${(importPreviewResult?.ignored_sections ?? []).length ?? 0}`
                                : `Trades: ${backtestResult?.metrics?.trade_count ?? 0}`}
                        </p>
                    </div>

                    <div className={diagnosticsPanelClass}>
                        <div className="mb-2 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
                            <Rocket className="h-3.5 w-3.5 text-primary" />
                            Scanner Profile
                        </div>
                        <p className="text-sm font-black text-white">
                            Profile State: {createdProfile?.profile_state ?? 'NOT_CREATED'}
                        </p>
                        <p className="mt-2 text-xs text-slate-400">
                            {createdProfile?.profile_name
                                ?? (runtimeMode === 'LOGIC_IMPORT'
                                    ? 'Save an imported rule profile after a successful import backtest.'
                                    : 'Create a Pine profile after a successful backtest.')}
                        </p>
                        {createdProfile && (
                            <div className="mt-3 space-y-1 text-[11px] text-slate-400">
                                <div>Source Type: {formatProfileSourceType(createdProfile.source_type)}</div>
                                <div>Ready At: {formatAuditStamp(createdProfile.ready_at)}</div>
                                <div>Last Activated: {formatAuditStamp(createdProfile.activated_at)}</div>
                                <div>Activations: {Number(createdProfile.activation_count ?? 0)}</div>
                            </div>
                        )}
                        {createdProfile && String(createdProfile.source_type || '').toUpperCase() === 'PINE_LOGIC_IMPORT' && (
                            <div className="mt-3 rounded-md border border-cyan-500/20 bg-cyan-500/10 px-3 py-3 text-xs text-cyan-100">
                                <div className="font-black uppercase tracking-[0.18em] text-cyan-300">Import-Only Profile</div>
                                <div className="mt-2">Saved for research reuse and Backtester replay. Scanner activation stays limited to native Pine runtime profiles.</div>
                            </div>
                        )}
                        {createdProfile?.profile_state === 'DRAFT' && (
                            <div className="mt-3 rounded-md border border-amber-500/20 bg-amber-500/10 px-3 py-3 text-xs text-amber-100">
                                <div className="font-black uppercase tracking-[0.18em] text-amber-300">Draft Hold</div>
                                <div className="mt-2">Activation is blocked until the failed promotion gates are fixed.</div>
                            </div>
                        )}
                        {failedGates.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-2">
                                {failedGates.map((gate) => (
                                    <span
                                        key={gate}
                                        className="rounded-md border border-amber-500/20 bg-amber-500/10 px-2 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-amber-300"
                                    >
                                        {formatGateLabel(gate)}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="section-surface industrial-corner scan-line relative flex min-h-[420px] flex-col overflow-hidden border border-white/10 bg-[linear-gradient(180deg,rgba(11,17,28,0.96),rgba(2,6,23,0.9))] p-10">
                    <div className="absolute top-0 left-0 flex h-12 w-full items-center justify-between border-b border-white/8 bg-white/[0.03] px-6">
                        <h3 className="font-heading font-black text-[9px] uppercase tracking-[0.4em] text-slate-400 flex items-center gap-4">
                            <div className="w-2 h-2 bg-emerald-500 industrial-corner" />
                            Pine_Runtime_Diagnostics
                        </h3>
                    </div>

                    <div className="mt-10 space-y-6">
                        {runtimeMode === 'LOGIC_IMPORT' && importPreviewResult && (
                            <div className="industrial-corner border border-white/8 bg-slate-950/55 p-5">
                                <p className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Import Preview</p>
                                <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
                                    <div className={diagnosticsInsetClass}>
                                        <div className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-300">Review Status</div>
                                        <div className="mt-2">{importPreviewResult.review_status ?? 'PENDING'}</div>
                                        <div className="mt-2 text-xs text-slate-400">
                                            Provider: {importPreviewResult.translation?.provider ?? 'LOCAL'} / {importPreviewResult.translation?.mode ?? 'PENDING'}
                                        </div>
                                        <div className="mt-2 text-xs text-slate-400">
                                            Approval: {operatorApproved ? 'APPROVED' : 'PENDING'}
                                        </div>
                                    </div>
                                    <div className={diagnosticsInsetClass}>
                                        <div className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-300">Long Entry Summary</div>
                                        <div className="mt-2">{importSummary.long_entry ?? 'No long entry mapped yet.'}</div>
                                        <div className="mt-2 text-xs text-slate-400">
                                            Confidence: {formatConfidencePercent(importConfidence?.per_signal?.long_entry)}
                                        </div>
                                    </div>
                                </div>
                                <div className={diagnosticsInsetClass}>
                                    <div className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-300">Risk Summary</div>
                                    <div className="mt-2 grid grid-cols-1 gap-2 text-xs text-slate-300 md:grid-cols-3">
                                        <div className="rounded-md border border-white/8 bg-slate-950/50 px-2 py-2">
                                            Missing Mappings: {importMissingSignals.length}
                                        </div>
                                        <div className="rounded-md border border-white/8 bg-slate-950/50 px-2 py-2">
                                            Warnings: {importWarnings.length}
                                        </div>
                                        <div className="rounded-md border border-white/8 bg-slate-950/50 px-2 py-2">
                                            Ignored Sections: {importIgnoredSections.length}
                                        </div>
                                        <div className="rounded-md border border-white/8 bg-slate-950/50 px-2 py-2">
                                            Unresolved References: {importUnresolvedReferences.length}
                                        </div>
                                    </div>
                                    {importMissingSignals.length > 0 && (
                                        <div className="mt-2 text-xs text-slate-400">
                                            Unmapped roles: {importMissingSignals.map((role) => formatSignalRole(role)).join(', ')}
                                        </div>
                                    )}
                                    {importUnresolvedReferences.length > 0 && (
                                        <div className="mt-2 space-y-1 text-xs text-amber-200">
                                            {importUnresolvedReferences.map((item: any, index: number) => (
                                                <div key={`${item?.name || 'unresolved'}-${index}`}>
                                                    {String(item?.name || 'Unknown signal')} -&gt; {Array.isArray(item?.references) ? item.references.join(', ') : '--'}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                                <div className={diagnosticsInsetClass}>
                                    <div className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-300">Overall Confidence</div>
                                    <div className="mt-2 text-lg font-black text-white">
                                        {formatConfidencePercent(importConfidence?.overall)}
                                    </div>
                                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-400 md:grid-cols-4">
                                        {IMPORT_SIGNAL_ROLES.map((role) => (
                                            <div key={`${role}-confidence`} className="rounded-md border border-white/8 bg-slate-950/50 px-2 py-2">
                                                <div className="font-black uppercase tracking-[0.14em] text-slate-500">
                                                    {formatSignalRole(role)}
                                                </div>
                                                <div className="mt-1 text-slate-200">
                                                    {formatConfidencePercent(importConfidence?.per_signal?.[role])}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                {importTranslation?.fallback_reason && (
                                    <div className="mt-4 rounded-md border border-amber-500/20 bg-amber-500/10 px-3 py-3 text-amber-100">
                                        <div className="font-black uppercase tracking-[0.18em] text-amber-300">AI Translator Fallback</div>
                                        <div className="mt-2 text-xs text-slate-200">
                                            Attempted: {String(importTranslation.attempted_provider || 'UNKNOWN').toUpperCase()}
                                        </div>
                                        <div className="mt-2 text-sm text-amber-100">
                                            {importTranslation.fallback_reason}
                                        </div>
                                    </div>
                                )}
                                <div className="mt-4 rounded-md border border-cyan-500/15 bg-cyan-500/5 px-3 py-3 text-cyan-100">
                                    <div className="font-black uppercase tracking-[0.18em] text-cyan-300">Review / Edit Signal Mapping</div>
                                    <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
                                        {IMPORT_SIGNAL_ROLES.map((role) => {
                                            const signal = importSignals?.[role] ?? {};
                                            const hasExplicitOverride = Object.prototype.hasOwnProperty.call(signalOverrides, role);
                                            const selectedValue = hasExplicitOverride
                                                ? String(signalOverrides[role] ?? '')
                                                : String(signal?.source_name ?? '');

                                            return (
                                                <div
                                                    key={role}
                                                    className="rounded-md border border-white/5 bg-black/20 px-3 py-3 text-sm text-slate-200"
                                                >
                                                    <label
                                                        htmlFor={`import-signal-${role}`}
                                                        className="text-[10px] font-black uppercase tracking-[0.18em] text-cyan-300"
                                                    >
                                                        {formatSignalRole(role)} Mapping
                                                    </label>
                                                    <select
                                                        id={`import-signal-${role}`}
                                                        aria-label={`${formatSignalRole(role)} Mapping`}
                                                        value={selectedValue}
                                                        onChange={(event) => onChangeSignalOverride?.(role, event.target.value)}
                                                        className="mt-3 industrial-corner w-full border border-white/5 bg-black/40 px-3 py-3 text-xs text-slate-200 outline-none transition focus:border-primary/50"
                                                    >
                                                        <option value="">Auto / Unmapped</option>
                                                        {importDefinitionOptions.map((name) => (
                                                            <option key={`${role}-${name}`} value={name}>
                                                                {name}
                                                            </option>
                                                        ))}
                                                    </select>
                                                    <div className="mt-3 text-xs text-slate-400">
                                                        Status: {String(signal?.status ?? 'missing').toUpperCase()}
                                                    </div>
                                                    <div className="mt-1 text-xs text-slate-400">
                                                        Current Source: {signal?.source_name ?? 'No mapped source'}
                                                    </div>
                                                    <div className="mt-2 text-xs text-slate-300">
                                                        {importSummary?.[role] ?? `No ${formatSignalRole(role).toLowerCase()} signal was mapped in this draft.`}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                                {importWarnings.length > 0 && (
                                    <div className="mt-4 rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-3 text-amber-100">
                                        <div className="font-black uppercase tracking-[0.18em] text-amber-300">Warnings</div>
                                        <ul className="mt-2 space-y-1 text-slate-200">
                                            {importWarnings.map((warning: string) => (
                                                <li key={warning}>{warning}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {importIgnoredSections.length > 0 && (
                                    <div className="mt-4 rounded-md border border-white/5 bg-black/20 px-3 py-3 text-slate-300">
                                        <div className="font-black uppercase tracking-[0.18em] text-slate-200">Ignored Pine Sections</div>
                                        <ul className="mt-2 space-y-1 text-xs">
                                            {importIgnoredSections.map((section: any) => (
                                                <li key={`${section.kind}-${section.line}-${section.source}`}>
                                                    {section.kind} @ line {section.line}: {section.source}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {importTraceability.length > 0 && (
                                    <div className="mt-4 rounded-md border border-cyan-500/20 bg-cyan-500/5 px-3 py-3 text-cyan-100">
                                        <div className="font-black uppercase tracking-[0.18em] text-cyan-300">Traceability</div>
                                        <ul className="mt-2 space-y-1 text-xs text-slate-200">
                                            {importTraceability.map((item: any) => (
                                                <li key={`${item.role}-${item.source_name}-${item.line}`}>
                                                    {item.role}: {item.source_name} @ line {item.line}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}

                        {runtimeMode === 'LOGIC_IMPORT' && importBacktestResult && (
                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                <div className="industrial-corner border border-white/5 bg-black/30 p-5">
                                    <p className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Import Backtest</p>
                                    <div className="mt-3 space-y-2 text-sm text-slate-300">
                                        <div>Total Return: {`${Number(importBacktestResult.metrics?.total_return ?? 0) > 0 ? '+' : ''}${Number(importBacktestResult.metrics?.total_return ?? 0).toFixed(2)}%`}</div>
                                        <div>Final Value: {Number(importBacktestResult.metrics?.final_value ?? 0).toLocaleString()}</div>
                                        <div>Trades: {Number(importBacktestResult.metrics?.trade_count ?? 0)}</div>
                                        <div>Win Rate: {Number(importBacktestResult.metrics?.win_rate ?? 0).toFixed(2)}%</div>
                                    </div>
                                </div>
                                <div className="industrial-corner border border-white/5 bg-black/30 p-5">
                                    <p className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Horus Core Comparison</p>
                                    {importCoreMetrics ? (
                                        <div className="mt-3 space-y-2 text-sm text-slate-300">
                                            <div>Horus Return: {`${Number(importCoreMetrics.total_return ?? 0) > 0 ? '+' : ''}${Number(importCoreMetrics.total_return ?? 0).toFixed(2)}%`}</div>
                                            <div>Horus Trades: {Number(importCoreMetrics.trade_count ?? 0)}</div>
                                            <div>Total Return Winner: {importComparison?.winner_by_metric?.total_return ?? 'TIE'}</div>
                                            <div>Trade Count Winner: {importComparison?.winner_by_metric?.trade_count ?? 'TIE'}</div>
                                        </div>
                                    ) : (
                                        <div className="mt-3 text-sm text-slate-500">Horus core comparison is unavailable for this run.</div>
                                    )}
                                </div>
                            </div>
                        )}

                        {runtimeMode === 'NATIVE_RUNTIME' && preflightResult && (
                            <div className="industrial-corner border border-white/5 bg-black/30 p-5">
                                <p className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Preflight Report</p>
                                <div className="mt-3 flex flex-wrap gap-6 text-xs text-slate-300">
                                    <span>Script Type: {preflightResult.script_type}</span>
                                    <span>Readiness: {preflightResult.readiness}</span>
                                    <span>Compatibility Score: {preflightResult.compatibility_score}</span>
                                </div>
                                {(supportedRuntimeFeatures.length > 0 || preflightIssues.length > 0 || preflightMessages.length > 0) && (
                                    <div className="mt-4 space-y-3 text-xs">
                                        {supportedRuntimeFeatures.length > 0 && (
                                            <div className="rounded-md border border-emerald-500/20 bg-emerald-500/5 px-3 py-3 text-emerald-100">
                                                <div className="font-black uppercase tracking-[0.18em] text-emerald-300">Supported Runtime Features</div>
                                                <ul className="mt-2 space-y-1 text-slate-200">
                                                    {supportedRuntimeFeatures.map((feature) => (
                                                        <li key={feature}>{feature}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                        {preflightIssues.length > 0 && (
                                            <div className="rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-3 text-amber-100">
                                                <div className="font-black uppercase tracking-[0.18em] text-amber-300">Runtime Limits</div>
                                                <ul className="mt-2 space-y-1 text-slate-200">
                                                    {preflightIssues.map((issue: string) => (
                                                        <li key={issue}>{issue}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                        {preflightMessages.length > 0 && (
                                            <div className="rounded-md border border-white/5 bg-black/20 px-3 py-3 text-slate-300">
                                                {preflightMessages.map((message: string) => (
                                                    <div key={message}>{message}</div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {createdProfile?.profile_state === 'DRAFT' && failedGates.length > 0 && (
                            <div className="industrial-corner border border-amber-500/20 bg-amber-500/5 p-5">
                                <p className="text-[10px] font-black uppercase tracking-[0.3em] text-amber-300">Draft Gate Reasons</p>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {failedGates.map((gate) => (
                                        <span
                                            key={gate}
                                            className="rounded-md border border-amber-500/20 bg-black/20 px-2 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-amber-200"
                                        >
                                            {formatGateLabel(gate)}
                                        </span>
                                    ))}
                                </div>
                                <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
                                    {failedGateBreakdown.map((gate) => (
                                        <div
                                            key={`${gate.gate}-breakdown`}
                                            className="rounded-md border border-amber-500/15 bg-black/30 px-3 py-3 text-xs text-amber-100"
                                        >
                                            <div className="font-black uppercase tracking-[0.18em] text-amber-300">
                                                {gate.label}
                                            </div>
                                            <div className="mt-2 text-slate-200">Actual: {gate.actual}</div>
                                            <div className="mt-1 text-slate-400">{gate.required}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {runtimeMode === 'NATIVE_RUNTIME' && backtestResult ? (
                            <>
                                <div className="h-[280px] industrial-corner border border-white/5 bg-black/20 p-4">
                                    {chartContent}
                                </div>
                                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                    <div className="industrial-corner border border-white/5 bg-black/30 p-5">
                                        <p className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Backtest Metrics</p>
                                        <div className="mt-3 space-y-2 text-sm text-slate-300">
                                            <div>Final Value: {Number(backtestResult.metrics?.final_value ?? 0).toLocaleString()}</div>
                                            <div>Win Rate: {Number(backtestResult.metrics?.win_rate ?? 0).toFixed(2)}%</div>
                                            <div>Drawdown: {Number(backtestResult.metrics?.max_drawdown ?? 0).toFixed(2)}%</div>
                                        </div>
                                    </div>
                                    <div className="industrial-corner border border-white/5 bg-black/30 p-5">
                                        <p className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Alignment + Ranking</p>
                                        <div className="mt-3 space-y-2 text-sm text-slate-300">
                                            <div>Alignment Score: {Number(backtestResult.alignment?.alignment_score ?? 0).toFixed(2)}</div>
                                            <div>Performance Score: {Number(backtestResult.rankings?.performance_score ?? 0).toFixed(2)}</div>
                                            <div>Combined Score: {Number(backtestResult.rankings?.combined_score ?? 0).toFixed(2)}</div>
                                        </div>
                                    </div>
                                </div>
                            </>
                        ) : runtimeMode === 'LOGIC_IMPORT' && !importPreviewResult ? (
                            <div className="flex min-h-[260px] items-center justify-center text-slate-600">
                                Logic import review will appear here after you extract a rule spec.
                            </div>
                        ) : runtimeMode === 'LOGIC_IMPORT' && !importBacktestResult ? (
                            <div className="flex min-h-[260px] items-center justify-center text-slate-600">
                                Approve the extracted rule spec to unlock import backtest and Horus core comparison.
                            </div>
                        ) : (
                            <div className="flex min-h-[260px] items-center justify-center text-slate-600">
                                Pine diagnostics will appear here after preflight or backtest.
                            </div>
                        )}
                    </div>
                </div>

                <div className="section-surface industrial-corner border border-white/10 p-6">
                    <div className="flex flex-col gap-4 border-b border-white/8 pb-5 md:flex-row md:items-center md:justify-between">
                        <div>
                            <h3 className="font-heading text-xs font-black uppercase tracking-[0.3em] text-white">Profile Registry</h3>
                            <p className="mt-2 text-xs text-slate-400">
                                Review every Pine scanner profile, filter by readiness, and activate a READY strategy without leaving Pine Lab.
                            </p>
                        </div>

                        <div className="flex flex-wrap gap-2">
                            {PROFILE_FILTERS.map((filter) => (
                                <button
                                    key={filter}
                                    type="button"
                                    onClick={() => setProfileFilter(filter)}
                                    className={clsx(
                                        'section-surface-muted rounded-md border px-3 py-2 text-[10px] font-black uppercase tracking-[0.25em] transition-all',
                                        profileFilter === filter
                                            ? 'border-primary/40 bg-primary/15 text-primary'
                                            : 'border-white/10 text-slate-300 hover:border-white/16 hover:text-white'
                                    )}
                                >
                                    {filter === 'ALL' ? 'All' : filter.charAt(0) + filter.slice(1).toLowerCase()}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="mt-4 flex flex-col gap-3 border-b border-white/8 pb-5 md:flex-row md:items-center md:justify-between">
                        <p className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Profile Sort</p>
                        <div className="flex flex-wrap gap-2">
                            {PROFILE_SORT_OPTIONS.map((option) => (
                                <button
                                    key={option.value}
                                    type="button"
                                    onClick={() => setProfileSort(option.value)}
                                    className={clsx(
                                        'section-surface-muted rounded-md border px-3 py-2 text-[10px] font-black uppercase tracking-[0.25em] transition-all',
                                        profileSort === option.value
                                            ? 'border-primary/40 bg-primary/15 text-primary'
                                            : 'border-white/10 text-slate-300 hover:border-white/16 hover:text-white'
                                    )}
                                >
                                    {option.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {profileRegistryLoading ? (
                        <div className="py-10 text-center text-sm text-slate-500">Loading Pine profile registry...</div>
                    ) : filteredProfiles.length === 0 ? (
                        <div className="py-10 text-center text-sm text-slate-500">
                            No Pine scanner profiles match this filter yet.
                        </div>
                    ) : (
                        <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
                            {sortedProfiles.map((profile) => {
                                const profileState = String(profile.profile_state || 'DRAFT').toUpperCase();
                                const profileSourceType = String(profile.source_type || 'PINE').toUpperCase();
                                const isImportOnlyProfile = profileSourceType === 'PINE_LOGIC_IMPORT';
                                const isFocused = focusedProfileId != null && String(profile.profile_id) === focusedProfileId;
                                const registryFailedGates = profile.promotion_summary?.failed_gates ?? [];
                                const totalReturn = Number(profile.backtest_summary?.total_return ?? 0);
                                const combinedScore = Number(profile.ranking_summary?.combined_score ?? 0);
                                const activationCount = Number(profile.activation_count ?? 0);
                                const lastActivationEvent = profile.activation_history?.[0];

                                return (
                                    <div
                                        key={profile.profile_id}
                                        className={clsx(
                                            'section-surface-muted industrial-corner border p-5 transition-all',
                                            isFocused
                                                ? 'border-cyan-400/40 bg-cyan-500/5 shadow-[0_0_0_1px_rgba(34,211,238,0.12)]'
                                                : 'border-white/8'
                                        )}
                                    >
                                        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                                            <div>
                                                <p className="text-sm font-black text-white">{profile.profile_name}</p>
                                                <p className="mt-2 text-[11px] font-black uppercase tracking-[0.2em] text-slate-500">
                                                    {profile.market ?? 'EGX30'} / {profile.timeframe ?? '1D'}
                                                </p>
                                                {isFocused && (
                                                    <p className="mt-3 inline-flex rounded-md border border-cyan-400/20 bg-cyan-500/10 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-cyan-300">
                                                        Focused from Scanner
                                                    </p>
                                                )}
                                            </div>

                                            <span
                                                className={clsx(
                                                    'rounded-md border px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em]',
                                                    profileState === 'ACTIVE' && 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300',
                                                    profileState === 'READY' && 'border-cyan-500/20 bg-cyan-500/10 text-cyan-300',
                                                    profileState === 'DRAFT' && 'border-amber-500/20 bg-amber-500/10 text-amber-300'
                                                )}
                                            >
                                                {profileState}
                                            </span>
                                        </div>

                                        <div className="mt-3 inline-flex rounded-md border border-cyan-500/15 bg-cyan-500/5 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-cyan-200">
                                            {formatProfileSourceType(profile.source_type)}
                                        </div>

                                        <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-300">
                                            <div className="section-surface-muted rounded-md border border-white/8 px-3 py-2">
                                                Return: {totalReturn > 0 ? '+' : ''}{totalReturn.toFixed(2)}%
                                            </div>
                                            <div className="section-surface-muted rounded-md border border-white/8 px-3 py-2">
                                                Combined Score: {combinedScore.toFixed(2)}
                                            </div>
                                            <div className="section-surface-muted rounded-md border border-white/8 px-3 py-2">
                                                Created: {formatAuditStamp(profile.created_at)}
                                            </div>
                                            <div className="section-surface-muted rounded-md border border-white/8 px-3 py-2">
                                                Ready: {formatAuditStamp(profile.ready_at)}
                                            </div>
                                            <div className="section-surface-muted rounded-md border border-white/8 px-3 py-2">
                                                Activated: {formatAuditStamp(profile.activated_at)}
                                            </div>
                                            <div className="section-surface-muted rounded-md border border-white/8 px-3 py-2">
                                                Activations: {activationCount}
                                            </div>
                                        </div>

                                        {registryFailedGates.length > 0 && (
                                            <div className="mt-4 flex flex-wrap gap-2">
                                                {registryFailedGates.map((gate) => (
                                                    <span
                                                        key={`${profile.profile_id}-${gate}`}
                                                        className="rounded-md border border-amber-500/20 bg-amber-500/5 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-amber-200"
                                                    >
                                                        {formatGateLabel(gate)}
                                                    </span>
                                                ))}
                                            </div>
                                        )}

                                        {lastActivationEvent && (
                                            <div className="mt-4 rounded-md border border-cyan-500/15 bg-cyan-500/5 px-3 py-3 text-xs text-cyan-100">
                                                <span className="font-black uppercase tracking-[0.18em] text-cyan-300">Last Activation</span>
                                                <div className="mt-2 text-slate-300">
                                                    {formatAuditStamp(lastActivationEvent.activated_at)}
                                                    {lastActivationEvent.previous_active_profile_name
                                                        ? ` replaced ${lastActivationEvent.previous_active_profile_name}`
                                                        : ' first activation'}
                                                </div>
                                            </div>
                                        )}

                                        <div className="mt-5 flex items-center justify-between gap-3">
                                            <p className="text-xs text-slate-500">
                                                {isImportOnlyProfile
                                                    ? 'Saved for reusable import backtests. Scanner activation is not available for Logic Import profiles.'
                                                    : profileState === 'ACTIVE'
                                                    ? 'Currently powering the default Pine scanner path.'
                                                    : profileState === 'READY'
                                                        ? 'Ready to promote into the live Pine scanner slot.'
                                                        : 'Needs stronger backtest quality before activation.'}
                                            </p>

                                            <div className="flex flex-wrap items-center justify-end gap-3">
                                                <button
                                                    type="button"
                                                    onClick={() => setDetailsProfile(profile)}
                                                    className="section-surface-muted industrial-corner border border-white/10 px-4 py-2 text-[10px] font-black uppercase tracking-[0.22em] text-slate-200 transition hover:border-white/16 hover:text-white"
                                                >
                                                    {`View Details ${profile.profile_name}`}
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        setProfileFilter('ACTIVE');
                                                        onActivateProfile(profile);
                                                    }}
                                                    disabled={activationLoading || profileState !== 'READY' || isImportOnlyProfile}
                                                    className={clsx(
                                                        'industrial-corner px-4 py-2 text-[10px] font-black uppercase tracking-[0.22em] transition-all',
                                                        activationLoading || profileState !== 'READY' || isImportOnlyProfile
                                                            ? 'border-white/8 bg-white/[0.04] text-slate-500'
                                                            : 'bg-cyan-500/15 text-cyan-300 hover:bg-cyan-500/20'
                                                    )}
                                                >
                                                    {isImportOnlyProfile
                                                        ? 'Import Only'
                                                        : profileState === 'ACTIVE'
                                                            ? 'Active'
                                                            : `Activate ${profile.profile_name}`}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>

            <PineProfileDetailsDialog
                isOpen={Boolean(detailsProfile)}
                profile={detailsProfile}
                onClose={() => setDetailsProfile(null)}
            />
        </div>
    );
}
