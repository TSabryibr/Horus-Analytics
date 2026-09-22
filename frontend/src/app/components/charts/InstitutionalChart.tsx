'use client';

import React, { useEffect, useRef } from 'react';
import {
    createChart,
    createSeriesMarkers,
    CandlestickSeries,
    LineSeries,
    ColorType,
    IChartApi,
    CandlestickData,
    LineData,
    SeriesMarker,
} from 'lightweight-charts';

interface InstitutionalChartProps {
    data: CandlestickData[];
    obvData?: LineData[];
    markers?: SeriesMarker<any>[];
    width?: number;
    height?: number;
}

export const InstitutionalChart: React.FC<InstitutionalChartProps> = ({
    data,
    obvData,
    markers,
    height = 400
}) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: '#0b0f19' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: '#1e293b' },
                horzLines: { color: '#1e293b' },
            },
            width: chartContainerRef.current.clientWidth,
            height: height,
            timeScale: {
                borderColor: '#334155',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        const chartApi = chart as IChartApi & {
            addSeries?: (seriesDefinition: unknown, options?: Record<string, unknown>) => any;
            addCandlestickSeries?: (options?: Record<string, unknown>) => any;
            addLineSeries?: (options?: Record<string, unknown>) => any;
        };

        const candlestickSeriesOptions = {
            upColor: '#10b981',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        };
        const candlestickSeries = typeof chartApi.addCandlestickSeries === 'function'
            ? chartApi.addCandlestickSeries(candlestickSeriesOptions)
            : chartApi.addSeries?.(CandlestickSeries, candlestickSeriesOptions);

        if (!candlestickSeries) {
            return undefined;
        }

        candlestickSeries.setData(data);

        if (obvData && obvData.length > 0) {
            const obvSeriesOptions = {
                color: '#06b6d4',
                lineWidth: 2,
                priceScaleId: 'left',
            };
            const obvSeries = typeof chartApi.addLineSeries === 'function'
                ? chartApi.addLineSeries(obvSeriesOptions)
                : chartApi.addSeries?.(LineSeries, obvSeriesOptions);
            if (obvSeries) {
                obvSeries.setData(obvData);
                chart.priceScale('left').applyOptions({
                    visible: true,
                    borderColor: '#334155',
                });
            }
        }

        if (markers && markers.length > 0) {
            if (typeof candlestickSeries.setMarkers === 'function') {
                candlestickSeries.setMarkers(markers);
            } else {
                createSeriesMarkers(candlestickSeries, markers);
            }
        }

        chart.timeScale().fitContent();
        chartRef.current = chart;

        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [data, obvData, markers, height]);

    return (
        <div
            ref={chartContainerRef}
            className="section-surface industrial-corner w-full overflow-hidden rounded-xl border border-white/10 bg-slate-950/80"
        />
    );
};
