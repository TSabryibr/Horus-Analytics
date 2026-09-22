'use client';

import React, { createContext, useContext, ReactNode } from 'react';
import { SectorStat, WhaleCandidate, ArbitrageMirror, Trap, StrategyProposal, OracleData } from '@/types';
import { SyncTimestampMap } from './syncTimestamps';
import { useMarketRuntime } from './hooks/useMarketRuntime';

export type MarketStreamScope = {
    sectors: boolean;
    whales: boolean;
    arbitrage: boolean;
    traps: boolean;
    strategy: boolean;
    oracle: boolean;
};

export type MarketContextValue = {
    sectors: SectorStat[];
    whales: { candidates: WhaleCandidate[] } | null;
    arbitrage: { mirrors: ArbitrageMirror[] } | null;
    traps: { bull_traps: Trap[]; bear_traps: Trap[] } | null;
    strategy: StrategyProposal | null;
    oracle: OracleData | null;
    loading: {
        sectors: boolean;
        whales: boolean;
        arbitrage: boolean;
        traps: boolean;
        strategy: boolean;
        oracle: boolean;
    };
    lastUpdated: SyncTimestampMap;
    refreshMarket: () => void;
    refreshOracleNoCache: () => void;
    refreshOracleWithProvider: (provider: 'OLLAMA') => void;
};

const MarketDataContext = createContext<MarketContextValue | undefined>(undefined);

export function MarketProvider({
    children,
    enabled = true,
    scope,
}: {
    children: ReactNode;
    enabled?: boolean;
    scope?: Partial<MarketStreamScope>;
}) {
    const value = useMarketRuntime({ enabled, scope });

    return (
        <MarketDataContext.Provider value={value}>
            {children}
        </MarketDataContext.Provider>
    );
}

export function useMarketData() {
    const context = useContext(MarketDataContext);
    if (context === undefined) {
        throw new Error('useMarketData must be used within a MarketProvider');
    }
    return context;
}
