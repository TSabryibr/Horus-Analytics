'use client';

import clsx from 'clsx';
import { Activity, Clock, RefreshCw, Send, ShieldAlert, ShieldCheck } from 'lucide-react';

export interface LatencyHistogramBucket {
    bucket: string;
    min_ms: number | null;
    max_ms: number | null;
    count: number;
    pct: number;
}

export interface DeliverySlaStats {
    count: number;
    avg_ms: number | null;
    p50_ms: number | null;
    p90_ms: number | null;
    p95_ms: number | null;
    p99_ms: number | null;
    min_ms: number | null;
    max_ms: number | null;
    breached_count: number;
    breach_rate_pct: number;
    histogram?: LatencyHistogramBucket[];
}

export interface DeliverySlaMetrics {
    window_days?: number;
    from_date?: string;
    to_date?: string;
    target_latency_ms?: number;
    total_deliveries?: number;
    sent_count?: number;
    failed_count?: number;
    skipped_count?: number;
    dry_run_count?: number;
    success_rate_pct?: number;
    sla_compliant?: boolean;
    by_status?: Record<string, number>;
    latency_stats?: DeliverySlaStats;
    error?: string;
}

interface StatusSlaPanelProps {
    deliverySla?: DeliverySlaMetrics | null;
    onRefresh?: () => void;
}

const BUCKET_COLORS: Record<string, { bar: string; text: string }> = {
    '<250ms': { bar: 'bg-emerald-500', text: 'text-emerald-400' },
    '250-500ms': { bar: 'bg-cyan-500', text: 'text-cyan-400' },
    '500-1000ms': { bar: 'bg-sky-500', text: 'text-sky-400' },
    '1-2.5s': { bar: 'bg-amber-400', text: 'text-amber-300' },
    '2.5-5s': { bar: 'bg-orange-500', text: 'text-orange-400' },
    '>5s': { bar: 'bg-rose-500', text: 'text-rose-400' },
};

export function StatusSlaPanel({ deliverySla, onRefresh }: StatusSlaPanelProps) {
    const stats = deliverySla?.latency_stats;
    const totalDeliveries = Number(deliverySla?.total_deliveries ?? 0);
    const sentCount = Number(deliverySla?.sent_count ?? 0);
    const failedCount = Number(deliverySla?.failed_count ?? 0);
    const successRatePct = deliverySla?.success_rate_pct ?? (sentCount + failedCount > 0 ? (sentCount / (sentCount + failedCount)) * 100 : 100);
    const isCompliant = deliverySla?.sla_compliant ?? true;
    const targetLatencyMs = Number(deliverySla?.target_latency_ms ?? 5000);
    const histogram = stats?.histogram ?? [];

    const hasData = totalDeliveries > 0;

    return (
        <div className="bg-[#0A0D14] border border-white/10 rounded-3xl p-6 lg:p-8 space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div className="p-2.5 bg-primary/10 rounded-2xl border border-primary/20">
                        <Send className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className="text-lg font-bold text-white uppercase tracking-tight">
                                Telegram Delivery SLA & Latency
                            </h3>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-white/5 text-slate-400 border border-white/10">
                                {deliverySla?.window_days ?? 7}D Window
                            </span>
                        </div>
                        <p className="text-xs text-slate-400">
                            Round-trip outbound dispatch telemetry & distribution across subscribers and channels
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <span
                        className={clsx(
                            'px-3 py-1 text-[10px] font-black uppercase rounded-full tracking-wider border flex items-center gap-1.5',
                            !hasData
                                ? 'bg-slate-900/60 text-slate-400 border-slate-700/50'
                                : isCompliant
                                    ? 'bg-emerald-950/40 text-emerald-400 border-emerald-800/60'
                                    : 'bg-rose-950/40 text-rose-400 border-rose-800/60',
                        )}
                    >
                        {hasData && (
                            <span
                                className={clsx(
                                    'w-1.5 h-1.5 rounded-full',
                                    isCompliant ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400',
                                )}
                            />
                        )}
                        {!hasData ? 'STANDBY / NO DISPATCHES' : isCompliant ? 'SLA COMPLIANT' : 'SLA AT RISK'}
                    </span>

                    {onRefresh && (
                        <button
                            onClick={onRefresh}
                            title="Refresh Delivery SLA Metrics"
                            className="p-2 text-slate-400 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all"
                        >
                            <RefreshCw className="w-4 h-4" />
                        </button>
                    )}
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-black/30 border border-white/10 rounded-2xl p-4">
                    <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Target SLA</div>
                    <div className="mt-1 text-xl font-mono font-bold text-white">
                        &lt; {targetLatencyMs.toLocaleString()} ms
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">Max latency threshold</div>
                </div>

                <div className="bg-black/30 border border-white/10 rounded-2xl p-4">
                    <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Success Rate</div>
                    <div
                        className={clsx(
                            'mt-1 text-xl font-mono font-bold',
                            successRatePct >= 95 ? 'text-emerald-400' : 'text-rose-400',
                        )}
                    >
                        {successRatePct.toFixed(1)}%
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">
                        {sentCount} sent / {failedCount} failed
                    </div>
                </div>

                <div className="bg-black/30 border border-white/10 rounded-2xl p-4">
                    <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">P95 Latency</div>
                    <div className="mt-1 text-xl font-mono font-bold text-cyan-300">
                        {stats?.p95_ms !== null && stats?.p95_ms !== undefined ? `${stats.p95_ms.toLocaleString()} ms` : '--'}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">
                        P50: {stats?.p50_ms !== null && stats?.p50_ms !== undefined ? `${stats.p50_ms} ms` : '--'}
                    </div>
                </div>

                <div className="bg-black/30 border border-white/10 rounded-2xl p-4">
                    <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Breached Sla</div>
                    <div
                        className={clsx(
                            'mt-1 text-xl font-mono font-bold',
                            (stats?.breached_count ?? 0) === 0 ? 'text-slate-300' : 'text-rose-400',
                        )}
                    >
                        {stats?.breached_count ?? 0}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">
                        Rate: {stats?.breach_rate_pct ?? 0}%
                    </div>
                </div>
            </div>

            {/* Latency Histogram Distribution */}
            <div className="border-t border-white/10 pt-5 space-y-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-cyan-400" />
                        <h4 className="text-xs font-black uppercase tracking-wider text-slate-300">
                            Dispatch Latency Distribution Histogram
                        </h4>
                    </div>
                    <span className="text-[11px] font-mono text-slate-400">
                        Total Measured: {stats?.count ?? 0}
                    </span>
                </div>

                {hasData && histogram.length > 0 ? (
                    <div className="space-y-2.5">
                        {histogram.map((item) => {
                            const config = BUCKET_COLORS[item.bucket] || {
                                bar: 'bg-slate-500',
                                text: 'text-slate-400',
                            };
                            return (
                                <div key={item.bucket} className="space-y-1">
                                    <div className="flex items-center justify-between text-[11px] font-mono">
                                        <span className={clsx('font-bold', config.text)}>
                                            {item.bucket}
                                        </span>
                                        <span className="text-slate-400">
                                            {item.count} <span className="text-slate-500">({item.pct.toFixed(1)}%)</span>
                                        </span>
                                    </div>
                                    <div className="h-2 w-full rounded-full bg-white/5 overflow-hidden">
                                        <div
                                            className={clsx('h-full rounded-full transition-all duration-500', config.bar)}
                                            style={{ width: `${Math.max(item.pct, item.count > 0 ? 2 : 0)}%` }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="p-6 text-center rounded-2xl bg-black/20 border border-white/5">
                        <Clock className="w-6 h-6 text-slate-600 mx-auto mb-2" />
                        <p className="text-xs text-slate-400">
                            No dispatch events recorded in this window yet.
                        </p>
                        <p className="text-[11px] text-slate-500 mt-1">
                            Live round-trip Telegram distribution buckets will display once signals are issued.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
