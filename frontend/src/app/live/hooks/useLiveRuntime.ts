'use client';

import { useMemo } from 'react';
import { useLiveContext, type Candle } from '../../context/LiveContext';

export type { Candle };

const compressCandles = (candles: Candle[], maxPoints = 180): Candle[] => {
    if (candles.length <= maxPoints) return candles;
    const stride = Math.ceil(candles.length / maxPoints);
    const reduced: Candle[] = [];
    for (let i = 0; i < candles.length; i += stride) {
        reduced.push(candles[i]);
    }
    const last = candles[candles.length - 1];
    if (reduced[reduced.length - 1]?.Date !== last.Date) {
        reduced.push(last);
    }
    return reduced;
};

export function useLiveRuntime() {
    const {
        ticker,
        setTicker,
        tickers,
        candleData,
        loading,
        refreshing,
        error,
        setError,
        lastUpdate,
        fetchIntradayData,
    } = useLiveContext();

    // Full-fidelity candle data rendered via hardware-accelerated Canvas API (no lossy stride compression)
    const data = useMemo(() => candleData, [candleData]);

    return {
        ticker,
        setTicker,
        tickers,
        data,
        loading,
        refreshing,
        error,
        setError,
        lastUpdate,
        fetchData: fetchIntradayData,
    };
}
