import React from 'react';
import { render, screen } from '@testing-library/react';
import { LiveIntradayChart } from './LiveIntradayChart';
import type { Candle } from '../hooks/useLiveRuntime';

jest.mock('lightweight-charts', () => {
    const fitContent = jest.fn();
    const priceScaleApplyOptions = jest.fn();
    const candlestickSetData = jest.fn();
    const volumeSetData = jest.fn();
    let crosshairCallback: ((param: any) => void) | null = null;

    const addSeries = jest.fn((def: any) => {
        if (def.type === 'candlestick') {
            return { setData: candlestickSetData };
        }
        return { setData: volumeSetData };
    });

    const chartApi = {
        addSeries,
        applyOptions: jest.fn(),
        remove: jest.fn(),
        priceScale: jest.fn(() => ({
            applyOptions: priceScaleApplyOptions,
        })),
        timeScale: jest.fn(() => ({
            fitContent,
        })),
        subscribeCrosshairMove: jest.fn((cb) => {
            crosshairCallback = cb;
        }),
        unsubscribeCrosshairMove: jest.fn(),
        __triggerCrosshair: (param: any) => {
            crosshairCallback?.(param);
        },
    };

    return {
        ColorType: {
            Solid: 'solid',
        },
        CrosshairMode: {
            Normal: 0,
        },
        CandlestickSeries: { type: 'candlestick' },
        HistogramSeries: { type: 'histogram' },
        LineSeries: { type: 'line' },
        createChart: jest.fn(() => chartApi),
    };
}, { virtual: true });

const testCandles: Candle[] = [
    {
        Date: '2026-02-17T09:30:00Z',
        Open: 100,
        High: 102,
        Low: 99,
        Close: 101,
        Volume: 5000,
        timeLabel: '09:30',
        wickRange: [99, 102],
        bodyRange: [100, 101],
        isBullish: true,
    },
    {
        Date: '2026-02-17T09:31:00Z',
        Open: 101,
        High: 103,
        Low: 100.5,
        Close: 102.5,
        Volume: 7500,
        timeLabel: '09:31',
        wickRange: [100.5, 103],
        bodyRange: [101, 102.5],
        isBullish: true,
    },
];

describe('LiveIntradayChart', () => {
    it('initializes TradingView Lightweight Charts and binds canvas container', () => {
        const { unmount } = render(<LiveIntradayChart data={testCandles} height={400} />);

        expect(screen.getByTestId('live-intraday-canvas-container')).toBeInTheDocument();

        const lightweightCharts = jest.requireMock('lightweight-charts');
        expect(lightweightCharts.createChart).toHaveBeenCalled();

        unmount();
        const chartApi = lightweightCharts.createChart.mock.results[0].value;
        expect(chartApi.remove).toHaveBeenCalled();
    });
});
