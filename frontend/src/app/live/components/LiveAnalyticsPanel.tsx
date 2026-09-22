'use client';

import React from 'react';

export interface LiveRadarItem {
    Ticker: string;
    Signal_Score?: number | string;
    Price: string;
    Risk_Reward_Ratio?: number | string;
    Resistance_20D?: string;
    Key_Resistance_1?: string;
}

interface LiveAnalyticsPanelProps {
    showRadar: boolean;
    analyticsLoading: boolean;
    radarItems: LiveRadarItem[];
    onSelectTicker: (ticker: string) => void;
}

export function LiveAnalyticsPanel({
    showRadar,
    analyticsLoading,
    radarItems,
    onSelectTicker,
}: LiveAnalyticsPanelProps) {
    if (!showRadar) {
        return null;
    }

    return (
        <div className="animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {radarItems.map((item) => (
                    <button
                        key={item.Ticker}
                        type="button"
                        aria-label={`Open ${item.Ticker}`}
                        onClick={() => onSelectTicker(item.Ticker)}
                        className="bg-[#0F172A]/60 border border-cyan-500/20 hover:border-cyan-300/40 rounded-2xl p-4 cursor-pointer transition-all hover:scale-[1.01] text-left"
                    >
                        <div className="flex justify-between items-start mb-3">
                            <h3 className="font-black text-white uppercase">{item.Ticker}</h3>
                            <span className="text-[10px] font-black bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-lg border border-emerald-500/20">
                                SCORE {item.Signal_Score ?? '-'}
                            </span>
                        </div>

                        <div className="flex items-end justify-between mb-4">
                            <div className="text-2xl font-black text-white font-mono tracking-tight">
                                {item.Price}
                            </div>
                            <div className="text-[10px] font-black text-cyan-300 tracking-widest uppercase mb-1">
                                RR {item.Risk_Reward_Ratio ?? '-'}X
                            </div>
                        </div>

                        <div className="space-y-1.5 text-[10px] border-t border-white/5 pt-3 font-mono tracking-tight">
                            <div className="flex justify-between">
                                <span className="text-gray-500 uppercase">Res 20D</span>
                                <span className="text-gray-300">{item.Resistance_20D ?? '0.000'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500 uppercase">Target 1</span>
                                <span className="text-emerald-300 font-black">{item.Key_Resistance_1 ?? '0.000'}</span>
                            </div>
                        </div>
                    </button>
                ))}
                {radarItems.length === 0 && analyticsLoading && (
                    <div className="col-span-full rounded-2xl border border-cyan-500/20 bg-cyan-500/5 p-5 text-sm text-cyan-200">
                        Loading analytics radar...
                    </div>
                )}
                {radarItems.length === 0 && !analyticsLoading && (
                    <div className="col-span-full rounded-2xl border border-white/10 bg-white/5 p-5 text-sm text-gray-300">
                        No analytics candidates available yet. Try refresh in a few seconds.
                    </div>
                )}
            </div>
        </div>
    );
}
