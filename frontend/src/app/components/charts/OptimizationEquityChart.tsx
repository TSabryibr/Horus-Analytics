'use client';

import { memo } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { MeasuredChartFrame } from './MeasuredChartFrame';

const OptimizationEquityChart = memo(function OptimizationEquityChart({ data }: { data: Array<{ date: string; value: number }> }) {
  return (
    <MeasuredChartFrame className="h-full w-full" fallbackHeight={320}>
      {({ width, height }) => (
        <AreaChart width={width} height={height} data={data} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
          <XAxis
            dataKey="date"
            stroke="#4b5563"
            fontSize={10}
            fontWeight={700}
            tickFormatter={(str) => {
              if (!str) return '';
              const d = new Date(str);
              return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
            }}
            axisLine={false}
            tickLine={false}
            minTickGap={40}
          />
          <YAxis
            stroke="#4b5563"
            fontSize={10}
            fontWeight={700}
            domain={['auto', 'auto']}
            tickFormatter={(val) => `E£${(val / 1000).toFixed(0)}K`}
            axisLine={false}
            tickLine={false}
            orientation="right"
          />
          <Tooltip
            contentStyle={{ backgroundColor: 'rgba(17, 24, 39, 0.95)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '16px', backdropFilter: 'blur(12px)' }}
            itemStyle={{ color: '#8b5cf6', fontSize: '12px', fontWeight: 900, textTransform: 'uppercase' }}
            labelStyle={{ color: '#9ca3af', marginBottom: '4px', fontSize: '10px', textTransform: 'uppercase', fontWeight: 700 }}
            formatter={(val: any) => [`E£ ${Number(val ?? 0).toLocaleString()}`, 'Equity']}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#8b5cf6"
            strokeWidth={3}
            fillOpacity={1}
            fill="url(#colorValue)"
          />
        </AreaChart>
      )}
    </MeasuredChartFrame>
  );
});

export default OptimizationEquityChart;
