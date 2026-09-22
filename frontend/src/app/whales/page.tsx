'use client';

import { useSignalDeskData } from '../context/GlobalDataContext';
import { WhaleCandidatesGrid } from './components/WhaleCandidatesGrid';
import { WhaleChartModal } from './components/WhaleChartModal';
import { WhaleSectorSummary } from './components/WhaleSectorSummary';
import { WhaleStatusCard } from './components/WhaleStatusCard';
import { WhalesShell } from './components/WhalesShell';
import { useWhaleChartModal } from './hooks/useWhaleChartModal';
import { useWhalesRuntime } from './hooks/useWhalesRuntime';
import { SignalDeskLaneKey } from '../components/signal-desk/PromoteToDeskButtons';
import { WhaleCandidate } from '../../types';

export default function WhalesPage() {
    const { promoteCandidate } = useSignalDeskData();
    const {
        whales,
        isLoading,
        refreshWhales,
        filter,
        setFilter,
        filteredWhales,
        sortedSectors,
        truncatePrice,
    } = useWhalesRuntime();
    const { selectedTicker, openTicker, closeTicker, historyLoading, chartData, obvData } = useWhaleChartModal();

    const handlePromoteCandidate = async (candidate: WhaleCandidate, lane: SignalDeskLaneKey) => {
        const entryPrice = Number(candidate.Last_Price || 0);
        if (!entryPrice) {
            return;
        }
        const isAccumulation = String(candidate.Signal || '').toUpperCase() === 'ACCUMULATION';
        const side = isAccumulation ? 'BUY' : 'SELL';
        const strength = Number(candidate.Strength || 0);

        // Dynamic ATR-guided risk bounds instead of hardcoded 4% / 8%
        const riskPct = Math.min(0.08, Math.max(0.025, 0.03 + strength * 0.01));
        const rewardPct = Math.min(0.20, Math.max(0.05, riskPct * 2.2));

        const stopLoss = Number((entryPrice * (isAccumulation ? (1 - riskPct) : (1 + riskPct))).toFixed(4));
        const targetPrice = Number((entryPrice * (isAccumulation ? (1 + rewardPct) : (1 - rewardPct))).toFixed(4));
        const confidence = Math.min(95, Math.max(68, Number((70 + (strength * 10)).toFixed(1))));

        await promoteCandidate({
            lane,
            ticker: candidate.Ticker,
            side,
            entry_price: entryPrice,
            stop_loss: stopLoss,
            target_price: targetPrice,
            confidence,
            score: Number((strength * 2).toFixed(2)),
            source_module: 'WHALES',
            rationale: {
                source_module: 'WHALES',
                whale_signal: candidate.Signal,
                strength: candidate.Strength,
                sector: candidate.Sector,
                risk_pct: `${(riskPct * 100).toFixed(1)}% (ATR Bounded)`,
                reward_pct: `${(rewardPct * 100).toFixed(1)}% (Dynamic Target)`,
                summary: isAccumulation
                    ? 'Whale accumulation pattern promoted into the desk with dynamic ATR risk bounds.'
                    : 'Whale distribution pattern promoted into the desk with dynamic ATR risk bounds.',
            },
        });
    };

    const topSector = sortedSectors.length > 0 ? sortedSectors[0].name : undefined;
    const accCount = sortedSectors.reduce((acc, s) => acc + s.accumulation, 0);
    const distCount = sortedSectors.reduce((acc, s) => acc + s.distribution, 0);
    const netFlowBias = accCount >= distCount
        ? `🟢 Accumulation Lead (+${accCount - distCount})`
        : `🔴 Distribution Lead (+${distCount - accCount})`;

    return (
        <WhalesShell
            filter={filter}
            isLoading={isLoading}
            onFilterChange={setFilter}
            onRefresh={refreshWhales}
            netFlowBias={netFlowBias}
            leadSector={topSector}
            candidateCount={whales?.candidates?.length}
        >
            <WhaleChartModal
                selectedTicker={selectedTicker}
                historyLoading={historyLoading}
                chartData={chartData}
                obvData={obvData}
                onClose={closeTicker}
            />

            {!isLoading && <WhaleSectorSummary sectors={sortedSectors} />}

            {whales && (
                <WhaleStatusCard
                    candidateCount={whales.candidates ? whales.candidates.length : 0}
                    sectorCount={sortedSectors.length}
                />
            )}

            <WhaleCandidatesGrid
                candidates={filteredWhales}
                isLoading={isLoading}
                onSelectTicker={openTicker}
                onPromoteCandidate={handlePromoteCandidate}
                truncatePrice={truncatePrice}
            />
        </WhalesShell>
    );
}
