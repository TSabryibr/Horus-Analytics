'use client';

import { useSeasonalityRuntime } from './hooks/useSeasonalityRuntime';
import { getCurrentMonthLabel } from './lib/seasonalityTransforms';
import { SeasonalityShell } from './components/SeasonalityShell';
import { SeasonalityLeadersTable } from './components/SeasonalityLeadersTable';
import { SeasonalityVerdictCard } from './components/SeasonalityVerdictCard';
import { SeasonalityMonthlyGrid } from './components/SeasonalityMonthlyGrid';

export default function SeasonalityPage() {
    const {
        marketStats,
        tickerStats,
        loadingMarket,
        loadingTicker,
        searchTicker,
        setSearchTicker,
        handleRefresh,
        handleSearch,
        fetchTickerStats,
    } = useSeasonalityRuntime();

    const currentMonthLabel = getCurrentMonthLabel();

    const activeWinRate = tickerStats?.overall_win_rate ?? marketStats?.top_historical_performers?.[0]?.win_rate;
    const activeBias = activeWinRate !== undefined ? `${activeWinRate}% ${activeWinRate >= 50 ? 'Bullish' : 'Bearish'}` : undefined;

    const onTickerClick = (ticker: string) => {
        setSearchTicker(ticker);
        fetchTickerStats(ticker);
    };

    return (
        <SeasonalityShell
            searchTicker={searchTicker}
            onSearchChange={setSearchTicker}
            onSearch={handleSearch}
            onRefresh={handleRefresh}
            loading={loadingMarket || loadingTicker}
            currentMonthLabel={currentMonthLabel}
            activeBias={activeBias}
        >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <SeasonalityLeadersTable
                    performers={marketStats?.top_historical_performers}
                    loading={loadingMarket}
                    currentMonthLabel={currentMonthLabel}
                    onTickerClick={onTickerClick}
                />
                <SeasonalityVerdictCard
                    tickerStats={tickerStats}
                    loading={loadingTicker}
                />
            </div>

            {tickerStats && (
                <div className="mt-6">
                    <SeasonalityMonthlyGrid
                        months={tickerStats.months}
                        ticker={tickerStats.ticker}
                    />
                </div>
            )}
        </SeasonalityShell>
    );
}
