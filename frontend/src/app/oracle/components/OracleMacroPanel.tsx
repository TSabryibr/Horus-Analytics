import React, { useMemo } from 'react';
import clsx from 'clsx';
import { ComposedChart, Area, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { MeasuredChartFrame } from '@/app/components/charts/MeasuredChartFrame';
import type { OracleIndex } from '../hooks/useOracleRuntime';

type OracleMacroPanelProps = {
    activeIndex: OracleIndex;
    setActiveIndex: (value: OracleIndex) => void;
    macro: any;
    macroSignalColor: string;
};

export function OracleMacroPanel({ activeIndex, setActiveIndex, macro, macroSignalColor }: OracleMacroPanelProps) {
    const chartData = useMemo(() => {
        if (!macro?.price_history) return [];
        return Object.keys(macro.price_history).map((dateKey) => {
            const timestamp = Number(dateKey);
            const formattedDate = !isNaN(timestamp)
                ? new Date(timestamp).toLocaleDateString(undefined, { month: '2-digit', day: '2-digit' })
                : dateKey;
            return {
                date: formattedDate,
                price: macro.price_history[dateKey],
                breadth: macro.breadth_history?.[dateKey] ?? 50,
            };
        });
    }, [macro]);

    return (
        <div className="bg-slate-950 border border-slate-800/80 rounded-none p-4 flex flex-col space-y-4 font-mono select-none">
            <div className="flex justify-between items-start">
                <div>
                    <div className="flex items-center gap-1 mb-3">
                        <span className="w-1.5 h-1.5 bg-cyan-500 animate-pulse" />
                        <span className="text-[9px] text-slate-500 font-bold uppercase tracking-widest">{'// ORACLE::MACRO_HEALTH'}</span>
                    </div>
                    <div className="flex items-center space-x-1 mb-3">
                        {(['EGX30', 'EGX70', 'EGX100'] as const).map((idx) => (
                            <button
                                key={idx}
                                onClick={() => setActiveIndex(idx)}
                                className={clsx(
                                    'px-2 py-0.5 text-[10px] font-bold rounded-none transition-all border',
                                    activeIndex === idx ? 'bg-cyan-950/30 text-cyan-400 border-cyan-500/50 shadow-[0_0_10px_rgba(6,182,212,0.1)]' : 'bg-slate-900/50 text-slate-500 border-slate-800 hover:text-slate-300'
                                )}
                            >
                                {idx}
                            </button>
                        ))}
                    </div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Macro Health ({activeIndex})</p>
                    <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                        CANARY_ANALYSIS [{activeIndex}]
                    </h3>
                    <p className="text-[10px] text-slate-600 uppercase tracking-tighter mt-0.5">Price vs Breadth Divergence Engine</p>
                </div>
                <div className="text-right">
                    {macro && (
                        <>
                            <div className={clsx('text-xs font-black uppercase tracking-widest', macroSignalColor)}>{macro.signal}</div>
                            <div className="text-[10px] text-slate-500 mt-0.5 tabular-nums">Correlation: {macro.correlation}</div>
                        </>
                    )}
                </div>
            </div>

            {macro && macro.message && (
                <div className="bg-black/40 p-3 rounded-none border border-slate-800/50 text-left relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-0.5 h-full bg-cyan-500/50" />
                    <p className="text-[11px] leading-relaxed text-slate-400 italic">
                        &quot;{macro.message}&quot;
                    </p>
                </div>
            )}

            <div className="flex-1 min-h-[280px] w-full border border-slate-800/50 rounded-none bg-slate-900/10 relative overflow-hidden p-2">
                {chartData.length > 0 ? (
                    <MeasuredChartFrame className="h-full w-full" fallbackHeight={280}>
                        {({ width, height }) => (
                            <ComposedChart width={width} height={height} data={chartData} margin={{ top: 10, right: 5, bottom: 5, left: 5 }}>
                                <defs>
                                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.2} />
                                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.02)" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    stroke="#4b5563"
                                    tick={{ fontSize: 9, fontWeight: 700, fill: '#64748b', fontFamily: 'var(--font-mono)' }}
                                    axisLine={false}
                                    tickLine={false}
                                />
                                <YAxis
                                    yAxisId="left"
                                    stroke="#4b5563"
                                    tick={{ fontSize: 9, fontWeight: 700, fill: '#06b6d4', fontFamily: 'var(--font-mono)' }}
                                    axisLine={false}
                                    tickLine={false}
                                    tickFormatter={(val) => `${Number(val).toLocaleString()}`}
                                />
                                <YAxis
                                    yAxisId="right"
                                    orientation="right"
                                    stroke="#4b5563"
                                    tick={{ fontSize: 9, fontWeight: 700, fill: '#fbbf24', fontFamily: 'var(--font-mono)' }}
                                    axisLine={false}
                                    tickLine={false}
                                    domain={[0, 100]}
                                    tickFormatter={(val) => `${val}%`}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'rgba(2,6,23,0.85)',
                                        borderColor: 'rgba(6,182,212,0.2)',
                                        borderRadius: '8px',
                                        backdropFilter: 'blur(16px)',
                                        boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
                                        fontFamily: 'var(--font-mono)',
                                        fontSize: '11px',
                                    }}
                                    labelStyle={{ color: '#64748b', fontWeight: 700 }}
                                />
                                <Area
                                    yAxisId="left"
                                    type="monotone"
                                    dataKey="price"
                                    name="Index Price"
                                    stroke="#06b6d4"
                                    fillOpacity={1}
                                    fill="url(#colorPrice)"
                                    strokeWidth={2}
                                />
                                <Line
                                    yAxisId="right"
                                    type="monotone"
                                    dataKey="breadth"
                                    name="Market Breadth"
                                    stroke="#fbbf24"
                                    strokeWidth={1.5}
                                    dot={false}
                                />
                            </ComposedChart>
                        )}
                    </MeasuredChartFrame>
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center bg-slate-900/10 group overflow-hidden">
                        <div className="absolute inset-0 bg-grid-slate-900/[0.1] bg-[size:20px_20px]" />
                        <p className="text-slate-700 text-[10px] font-bold uppercase tracking-widest z-10 opacity-60">
                            [ AWAITING_CANARY_TELEMETRY ]
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
