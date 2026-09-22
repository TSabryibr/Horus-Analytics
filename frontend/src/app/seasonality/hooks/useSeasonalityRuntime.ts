import { useState, useEffect, useCallback } from 'react';
import { getBaseUrl, isIgnorableNetworkError } from '@/lib/api';

export interface MarketStats {
    top_historical_performers: Array<{
        ticker: string;
        avg_return: number;
        win_rate: number;
        best_month: string;
    }>;
    status: string;
}

export interface TickerMonth {
    label: string;
    average_return: number;
    win_rate: number;
    count: number;
}

export interface TickerStats {
    ticker: string;
    status: string;
    overall_win_rate?: number;
    verdict: {
        best_month: string;
        worst_month: string;
        summary: string;
    };
    months: TickerMonth[];
}

export function useSeasonalityRuntime(initialSearchTicker = 'COMI') {
    const [marketStats, setMarketStats] = useState<MarketStats | null>(null);
    const [tickerStats, setTickerStats] = useState<TickerStats | null>(null);
    const [loadingMarket, setLoadingMarket] = useState(true);
    const [loadingTicker, setLoadingTicker] = useState(false);
    const [searchTicker, setSearchTicker] = useState(initialSearchTicker);

    const API_URL = getBaseUrl();

    const fetchMarketStats = useCallback(async () => {
        setLoadingMarket(true);
        try {
            const res = await fetch(`${API_URL}/api/v1/seasonality/market`);
            const json = await res.json();
            if (json.status === 'success') {
                setMarketStats(json);
            }
        } catch (e) {
            if (!isIgnorableNetworkError(e)) {
                console.error(e);
            }
        } finally {
            setLoadingMarket(false);
        }
    }, [API_URL]);

    const fetchTickerStats = useCallback(async (t: string) => {
        if (!t) return;
        setLoadingTicker(true);
        try {
            const res = await fetch(`${API_URL}/api/v1/seasonality?ticker=${t.toUpperCase()}`);
            const json = await res.json();
            if (json.status === 'success') {
                setTickerStats(json);
            } else {
                setTickerStats(null);
            }
        } catch (e) {
            if (!isIgnorableNetworkError(e)) {
                console.error(e);
            }
            setTickerStats(null);
        } finally {
            setLoadingTicker(false);
        }
    }, [API_URL]);

    const handleRefresh = useCallback(() => {
        fetchMarketStats();
        fetchTickerStats(searchTicker);
    }, [fetchMarketStats, fetchTickerStats, searchTicker]);

    const handleSearch = useCallback((t?: string) => {
        const target = t || searchTicker;
        fetchTickerStats(target);
    }, [fetchTickerStats, searchTicker]);

    useEffect(() => {
        fetchMarketStats();
        fetchTickerStats(searchTicker);
    }, []); // Only on mount

    return {
        marketStats,
        tickerStats,
        loadingMarket,
        loadingTicker,
        searchTicker,
        setSearchTicker,
        handleRefresh,
        handleSearch,
        fetchTickerStats, // Exposed for table row clicks
    };
}
