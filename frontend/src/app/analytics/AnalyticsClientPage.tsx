'use client';

import { useSignalDeskData } from '../context/GlobalDataContext';
import { AnalyticsFilters } from './components/AnalyticsFilters';
import { AnalyticsShell } from './components/AnalyticsShell';
import { AnalyticsTable } from './components/AnalyticsTable';
import { useAnalyticsActions } from './hooks/useAnalyticsActions';
import { useAnalyticsRuntime } from './hooks/useAnalyticsRuntime';
import { SignalDeskLaneKey } from '../components/signal-desk/PromoteToDeskButtons';
import { AnalyticsItem } from '@/types';

export default function AnalyticsClientPage() {
    const { promoteCandidate } = useSignalDeskData();
    const {
        columns,
        data,
        fetchData,
        filterStatus,
        formattedLastUpdated,
        lastUpdated,
        loading,
        minScore,
        requestSort,
        search,
        setFilterStatus,
        setLastUpdated,
        setMinScore,
        setSearch,
        setShowColMenu,
        setStatus,
        showColMenu,
        sortedData,
        status,
        toggleColumn,
    } = useAnalyticsRuntime();
    const { handleBroadcast, runScan } = useAnalyticsActions({
        fetchData,
        setLastUpdated,
        setStatus,
    });

    const handlePromoteCandidate = async (item: AnalyticsItem, lane: SignalDeskLaneKey) => {
        const entryPrice = Number(item.Price || 0);
        if (!entryPrice) {
            return;
        }
        const side = String(item.Trend || '').toUpperCase() === 'BEARISH' ? 'SELL' : 'BUY';

        // Enforce a solid 2.2x Risk:Reward ratio on fallback stop/target calculations
        const fallbackStopPct = 0.04; // 4.0% stop loss
        const fallbackRewardPct = 0.088; // 8.8% target (2.2x R:R ratio)

        const stopLoss = Number(item.Stop_Loss || (side === 'BUY' ? entryPrice * (1 - fallbackStopPct) : entryPrice * (1 + fallbackStopPct)));
        const targetPrice = Number(item.Target_1 || (side === 'BUY' ? entryPrice * (1 + fallbackRewardPct) : entryPrice * (1 - fallbackRewardPct)));

        await promoteCandidate({
            lane,
            ticker: item.Ticker,
            side,
            entry_price: entryPrice,
            stop_loss: stopLoss,
            target_price: targetPrice,
            confidence: Math.min(96, Math.max(65, Number((60 + (Number(item.Signal_Score || 0) * 4)).toFixed(1)))),
            score: Number(item.Signal_Score || 0),
            source_module: 'ANALYTICS',
            rationale: {
                source_module: 'ANALYTICS',
                status: item.Status,
                trend: item.Trend,
                rsi: item.RSI,
                target_2: item.Target_2,
                risk_reward_ratio: item.Risk_Reward_Ratio || '2.2x (Enforced Fallback)',
                summary: 'Analytics matrix candidate promoted into the desk with enforced Risk:Reward structure.',
            },
        });
    };

    const bullCount = data.filter((item) => String(item.Trend || '').toUpperCase() === 'BULLISH' || String(item.Status || '').includes('BUY')).length;
    const bearCount = data.filter((item) => String(item.Trend || '').toUpperCase() === 'BEARISH' || String(item.Status || '').includes('SELL')).length;
    const highConvictionCount = data.filter((item) => Number(item.Signal_Score || 0) >= 8.0).length;

    return (
        <AnalyticsShell
            dataCount={data.length}
            isScanning={status === 'RUNNING'}
            lastUpdatedLabel={formattedLastUpdated || lastUpdated}
            onRunScan={runScan}
            bullCount={bullCount}
            bearCount={bearCount}
            highConvictionCount={highConvictionCount}
        >
            <AnalyticsFilters
                columns={columns}
                filterStatus={filterStatus}
                minScore={minScore}
                search={search}
                setFilterStatus={setFilterStatus}
                setMinScore={setMinScore}
                setSearch={setSearch}
                setShowColMenu={setShowColMenu}
                showColMenu={showColMenu}
                toggleColumn={toggleColumn}
            />

            <AnalyticsTable
                columns={columns}
                loading={loading}
                onBroadcast={handleBroadcast}
                onPromoteCandidate={handlePromoteCandidate}
                onRequestSort={requestSort}
                rows={sortedData}
            />
        </AnalyticsShell>
    );
}
