'use client';

import React, { createContext, useContext, ReactNode, useCallback, useMemo } from 'react';
import useSWR from 'swr';
import { swrFetcher } from '@/lib/api';
import { usePortfolioData } from './PortfolioContext';
import { DashboardState, MetricData, EquityPoint, Signal, SystemHealth } from '@/types';
import { extractSyncTimestamp } from './syncTimestamps';

type DashboardContextValue = {
    dashboard: DashboardState;
    dashboardLoading: boolean;
    dashboardUpdatedAt: string | null;
    refreshDashboard: () => void;
};

const DashboardDataContext = createContext<DashboardContextValue | undefined>(undefined);

export function DashboardProvider({ children, enabled = true }: { children: ReactNode; enabled?: boolean }) {
    const { activePortfolioId } = usePortfolioData();

    // Parallel SWR hooks for different dashboard segments
    const { data: metrics, error: mErr, isLoading: mLoading, mutate: mMutate } = useSWR(
        enabled && activePortfolioId ? `/api/v1/portfolio/metrics?portfolio_id=${activePortfolioId}` : null,
        swrFetcher,
        { refreshInterval: 45000, dedupingInterval: 45000, focusThrottleInterval: 45000 }
    );

    const { data: curve, error: cErr, isLoading: cLoading, mutate: cMutate } = useSWR(
        enabled && activePortfolioId ? `/api/v1/portfolio/curve?portfolio_id=${activePortfolioId}` : null,
        swrFetcher,
        { refreshInterval: 60000, dedupingInterval: 60000, focusThrottleInterval: 60000 }
    );

    const { data: signals, error: sErr, isLoading: sLoading, mutate: sMutate } = useSWR(
        enabled ? '/api/v1/scanner/history' : null,
        swrFetcher,
        { refreshInterval: 30000, dedupingInterval: 30000, focusThrottleInterval: 30000 }
    );

    const { data: health, error: hErr, isLoading: hLoading, mutate: hMutate } = useSWR(
        enabled ? '/api/v1/strategy/health?days=60' : null,
        swrFetcher,
        { refreshInterval: 300000, dedupingInterval: 60000, focusThrottleInterval: 60000 }
    );

    // Keep a stable callback identity to avoid effect-triggered refresh loops in consumers.
    const refreshDashboard = useCallback(() => {
        if (!enabled) {
            return;
        }
        void mMutate();
        void cMutate();
        void sMutate();
        void hMutate();
    }, [enabled, mMutate, cMutate, sMutate, hMutate]);

    const value = useMemo(() => {
        const hasLiveMetrics = Boolean(
            metrics && ((metrics.total_trades ?? 0) > 0 || (metrics.unrealized_pnl ?? 0) !== 0 || (metrics.total_pnl ?? 0) !== 0)
        );

        const dashboard: DashboardState = {
            metrics: metrics as MetricData,
            curve: (Array.isArray(curve) ? curve : []) as EquityPoint[],
            signals: (Array.isArray(signals) ? signals.slice(0, 5) : []) as Signal[],
            health: health as SystemHealth,
            dataSource: !enabled ? 'FALLBACK' : mLoading ? 'LOADING' : (hasLiveMetrics ? 'LIVE' : 'FALLBACK'),
            loading: enabled && (mLoading || cLoading || sLoading || hLoading),
            error: enabled && (mErr || cErr || sErr || hErr) ? 'Dashboard stream degraded' : null,
            portfolioId: activePortfolioId,
            // Keep SSR/CSR initial render deterministic; sidebar sync badge uses backend timestamps.
            lastSync: null
        };

        return {
            dashboard,
            dashboardLoading: dashboard.loading,
            dashboardUpdatedAt:
                extractSyncTimestamp(metrics) ??
                extractSyncTimestamp(curve) ??
                extractSyncTimestamp(signals) ??
                extractSyncTimestamp(health),
            refreshDashboard
        };
    }, [enabled, metrics, curve, signals, health, mLoading, cLoading, sLoading, hLoading, mErr, cErr, sErr, hErr, activePortfolioId, refreshDashboard]);

    return (
        <DashboardDataContext.Provider value={value}>
            {children}
        </DashboardDataContext.Provider>
    );
}

export function useDashboardData() {
    const context = useContext(DashboardDataContext);
    if (context === undefined) {
        throw new Error('useDashboardData must be used within a DashboardProvider');
    }
    return context;
}
