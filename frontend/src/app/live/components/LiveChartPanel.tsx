'use client';

import React from 'react';
import { Activity, RefreshCw, Target } from 'lucide-react';

import EmptyState from '../../components/EmptyState';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';
import type { Candle } from '../hooks/useLiveRuntime';
import { LiveIntradayChart } from './LiveIntradayChart';

interface LiveChartPanelProps {
    ticker: string;
    data: Candle[];
    isMounted: boolean;
    hasData: boolean;
    loading: boolean;
    refreshing: boolean;
    yDomain?: [number, number];
    renderCandleTooltip?: (props: {
        active?: boolean;
        payload?: readonly { payload?: Candle }[];
    }) => React.ReactNode;
}

export function LiveChartPanel({
    ticker,
    data,
    isMounted,
    loading,
    refreshing,
}: LiveChartPanelProps) {
    const validData = data.filter((entry) => (
        Number.isFinite(entry.Open)
        && Number.isFinite(entry.High)
        && Number.isFinite(entry.Low)
        && Number.isFinite(entry.Close)
        && Number.isFinite(entry.Volume)
    ));
    const canRenderChart = isMounted && validData.length > 0;

    return (
        <IndustrialCard
            tone="secondary"
            className="relative flex-1 min-w-0 min-h-[520px] w-full rounded-3xl overflow-hidden"
            contentClassName="relative p-4 md:p-6"
        >
            <div className="absolute top-5 left-5 z-10">
                <div className="flex items-center gap-2 bg-black/40 px-3 py-1.5 rounded-full border border-white/10">
                    <Target className="h-3.5 w-3.5 text-cyan-300" />
                    <span className="text-[10px] font-black tracking-widest uppercase text-gray-200">
                        {ticker} intraday 1m ({validData.length} bars)
                    </span>
                </div>
            </div>

            {refreshing && canRenderChart && (
                <div className="absolute top-5 right-5 z-10 flex items-center gap-2 bg-black/45 border border-white/10 rounded-full px-3 py-1.5 text-[10px] font-black tracking-widest uppercase text-cyan-200">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    Syncing
                </div>
            )}

            {canRenderChart ? (
                <div data-testid="live-chart-viewport" className="min-w-0 h-[440px] w-full md:h-[520px] pt-8">
                    <LiveIntradayChart data={validData} height={480} />
                </div>
            ) : isMounted && !loading ? (
                <EmptyState
                    title="No Intraday Data"
                    message="Select a ticker and wait for market data to load."
                    icon="chart"
                />
            ) : null}

            {loading && (
                <div className="absolute inset-0 bg-black/35 flex items-center justify-center z-20">
                    <div className="flex flex-col items-center gap-4">
                        <div className="relative h-12 w-12">
                            <Activity className="h-full w-full text-cyan-300" />
                            <div className="absolute inset-0 border-2 border-cyan-300/20 rounded-full animate-ping" />
                        </div>
                        <span className="text-[10px] font-black tracking-[0.2em] uppercase text-cyan-200">Loading stream...</span>
                    </div>
                </div>
            )}
        </IndustrialCard>
    );
}
