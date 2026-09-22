'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';

import type { PineProfileRecord } from './usePineProfilePromotion';

type UiMessage = {
    type: 'error' | 'success';
    text: string;
} | null;

type UseBacktestLabOptions = {
    optIndex: string;
    showMessage: (message: UiMessage) => void;
    enabled?: boolean;
};

export type BacktestSource = 'HORUS' | 'PINE_PROFILE';

export type PineRunConfig = {
    market: string;
    timeframe: string;
    dateFrom: string;
    dateTo: string;
    capital: number;
    commissionPct: number;
    slippagePct: number;
};

type BacktestResult = {
    source_metadata?: Record<string, unknown>;
    [key: string]: unknown;
};

type SimulationParams = {
    RSI_MIN: number;
    RSI_MAX: number;
    VOL_SPIKE: number;
    MOMENTUM: number;
    SL_PCT: number;
    TP1_PCT: number;
    MAX_POSITIONS: number;
    TRAILING_STOP_ENABLED: boolean;
    TRAILING_STOP_TYPE: string;
    TRAILING_STOP_VALUE: number;
};

function buildDefaultDateRange() {
    const now = new Date();
    return {
        dateFrom: `${now.getFullYear()}-01-01`,
        dateTo: now.toISOString().slice(0, 10),
    };
}

function buildDefaultPineRunConfig(): PineRunConfig {
    const { dateFrom, dateTo } = buildDefaultDateRange();
    return {
        market: 'EGX30',
        timeframe: '1D',
        dateFrom,
        dateTo,
        capital: 100000,
        commissionPct: 0.05,
        slippagePct: 0.1,
    };
}

function attachSourceMetadata(result: BacktestResult, metadata: Record<string, unknown>) {
    return {
        ...result,
        source_metadata: {
            ...(typeof result?.source_metadata === 'object' && result.source_metadata ? result.source_metadata : {}),
            ...metadata,
        },
    };
}

export function useBacktestLab({ optIndex, showMessage, enabled = true }: UseBacktestLabOptions) {
    const [simParams, setSimParams] = useState<SimulationParams>({
        RSI_MIN: 55,
        RSI_MAX: 85,
        VOL_SPIKE: 1.5,
        MOMENTUM: 2.5,
        SL_PCT: 1.5,
        TP1_PCT: 4.0,
        MAX_POSITIONS: 10,
        TRAILING_STOP_ENABLED: false,
        TRAILING_STOP_TYPE: 'PERCENT',
        TRAILING_STOP_VALUE: 2.0,
    });
    const [simResult, setSimResult] = useState<any>(null);
    const [simLoading, setSimLoading] = useState(false);
    const [applyConfirmOpen, setApplyConfirmOpen] = useState(false);
    const [pendingApplyParams, setPendingApplyParams] = useState<any>(null);
    const [backtestSource, setBacktestSource] = useState<BacktestSource>('HORUS');
    const [selectedPineProfileId, setSelectedPineProfileIdState] = useState<number | null>(null);
    const [profileRegistry, setProfileRegistry] = useState<PineProfileRecord[]>([]);
    const [profileRegistryLoading, setProfileRegistryLoading] = useState(false);
    const [pineRunConfig, setPineRunConfig] = useState<PineRunConfig>(() => buildDefaultPineRunConfig());

    const selectedPineProfile = useMemo(
        () => profileRegistry.find((profile) => profile.profile_id === selectedPineProfileId) ?? null,
        [profileRegistry, selectedPineProfileId]
    );

    const validateSimulationParams = (paramsToValidate: SimulationParams) => {
        if (paramsToValidate.RSI_MIN >= paramsToValidate.RSI_MAX) {
            return 'RSI Entry must be lower than RSI Overbought.';
        }
        if (paramsToValidate.SL_PCT <= 0) {
            return 'Stop Loss must be greater than 0%.';
        }
        if (paramsToValidate.TP1_PCT <= 0) {
            return 'Target 1 must be greater than 0%.';
        }
        if (paramsToValidate.MAX_POSITIONS < 1) {
            return 'Max Slots must be at least 1.';
        }
        if (paramsToValidate.TRAILING_STOP_ENABLED && paramsToValidate.TRAILING_STOP_VALUE <= 0) {
            return 'Trail Buffer must be greater than 0% when trailing stop is enabled.';
        }
        return null;
    };

    const loadPineProfiles = useCallback(async () => {
        setProfileRegistryLoading(true);
        try {
            const res = await apiFetch('/api/v1/strategy/pine/scanner-profiles');
            const data = await readJsonSafe<any>(res);
            if (!res.ok) {
                showMessage({ type: 'error', text: pickApiMessage(data, 'Failed to load Pine profiles for Backtester.') });
                return;
            }
            setProfileRegistry(Array.isArray(data?.profiles) ? data.profiles : []);
        } catch {
            showMessage({ type: 'error', text: 'Network error while loading Pine profiles for Backtester.' });
        } finally {
            setProfileRegistryLoading(false);
        }
    }, [showMessage]);

    useEffect(() => {
        if (!enabled || backtestSource !== 'PINE_PROFILE' || profileRegistry.length > 0 || profileRegistryLoading) {
            return;
        }
        void loadPineProfiles();
    }, [backtestSource, enabled, loadPineProfiles, profileRegistry.length, profileRegistryLoading]);

    const setSelectedPineProfileId = useCallback((profileId: number | null) => {
        setSelectedPineProfileIdState(profileId);
        if (profileId == null) {
            return;
        }

        setPineRunConfig((current) => {
            const selectedProfile = profileRegistry.find((profile) => profile.profile_id === profileId);
            if (!selectedProfile) {
                return current;
            }
            return {
                ...current,
                market: selectedProfile.market || current.market,
                timeframe: selectedProfile.timeframe || current.timeframe,
            };
        });
    }, [profileRegistry]);

    const runSimulation = async (paramOverride?: Partial<SimulationParams>) => {
        const paramsForRun = paramOverride ? { ...simParams, ...paramOverride } : simParams;
        const validationError = validateSimulationParams(paramsForRun);
        if (validationError) {
            showMessage({ type: 'error', text: validationError });
            return;
        }
        setSimLoading(true);
        try {
            const res = await apiFetch('/api/v1/strategy/backtest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index: optIndex,
                    capital: 200000,
                    params: paramsForRun,
                }),
            });
            const data = await readJsonSafe<any>(res);
            if (!res.ok) {
                showMessage({ type: 'error', text: pickApiMessage(data, 'Simulation failed.') });
                return;
            }
            const tradeCount = Number(data?.metrics?.trade_count ?? 0);
            if (tradeCount === 0) {
                showMessage({
                    type: 'success',
                    text: 'Backtest completed with 0 trades. Try a wider date window or less strict filters.',
                });
            } else {
                showMessage(null);
            }
            setSimResult(
                attachSourceMetadata(data, {
                    backtest_source: 'HORUS',
                })
            );
        } catch {
            showMessage({ type: 'error', text: 'Network error while running simulation.' });
        } finally {
            setSimLoading(false);
        }
    };

    const runBacktest = async (profileIdOverride?: number | null) => {
        if (backtestSource === 'HORUS') {
            await runSimulation();
            return;
        }

        const resolvedProfileId = profileIdOverride ?? selectedPineProfileId;
        const resolvedPineProfile =
            profileRegistry.find((profile) => profile.profile_id === resolvedProfileId) ?? selectedPineProfile;

        if (!resolvedPineProfile) {
            showMessage({ type: 'error', text: 'Select a Pine profile before running a Pine backtest.' });
            return;
        }

        setSimLoading(true);
        try {
            const detailResponse = await apiFetch(`/api/v1/strategy/pine/scanner-profile/${resolvedPineProfile.profile_id}`);
            const detailData = await readJsonSafe<any>(detailResponse);
            if (!detailResponse.ok) {
                showMessage({ type: 'error', text: pickApiMessage(detailData, 'Failed to load the selected Pine profile.') });
                return;
            }

            const scriptSource = String(detailData?.script_source || '').trim();
            if (!scriptSource) {
                showMessage({ type: 'error', text: 'The selected Pine profile does not include a stored script source.' });
                return;
            }

            const profileDetails = detailData?.profile ?? resolvedPineProfile;
            const profileSourceType = String(profileDetails?.source_type || resolvedPineProfile.source_type || '').toUpperCase();
            const isImportedLogicProfile = profileSourceType === 'PINE_LOGIC_IMPORT';
            const backtestResponse = isImportedLogicProfile
                ? await apiFetch('/api/v1/strategy/pine/import-backtest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        rule_spec: detailData?.import_rule_spec ?? {},
                        operator_approved: true,
                        market: pineRunConfig.market,
                        timeframe: pineRunConfig.timeframe,
                        date_from: pineRunConfig.dateFrom,
                        date_to: pineRunConfig.dateTo,
                        capital: pineRunConfig.capital,
                        commission_pct: pineRunConfig.commissionPct,
                        slippage_pct: pineRunConfig.slippagePct,
                    }),
                })
                : await apiFetch('/api/v1/strategy/pine/backtest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        script_source: scriptSource,
                        market: pineRunConfig.market,
                        timeframe: pineRunConfig.timeframe,
                        date_from: pineRunConfig.dateFrom,
                        date_to: pineRunConfig.dateTo,
                        capital: pineRunConfig.capital,
                        commission_pct: pineRunConfig.commissionPct,
                        slippage_pct: pineRunConfig.slippagePct,
                    }),
                });
            const backtestData = await readJsonSafe<any>(backtestResponse);
            if (!backtestResponse.ok) {
                showMessage({ type: 'error', text: pickApiMessage(backtestData, 'Pine backtest failed.') });
                return;
            }

            showMessage(null);
            setSimResult(
                attachSourceMetadata(backtestData, {
                    backtest_source: 'PINE_PROFILE',
                    profile_id: profileDetails.profile_id ?? resolvedPineProfile.profile_id,
                    profile_name: profileDetails.profile_name ?? resolvedPineProfile.profile_name,
                    profile_state: profileDetails.profile_state ?? resolvedPineProfile.profile_state,
                    profile_source_type: profileSourceType || 'PINE',
                })
            );
        } catch {
            showMessage({ type: 'error', text: 'Network error while running Pine backtest.' });
        } finally {
            setSimLoading(false);
        }
    };

    const applySettings = async (params: any) => {
        try {
            const res = await apiFetch('/api/v1/strategy/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ params }),
            });
            const body = await readJsonSafe<any>(res);
            if (!res.ok) {
                showMessage({ type: 'error', text: pickApiMessage(body, 'Failed to apply settings.') });
                return;
            }
            showMessage({ type: 'success', text: 'Settings applied successfully.' });
        } catch {
            showMessage({ type: 'error', text: 'Network error while applying settings.' });
        }
    };

    const promptApplySettings = (params: any) => {
        setPendingApplyParams({ ...params });
        setApplyConfirmOpen(true);
    };

    const closeApplyConfirm = () => {
        setApplyConfirmOpen(false);
        setPendingApplyParams(null);
    };

    const confirmApplySettings = async () => {
        if (!pendingApplyParams) {
            setApplyConfirmOpen(false);
            return;
        }
        const params = pendingApplyParams;
        closeApplyConfirm();
        await applySettings(params);
    };

    return {
        simParams,
        setSimParams,
        simResult,
        simLoading,
        runSimulation,
        runBacktest,
        applyConfirmOpen,
        pendingApplyParams,
        promptApplySettings,
        closeApplyConfirm,
        confirmApplySettings,
        backtestSource,
        setBacktestSource,
        profileRegistry,
        profileRegistryLoading,
        selectedPineProfileId,
        setSelectedPineProfileId,
        selectedPineProfile,
        pineRunConfig,
        setPineRunConfig,
    };
}
