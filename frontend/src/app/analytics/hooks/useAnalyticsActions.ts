import { AnalyticsItem } from '@/types';
import { apiFetch, readJsonSafe } from '@/lib/api';

import { AnalyticsStatusResponse } from '../lib/analyticsTransforms';

interface UseAnalyticsActionsOptions {
    fetchData: () => Promise<void>;
    setStatus: (value: string) => void;
    setLastUpdated: (value: string) => void;
    pollDelayMs?: number;
    pollTimeoutMs?: number;
}

export function useAnalyticsActions({
    fetchData,
    setStatus,
    setLastUpdated,
    pollDelayMs = 2500,
    pollTimeoutMs = 150000,
}: UseAnalyticsActionsOptions) {
    const waitForScanCompletion = async (scanId: string | null) => {
        const startedAt = Date.now();
        while (Date.now() - startedAt < pollTimeoutMs) {
            await new Promise((resolve) => window.setTimeout(resolve, pollDelayMs));
            try {
                const res = await apiFetch('/api/v1/analytics/status', { cache: 'no-store' });
                if (!res.ok) continue;
                const json = await readJsonSafe<AnalyticsStatusResponse>(res);
                if (json.status) setStatus(json.status);
                if (json.last_updated) setLastUpdated(json.last_updated);
                if (json.status === 'ERROR') return;
                const sameScan = !scanId || !json.scan_id || json.scan_id === scanId;
                if (sameScan && json.status !== 'RUNNING') return;
            } catch {
                // Keep polling on transient errors.
            }
        }
    };

    const runScan = async () => {
        try {
            const res = await apiFetch('/api/v1/analytics/refresh', { method: 'POST' });
            if (!res.ok) {
                throw new Error(`Refresh failed: HTTP ${res.status}`);
            }
            const refresh = await readJsonSafe<AnalyticsStatusResponse>(res);
            setStatus(refresh.status || 'RUNNING');
            await waitForScanCompletion(refresh.scan_id || null);
            await fetchData();
        } catch (error) {
            console.error('Analytics Refresh Trigger Error:', error);
        }
    };

    const handleBroadcast = async (item: AnalyticsItem) => {
        try {
            const res = await apiFetch('/api/v1/telegram/signal-card', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker: item.Ticker,
                    entry: item.Price,
                    sl: item.Stop_Loss || (item.Price * 0.95),
                    tp1: item.Target_1 || (item.Price * 1.04),
                    tp2: item.Target_2,
                    score: item.Signal_Score,
                    rsi: item.RSI,
                    volume_x: item.Rel_Volume,
                    confirmation: item.Status,
                }),
            });

            if (res.ok) {
                alert(`✅ Successfully broadcasted ${item.Ticker} to Telegram.`);
            } else {
                const err = await readJsonSafe<{ detail?: string }>(res);
                alert(`❌ Failed to broadcast: ${err.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Broadcast Error:', error);
            alert('❌ Network Error while broadcasting.');
        }
    };

    return {
        handleBroadcast,
        runScan,
    };
}
