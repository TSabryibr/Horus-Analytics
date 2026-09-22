import React from 'react';
import { render, screen } from '@testing-library/react';

import type { Candle } from '../hooks/useLiveRuntime';
import { LiveChartPanel } from './LiveChartPanel';

jest.mock('lightweight-charts', () => {
    const fitContent = jest.fn();
    const priceScaleApplyOptions = jest.fn();
    const addSeries = jest.fn(() => ({
        setData: jest.fn(),
    }));

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
        subscribeCrosshairMove: jest.fn(),
        unsubscribeCrosshairMove: jest.fn(),
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


const candles: Candle[] = [
    {
        Date: '2026-02-17T09:30:00Z',
        Open: 101,
        High: 103,
        Low: 100,
        Close: 102,
        Volume: 15000,
        timeLabel: '09:30',
        wickRange: [100, 103],
        bodyRange: [101, 102],
        isBullish: true,
    },
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
];

describe('LiveChartPanel', () => {
    const resizeObserverInstances: Array<{ callback: ResizeObserverCallback }> = [];
    let originalResizeObserver: typeof ResizeObserver | undefined;

    beforeEach(() => {
        resizeObserverInstances.length = 0;
        originalResizeObserver = global.ResizeObserver;
        global.ResizeObserver = class ResizeObserver {
            callback: ResizeObserverCallback;

            constructor(callback: ResizeObserverCallback) {
                this.callback = callback;
                resizeObserverInstances.push({ callback });
            }

            observe(target: Element) {
                this.callback(
                    [
                        {
                            target,
                            contentRect: {
                                width: 960,
                                height: 520,
                            } as DOMRectReadOnly,
                        } as ResizeObserverEntry,
                    ],
                    this as unknown as ResizeObserver
                );
            }

            disconnect() {}

            unobserve() {}
        } as typeof ResizeObserver;

        jest.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function () {
            if ((this as HTMLElement).dataset.testid === 'live-chart-viewport') {
                return {
                    width: 960,
                    height: 520,
                    top: 0,
                    left: 0,
                    right: 960,
                    bottom: 520,
                    x: 0,
                    y: 0,
                    toJSON: () => ({}),
                } as DOMRect;
            }

            return {
                width: 0,
                height: 0,
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                x: 0,
                y: 0,
                toJSON: () => ({}),
            } as DOMRect;
        });
    });

    afterEach(() => {
        jest.restoreAllMocks();
        global.ResizeObserver = originalResizeObserver as typeof ResizeObserver;
    });

    it('renders the chart header and chart surface when mounted with data', () => {
        render(
            <LiveChartPanel
                ticker="COMI"
                data={candles}
                isMounted={true}
                hasData={true}
                loading={false}
                refreshing={false}
                yDomain={[99, 105]}
                renderCandleTooltip={() => null}
            />
        );

        expect(screen.getByText(/COMI intraday 1m \(2 bars\)/i)).toBeInTheDocument();
        expect(screen.getByTestId('live-chart-viewport')).toHaveClass('min-w-0', 'h-[440px]', 'md:h-[520px]');
        expect(screen.getByTestId('live-intraday-canvas-container')).toBeInTheDocument();
    });

    it('renders the syncing chip and loading overlay when requested', () => {
        render(
            <LiveChartPanel
                ticker="COMI"
                data={candles}
                isMounted={true}
                hasData={true}
                loading={true}
                refreshing={true}
                yDomain={[99, 105]}
                renderCandleTooltip={() => null}
            />
        );

        expect(screen.getByText(/Syncing/i)).toBeInTheDocument();
        expect(screen.getByText(/Loading stream/i)).toBeInTheDocument();
    });

    it('renders the empty state when mounted without data and not loading', () => {
        render(
            <LiveChartPanel
                ticker="COMI"
                data={[]}
                isMounted={true}
                hasData={false}
                loading={false}
                refreshing={false}
                yDomain={[0, 1]}
                renderCandleTooltip={() => null}
            />
        );

        expect(screen.getByText(/No Intraday Data/i)).toBeInTheDocument();
        expect(screen.getByText(/Select a ticker and wait for market data to load/i)).toBeInTheDocument();
    });

    it('falls back to the empty state when candle rows are malformed', () => {
        const malformedCandles = [
            {
                ...candles[0],
                High: Number.NaN,
            },
        ] as unknown as Candle[];

        render(
            <LiveChartPanel
                ticker="COMI"
                data={malformedCandles}
                isMounted={true}
                hasData={true}
                loading={false}
                refreshing={false}
                yDomain={[0, 1]}
                renderCandleTooltip={() => null}
            />
        );

        expect(screen.getByText(/No Intraday Data/i)).toBeInTheDocument();
        expect(screen.queryByTestId('live-intraday-canvas-container')).not.toBeInTheDocument();
    });
});

