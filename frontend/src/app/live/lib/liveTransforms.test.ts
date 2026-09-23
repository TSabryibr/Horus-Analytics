import {
    toNumber,
    truncatePrice,
    formatPrice,
    calculateYDomain,
    calculateLiveMetrics,
    calculateRadarTargets,
    parseToUtcTimestamp,
    transformToChartData,
} from './liveTransforms';
import { Candle } from '../hooks/useLiveRuntime';

describe('liveTransforms', () => {
    describe('toNumber', () => {
        it('strips commas and converts dynamically', () => {
            expect(toNumber('1,000.50')).toBe(1000.5);
            expect(toNumber(100.25)).toBe(100.25);
            expect(toNumber('invalid')).toBe(0);
        });
    });

    describe('truncatePrice', () => {
        it('truncates math without rounding up edges', () => {
            expect(truncatePrice(5.9999, 2)).toBe('5.99');
            expect(truncatePrice('0.1235', 3)).toBe('0.123');
            expect(truncatePrice(null, 3)).toBe('0.000');
        });
    });

    describe('formatPrice', () => {
        it('enforces 3-decimal truncation proxy', () => {
            expect(formatPrice(100.5559)).toBe('100.555');
        });
    });

    describe('calculateYDomain', () => {
        it('provides default boundaries when uninitialized', () => {
            expect(calculateYDomain([], false)).toEqual([0, 1]);
        });

        it('expands domain using high/low 10% buffering rules', () => {
            const data: Partial<Candle>[] = [
                { Low: 90, High: 100 },
                { Low: 80, High: 110 }
            ];
            // Range = 110 - 80 = 30. Pad = 3.
            // Min: 80 - 3 = 77. Max: 110 + 3 = 113.
            expect(calculateYDomain(data as Candle[], true)).toEqual([77, 113]);
        });
    });

    describe('calculateLiveMetrics', () => {
        it('returns zeroized fallback gracefully', () => {
            const res = calculateLiveMetrics([], false);
            expect(res.pctChange).toBe(0);
            expect(res.lastCandle.Close).toBe(0);
        });

        it('computes differentials between closing intervals', () => {
            const data: Partial<Candle>[] = [
                { Close: 100 },
                { Close: 110 }
            ];
            const res = calculateLiveMetrics(data as Candle[], true);
            expect(res.priceChange).toBe(10);
            expect(res.pctChange).toBe(10); // 10 / 100 * 100
        });
    });

    describe('calculateRadarTargets', () => {
        it('returns high conviction bypasses instantly', () => {
            const hc = [{ Ticker: 'A' }];
            const ad = [{ Ticker: 'B' }];
            expect(calculateRadarTargets(ad, hc)).toEqual(hc);
        });

        it('defaults to algorithmic slice of base list sorting by score', () => {
            const ad = [
                { Ticker: 'B', Signal_Score: '50' },
                { Ticker: 'A', Signal_Score: '90' },
                { Ticker: 'C', Signal_Score: '10' }
            ];
            const result = calculateRadarTargets(ad, []);
            expect(result[0].Ticker).toBe('A');
            expect(result[1].Ticker).toBe('B');
            expect(result[2].Ticker).toBe('C');
        });
    });

    describe('parseToUtcTimestamp', () => {
        it('parses valid ISO string to seconds', () => {
            const res = parseToUtcTimestamp('2026-02-17T09:30:00Z');
            expect(res).toBe(Math.floor(Date.parse('2026-02-17T09:30:00Z') / 1000));
        });

        it('handles space separated dates and invalid dates', () => {
            const res = parseToUtcTimestamp('2026-02-17 09:30:00');
            expect(res).not.toBeNull();
            expect(parseToUtcTimestamp('')).toBeNull();
            expect(parseToUtcTimestamp('invalid-date')).toBeNull();
        });
    });

    describe('transformToChartData', () => {
        it('converts valid candles into sorted candlestick and volume series', () => {
            const candles: Candle[] = [
                {
                    Date: '2026-02-17T09:31:00Z',
                    Open: 102,
                    High: 104,
                    Low: 101,
                    Close: 103,
                    Volume: 18000,
                    timeLabel: '09:31',
                    wickRange: [101, 104],
                    bodyRange: [102, 103],
                    isBullish: true,
                },
                {
                    Date: '2026-02-17T09:30:00Z',
                    Open: 101,
                    High: 103,
                    Low: 100,
                    Close: 100.5,
                    Volume: 15000,
                    timeLabel: '09:30',
                    wickRange: [100, 103],
                    bodyRange: [100.5, 101],
                    isBullish: false,
                },
            ];

            const { candlestickData, volumeData } = transformToChartData(candles);
            expect(candlestickData).toHaveLength(2);
            expect(volumeData).toHaveLength(2);
            // Must be sorted ascending
            expect(candlestickData[0].time).toBeLessThan(candlestickData[1].time);
            expect(candlestickData[0].open).toBe(101);
            expect(candlestickData[1].open).toBe(102);
            expect(volumeData[0].value).toBe(15000);
            expect(volumeData[1].value).toBe(18000);
        });
    });
});

