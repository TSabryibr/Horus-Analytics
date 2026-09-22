'use client';

import { useState } from 'react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';

import { ReportPeriod } from '../lib/weeklyReportTransforms';

type UseWeeklyReportActionsOptions = {
    period: ReportPeriod;
    loadReport: (forceRefresh?: boolean, selectedPeriod?: ReportPeriod) => Promise<void>;
    setFeedback: (message: string) => void;
};

export function useWeeklyReportActions({
    period,
    loadReport,
    setFeedback,
}: UseWeeklyReportActionsOptions) {
    const [broadcasting, setBroadcasting] = useState(false);

    const broadcastReport = async () => {
        setBroadcasting(true);
        setFeedback('');

        try {
            const res = await apiFetch('/reports/analysis/broadcast', {
                method: 'POST',
                body: JSON.stringify({ period, force_refresh: true }),
            });
            const json = await readJsonSafe<unknown>(res);

            if (!res.ok) {
                throw new Error(pickApiMessage(json, 'Broadcast failed.'));
            }

            setFeedback(`${period === 'weekly' ? 'Weekly' : 'Monthly'} report broadcast sent to Telegram.`);
            await loadReport(true, period);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Broadcast failed.';
            setFeedback(message);
        } finally {
            setBroadcasting(false);
        }
    };

    return {
        broadcasting,
        broadcastReport,
    };
}
