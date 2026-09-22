'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
    createChart,
    CandlestickSeries,
    HistogramSeries,
    ColorType,
    CrosshairMode,
    IChartApi,
} from 'lightweight-charts';
import type { Candle } from '../hooks/useLiveRuntime';
import { transformToChartData, truncatePrice } from '../lib/liveTransforms';
import clsx from 'clsx';

interface LiveIntradayChartProps {
    data: Candle[];
    height?: number;
}

interface HoveredBarState {
    timeLabel: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    isBullish: boolean;
}

export function LiveIntradayChart({ data, height = 480 }: LiveIntradayChartProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candlestickSeriesRef = useRef<any>(null);
    const volumeSeriesRef = useRef<any>(null);
    const [hoveredBar, setHoveredBar] = useState<HoveredBarState | null>(null);

    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        const chart = createChart(container, {
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.03)' },
            },
            width: container.clientWidth || 800,
            height: height,
            timeScale: {
                borderColor: '#334155',
                timeVisible: true,
                secondsVisible: false,
            },
            crosshair: {
                mode: CrosshairMode.Normal,
                vertLine: {
                    color: 'rgba(148, 163, 184, 0.4)',
                    width: 1,
                    style: 3,
                },
                horzLine: {
                    color: 'rgba(148, 163, 184, 0.4)',
                    width: 1,
                    style: 3,
                },
            },
            rightPriceScale: {
                borderColor: '#334155',
                scaleMargins: {
                    top: 0.08,
                    bottom: 0.25,
                },
            },
        });

        const chartApi = chart as IChartApi & {
            addSeries?: (seriesDefinition: unknown, options?: Record<string, unknown>) => any;
            addCandlestickSeries?: (options?: Record<string, unknown>) => any;
            addHistogramSeries?: (options?: Record<string, unknown>) => any;
        };

        const candlestickSeriesOptions = {
            upColor: '#10b981',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
            priceScaleId: 'right',
        };

        const candlestickSeries = typeof chartApi.addCandlestickSeries === 'function'
            ? chartApi.addCandlestickSeries(candlestickSeriesOptions)
            : chartApi.addSeries?.(CandlestickSeries, candlestickSeriesOptions);

        const volumeSeriesOptions = {
            priceFormat: { type: 'volume' },
            priceScaleId: 'volume',
        };

        const volumeSeries = typeof chartApi.addHistogramSeries === 'function'
            ? chartApi.addHistogramSeries(volumeSeriesOptions)
            : chartApi.addSeries?.(HistogramSeries, volumeSeriesOptions);

        if (chart.priceScale('volume')) {
            chart.priceScale('volume').applyOptions({
                scaleMargins: {
                    top: 0.8,
                    bottom: 0,
                },
            });
        }

        candlestickSeriesRef.current = candlestickSeries;
        volumeSeriesRef.current = volumeSeries;
        chartRef.current = chart;

        // Populate initial data immediately if available
        if (data.length > 0) {
            const { candlestickData, volumeData } = transformToChartData(data);
            candlestickSeries?.setData(candlestickData);
            volumeSeries?.setData(volumeData);
            chart.timeScale().fitContent();
        }

        chart.subscribeCrosshairMove((param) => {
            if (
                !param.time ||
                !param.point ||
                param.point.x < 0 ||
                param.point.x > container.clientWidth ||
                param.point.y < 0 ||
                param.point.y > height
            ) {
                setHoveredBar(null);
                return;
            }

            const candle = candlestickSeries ? (param.seriesData.get(candlestickSeries) as any) : null;
            const vol = volumeSeries ? (param.seriesData.get(volumeSeries) as any) : null;

            if (candle) {
                const dateObj = typeof param.time === 'number' ? new Date(param.time * 1000) : new Date();
                const timeLabel = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });

                setHoveredBar({
                    timeLabel,
                    open: candle.open,
                    high: candle.high,
                    low: candle.low,
                    close: candle.close,
                    volume: vol?.value ?? 0,
                    isBullish: candle.close >= candle.open,
                });
            } else {
                setHoveredBar(null);
            }
        });

        const resizeObserver = typeof ResizeObserver !== 'undefined'
            ? new ResizeObserver((entries) => {
                  const entry = entries[0];
                  if (entry && chartRef.current) {
                      chartRef.current.applyOptions({
                          width: Math.max(0, Math.round(entry.contentRect.width)),
                          height: Math.max(0, Math.round(entry.contentRect.height || height)),
                      });
                  }
              })
            : null;

        resizeObserver?.observe(container);

        return () => {
            resizeObserver?.disconnect();
            chart.remove();
            chartRef.current = null;
            candlestickSeriesRef.current = null;
            volumeSeriesRef.current = null;
        };
    }, [height]);

    // Data updating on poll or WebSocket event
    useEffect(() => {
        if (!chartRef.current || !candlestickSeriesRef.current || !volumeSeriesRef.current) return;
        const { candlestickData, volumeData } = transformToChartData(data);
        candlestickSeriesRef.current.setData(candlestickData);
        volumeSeriesRef.current.setData(volumeData);
    }, [data]);

    return (
        <div className="relative h-full w-full">
            {hoveredBar && (
                <div
                    data-testid="live-chart-hud"
                    className="absolute top-2 left-2 z-20 flex flex-wrap items-center gap-2 rounded-lg border border-white/10 bg-slate-950/85 px-2.5 py-1 text-[11px] font-mono shadow-lg backdrop-blur-sm pointer-events-none"
                >
                    <span className="text-slate-400">{hoveredBar.timeLabel}</span>
                    <span className="text-slate-500">O:</span>
                    <span className="text-slate-200">{truncatePrice(hoveredBar.open)}</span>
                    <span className="text-slate-500">H:</span>
                    <span className="text-emerald-400">{truncatePrice(hoveredBar.high)}</span>
                    <span className="text-slate-500">L:</span>
                    <span className="text-rose-400">{truncatePrice(hoveredBar.low)}</span>
                    <span className="text-slate-500">C:</span>
                    <span className={clsx(hoveredBar.isBullish ? 'text-emerald-400' : 'text-rose-400')}>
                        {truncatePrice(hoveredBar.close)}
                    </span>
                    <span className="text-slate-500">V:</span>
                    <span className="text-cyan-300">{Math.round(hoveredBar.volume).toLocaleString()}</span>
                </div>
            )}
            <div
                ref={containerRef}
                data-testid="live-intraday-canvas-container"
                className="h-full w-full"
            />
        </div>
    );
}
