import EmptyState from './EmptyState';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';

type HomeEquityPanelProps = {
    chart: React.ReactNode;
    hasCurve: boolean;
};

export function HomeEquityPanel({ chart, hasCurve }: HomeEquityPanelProps) {
    return (
        <IndustrialCard
            tone="secondary"
            className="scan-line relative group lg:col-span-2"
            contentClassName="relative p-10"
        >
            <div className="absolute top-4 right-4 text-white/5 font-black text-8xl pointer-events-none select-none">
                01
            </div>

            <div className="flex justify-between items-end mb-12">
                <div>
                    <h3 className="meta-label mb-2 text-primary/60">Propagation Matrix</h3>
                    <p className="text-3xl heading-title text-white tracking-tighter">EQUITY_CURVE_REALTIME</p>
                </div>
                <div className="flex flex-col items-end gap-2">
                    <div className="flex items-center gap-3 bg-primary/5 px-4 py-2 border border-primary/20 industrial-corner">
                        <span className="h-2 w-2 rounded-full bg-primary" />
                        <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em]">Live Stream</span>
                    </div>
                    <span className="text-[9px] text-slate-600 font-mono">ID: 8820-XP9</span>
                </div>
            </div>

            <div className="h-[400px] w-full min-w-0">
                {hasCurve ? (
                    chart
                ) : (
                    <EmptyState
                        title="Telemetry Offline"
                        message="Data points required for curve generation."
                        icon="chart"
                    />
                )}
            </div>
        </IndustrialCard>
    );
}
