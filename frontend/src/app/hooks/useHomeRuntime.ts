import { useEffect, useMemo, useState } from 'react';
import useSWR from 'swr';

import { swrFetcher } from '@/lib/api';

import { useDashboardData, usePortfolioData, useSignalDeskData } from '../context/GlobalDataContext';
import { groupRecentSignalsByDate, HomeArchiveEntry } from '../lib/homeTransforms';

export function useHomeRuntime() {
    const { activePortfolioId } = usePortfolioData();
    const { dashboard, refreshDashboard } = useDashboardData();
    const { desk, deskLoading, deskError, lifecycleSummary, followUpSummary, refreshDesk } = useSignalDeskData();
    const [showArchives, setShowArchives] = useState(false);

    const { data: allSignals } = useSWR(
        showArchives ? '/api/v1/scanner/history' : null,
        swrFetcher,
    );

    useEffect(() => {
        if (!activePortfolioId) {
            return;
        }

        void refreshDashboard();
        void refreshDesk();
    }, [activePortfolioId, refreshDashboard, refreshDesk]);

    const archivesByDate = useMemo(
        () => groupRecentSignalsByDate<HomeArchiveEntry>(allSignals),
        [allSignals],
    );

    const { metrics, curve, signals, health, loading, dataSource, error } = dashboard;
    const isSourceLoading = dataSource === 'LOADING' || (loading && !metrics && curve.length === 0);
    const signalDesk = {
        operatingMode: desk?.operating_mode ?? 'MANUAL',
        autopilotArmed: Boolean(desk?.autopilot_armed),
        intradayCount: desk?.lanes?.intraday?.count ?? 0,
        swingCount: desk?.lanes?.swing?.count ?? 0,
        positionCount: desk?.lanes?.position?.count ?? 0,
        failedDeliveryCount: Number(desk?.failed_delivery_count ?? 0),
        latestFailedDelivery: desk?.latest_failed_delivery ?? null,
        lifecycleSummary: {
            total: Number(lifecycleSummary?.total ?? 0),
            activeCount: Number(lifecycleSummary?.active_count ?? 0),
            ambiguousCount: Number(lifecycleSummary?.ambiguous_count ?? 0),
            openCount: Number(lifecycleSummary?.counts_by_state?.OPEN ?? 0),
            tp1Count: Number(lifecycleSummary?.counts_by_state?.TP1_HIT ?? 0),
        },
        followUps: {
            total: Number(followUpSummary?.total ?? 0),
            pendingCount: Number(followUpSummary?.pending_count ?? 0),
            readyCount: Number(followUpSummary?.ready_count ?? 0),
            failedCount: Number(followUpSummary?.failed_count ?? 0),
            suppressedCount: Number(followUpSummary?.suppressed_count ?? 0),
            stalePendingCount: Number(followUpSummary?.stale_pending_count ?? 0),
        },
        loading: deskLoading,
        error: deskError,
        desk,
    };

    return {
        activePortfolioId,
        archivesByDate,
        curve,
        dataSource,
        error,
        health,
        isSourceLoading,
        loading,
        metrics,
        refreshDashboard,
        refreshDesk,
        setShowArchives,
        signalDesk,
        showArchives,
        signals,
        hasCurve: curve.length > 0,
        hasHealth: Boolean(health && health.win_rate !== undefined),
        hasMetrics: Boolean(metrics && (metrics.total_trades > 0 || metrics.total_pnl !== 0)),
        hasSignals: signals.length > 0,
    };
}
