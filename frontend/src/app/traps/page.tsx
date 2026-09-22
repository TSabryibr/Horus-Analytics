'use client';

import { useState, useEffect } from 'react';
import { useSignalDeskData, usePortfolioData } from '../context/GlobalDataContext';
import { useTrapsRuntime } from './hooks/useTrapsRuntime';
import { TrapsShell } from './components/TrapsShell';
import { TrapsEmptyBanner } from './components/TrapsEmptyBanner';
import { TrapCategoryList } from './components/TrapCategoryList';
import { SignalDeskLaneKey } from '../components/signal-desk/PromoteToDeskButtons';
import { Trap } from '../../types';
import { apiFetch, readJsonSafe } from '@/lib/api';

export default function TrapsPage() {
    const { promoteCandidate } = useSignalDeskData();
    const { activePortfolioId } = usePortfolioData();
    const [heldTickers, setHeldTickers] = useState<Set<string>>(new Set());
    const { 
        bullTraps, 
        bearTraps, 
        isLoading, 
        hasAnyTraps, 
        onRefresh 
    } = useTrapsRuntime();

    useEffect(() => {
        let mounted = true;
        async function fetchHeldPositions() {
            if (!activePortfolioId) return;
            try {
                const res = await apiFetch(`/api/v1/portfolio?portfolio_id=${activePortfolioId}`);
                if (!res.ok) return;
                const json = await readJsonSafe<{ status: string; positions?: Array<{ ticker?: string; Ticker?: string }> }>(res);
                if (json?.status === 'active' && Array.isArray(json.positions)) {
                    const tickers = new Set<string>(
                        json.positions.map((p) => String(p.ticker || p.Ticker || '')).filter(Boolean)
                    );
                    if (mounted) setHeldTickers(tickers);
                }
            } catch {
                // Ignore network errors in polling
            }
        }
        fetchHeldPositions();
        return () => { mounted = false; };
    }, [activePortfolioId]);

    const handlePromoteTrap = async (trapType: 'bull' | 'bear', item: Trap, lane: SignalDeskLaneKey) => {
        const entryPrice = Number(item.Price || 0);
        if (!entryPrice) {
            return;
        }
        const depthPct = Math.abs(Number(item['Fakeout_Depth_%'] || 0));
        const inferredSide = trapType === 'bull' ? 'SELL' : 'BUY';

        // ATR-bounded risk calculation capping max stop risk at 5.0%
        const riskPct = Math.min(0.05, Math.max(0.025, depthPct / 100));
        const rewardPct = Math.min(0.15, Math.max(0.04, riskPct * 2.2));

        const stopLoss = inferredSide === 'BUY'
            ? Number((entryPrice * (1 - riskPct)).toFixed(4))
            : Number((entryPrice * (1 + riskPct)).toFixed(4));
        const targetPrice = inferredSide === 'BUY'
            ? Number((entryPrice * (1 + rewardPct)).toFixed(4))
            : Number((entryPrice * (1 - rewardPct)).toFixed(4));
        const confidence = Math.min(94, Math.max(69, Number((72 + (depthPct * 4)).toFixed(1))));

        await promoteCandidate({
            lane,
            ticker: item.Ticker,
            side: inferredSide,
            entry_price: entryPrice,
            stop_loss: stopLoss,
            target_price: targetPrice,
            confidence,
            score: Number((depthPct * 2).toFixed(2)),
            source_module: 'TRAPS',
            rationale: {
                source_module: 'TRAPS',
                trap_type: inferredSide === 'BUY' ? 'BEAR_TRAP' : 'BULL_TRAP',
                fakeout_depth_pct: item['Fakeout_Depth_%'],
                risk_pct: `${(riskPct * 100).toFixed(1)}% (ATR Capped)`,
                reward_pct: `${(rewardPct * 100).toFixed(1)}% (Dynamic Target)`,
                details: item.Details,
                summary: inferredSide === 'BUY'
                    ? 'Bear-trap reversal promoted into the desk with ATR-capped risk bounds.'
                    : 'Bull-trap fade promoted into the desk with ATR-capped risk bounds.',
            },
        });
    };

    const totalTrapsCount = bullTraps.length + bearTraps.length;
    const dominantBias = bullTraps.length >= bearTraps.length
        ? `🔴 BULL TRAPS DOMINANT (${bullTraps.length}/${totalTrapsCount})`
        : `🟢 BEAR TRAPS DOMINANT (${bearTraps.length}/${totalTrapsCount})`;

    const allDepths = [...bullTraps, ...bearTraps].map((t) => Math.abs(Number(t['Fakeout_Depth_%'] || 0)));
    const maxDepth = allDepths.length > 0 ? Math.max(...allDepths) : undefined;

    return (
        <TrapsShell
            loading={isLoading}
            onRefresh={onRefresh}
            dominantBias={dominantBias}
            maxDepth={maxDepth}
            trapCount={totalTrapsCount}
        >
            {!hasAnyTraps && !isLoading && <TrapsEmptyBanner />}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-4">
                <TrapCategoryList type="bull" items={bullTraps} heldTickers={heldTickers} onPromoteCandidate={handlePromoteTrap} />
                <TrapCategoryList type="bear" items={bearTraps} heldTickers={heldTickers} onPromoteCandidate={handlePromoteTrap} />
            </div>
        </TrapsShell>
    );
}
