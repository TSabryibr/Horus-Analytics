import { useState, useEffect, useMemo, useCallback } from 'react';
import { usePolling } from '@/hooks/usePolling';
import { useLiveRuntime } from './useLiveRuntime';
import { useLiveAnalytics } from './useLiveAnalytics';
import { useLiveControls } from './useLiveControls';
import { useSovereignAlerts } from './useSovereignAlerts';
import { calculateRadarTargets, calculateYDomain, calculateLiveMetrics, formatPrice, truncatePrice } from '../lib/liveTransforms';

const POLL_OPTIONS = [5000, 15000, 30000, 60000];

export function useLiveDashboard() {
    const {
        ticker, setTicker, tickers, data, loading, refreshing, error, setError, lastUpdate, fetchData,
    } = useLiveRuntime();
    const { analyticsData, analyticsLoading, fetchAnalytics } = useLiveAnalytics();
    
    const [showRadar, setShowRadar] = useState(false);
    const [isMounted, setIsMounted] = useState(false);
    const [autoRefreshMs, setAutoRefreshMs] = useState(15000);
    const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
    
    const { sovereignAlerts, dismissSovereignAlert, wsConnected } = useSovereignAlerts();

    const {
        liveStatus,
        liveRunning,
        marketOpen,
        liveLastUpdate,
        handleLiveFeedAction,
    } = useLiveControls({
        onSetError: setError,
        onEnableAutoRefresh: () => setAutoRefreshEnabled(true),
        onStartSuccess: () => void fetchData('background'),
    });

    useEffect(() => {
        setIsMounted(true);
    }, []);

    // NOTE: Redundant fetchLiveStatus removed as it's now handled by global LiveContext polling.

    usePolling(
        () => {
            if (!loading && liveRunning) {
                void fetchData('background');
            }
        },
        {
            intervalMs: autoRefreshMs,
            enabled: autoRefreshEnabled && liveStatus?.market_open !== false,
            runImmediately: false,
            // Keep fetching even if page is hidden to ensure data is "fresh" on return
            pauseWhenHidden: false 
        }
    );

    const hasData = data.length > 0;

    const highConvictionItems = useMemo(
        () => analyticsData.filter((item) => item.Status?.toUpperCase().includes('HIGH CONVICTION')),
        [analyticsData]
    );

    const radarItems = useMemo(
        () => calculateRadarTargets(analyticsData, highConvictionItems),
        [analyticsData, highConvictionItems]
    );

    const yDomain = useMemo(() => calculateYDomain(data, hasData), [data, hasData]);
    const metrics = useMemo(() => calculateLiveMetrics(data, hasData), [data, hasData]);
    const pollLabel = autoRefreshMs >= 60000 ? `${autoRefreshMs / 60000}m` : `${autoRefreshMs / 1000}s`;

    const handleToggleRadar = useCallback(() => {
        setShowRadar(prev => {
            const next = !prev;
            if (next && radarItems.length === 0 && !analyticsLoading) {
                void fetchAnalytics();
            }
            return next;
        });
    }, [radarItems.length, analyticsLoading, fetchAnalytics]);

    const handleSelectTicker = useCallback((nextTicker: string) => {
        setTicker(nextTicker);
        setShowRadar(false);
    }, [setTicker]);

    return {
        shellProps: {
            lastUpdate,
            liveRunning,
            marketOpen,
            pollOptions: POLL_OPTIONS,
            autoRefreshMs,
            autoRefreshEnabled,
            ticker,
            tickers,
            radarCount: radarItems.length,
            showRadar,
            refreshing,
            wsConnected,
            error,
            sovereignAlerts,
            onToggleRadar: handleToggleRadar,
            onChangeTicker: setTicker,
            onChangeAutoRefreshMs: setAutoRefreshMs,
            onToggleAutoRefresh: () => setAutoRefreshEnabled(prev => !prev),
            onRefresh: () => void fetchData('background'),
            onToggleLiveFeed: () => void handleLiveFeedAction(liveRunning ? 'stop' : 'start'),
            onDismissSovereignAlert: dismissSovereignAlert,
        },
        analyticsProps: {
            showRadar,
            analyticsLoading,
            radarItems: radarItems.map((item) => ({
                Ticker: item.Ticker,
                Signal_Score: item.Signal_Score,
                Price: formatPrice(item.Price ?? 0),
                Risk_Reward_Ratio: item.Risk_Reward_Ratio ?? '-',
                Resistance_20D: truncatePrice(item.Resistance_20D ?? 0),
                Key_Resistance_1: truncatePrice(item.Key_Resistance_1 ?? 0),
            })),
            onSelectTicker: handleSelectTicker,
        },
        statusProps: {
            lastPrice: truncatePrice(metrics.lastCandle.Close),
            pctChange: metrics.pctChange.toFixed(2),
            priceChangePositive: metrics.priceChange >= 0,
            volumeLabel: Math.round(metrics.lastCandle.Volume).toLocaleString(),
            liveRunning,
            marketOpen,
            pollLabel,
            liveLastUpdate,
        },
        chartProps: {
            ticker,
            data,
            isMounted,
            hasData,
            loading,
            refreshing,
            yDomain,
        }
    };
}
