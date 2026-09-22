'use client';

import { Network, RefreshCcw } from 'lucide-react';
import clsx from 'clsx';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';

interface StatusFreshnessPanelProps {
    status: any;
    syncingData: boolean;
    syncStatusMessage: string | null;
    triggerDataSync: () => void | Promise<void>;
    historySymbolCount: number;
    historyAgeHours: number;
    sourceEngine: string;
    driftValue: string;
}

export function StatusFreshnessPanel({
    status,
    syncingData,
    syncStatusMessage,
    triggerDataSync,
    historySymbolCount,
    historyAgeHours,
    sourceEngine,
    driftValue,
}: StatusFreshnessPanelProps) {
    const intradayStatus = String(status?.data_status?.intraday?.status || '').toUpperCase();
    const intradayDecisionReason = String(status?.data_status?.source?.intraday_decision?.reason || '').toLowerCase();
    const realtimeOverlay = status?.data_status?.source?.realtime_overlay || null;
    const realtimeOverlayStatus = String(realtimeOverlay?.status || '').toUpperCase();
    const realtimeOverlayLabel = realtimeOverlayStatus
        ? `${realtimeOverlayStatus}${realtimeOverlay?.price_field ? ` (field ${realtimeOverlay.price_field})` : ''}`
        : null;
    const feedModeLabel =
        intradayStatus === 'LIVE' && intradayDecisionReason === 'upstream_intraday_stale'
            ? 'Realtime live, archive stale'
            : null;

    return (
        <IndustrialCard tone="secondary" className="relative overflow-hidden rounded-3xl" contentClassName="p-6 sm:p-8">
            <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex flex-wrap items-center gap-3">
                    <Network className="w-6 h-6 text-primary" />
                    <h2 className="text-xl font-bold text-white uppercase tracking-tighter">Data Lake Freshness</h2>
                    <span className={clsx(
                        'ml-2 px-2 py-0.5 rounded text-[10px] font-black tracking-tighter uppercase',
                        status?.freshness?.session_mode === 'ANALYSIS'
                            ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                            : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    )}>
                        {status?.freshness?.session_mode || 'LIVE'}
                    </span>
                </div>
                <button
                    onClick={triggerDataSync}
                    disabled={syncingData}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-primary/20 bg-primary/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-primary transition-colors hover:bg-primary/20 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
                >
                    <RefreshCcw size={12} className={clsx(syncingData && 'animate-spin')} />
                    Sync History + Intraday
                </button>
            </div>
            {syncStatusMessage ? (
                <p className="text-[10px] font-medium text-slate-400 -mt-4 mb-6">{syncStatusMessage}</p>
            ) : null}

            <div className="grid grid-cols-1 gap-10 md:grid-cols-2 md:gap-12">
                <div className="space-y-6">
                    <div className="flex justify-between items-center">
                        <h3 className="text-slate-400 font-bold text-xs uppercase tracking-widest">History (Daily)</h3>
                        <span className={clsx(
                            'px-2 py-0.5 rounded text-[10px] font-black tracking-tighter',
                            status?.data_status?.history?.status === 'FRESH' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'
                        )}>
                            {status?.data_status?.history?.status || 'UNKNOWN'}
                        </span>
                    </div>
                    <div className="space-y-4">
                        <DataMetric label="Last EOD Update" value={status?.data_status?.history?.last_updated || 'No Data'} />
                        <DataMetric label="Retention Depth" value={`${historySymbolCount} Tickers`} />
                        <DataMetric label="Latency" value={`${historyAgeHours} Hours`} />
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="flex justify-between items-center">
                        <h3 className="text-slate-400 font-bold text-xs uppercase tracking-widest">Intraday (1m)</h3>
                        <span className={clsx(
                            'px-2 py-0.5 rounded text-[10px] font-black tracking-tighter',
                            status?.data_status?.intraday?.status === 'LIVE' ? 'bg-cyan-500/10 text-cyan-500' : 'bg-rose-500/10 text-rose-500'
                        )}>
                            {status?.data_status?.intraday?.status || 'OFFLINE'}
                        </span>
                    </div>
                    <div className="space-y-4">
                        <DataMetric label="Last 1m Bar" value={status?.data_status?.intraday?.last_bar || 'Pending'} />
                        <DataMetric label="Source Engine" value={sourceEngine} />
                        {feedModeLabel ? <DataMetric label="Feed Mode" value={feedModeLabel} tone="warning" /> : null}
                        {realtimeOverlayLabel ? (
                            <DataMetric
                                label="Realtime Overlay"
                                value={realtimeOverlayLabel}
                                tone={realtimeOverlay?.active ? 'success' : realtimeOverlayStatus === 'STANDBY' ? 'warning' : 'neutral'}
                            />
                        ) : null}
                        {realtimeOverlay?.guard ? (
                            <DataMetric
                                label="Overlay Guard"
                                value={String(realtimeOverlay.guard)}
                                tone={realtimeOverlay?.active ? 'warning' : 'neutral'}
                            />
                        ) : null}
                        <DataMetric label="Drift" value={driftValue} />
                    </div>
                </div>
            </div>

            <div className="mt-12 h-1 w-full bg-slate-900 rounded-full overflow-hidden flex">
                <div className="h-full bg-emerald-500" style={{ width: '100%' }} />
            </div>
        </IndustrialCard>
    );
}

function DataMetric({ label, value, tone = 'neutral' }: { label: string; value: string; tone?: 'neutral' | 'warning' | 'success' }) {
    return (
        <div className="group flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <span className="text-[10px] font-bold text-slate-400 group-hover:text-slate-400 transition-colors uppercase tracking-tight">{label}</span>
            <span className={clsx(
                'section-surface-muted industrial-corner max-w-full break-words rounded px-2 py-0.5 text-left font-mono text-[11px] font-bold leading-tight sm:text-right',
                tone === 'warning' && 'text-amber-200',
                tone === 'success' && 'text-cyan-200',
                tone === 'neutral' && 'text-slate-300'
            )}>{value}</span>
        </div>
    );
}
