import { Candle } from '../hooks/useLiveRuntime';

export const toNumber = (value: unknown): number => {
    const normalized = typeof value === 'string' ? value.replace(/,/g, '') : value;
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : 0;
};

export const truncatePrice = (value: unknown, decimals: number = 3): string => {
    const parsed = toNumber(value);
    if (!Number.isFinite(parsed)) return '0.000';
    const factor = Math.pow(10, decimals);
    // Truncate instead of rounding
    const truncated = Math.trunc(parsed * factor) / factor;
    return truncated.toFixed(decimals);
};

export const formatPrice = (value: unknown): string => {
    return truncatePrice(value, 3);
};

export const calculateYDomain = (data: Candle[], hasData: boolean): [number, number] => {
    if (!hasData || data.length === 0) return [0, 1];
    const allLows = data.map((d) => d.Low);
    const allHighs = data.map((d) => d.High);
    const minLow = Math.min(...allLows);
    const maxHigh = Math.max(...allHighs);
    const range = maxHigh - minLow;
    const padding = Math.max(range * 0.1, 0.1); // Ensure minimum padding
    return [minLow - padding, maxHigh + padding];
};

export const calculateLiveMetrics = (data: Candle[], hasData: boolean) => {
    const fallback: Candle = {
        Date: '',
        Open: 0,
        High: 0,
        Low: 0,
        Close: 0,
        Volume: 0,
        timeLabel: '--:--',
        wickRange: [0, 0],
        bodyRange: [0, 0],
        isBullish: true
    };

    if (!hasData || data.length === 0) {
        return {
            lastCandle: fallback,
            priceChange: 0,
            pctChange: 0
        };
    }

    const lastCandle = data[data.length - 1];
    const prevCandle = data[data.length - 2] || lastCandle;
    const priceChange = lastCandle.Close - prevCandle.Close;
    const pctChange = prevCandle.Close !== 0 ? (priceChange / prevCandle.Close) * 100 : 0;

    return { lastCandle, priceChange, pctChange };
};

export const calculateRadarTargets = (analyticsData: any[], highConvictionItems: any[]) => {
    if (highConvictionItems.length > 0) {
        return highConvictionItems;
    }
    return [...analyticsData]
        .filter((item) => Boolean(item.Ticker))
        .sort((a, b) => toNumber(b.Signal_Score) - toNumber(a.Signal_Score))
        .slice(0, 16);
};

export type ChartTimestamp = number;

export interface ChartCandlePoint {
    time: ChartTimestamp;
    open: number;
    high: number;
    low: number;
    close: number;
}

export interface ChartVolumePoint {
    time: ChartTimestamp;
    value: number;
    color: string;
}

export const parseToUtcTimestamp = (dateStr: string): ChartTimestamp | null => {
    if (!dateStr) return null;
    const ts = Date.parse(dateStr);
    if (!Number.isNaN(ts)) {
        return Math.floor(ts / 1000);
    }
    const normalized = dateStr.replace(' ', 'T');
    const fallbackTs = Date.parse(normalized);
    if (!Number.isNaN(fallbackTs)) {
        return Math.floor(fallbackTs / 1000);
    }
    return null;
};

export const transformToChartData = (candles: Candle[]): {
    candlestickData: ChartCandlePoint[];
    volumeData: ChartVolumePoint[];
} => {
    const candlesMap = new Map<number, { candle: ChartCandlePoint; volume: ChartVolumePoint }>();

    for (const c of candles) {
        if (
            !Number.isFinite(c.Open) ||
            !Number.isFinite(c.High) ||
            !Number.isFinite(c.Low) ||
            !Number.isFinite(c.Close)
        ) {
            continue;
        }
        const time = parseToUtcTimestamp(c.Date);
        if (time === null) continue;

        const isBullish = c.Close >= c.Open;
        candlesMap.set(time, {
            candle: {
                time,
                open: c.Open,
                high: c.High,
                low: c.Low,
                close: c.Close,
            },
            volume: {
                time,
                value: Number.isFinite(c.Volume) ? Math.max(0, c.Volume) : 0,
                color: isBullish ? 'rgba(16, 185, 129, 0.45)' : 'rgba(239, 68, 68, 0.45)',
            },
        });
    }

    const sortedTimes = Array.from(candlesMap.keys()).sort((a, b) => a - b);
    const candlestickData: ChartCandlePoint[] = [];
    const volumeData: ChartVolumePoint[] = [];

    for (const t of sortedTimes) {
        const item = candlesMap.get(t);
        if (item) {
            candlestickData.push(item.candle);
            volumeData.push(item.volume);
        }
    }

    return { candlestickData, volumeData };
};

