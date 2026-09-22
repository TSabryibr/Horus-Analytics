import { useMemo } from 'react';
import useSWR from 'swr';
import { swrFetcher } from '@/lib/api';
import { extractSyncTimestamp } from '../syncTimestamps';
import { normalizeTrapsPayload, fetchOracleBundle } from '../lib/marketTransforms';
import { MarketStreamScope } from '../MarketContext';

interface UseMarketRuntimeOptions {
    enabled?: boolean;
    scope?: Partial<MarketStreamScope>;
}

const DEFAULT_MARKET_SCOPE: MarketStreamScope = {
    sectors: true,
    whales: true,
    arbitrage: true,
    traps: true,
    strategy: true,
    oracle: true,
};

export function useMarketRuntime({ enabled = true, scope }: UseMarketRuntimeOptions = {}) {
    const resolvedScope: MarketStreamScope = {
        ...DEFAULT_MARKET_SCOPE,
        ...(scope || {}),
    };

    const sectorsKey = enabled && resolvedScope.sectors ? '/api/v1/sectors' : null;
    const whalesKey = enabled && resolvedScope.whales ? '/api/v1/whales' : null;
    const arbitrageKey = enabled && resolvedScope.arbitrage ? '/api/v1/arbitrage' : null;
    const trapsKey = enabled && resolvedScope.traps ? '/api/v1/traps' : null;
    const strategyKey = enabled && resolvedScope.strategy ? '/api/v1/strategy' : null;
    const oracleKey = enabled && resolvedScope.oracle ? 'market-oracle' : null;

    const { data: sectors, isLoading: sLoading, mutate: sMutate } = useSWR(sectorsKey, swrFetcher, { refreshInterval: 600000, dedupingInterval: 60000, focusThrottleInterval: 60000 });
    const { data: whales, isLoading: wLoading, mutate: wMutate } = useSWR(whalesKey, swrFetcher, { refreshInterval: 300000, dedupingInterval: 60000, focusThrottleInterval: 60000 });
    const { data: arbitrage, isLoading: aLoading, mutate: aMutate } = useSWR(arbitrageKey, swrFetcher, { refreshInterval: 300000, dedupingInterval: 60000, focusThrottleInterval: 60000 });
    const { data: traps, isLoading: tLoading, mutate: tMutate } = useSWR(trapsKey, swrFetcher, { refreshInterval: 300000, dedupingInterval: 60000, focusThrottleInterval: 60000 });
    const { data: strategy, isLoading: stLoading, mutate: stMutate } = useSWR(strategyKey, swrFetcher, { refreshInterval: 600000, dedupingInterval: 60000, focusThrottleInterval: 60000 });
    const { data: oracle, isLoading: oLoading, mutate: oMutate } = useSWR(oracleKey, () => fetchOracleBundle(), { refreshInterval: 600000, dedupingInterval: 60000, focusThrottleInterval: 60000 });

    const value = useMemo(() => ({
        sectors: sectors || [],
        whales: whales || null,
        arbitrage: arbitrage || null,
        traps: normalizeTrapsPayload(traps),
        strategy: strategy?.status === 'success' ? strategy.data : null,
        oracle: oracle || null,
        loading: {
            sectors: Boolean(sectorsKey) && sLoading,
            whales: Boolean(whalesKey) && wLoading,
            arbitrage: Boolean(arbitrageKey) && aLoading,
            traps: Boolean(trapsKey) && tLoading,
            strategy: Boolean(strategyKey) && stLoading,
            oracle: Boolean(oracleKey) && oLoading
        },
        lastUpdated: {
            sectors: extractSyncTimestamp(sectors),
            whales: extractSyncTimestamp(whales),
            arbitrage: extractSyncTimestamp(arbitrage),
            traps: extractSyncTimestamp(traps),
            strategy: extractSyncTimestamp(strategy),
            oracle: extractSyncTimestamp(oracle),
        },
        refreshMarket: () => {
            if (!enabled) {
                return;
            }
            if (sectorsKey) sMutate();
            if (whalesKey) wMutate();
            if (arbitrageKey) aMutate();
            if (trapsKey) tMutate();
            if (strategyKey) stMutate();
            if (oracleKey) oMutate();
        },
        refreshOracleNoCache: () => {
            if (!enabled || !oracleKey) {
                return;
            }
            oMutate(fetchOracleBundle({ forceRefresh: true }), { revalidate: false });
        },
        refreshOracleWithProvider: (provider: 'OLLAMA') => {
            if (!enabled || !oracleKey) {
                return;
            }
            oMutate(fetchOracleBundle({ provider }), { revalidate: false });
        }
    }), [
        enabled,
        sectors,
        whales,
        arbitrage,
        traps,
        strategy,
        oracle,
        sectorsKey,
        whalesKey,
        arbitrageKey,
        trapsKey,
        strategyKey,
        oracleKey,
        sLoading,
        wLoading,
        aLoading,
        tLoading,
        stLoading,
        oLoading,
        sMutate,
        wMutate,
        aMutate,
        tMutate,
        stMutate,
        oMutate,
    ]);

    return value;
}
