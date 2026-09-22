import React, { memo } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { EquityPoint } from '@/types';
import { MeasuredChartFrame } from './MeasuredChartFrame';

function HomeEquityChartComponent({ curve }: { curve: EquityPoint[] }) {
  return (
    <MeasuredChartFrame className="h-full w-full" fallbackHeight={420}>
      {({ width, height }) => (
        <AreaChart width={width} height={height} data={curve} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="colorPnL" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.02)" vertical={false} />
          <XAxis
            dataKey="date"
            stroke="#4b5563"
            tick={{ fontSize: 10, fontWeight: 700, fill: '#64748b', fontFamily: 'var(--font-mono)' }}
            tickFormatter={(str) => {
              if (!str || typeof str !== 'string') return '';
              return str.split('-').slice(1).join('/');
            }}
            axisLine={false}
            tickLine={false}
            minTickGap={40}
          />
          <YAxis
            stroke="#4b5563"
            tick={{ fontSize: 10, fontWeight: 700, fill: '#64748b', fontFamily: 'var(--font-mono)' }}
            axisLine={false}
            tickLine={false}
            orientation="right"
            tickFormatter={(val) => `E£${(val / 1000).toFixed(0)}K`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(2,6,23,0.8)',
              borderColor: 'rgba(59,130,246,0.2)',
              borderRadius: '20px',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)'
            }}
            itemStyle={{ color: 'var(--color-primary)', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}
            labelStyle={{ color: '#64748b', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '4px', fontWeight: 700 }}
          />
          <Area
            type="monotone"
            dataKey="equity"
            stroke="var(--color-primary)"
            fillOpacity={1}
            fill="url(#colorPnL)"
            strokeWidth={4}
            animationDuration={2500}
          />
        </AreaChart>
      )}
    </MeasuredChartFrame>
  );
}

const HomeEquityChart = memo(HomeEquityChartComponent, (prev, next) => {
  if (prev.curve === next.curve) return true;
  if (prev.curve.length !== next.curve.length) return false;
  return prev.curve[prev.curve.length - 1]?.equity === next.curve[next.curve.length - 1]?.equity;
});

export default HomeEquityChart;
