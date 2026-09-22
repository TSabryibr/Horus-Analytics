/**
 * Runtime hook for the Arbitrage page.
 * Manages arbitrage fetch state, filter state, and execute action side-effects.
 */

import { useEffect, useState } from 'react';
import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';
import { filterMirrors } from '../lib/arbitrageTransforms';

export type ActionStatus = {
    id: number;
    msg: string;
    type: 'success' | 'error';
} | null;

export type ArbitrageUniverse = 'default' | 'extended';

type ArbitragePayload = {
    mirrors?: any[];
};

export function useArbitrageRuntime() {
    const [arbitrage, setArbitrage] = useState<ArbitragePayload | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [universe, setUniverse] = useState<ArbitrageUniverse>('default');
    const [refreshKey, setRefreshKey] = useState(0);
    const [filter, setFilter] = useState('');
    const [executing, setExecuting] = useState<Record<number, boolean>>({});
    const [actionStatus, setActionStatus] = useState<ActionStatus>(null);

    useEffect(() => {
        let cancelled = false;

        async function loadArbitrage() {
            setIsLoading(true);
            try {
                const endpoint = universe === 'extended'
                    ? '/api/v1/arbitrage?universe=extended'
                    : '/api/v1/arbitrage';
                const res = await apiFetch(endpoint);
                const data = await readJsonSafe<ArbitragePayload>(res);
                if (!res.ok) {
                    throw new Error(pickApiMessage(data, 'Failed to load arbitrage scan'));
                }
                if (!cancelled) {
                    setArbitrage(data || { mirrors: [] });
                }
            } catch {
                if (!cancelled) {
                    setArbitrage({ mirrors: [] });
                }
            } finally {
                if (!cancelled) {
                    setIsLoading(false);
                }
            }
        }

        loadArbitrage();

        return () => {
            cancelled = true;
        };
    }, [refreshKey, universe]);

    const filteredMirrors = filterMirrors(arbitrage?.mirrors || [], filter);

    const handleExecute = async (mirror: any, idx: number) => {
        setExecuting(prev => ({ ...prev, [idx]: true }));
        setActionStatus(null);
        try {
            const payload = {
                leader: mirror.Leader,
                follower: mirror.Follower,
                type: mirror.Type,
                z_score: mirror.ZScore || 0,
                stop_loss_pct: mirror.StopLossPct || 1.5,
                take_profit_pct: mirror.TakeProfitPct || 2.5,
            };

            const res = await fetch('/api/v1/execute-arbitrage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await res.json();
            if (res.ok) {
                setActionStatus({
                    id: idx,
                    msg: data.message || `Executed spread on ${mirror.Follower}`,
                    type: 'success',
                });
            } else {
                setActionStatus({ id: idx, msg: data.detail || 'Execution failed', type: 'error' });
            }
        } catch (err: any) {
            setActionStatus({ id: idx, msg: err.message || 'Network error', type: 'error' });
        } finally {
            setExecuting(prev => ({ ...prev, [idx]: false }));
            setTimeout(() => setActionStatus(null), 5000);
        }
    };

    return {
        isLoading,
        universe,
        setUniverse,
        filter,
        setFilter,
        filteredMirrors,
        executing,
        actionStatus,
        onRefresh: () => setRefreshKey((current) => current + 1),
        onExecute: handleExecute,
    };
}
