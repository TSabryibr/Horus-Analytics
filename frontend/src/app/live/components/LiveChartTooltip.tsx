import React from 'react';
import clsx from 'clsx';
import { truncatePrice } from '../lib/liveTransforms';
import { Candle } from '../hooks/useLiveRuntime';

interface LiveChartTooltipProps {
    active?: boolean;
    payload?: readonly { payload?: Candle }[];
}

export function LiveChartTooltip(props: LiveChartTooltipProps) {
    const { active, payload } = props;
    if (!active || !payload?.length || !payload[0]?.payload) return null;
    const candle = payload[0].payload;

    return (
        <div className="rounded-xl border border-slate-500/40 bg-slate-950/95 px-3 py-2">
            <p className="text-[10px] text-slate-400 uppercase tracking-widest mb-1">{candle.timeLabel}</p>
            <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] font-mono">
                <span className="text-slate-400">O</span><span className="text-slate-100">{truncatePrice(candle.Open)}</span>
                <span className="text-slate-400">H</span><span className="text-emerald-300">{truncatePrice(candle.High)}</span>
                <span className="text-slate-400">L</span><span className="text-rose-300">{truncatePrice(candle.Low)}</span>
                <span className="text-slate-400">C</span>
                <span className={clsx(candle.isBullish ? 'text-emerald-300' : 'text-rose-300')}>
                    {truncatePrice(candle.Close)}
                </span>
                <span className="text-slate-400">Vol</span><span className="text-cyan-300">{Math.round(candle.Volume).toLocaleString()}</span>
            </div>
        </div>
    );
}
