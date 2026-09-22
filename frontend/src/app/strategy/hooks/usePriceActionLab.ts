'use client';

import { useEffect, useMemo, useState } from 'react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';
import type {
    PriceActionBacktestResponse,
    PriceActionCatalogResponse,
    PriceActionCatalogStrategy,
    PriceActionEvaluateResponse,
} from '@/types/domain';
import type { ScannerStrategyProfileAudit } from '@/types';

const DEFAULT_DATES = {
    dateFrom: '2025-01-01',
    dateTo: '2025-12-31',
};

export function usePriceActionLab() {
    const [catalog, setCatalog] = useState<PriceActionCatalogStrategy[]>([]);
    const [catalogLoading, setCatalogLoading] = useState(true);
    const [catalogError, setCatalogError] = useState('');
    const [actionError, setActionError] = useState('');
    const [actionSuccess, setActionSuccess] = useState('');
    const [busyAction, setBusyAction] = useState<'evaluate' | 'backtest' | 'promote' | 'activate' | null>(null);
    const [familyFilter, setFamilyFilter] = useState<'ALL' | 'INTRADAY' | 'SWING' | 'POSITION'>('SWING');
    const [ticker, setTicker] = useState('COMI');
    const [market, setMarket] = useState('EGX30');
    const [dateFrom, setDateFrom] = useState(DEFAULT_DATES.dateFrom);
    const [dateTo, setDateTo] = useState(DEFAULT_DATES.dateTo);
    const [capital, setCapital] = useState(100000);
    const [profileName, setProfileName] = useState('EGX Price Action Pack');
    const [selectedStrategyId, setSelectedStrategyId] = useState('');
    const [signals, setSignals] = useState<PriceActionEvaluateResponse['signals']>([]);
    const [backtestResult, setBacktestResult] = useState<PriceActionBacktestResponse | null>(null);
    const [promotedProfile, setPromotedProfile] = useState<ScannerStrategyProfileAudit | null>(null);

    const filteredCatalog = useMemo(() => (
        familyFilter === 'ALL'
            ? catalog
            : catalog.filter((strategy) => strategy.family === familyFilter)
    ), [catalog, familyFilter]);

    const selectedStrategy = useMemo(
        () => catalog.find((strategy) => strategy.strategy_id === selectedStrategyId) ?? null,
        [catalog, selectedStrategyId],
    );

    const loadCatalog = async () => {
        setCatalogLoading(true);
        setCatalogError('');
        try {
            const res = await apiFetch('/strategy/price-action/catalog');
            const json = await readJsonSafe<PriceActionCatalogResponse>(res);
            if (!res.ok) {
                throw new Error(pickApiMessage(json, 'Failed to load the price-action catalog.'));
            }
            setCatalog(json.strategies ?? []);
            setSelectedStrategyId((current) => current || json.strategies?.find((item) => !item.warning_only)?.strategy_id || json.strategies?.[0]?.strategy_id || '');
        } catch (error) {
            setCatalogError(error instanceof Error ? error.message : 'Failed to load the price-action catalog.');
        } finally {
            setCatalogLoading(false);
        }
    };

    useEffect(() => {
        void loadCatalog();
    }, []);

    useEffect(() => {
        if (!filteredCatalog.length) {
            return;
        }
        if (!filteredCatalog.some((item) => item.strategy_id === selectedStrategyId)) {
            setSelectedStrategyId(filteredCatalog[0].strategy_id);
        }
    }, [filteredCatalog, selectedStrategyId]);

    const runAction = async <T,>(action: 'evaluate' | 'backtest' | 'promote' | 'activate', task: () => Promise<T>) => {
        setBusyAction(action);
        setActionError('');
        setActionSuccess('');
        try {
            return await task();
        } catch (error) {
            const message = error instanceof Error ? error.message : 'The request failed.';
            setActionError(message);
            return null;
        } finally {
            setBusyAction(null);
        }
    };

    const evaluateStrategy = async () => runAction('evaluate', async () => {
        const family = selectedStrategy?.family ?? (familyFilter === 'ALL' ? 'SWING' : familyFilter);
        const res = await apiFetch('/strategy/price-action/evaluate', {
            method: 'POST',
            body: JSON.stringify({
                ticker,
                family,
                include_warning_only: true,
                intraday_data_available: false,
            }),
        });
        const json = await readJsonSafe<PriceActionEvaluateResponse>(res);
        if (!res.ok) {
            throw new Error(pickApiMessage(json, 'Failed to evaluate the strategy.'));
        }
        setSignals(json.signals ?? []);
        setActionSuccess(`Evaluated ${json.signal_count} signal${json.signal_count === 1 ? '' : 's'} for ${ticker}.`);
        return json;
    });

    const backtestStrategy = async () => {
        if (!selectedStrategyId) return null;
        return runAction('backtest', async () => {
            const res = await apiFetch('/strategy/price-action/backtest', {
                method: 'POST',
                body: JSON.stringify({
                    strategy_id: selectedStrategyId,
                    market,
                    date_from: dateFrom,
                    date_to: dateTo,
                    capital,
                    commission_pct: 0.05,
                    slippage_pct: 0.1,
                }),
            });
            const json = await readJsonSafe<PriceActionBacktestResponse>(res);
            if (!res.ok) {
                throw new Error(pickApiMessage(json, 'Failed to backtest the strategy.'));
            }
            setBacktestResult(json);
            setActionSuccess(`Backtest completed for ${json.config.strategy_name}.`);
            return json;
        });
    };

    const promoteStrategy = async () => {
        if (!selectedStrategyId) return null;
        return runAction('promote', async () => {
            const resolvedProfileName = `${profileName.trim() || 'EGX Price Action'} - ${selectedStrategy?.display_name || selectedStrategyId}`;
            const res = await apiFetch('/strategy/price-action/promote', {
                method: 'POST',
                body: JSON.stringify({
                    profile_name: resolvedProfileName,
                    strategy_id: selectedStrategyId,
                    market,
                    date_from: dateFrom,
                    date_to: dateTo,
                    capital,
                    commission_pct: 0.05,
                    slippage_pct: 0.1,
                }),
            });
            const json = await readJsonSafe<ScannerStrategyProfileAudit & { status?: string }>(res);
            if (!res.ok) {
                throw new Error(pickApiMessage(json, 'Failed to promote the strategy.'));
            }
            setPromotedProfile(json);
            setActionSuccess(`Promoted ${resolvedProfileName} as a scanner-ready profile.`);
            return json;
        });
    };

    const activateProfile = async () => {
        if (!promotedProfile?.profile_id) return null;
        return runAction('activate', async () => {
            const res = await apiFetch('/strategy/price-action/activate-profile', {
                method: 'POST',
                body: JSON.stringify({ profile_id: promotedProfile.profile_id }),
            });
            const json = await readJsonSafe<ScannerStrategyProfileAudit & { status?: string }>(res);
            if (!res.ok) {
                throw new Error(pickApiMessage(json, 'Failed to activate the promoted profile.'));
            }
            setPromotedProfile(json);
            setActionSuccess(`Activated ${json.profile_name} for scanner execution.`);
            return json;
        });
    };

    return {
        catalog,
        catalogError,
        catalogLoading,
        filteredCatalog,
        selectedStrategy,
        selectedStrategyId,
        setSelectedStrategyId,
        familyFilter,
        setFamilyFilter,
        ticker,
        setTicker,
        market,
        setMarket,
        dateFrom,
        setDateFrom,
        dateTo,
        setDateTo,
        capital,
        setCapital,
        profileName,
        setProfileName,
        signals,
        backtestResult,
        promotedProfile,
        actionError,
        actionSuccess,
        busyAction,
        evaluateStrategy,
        backtestStrategy,
        promoteStrategy,
        activateProfile,
        reloadCatalog: loadCatalog,
    };
}
