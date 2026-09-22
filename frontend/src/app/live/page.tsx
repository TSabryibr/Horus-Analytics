'use client';

import dynamic from 'next/dynamic';
import { LiveAnalyticsPanel } from './components/LiveAnalyticsPanel';
import { LiveShell } from './components/LiveShell';
import { LiveStatusPanel } from './components/LiveStatusPanel';
import { LiveChartTooltip } from './components/LiveChartTooltip';

const LiveChartPanel = dynamic(
    () => import('./components/LiveChartPanel').then(mod => mod.LiveChartPanel),
    { ssr: false, loading: () => <div className="flex h-[520px] w-full items-center justify-center bg-slate-950/80 rounded-3xl text-slate-500 border border-white/10">Loading chart component...</div> }
);
import { useLiveDashboard } from './hooks/useLiveDashboard';

export default function LiveMonitorPage() {
    const { shellProps, analyticsProps, statusProps, chartProps } = useLiveDashboard();

    return (
        <LiveShell {...shellProps}>
            <LiveAnalyticsPanel {...analyticsProps} />
            <LiveStatusPanel {...statusProps} />
            <LiveChartPanel {...chartProps} renderCandleTooltip={LiveChartTooltip} />
        </LiveShell>
    );
}
