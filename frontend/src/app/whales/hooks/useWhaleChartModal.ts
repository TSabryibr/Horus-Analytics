'use client';

import { useMemo, useState } from 'react';
import useSWR from 'swr';

import { swrFetcher } from '@/lib/api';

interface WhaleHistoryPoint {
    Date: string;
    Open: number;
    High: number;
    Low: number;
    Close: number;
    OBV: number;
}

export function useWhaleChartModal(initialTicker: string | null = null) {
    const [selectedTicker, setSelectedTicker] = useState<string | null>(initialTicker);

    const historyKey = selectedTicker ? `/api/v1/data/ticker/${selectedTicker}?limit=100&obv=true` : null;
    const { data: rawHistory, isLoading: historyLoading } = useSWR<WhaleHistoryPoint[]>(historyKey, swrFetcher);

    const chartData = useMemo(
        () =>
            rawHistory?.map((point) => ({
                time: point.Date.split(' ')[0],
                open: point.Open,
                high: point.High,
                low: point.Low,
                close: point.Close,
            })) ?? [],
        [rawHistory],
    );

    const obvData = useMemo(
        () =>
            rawHistory?.map((point) => ({
                time: point.Date.split(' ')[0],
                value: point.OBV,
            })) ?? [],
        [rawHistory],
    );

    return {
        selectedTicker,
        openTicker: setSelectedTicker,
        closeTicker: () => setSelectedTicker(null),
        historyLoading,
        chartData,
        obvData,
    };
}
