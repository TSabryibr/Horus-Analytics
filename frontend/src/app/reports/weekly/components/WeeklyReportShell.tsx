import clsx from 'clsx';
import { AlertTriangle, FileText, RefreshCw, Share2 } from 'lucide-react';
import { ReactNode } from 'react';
import { CommandHeader } from '@/app/components/custom/CommandHeader';

import { ReportPeriod } from '../lib/weeklyReportTransforms';

type CacheInfo = {
    cached: boolean;
    ttlSec: number | null;
    ageSec: number | null;
} | null;

type WeeklyReportShellProps = {
    broadcasting: boolean;
    cacheInfo?: CacheInfo;
    children: ReactNode;
    error?: string;
    feedback?: string;
    loading: boolean;
    onBroadcast: () => void;
    onRefresh: () => void;
    onSetPeriod: (period: ReportPeriod) => void;
    period: ReportPeriod;
};

function formatAge(sec: number | null): string {
    if (sec === null) return '--';
    if (sec < 60) return `${sec}s ago`;
    if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
    return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m ago`;
}

function formatTtl(sec: number | null): string {
    if (sec === null) return '--';
    if (sec <= 0) return 'expired';
    if (sec < 60) return `${sec}s`;
    if (sec < 3600) return `${Math.floor(sec / 60)}m`;
    return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`;
}

export function WeeklyReportShell({
    broadcasting,
    cacheInfo,
    children,
    error,
    feedback,
    loading,
    onBroadcast,
    onRefresh,
    onSetPeriod,
    period,
}: WeeklyReportShellProps) {
    const isStale = cacheInfo?.cached && cacheInfo.ageSec !== null && cacheInfo.ageSec > 300;

    return (
        <div className="page-shell page-shell-wide text-white/90 space-y-8">
            <CommandHeader
                eyebrow="Executive Intelligence"
                title="Market Analysis Report"
                description="Combined regime summary and signal-performance review for configured timeframe."
                icon={<FileText className="h-7 w-7" />}
                iconClassName="border-blue-400/20 bg-blue-500/10 text-blue-200 shadow-[0_16px_34px_rgba(59,130,246,0.16)]"
                statusItems={[
                    {
                        label: 'Period',
                        value: `📅 ${period.toUpperCase()} REVIEW`,
                        tone: 'primary',
                    },
                    {
                        label: 'Cache',
                        value: cacheInfo?.cached ? `⚡ CACHED (${formatAge(cacheInfo.ageSec)})` : '⚡ FRESH',
                        tone: isStale ? 'warning' : 'success',
                    },
                    {
                        label: 'Broadcast',
                        value: broadcasting ? '📡 TRANSMITTING' : '📡 READY',
                        tone: broadcasting ? 'warning' : 'info',
                    },
                    { label: 'Scope', value: 'EGX Ecosystem', tone: 'muted' },
                ]}
                actions={
                    <div className="flex items-center gap-2 flex-wrap">
                        <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-1 flex gap-1">
                            <button
                                type="button"
                                onClick={() => onSetPeriod('weekly')}
                                className={clsx(
                                    'px-3 py-1.5 rounded-[0.85rem] text-[10px] font-black uppercase tracking-[0.24em] transition',
                                    period === 'weekly'
                                        ? 'bg-blue-500 text-slate-950'
                                        : 'text-slate-300 hover:bg-white/[0.05]',
                                )}
                            >
                                Weekly
                            </button>
                            <button
                                type="button"
                                onClick={() => onSetPeriod('monthly')}
                                className={clsx(
                                    'px-3 py-1.5 rounded-[0.85rem] text-[10px] font-black uppercase tracking-[0.24em] transition',
                                    period === 'monthly'
                                        ? 'bg-blue-500 text-slate-950'
                                        : 'text-slate-300 hover:bg-white/[0.05]',
                                )}
                            >
                                Monthly
                            </button>
                        </div>
                        <button
                            type="button"
                            onClick={onRefresh}
                            disabled={loading}
                            className="action-secondary px-4 py-2 text-xs tracking-widest disabled:opacity-50"
                        >
                            <RefreshCw className={clsx('h-3 w-3 mr-2', loading && 'animate-spin')} />
                            Refresh
                        </button>
                        <button
                            type="button"
                            onClick={onBroadcast}
                            disabled={broadcasting || loading}
                            className="action-primary px-4 py-2 text-xs tracking-widest disabled:opacity-50"
                        >
                            <Share2 className="h-3 w-3 mr-2" />
                            Broadcast
                        </button>
                    </div>
                }
            />

            {error && (
                <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-sm flex items-center">
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    {error}
                </div>
            )}
            {feedback && (
                <div className="p-4 rounded-xl border border-blue-500/30 bg-blue-500/10 text-blue-200 text-sm">
                    {feedback}
                </div>
            )}

            {children}
        </div>
    );
}
