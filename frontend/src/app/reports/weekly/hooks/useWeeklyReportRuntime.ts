'use client';

import { useCallback, useEffect, useState } from 'react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';

import {
    analysisResponseSchema,
    AnalysisResponse,
    getWeeklyReportFailed,
    getWeeklyReportKeyShifts,
    getWeeklyReportMarketSummary,
    getWeeklyReportNotes,
    getWeeklyReportRecommendations,
    getWeeklyReportSignalReview,
    getWeeklyReportWarnings,
    getWeeklyReportWorked,
    getWeeklyReportCacheInfo,
    ReportPeriod,
} from '../lib/weeklyReportTransforms';

export function useWeeklyReportRuntime() {
    const [period, setPeriod] = useState<ReportPeriod>('weekly');
    const [data, setData] = useState<AnalysisResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [feedback, setFeedback] = useState('');

    const loadReport = useCallback(
        async (forceRefresh = false, selectedPeriod: ReportPeriod = period) => {
            setLoading(true);
            setError('');

            try {
                const res = await apiFetch(
                    `/reports/analysis?period=${selectedPeriod}${forceRefresh ? '&force_refresh=true' : ''}`,
                );
                const json = await readJsonSafe<unknown>(res);

                if (!res.ok) {
                    throw new Error(pickApiMessage(json, 'Failed to load analysis report.'));
                }

                const parsed = analysisResponseSchema.safeParse(json);
                if (!parsed.success) {
                    console.warn('[AnalysisReport] Schema validation warnings:', parsed.error.flatten());
                }
                setData(parsed.success ? parsed.data : json as AnalysisResponse);
            } catch (err: unknown) {
                const message = err instanceof Error ? err.message : 'Failed to load analysis report.';
                setError(message);
                setData(null);
            } finally {
                setLoading(false);
            }
        },
        [period],
    );

    useEffect(() => {
        void loadReport(false, period);
    }, [loadReport, period]);

    return {
        period,
        setPeriod,
        data,
        loading,
        error,
        setError,
        feedback,
        setFeedback,
        loadReport,
        market: getWeeklyReportMarketSummary(data),
        review: getWeeklyReportSignalReview(data),
        keyShifts: getWeeklyReportKeyShifts(data),
        worked: getWeeklyReportWorked(data),
        failed: getWeeklyReportFailed(data),
        warnings: getWeeklyReportWarnings(data),
        notes: getWeeklyReportNotes(data),
        recommendations: getWeeklyReportRecommendations(data),
        cacheInfo: getWeeklyReportCacheInfo(data),
    };
}
