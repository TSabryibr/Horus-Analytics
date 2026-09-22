'use client';

import React, { ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { PortfolioProvider } from './PortfolioContext';
import { NewsProvider, useNewsData } from './NewsContext';
import { DashboardProvider, useDashboardData } from './DashboardContext';
import { MarketProvider, MarketStreamScope, useMarketData } from './MarketContext';
import { LiveProvider } from './LiveContext';
import { SignalDeskCoreProvider, useSignalDeskCore } from './SignalDeskCoreContext';
import { SignalLifecycleProvider, useSignalLifecycle } from './SignalLifecycleContext';
import { SignalFollowUpProvider, useSignalFollowUp } from './SignalFollowUpContext';

type GlobalStreamPolicy = {
    dashboard: boolean;
    news: boolean;
    market: boolean;
    live: boolean;
    signalDesk: boolean;
    marketScope: MarketStreamScope;
};

const EMPTY_MARKET_SCOPE: MarketStreamScope = {
    sectors: false,
    whales: false,
    arbitrage: false,
    traps: false,
    strategy: false,
    oracle: false,
};

function isRouteMatch(pathname: string | null | undefined, route: string): boolean {
    if (!pathname) {
        return false;
    }
    return pathname === route || pathname.startsWith(`${route}/`);
}

export function resolveGlobalStreamPolicy(pathname: string | null | undefined): GlobalStreamPolicy {
    if (isRouteMatch(pathname, '/')) {
        return {
            dashboard: true,
            news: false,
            market: false,
            live: false,
            signalDesk: true,
            marketScope: EMPTY_MARKET_SCOPE,
        };
    }

    if (isRouteMatch(pathname, '/news')) {
        return {
            dashboard: false,
            news: true,
            market: false,
            live: false,
            signalDesk: false,
            marketScope: EMPTY_MARKET_SCOPE,
        };
    }

    if (isRouteMatch(pathname, '/oracle')) {
        return {
            dashboard: false,
            news: false,
            market: true,
            live: false,
            signalDesk: false,
            marketScope: {
                ...EMPTY_MARKET_SCOPE,
                oracle: true,
            },
        };
    }

    if (isRouteMatch(pathname, '/sectors')) {
        return {
            dashboard: false,
            news: false,
            market: true,
            live: false,
            signalDesk: false,
            marketScope: {
                ...EMPTY_MARKET_SCOPE,
                sectors: true,
            },
        };
    }

    if (isRouteMatch(pathname, '/whales')) {
        return {
            dashboard: false,
            news: false,
            market: true,
            live: false,
            signalDesk: false,
            marketScope: {
                ...EMPTY_MARKET_SCOPE,
                whales: true,
            },
        };
    }

    if (isRouteMatch(pathname, '/arbitrage')) {
        return {
            dashboard: false,
            news: false,
            market: true,
            live: false,
            signalDesk: false,
            marketScope: {
                ...EMPTY_MARKET_SCOPE,
                arbitrage: true,
            },
        };
    }

    if (isRouteMatch(pathname, '/traps')) {
        return {
            dashboard: false,
            news: false,
            market: true,
            live: false,
            signalDesk: false,
            marketScope: {
                ...EMPTY_MARKET_SCOPE,
                traps: true,
            },
        };
    }

    if (isRouteMatch(pathname, '/strategy')) {
        return {
            dashboard: false,
            news: false,
            market: true,
            live: false,
            signalDesk: false,
            marketScope: {
                ...EMPTY_MARKET_SCOPE,
                strategy: true,
            },
        };
    }

    if (isRouteMatch(pathname, '/live')) {
        return {
            dashboard: false,
            news: false,
            market: false,
            live: true,
            signalDesk: false,
            marketScope: EMPTY_MARKET_SCOPE,
        };
    }

    if (isRouteMatch(pathname, '/telegram')) {
        return {
            dashboard: false,
            news: false,
            market: false,
            live: false,
            signalDesk: true,
            marketScope: EMPTY_MARKET_SCOPE,
        };
    }

    return {
        dashboard: false,
        news: false,
        market: false,
        live: false,
        signalDesk: false,
        marketScope: EMPTY_MARKET_SCOPE,
    };
}

export function GlobalDataProvider({ children, initialData }: { children: ReactNode, initialData?: { news?: any } }) {
    const pathname = usePathname();
    const streamPolicy = resolveGlobalStreamPolicy(pathname);

    return (
        <PortfolioProvider>
            <SignalLifecycleProvider enabled={streamPolicy.signalDesk}>
                <SignalFollowUpProvider enabled={streamPolicy.signalDesk}>
                    <SignalDeskCoreProvider enabled={streamPolicy.signalDesk}>
                        <DashboardProvider enabled={streamPolicy.dashboard}>
                            <NewsProvider initialData={initialData?.news} enabled={streamPolicy.news}>
                                <MarketProvider enabled={streamPolicy.market} scope={streamPolicy.marketScope}>
                                    <LiveProvider enabled={streamPolicy.live}>
                                        {children}
                                    </LiveProvider>
                                </MarketProvider>
                            </NewsProvider>
                        </DashboardProvider>
                    </SignalDeskCoreProvider>
                </SignalFollowUpProvider>
            </SignalLifecycleProvider>
        </PortfolioProvider>
    );
}

// Re-export hooks from specialized contexts for backward compatibility
export { usePortfolioData } from './PortfolioContext';
export { useNewsData } from './NewsContext';
export { useDashboardData } from './DashboardContext';
export { useMarketData } from './MarketContext';
export { useLiveContext } from './LiveContext';

// Composite facade hook for backward compatibility with older components
export function useSignalDeskData() {
    const core = useSignalDeskCore();
    const lifecycle = useSignalLifecycle();
    const followUp = useSignalFollowUp();

    return {
        ...core,
        ...lifecycle,
        ...followUp,
    };
}

// Market Data specialized shims (Phase 12 Compatibility)
export function useWhalesData() {
    const { whales, loading, refreshMarket } = useMarketData();
    return {
        whales,
        whalesLoading: loading.whales,
        refreshWhales: refreshMarket
    };
}

export function useArbitrageData() {
    const { arbitrage, loading, refreshMarket } = useMarketData();
    return {
        arbitrage,
        arbitrageLoading: loading.arbitrage,
        refreshArbitrage: refreshMarket
    };
}

export function useTrapsData() {
    const { traps, loading, refreshMarket } = useMarketData();
    return {
        traps,
        trapsLoading: loading.traps,
        refreshTraps: refreshMarket
    };
}

export function useStrategyData() {
    const { strategy, loading, refreshMarket } = useMarketData();
    return {
        strategy,
        strategyLoading: loading.strategy,
        refreshStrategy: refreshMarket
    };
}

export function useOracleData() {
    const { oracle, loading, refreshMarket, refreshOracleNoCache, refreshOracleWithProvider } = useMarketData();
    return {
        oracle,
        oracleLoading: loading.oracle,
        refreshOracle: refreshMarket,
        refreshOracleNoCache,
        refreshOracleWithProvider
    };
}

// Specialized hook to aggregate loading states from all domain contexts
export function useDataSyncStatus() {
    const { newsLoading, newsUpdatedAt } = useNewsData();
    const { dashboardLoading, dashboardUpdatedAt } = useDashboardData();
    const { loading: marketLoading, lastUpdated: marketLastUpdated } = useMarketData();

    return {
        loading: {
            news: newsLoading,
            dashboard: dashboardLoading,
            whales: marketLoading.whales,
            arbitrage: marketLoading.arbitrage,
            traps: marketLoading.traps,
            strategy: marketLoading.strategy,
            oracle: marketLoading.oracle
        },
        lastUpdated: {
            news: newsUpdatedAt,
            dashboard: dashboardUpdatedAt,
            whales: marketLastUpdated.whales ?? null,
            arbitrage: marketLastUpdated.arbitrage ?? null,
            traps: marketLastUpdated.traps ?? null,
            strategy: marketLastUpdated.strategy ?? null,
            oracle: marketLastUpdated.oracle ?? null,
            sectors: marketLastUpdated.sectors ?? null,
        }
    };
}
