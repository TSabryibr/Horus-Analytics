'use client';

import { Strategy } from '@/types/domain';
import {
    XAxis, YAxis,
    Tooltip, CartesianGrid, Legend, AreaChart, Area,
} from 'recharts';
import { MeasuredChartFrame } from '@/app/components/charts/MeasuredChartFrame';

interface AuditChartsPanelProps {
    comparisonData: Array<Record<string, unknown>>;
    strategies: Strategy[];
    colors: string[];
}

export function AuditChartsPanel({ comparisonData, strategies, colors }: AuditChartsPanelProps) {
    return (
        <div className="col-span-12 lg:col-span-8 bg-slate-900/30 border border-white/5 rounded-[2rem] p-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h3 className="text-lg font-black text-white uppercase tracking-tighter">Strategic Benchmarking</h3>
                    <p className="text-xs text-slate-500 font-medium">Cumulative Prophecy Performance Comparison</p>
                </div>
                <div className="flex gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                        <span className="text-[10px] text-slate-400 font-bold uppercase">Alpha</span>
                    </div>
                </div>
            </div>

            <MeasuredChartFrame className="h-[350px] w-full" fallbackHeight={350}>
                {({ width, height }) => (
                    <AreaChart width={width} height={height} data={comparisonData}>
                        <defs>
                            {strategies.map((strategy, idx) => (
                                <linearGradient key={strategy.name} id={`color${idx}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={colors[idx % colors.length]} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={colors[idx % colors.length]} stopOpacity={0} />
                                </linearGradient>
                            ))}
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                        <XAxis dataKey="name" hide />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#475569', fontSize: 10, fontWeight: 700 }}
                            tickFormatter={(val) => `${val}%`}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#0f172a', borderRadius: '1rem', border: '1px solid #ffffff10', fontSize: '10px' }}
                            itemStyle={{ fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.05em' }}
                        />
                        <Legend
                            iconType="circle"
                            wrapperStyle={{ paddingTop: '2rem', fontSize: '10px', fontWeight: 900, textTransform: 'uppercase' }}
                        />
                        {strategies.map((strategy, idx) => (
                            <Area
                                key={strategy.name}
                                type="monotone"
                                dataKey={strategy.name}
                                stroke={colors[idx % colors.length]}
                                strokeWidth={3}
                                fillOpacity={1}
                                fill={`url(#color${idx})`}
                                dot={false}
                                activeDot={{ r: 4, strokeWidth: 0 }}
                            />
                        ))}
                    </AreaChart>
                )}
            </MeasuredChartFrame>
        </div>
    );
}
