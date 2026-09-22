import { render } from '@testing-library/react';

jest.mock('lightweight-charts', () => {
    const fitContent = jest.fn();
    const priceScaleApplyOptions = jest.fn();
    const addSeries = jest.fn()
        .mockReturnValueOnce({
            setData: jest.fn(),
        })
        .mockReturnValueOnce({
            setData: jest.fn(),
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
    };

    return {
        ColorType: {
            Solid: 'solid',
        },
        CandlestickSeries: { type: 'candlestick' },
        LineSeries: { type: 'line' },
        createSeriesMarkers: jest.fn(),
        createChart: jest.fn(() => chartApi),
    };
}, { virtual: true });

import { InstitutionalChart } from './InstitutionalChart';

describe('InstitutionalChart', () => {
    it('initializes the chart with the v5 addSeries API when helper methods are absent', () => {
        const data = [
            { time: '2026-03-20', open: 10, high: 12, low: 9, close: 11 },
            { time: '2026-03-21', open: 11, high: 13, low: 10, close: 12 },
        ];
        const obvData = [
            { time: '2026-03-20', value: 1000 },
            { time: '2026-03-21', value: 1300 },
        ];
        const markers = [
            { time: '2026-03-21', position: 'belowBar', color: '#10b981', shape: 'arrowUp', text: 'ACC' },
        ];

        expect(() => {
            const { unmount } = render(
                <InstitutionalChart
                    data={data}
                    obvData={obvData}
                    markers={markers}
                    height={320}
                />
            );
            unmount();
        }).not.toThrow();

        const lightweightCharts = jest.requireMock('lightweight-charts');
        const chartApi = lightweightCharts.createChart.mock.results[0].value;
        const candlestickSeries = chartApi.addSeries.mock.results[0].value;
        const lineSeries = chartApi.addSeries.mock.results[1].value;

        expect(chartApi.addSeries).toHaveBeenNthCalledWith(
            1,
            expect.objectContaining({ type: 'candlestick' }),
            expect.objectContaining({
                upColor: '#10b981',
                downColor: '#ef4444',
            })
        );
        expect(chartApi.addSeries).toHaveBeenNthCalledWith(
            2,
            expect.objectContaining({ type: 'line' }),
            expect.objectContaining({
                color: '#06b6d4',
                priceScaleId: 'left',
            })
        );
        expect(candlestickSeries.setData).toHaveBeenCalledWith(data);
        expect(lineSeries.setData).toHaveBeenCalledWith(obvData);
        expect(lightweightCharts.createSeriesMarkers).toHaveBeenCalledWith(candlestickSeries, markers);
        expect(chartApi.timeScale().fitContent).toHaveBeenCalled();
        expect(chartApi.remove).toHaveBeenCalled();
    });
});
