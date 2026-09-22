import { ReactNode } from 'react';
import { Repeat, RefreshCw, Search } from 'lucide-react';
import clsx from 'clsx';
import { CommandHeader } from '@/app/components/custom/CommandHeader';
import type { ArbitrageUniverse } from '../hooks/useArbitrageRuntime';

interface ArbitrageShellProps {
    loading: boolean;
    universe: ArbitrageUniverse;
    onUniverseChange: (val: ArbitrageUniverse) => void;
    filter: string;
    onFilterChange: (val: string) => void;
    onRefresh: () => void;
    children: ReactNode;
    activeCount?: number;
    executionMode?: string;
}

export function ArbitrageShell({
    loading,
    universe,
    onUniverseChange,
    filter,
    onFilterChange,
    onRefresh,
    children,
    activeCount,
    executionMode = '⚡ SINGLE-LEG',
}: ArbitrageShellProps) {
    return (
        <div className="page-shell">
            <CommandHeader
                eyebrow="Spread Intelligence"
                title="Pair Trading Scanner"
                description="Lead-lag arbitrage and correlation scanning across configured market universes."
                icon={<Repeat className="h-7 w-7" />}
                iconClassName="border-emerald-400/20 bg-emerald-500/10 text-emerald-200 shadow-[0_16px_34px_rgba(16,185,129,0.16)]"
                statusItems={[
                    {
                        label: 'Active Pairs',
                        value: activeCount !== undefined ? `🟢 ${activeCount} Pairs Active` : 'Spread Matrix',
                        tone: 'success',
                    },
                    {
                        label: 'Execution',
                        value: executionMode,
                        tone: 'primary',
                    },
                    { label: 'Universe', value: universe === 'default' ? 'EGX100' : 'Extended', tone: 'warning' },
                    { label: 'Filter', value: filter.trim() || 'All Pairs', tone: 'muted' },
                ]}
                actions={
                    <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center lg:w-auto lg:flex-wrap lg:justify-end">
                        <div className="flex w-full rounded-[1rem] border border-white/10 bg-white/[0.03] p-1 sm:w-auto">
                            <button
                                type="button"
                                onClick={() => onUniverseChange('default')}
                                className={clsx(
                                    'flex-1 rounded-[0.85rem] px-3 py-2 text-[10px] font-black uppercase tracking-[0.24em] transition sm:flex-none',
                                    universe === 'default'
                                        ? 'bg-emerald-500 text-slate-950'
                                        : 'text-slate-300 hover:bg-white/[0.05]',
                                )}
                            >
                                EGX100
                            </button>
                            <button
                                type="button"
                                onClick={() => onUniverseChange('extended')}
                                className={clsx(
                                    'flex-1 rounded-[0.85rem] px-3 py-2 text-[10px] font-black uppercase tracking-[0.24em] transition sm:flex-none',
                                    universe === 'extended'
                                        ? 'bg-cyan-400 text-slate-950'
                                        : 'text-slate-300 hover:bg-white/[0.05]',
                                )}
                            >
                                Extended
                            </button>
                        </div>
                        <div className="relative w-full sm:flex-1 lg:w-64">
                            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                            <input
                                type="text"
                                placeholder="Filter pairs..."
                                value={filter}
                                onChange={(e) => onFilterChange(e.target.value)}
                                className="w-full rounded-[1rem] border border-white/10 bg-slate-950/80 py-2.5 pl-10 pr-4 text-sm text-slate-100 transition focus:border-emerald-500/40 focus:outline-none"
                            />
                        </div>
                        <button
                            type="button"
                            onClick={onRefresh}
                            disabled={loading}
                            aria-label="Refresh arbitrage data"
                            className="self-end rounded-[1rem] border border-white/10 bg-white/[0.03] p-2.5 transition hover:border-emerald-400/25 hover:bg-white/[0.05] disabled:opacity-50 sm:self-auto"
                        >
                            <RefreshCw className={clsx('h-5 w-5 text-slate-300', loading && 'animate-spin')} />
                        </button>
                    </div>
                }
            />
            {children}
        </div>
    );
}
