import { useState } from 'react';

import { apiFetch, readJsonSafe } from '@/lib/api';

type UseOracleActionsArgs = {
    aiReport: any;
    refreshOracle: () => void;
    refreshOracleNoCache: () => void;
    refreshOracleWithProvider: (provider: 'OLLAMA') => void;
};

export function useOracleActions({
    aiReport,
    refreshOracle,
    refreshOracleNoCache,
    refreshOracleWithProvider,
}: UseOracleActionsArgs) {
    const [broadcastingReport, setBroadcastingReport] = useState(false);
    const [broadcastFeedback, setBroadcastFeedback] = useState<string | null>(null);

    const handleRefresh = () => {
        refreshOracle();
    };

    const handleRefreshNoCache = () => {
        refreshOracleNoCache();
    };

    const handleRefreshWithProvider = (provider: 'OLLAMA') => {
        refreshOracleWithProvider(provider);
    };

    const handleBroadcastAiReport = async () => {
        if (!aiReport || broadcastingReport) return;
        setBroadcastingReport(true);
        setBroadcastFeedback(null);
        try {
            const res = await apiFetch('/api/v1/ai/daily-report/broadcast', {
                method: 'POST',
                body: JSON.stringify({
                    force_refresh: false,
                    use_llm: true,
                }),
            });
            const body = await readJsonSafe<any>(res);
            if (res.ok && body?.status === 'sent') {
                setBroadcastFeedback('AI daily report broadcast sent to Telegram.');
            } else {
                setBroadcastFeedback(String(body?.detail || body?.message || 'Broadcast failed.'));
            }
        } catch {
            setBroadcastFeedback('Network error while broadcasting AI report.');
        } finally {
            setBroadcastingReport(false);
        }
    };

    return {
        broadcastingReport,
        broadcastFeedback,
        handleRefresh,
        handleRefreshNoCache,
        handleRefreshWithProvider,
        handleBroadcastAiReport,
    };
}
