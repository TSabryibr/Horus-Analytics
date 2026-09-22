'use client';

import { useCallback, useEffect, useState } from 'react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';

import type { PineLabForm } from './usePineBacktest';

type UiMessage = {
    type: 'error' | 'success';
    text: string;
} | null;

export type PinePromotionSummary = {
    failed_gates?: string[];
    thresholds?: Record<string, number>;
    actuals?: Record<string, string | number>;
};

export type PineActivationEvent = {
    event_type: string;
    activated_at: string;
    previous_state?: string | null;
    previous_active_profile_id?: number | null;
    previous_active_profile_name?: string | null;
};

export type PineProfileRecord = {
    profile_id: number;
    profile_name: string;
    profile_state: 'DRAFT' | 'READY' | 'ACTIVE' | string;
    market?: string;
    timeframe?: string;
    source_type?: string;
    is_active?: boolean;
    promotion_summary?: PinePromotionSummary;
    backtest_summary?: Record<string, any>;
    compatibility_summary?: Record<string, any>;
    ranking_summary?: Record<string, any>;
    created_at?: string | null;
    ready_at?: string | null;
    activated_at?: string | null;
    activation_count?: number;
    activation_history?: PineActivationEvent[];
};

const PROMOTION_GATE_LABELS: Record<string, string> = {
    readiness: 'Preflight readiness is not ready',
    compatibility_score: 'Compatibility score below ready threshold',
    combined_score: 'Combined score below ready threshold',
    trade_count: 'Trade count below ready minimum',
    total_return: 'Total return must stay positive',
    max_drawdown: 'Drawdown is above the safety ceiling',
};

function formatPromotionGate(gate: string) {
    return PROMOTION_GATE_LABELS[gate] ?? gate.replaceAll('_', ' ');
}

type UsePineProfilePromotionOptions = {
    pineForm: PineLabForm;
    preflightResult: any;
    backtestResult: any;
    importPreviewResult?: any;
    importBacktestResult?: any;
    operatorApproved?: boolean;
    showMessage: (message: UiMessage) => void;
    enabled?: boolean;
};

export function usePineProfilePromotion({
    pineForm,
    preflightResult,
    backtestResult,
    importPreviewResult,
    importBacktestResult,
    operatorApproved = false,
    showMessage,
    enabled = true,
}: UsePineProfilePromotionOptions) {
    const [promotionLoading, setPromotionLoading] = useState(false);
    const [importProfileLoading, setImportProfileLoading] = useState(false);
    const [activationLoading, setActivationLoading] = useState(false);
    const [createdProfile, setCreatedProfile] = useState<PineProfileRecord | null>(null);
    const [profileRegistry, setProfileRegistry] = useState<PineProfileRecord[]>([]);
    const [profileRegistryLoading, setProfileRegistryLoading] = useState(false);

    const refreshProfiles = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
        const shouldShowLoadingState = !silent || profileRegistry.length === 0;
        if (shouldShowLoadingState) {
            setProfileRegistryLoading(true);
        }
        try {
            const res = await apiFetch('/api/v1/strategy/pine/scanner-profiles');
            const data = await readJsonSafe<any>(res);
            if (!res.ok) {
                if (!silent) {
                    showMessage({ type: 'error', text: pickApiMessage(data, 'Failed to load Pine scanner profiles.') });
                }
                return [];
            }

            const profiles = Array.isArray(data?.profiles) ? data.profiles : [];
            setProfileRegistry(profiles);
            setCreatedProfile((current) => {
                if (!current) {
                    return current;
                }
                return profiles.find((profile: PineProfileRecord) => profile.profile_id === current.profile_id) ?? current;
            });
            return profiles;
        } catch {
            if (!silent) {
                showMessage({ type: 'error', text: 'Network error while loading Pine scanner profiles.' });
            }
            return [];
        } finally {
            if (shouldShowLoadingState) {
                setProfileRegistryLoading(false);
            }
        }
    }, [profileRegistry.length, showMessage]);

    useEffect(() => {
        if (!enabled) {
            return;
        }
        void refreshProfiles({ silent: true });
    }, [enabled, refreshProfiles]);

    const createProfile = async () => {
        if (!pineForm.profileName.trim()) {
            showMessage({ type: 'error', text: 'Profile Name is required before creating a scanner profile.' });
            return;
        }
        if (!preflightResult || !backtestResult) {
            showMessage({ type: 'error', text: 'Run Pine preflight and Pine backtest before creating a scanner profile.' });
            return;
        }

        setPromotionLoading(true);
        try {
            const res = await apiFetch('/api/v1/strategy/pine/create-scanner-profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    script_source: pineForm.scriptSource,
                    profile_name: pineForm.profileName,
                    market: pineForm.market,
                    timeframe: pineForm.timeframe,
                    backtest_summary: backtestResult.metrics,
                    compatibility_summary: {
                        ...(preflightResult ?? {}),
                        ...(backtestResult.compatibility ?? {}),
                    },
                    ranking_summary: backtestResult.rankings,
                }),
            });
            const data = await readJsonSafe<any>(res);
            if (!res.ok) {
                showMessage({ type: 'error', text: pickApiMessage(data, 'Failed to create Pine scanner profile.') });
                return;
            }
            setCreatedProfile({
                profile_id: data.profile_id,
                profile_name: data.profile_name,
                profile_state: data.profile_state,
                market: pineForm.market,
                timeframe: pineForm.timeframe,
                source_type: data.source_type ?? 'PINE',
                promotion_summary: data.promotion_summary,
                created_at: data.created_at,
                ready_at: data.ready_at,
                activated_at: data.activated_at,
                activation_count: data.activation_count,
                activation_history: data.activation_history,
            });
            await refreshProfiles({ silent: true });
            const stateLabel = String(data.profile_state || 'DRAFT').toUpperCase();
            if (stateLabel === 'READY') {
                showMessage({ type: 'success', text: `Pine scanner profile "${data.profile_name}" created successfully and is READY for activation.` });
            } else {
                const failedGates = Array.isArray(data?.promotion_summary?.failed_gates) ? data.promotion_summary.failed_gates : [];
                const gateSummary = failedGates.length > 0
                    ? ` Fix these promotion gates before activation: ${failedGates.map((gate: string) => formatPromotionGate(gate)).join('; ')}.`
                    : '';
                showMessage({
                    type: 'success',
                    text: `Pine scanner profile "${data.profile_name}" created successfully, but it stayed ${stateLabel}.${gateSummary}`,
                });
            }
        } catch {
            showMessage({ type: 'error', text: 'Network error while creating Pine scanner profile.' });
        } finally {
            setPromotionLoading(false);
        }
    };

    const saveImportedProfile = async () => {
        if (!pineForm.profileName.trim()) {
            showMessage({ type: 'error', text: 'Profile Name is required before saving an imported Pine profile.' });
            return;
        }
        if (!importPreviewResult?.rule_spec) {
            showMessage({ type: 'error', text: 'Extract a Pine logic import rule spec before saving an imported profile.' });
            return;
        }
        if (!operatorApproved) {
            showMessage({ type: 'error', text: 'Approve the imported rule spec before saving it as a reusable profile.' });
            return;
        }
        if (!importBacktestResult) {
            showMessage({ type: 'error', text: 'Run the import backtest before saving an imported Pine profile.' });
            return;
        }

        setImportProfileLoading(true);
        try {
            const res = await apiFetch('/api/v1/strategy/pine/import-profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profile_name: pineForm.profileName,
                    script_source: pineForm.scriptSource,
                    rule_spec: importPreviewResult.rule_spec,
                    operator_approved: true,
                    market: pineForm.market,
                    timeframe: pineForm.timeframe,
                    backtest_summary: importBacktestResult.metrics,
                    ranking_summary: importBacktestResult.rankings,
                }),
            });
            const data = await readJsonSafe<any>(res);
            if (!res.ok) {
                showMessage({ type: 'error', text: pickApiMessage(data, 'Failed to save imported Pine profile.') });
                return;
            }

            setCreatedProfile({
                profile_id: data.profile_id,
                profile_name: data.profile_name,
                profile_state: data.profile_state,
                source_type: data.source_type,
                market: pineForm.market,
                timeframe: pineForm.timeframe,
                created_at: data.created_at,
                ready_at: data.ready_at,
                activated_at: null,
                activation_count: 0,
                activation_history: [],
                backtest_summary: importBacktestResult.metrics,
                ranking_summary: importBacktestResult.rankings,
                promotion_summary: {
                    failed_gates: [],
                },
            });
            await refreshProfiles({ silent: true });
            showMessage({ type: 'success', text: `Imported Pine profile "${data.profile_name}" saved successfully for reuse in Backtester.` });
        } catch {
            showMessage({ type: 'error', text: 'Network error while saving imported Pine profile.' });
        } finally {
            setImportProfileLoading(false);
        }
    };

    const activateProfile = async (targetProfile?: PineProfileRecord | null) => {
        const profileToActivate = targetProfile ?? createdProfile;
        if (!profileToActivate) {
            showMessage({ type: 'error', text: 'Create a Pine scanner profile before activating it.' });
            return;
        }
        if (String(profileToActivate.source_type || 'PINE').toUpperCase() !== 'PINE') {
            showMessage({ type: 'error', text: 'Logic Import profiles are saved for research reuse and cannot be activated in Scanner.' });
            return;
        }
        if (profileToActivate.profile_state === 'DRAFT') {
            showMessage({ type: 'error', text: 'This Pine scanner profile is still DRAFT and cannot be activated yet.' });
            return;
        }
        if (profileToActivate.profile_state === 'ACTIVE') {
            showMessage({ type: 'success', text: `Pine scanner profile "${profileToActivate.profile_name}" is already active in Scanner.` });
            return;
        }

        setActivationLoading(true);
        try {
            const res = await apiFetch('/api/v1/strategy/pine/activate-scanner-profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileToActivate.profile_id }),
            });
            const data = await readJsonSafe<any>(res);
            if (!res.ok) {
                showMessage({ type: 'error', text: pickApiMessage(data, 'Failed to activate Pine scanner profile.') });
                return;
            }
            setCreatedProfile((current) => {
                if (current?.profile_id !== data.profile_id) {
                    return current;
                }
                return {
                    ...current,
                    profile_id: data.profile_id,
                    profile_name: data.profile_name,
                    profile_state: data.profile_state,
                    is_active: true,
                    created_at: data.created_at,
                    ready_at: data.ready_at,
                    activated_at: data.activated_at,
                    activation_count: data.activation_count,
                    activation_history: data.activation_history,
                    promotion_summary: {
                        failed_gates: [],
                    },
                };
            });
            await refreshProfiles({ silent: true });
            showMessage({ type: 'success', text: `Pine scanner profile "${data.profile_name}" is now active in Scanner.` });
        } catch {
            showMessage({ type: 'error', text: 'Network error while activating Pine scanner profile.' });
        } finally {
            setActivationLoading(false);
        }
    };

    return {
        promotionLoading,
        importProfileLoading,
        activationLoading,
        createdProfile,
        profileRegistry,
        profileRegistryLoading,
        refreshProfiles,
        createProfile,
        saveImportedProfile,
        activateProfile,
    };
}
