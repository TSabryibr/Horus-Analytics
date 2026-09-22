'use client';

import { ReactNode } from 'react';
import { Download, History, RefreshCw, Wifi, WifiOff } from 'lucide-react';
import clsx from 'clsx';
import { CommandHeader } from '@/app/components/custom/CommandHeader';

interface AuditShellProps {
    days: number | 'ALL';
    setDays: (days: number | 'ALL') => void;
    fetchData: () => void | Promise<void>;
    handleExport: () => void;
    loading: boolean;
    wsConnected: boolean;
    lastUpdated: Date | null;
    children: ReactNode;
}

const DAY_OPTIONS = [7, 30, 90, 'ALL'] as const;

function formatTimeSince(date: Date): string {
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
}

function isStale(lastUpdated: Date | null): boolean {
    if (!lastUpdated) return true;
    return Date.now() - lastUpdated.getTime() > 5 * 60 * 1000;
}

export function AuditShell({
    days,
    setDays,
    fetchData,
    handleExport,
    loading,
    wsConnected,
    lastUpdated,
    children,
}: AuditShellProps) {
    const stale = isStale(lastUpdated);

    return (
        <div className="page-shell">
            <CommandHeader
                eyebrow="Memory Ledger"
                title="Audit Trail"
                description="Institutional strategy verification, historical traceability, and market-memory review across stored execution evidence."
                icon={<History className="h-7 w-7" />}
                iconClassName="border-blue-400/20 bg-blue-500/10 text-blue-200 shadow-[0_16px_34px_rgba(96,165,250,0.16)]"
                statusItems={[
                    { label: 'Stream', value: wsConnected ? '⚡ WS LIVE' : '🔌 DISCONNECTED', tone: wsConnected ? 'success' : 'danger' },
                    { label: 'Sync', value: lastUpdated ? formatTimeSince(lastUpdated) : '--', tone: stale ? 'warning' : 'info' },
                    { label: 'Window', value: days === 'ALL' ? 'Total' : `${days} Days`, tone: 'primary' },
                    { label: 'State', value: loading ? 'Consulting' : 'Ready', tone: loading ? 'warning' : 'muted' },
                ]}
                actions={
                    <div className="flex w-full flex-wrap items-stretch gap-3 xl:w-auto xl:justify-end">
                        <div className="flex min-w-0 flex-1 flex-wrap gap-1 rounded-[1rem] border border-white/10 bg-white/[0.03] p-1 xl:flex-none">
                            {DAY_OPTIONS.map((value) => (
                                <button
                                    key={value}
                                    onClick={() => setDays(value)}
                                    className={clsx(
                                        'min-w-[4.5rem] flex-1 rounded-[0.85rem] px-4 py-2 text-[10px] font-black uppercase tracking-[0.24em] transition xl:flex-none',
                                        days === value
                                            ? 'bg-blue-500 text-slate-950'
                                            : 'text-slate-400 hover:bg-white/[0.05] hover:text-slate-200'
                                    )}
                                >
                                    {value === 'ALL' ? 'Total' : `${value}D`}
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={handleExport}
                            className="flex flex-1 items-center justify-center gap-2 rounded-[1rem] border border-white/10 bg-white/[0.03] px-6 py-2 text-[10px] font-black uppercase tracking-[0.24em] text-slate-200 transition hover:border-blue-400/25 hover:bg-white/[0.05] sm:flex-none"
                        >
                            <Download size={14} className="text-blue-300" /> Export Log
                        </button>

                        <button
                            type="button"
                            aria-label="Refresh audit data"
                            onClick={fetchData}
                            disabled={loading}
                            className="flex h-11 w-11 items-center justify-center rounded-[1rem] border border-white/10 bg-white/[0.03] transition hover:border-blue-400/25 hover:bg-white/[0.05] disabled:opacity-50"
                        >
                            <RefreshCw className={clsx('h-5 w-5 text-blue-300', loading && 'animate-spin')} />
                        </button>
                    </div>
                }
            />

            {!loading && lastUpdated && (
                <div className={clsx(
                    'flex items-center gap-2 rounded-xl px-4 py-2 text-[10px] font-black uppercase tracking-[0.2em] mb-4',
                    !wsConnected
                        ? 'border border-rose-400/30 bg-rose-500/10 text-rose-300'
                        : stale
                            ? 'border border-amber-400/30 bg-amber-500/10 text-amber-300'
                            : 'border border-emerald-400/20 bg-emerald-500/10 text-emerald-300'
                )}>
                    {!wsConnected ? (
                        <WifiOff size={12} />
                    ) : (
                        <Wifi size={12} />
                    )}
                    <span>
                        {!wsConnected
                            ? 'LIVE STREAM OFFLINE'
                            : stale
                                ? 'DATA MAY BE STALE'
                                : 'LIVE'}
                    </span>
                    <span className="text-[9px] font-normal normal-case tracking-normal text-slate-400">
                        · Updated {formatTimeSince(lastUpdated)}
                    </span>
                </div>
            )}

            {loading ? (
                <div className="section-surface industrial-corner flex min-h-[18rem] flex-col items-center justify-center space-y-4 rounded-[1.6rem]">
                    <RefreshCw className="h-12 w-12 animate-spin text-blue-400" />
                    <p className="font-mono text-[10px] uppercase tracking-[0.34em] text-slate-500">Consulting the ravens...</p>
                </div>
            ) : children}
        </div>
    );
}
