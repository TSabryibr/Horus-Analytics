
'use client';

import { RefreshCw, X } from 'lucide-react';
import dynamic from 'next/dynamic';

const InstitutionalChart = dynamic(
    () => import('../../components/charts/InstitutionalChart').then(mod => mod.InstitutionalChart),
    { ssr: false, loading: () => <div className="flex h-[400px] w-full items-center justify-center bg-slate-950/80 rounded-xl text-slate-500 border border-white/10">Loading chart...</div> }
);

interface WhaleChartModalProps {
    selectedTicker: string | null;
    historyLoading: boolean;
    chartData: Array<{ time: string; open: number; high: number; low: number; close: number }>;
    obvData: Array<{ time: string; value: number }>;
    onClose: () => void;
}

export function WhaleChartModal({
    selectedTicker,
    historyLoading,
    chartData,
    obvData,
    onClose,
}: WhaleChartModalProps) {
    if (!selectedTicker) {
        return null;
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80">
            <div className="section-surface industrial-corner w-full max-w-5xl overflow-hidden rounded-2xl animate-in fade-in zoom-in duration-200">
                <div className="flex justify-between items-center p-6 border-b border-white/10 bg-slate-950/55">
                    <div>
                        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                            {selectedTicker}
                            <span className="text-sm font-normal text-slate-500">Institutional Trace</span>
                        </h2>
                        <p className="text-xs text-slate-400">Price vs. On-Balance Volume (OBV) Divergence</p>
                    </div>
                    <button onClick={onClose} className="rounded-full p-2 transition hover:bg-white/[0.05]">
                        <X className="w-6 h-6 text-slate-400" />
                    </button>
                </div>
                <div className="p-6">
                    {historyLoading ? (
                        <div className="h-[400px] flex items-center justify-center">
                            <RefreshCw className="w-10 h-10 text-cyan-500 animate-spin" />
                        </div>
                    ) : chartData.length > 0 ? (
                        <InstitutionalChart data={chartData} obvData={obvData} height={400} />
                    ) : (
                        <div className="h-[400px] flex items-center justify-center text-slate-500">
                            No historical data available for analysis.
                        </div>
                    )}
                </div>
                <div className="flex justify-between items-center border-t border-white/10 bg-slate-950/55 px-6 py-4">
                    <div className="flex gap-4">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-emerald-500" />
                            <span className="text-[10px] text-slate-400 uppercase">Price Action</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-cyan-500" />
                            <span className="text-[10px] text-slate-400 uppercase">Whale Accumulation (OBV)</span>
                        </div>
                    </div>
                    <p className="text-[10px] text-slate-500 italic">Data powered by Vanaheim Whale Engine</p>
                </div>
            </div>
        </div>
    );
}
