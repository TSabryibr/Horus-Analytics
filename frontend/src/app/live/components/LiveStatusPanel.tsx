'use client';

import React from 'react';
import clsx from 'clsx';
import { TrendingDown, TrendingUp } from 'lucide-react';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';

interface LiveStatusPanelProps {
    lastPrice: string;
    pctChange: string;
    priceChangePositive: boolean;
    volumeLabel: string;
    liveRunning: boolean;
    marketOpen: boolean;
    pollLabel: string;
    liveLastUpdate: string;
}

export function LiveStatusPanel({
    lastPrice,
    pctChange,
    priceChangePositive,
    volumeLabel,
    liveRunning,
    marketOpen,
    pollLabel,
    liveLastUpdate,
}: LiveStatusPanelProps) {
    return (
        <div className="grid gap-4 md:grid-cols-4">
            <IndustrialCard tone="secondary" className="rounded-2xl border-cyan-400/20 bg-[linear-gradient(180deg,rgba(6,24,34,0.92),rgba(2,6,23,0.88))]" contentClassName="p-5">
                <p className="text-gray-400 text-[10px] font-black tracking-widest uppercase mb-1">Mkt Price</p>
                <h2 className="text-4xl font-black font-mono tracking-tight text-white">
                    {lastPrice}
                </h2>
            </IndustrialCard>

            <IndustrialCard tone="secondary" className="rounded-2xl" contentClassName="p-5">
                <p className="text-gray-400 text-[10px] font-black tracking-widest uppercase mb-1">Momentum</p>
                <div className={clsx('flex items-center text-3xl font-black font-mono tracking-tight', priceChangePositive ? 'text-emerald-300' : 'text-rose-300')}>
                    {priceChangePositive ? <TrendingUp className="h-6 w-6 mr-2" /> : <TrendingDown className="h-6 w-6 mr-2" />}
                    {pctChange}%
                </div>
            </IndustrialCard>

            <IndustrialCard tone="secondary" className="rounded-2xl" contentClassName="p-5">
                <p className="text-gray-400 text-[10px] font-black tracking-widest uppercase mb-1">Volume 1M</p>
                <h2 className="text-3xl font-black font-mono tracking-tight text-blue-300">
                    {volumeLabel}
                </h2>
            </IndustrialCard>

            <IndustrialCard tone="secondary" className="rounded-2xl" contentClassName="p-5">
                <p className="text-gray-400 text-[10px] font-black tracking-widest uppercase mb-2">System Status</p>
                <div className="flex items-center gap-2 mb-1">
                    <span className={clsx('h-2 w-2 rounded-full', liveRunning ? 'bg-emerald-400  ' : 'bg-amber-400  ')} />
                    <span className="text-xs font-black tracking-widest uppercase text-white">
                        {liveRunning ? 'Feed running' : 'Feed paused'}
                    </span>
                </div>
                <p className="text-[10px] text-gray-500 font-mono tracking-wider uppercase">
                    {marketOpen ? `Poll ${pollLabel}` : 'Market Closed'} | Last feed {liveLastUpdate}
                </p>
            </IndustrialCard>
        </div>
    );
}
