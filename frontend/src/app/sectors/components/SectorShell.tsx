import { Layers, RefreshCw } from 'lucide-react';
import clsx from 'clsx';
import { CommandHeader } from '@/app/components/custom/CommandHeader';

import type { SectorViewMode } from '../lib/sectorTransforms';

interface SectorShellProps {
    children: React.ReactNode;
    loading: boolean;
    onRefresh: () => void;
    sectorsList: readonly string[];
    selectedSector: string;
    setSelectedSector: (value: string) => void;
    setViewMode: (value: SectorViewMode) => void;
    viewMode: SectorViewMode;
    leadingCount?: number;
    benchmark?: string;
}

export function SectorShell({
    children,
    loading,
    onRefresh,
    sectorsList,
    selectedSector,
    setSelectedSector,
    setViewMode,
    viewMode,
    leadingCount,
    benchmark = 'EGX30',
}: SectorShellProps) {
    return (
        <div className="page-shell page-shell-compact">
            <CommandHeader
                eyebrow="Rotation Intelligence"
                title="Sector Rotation (RRG)"
                description={`${viewMode === 'sectors' ? 'Sector rotation' : 'Stock dispersion'} versus ${benchmark} in the shared command environment.`}
                icon={<Layers className="h-7 w-7" />}
                iconClassName="border-fuchsia-400/20 bg-fuchsia-500/10 text-fuchsia-200 shadow-[0_16px_34px_rgba(217,70,239,0.16)]"
                statusItems={[
                    {
                        label: 'Leading',
                        value: leadingCount !== undefined ? `🟢 ${leadingCount} Leading` : 'Rotation Matrix',
                        tone: 'success',
                    },
                    {
                        label: 'Benchmark',
                        value: benchmark,
                        tone: 'info',
                    },
                    { label: 'View', value: viewMode === 'sectors' ? 'Sectors' : 'Stocks', tone: 'primary' },
                    { label: 'Filter', value: selectedSector || 'All Sectors', tone: 'muted' },
                ]}
                actions={
                    <div className="flex items-center gap-2 flex-wrap">
                        <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-1 flex gap-1">
                            <button
                                onClick={() => setViewMode('sectors')}
                                className={clsx(
                                    'px-3 py-2 rounded-[0.85rem] text-[10px] font-black uppercase tracking-[0.24em] transition-all',
                                    viewMode === 'sectors' ? 'bg-fuchsia-500 text-slate-950' : 'text-slate-400 hover:text-slate-200',
                                )}
                            >
                                Sectors
                            </button>
                            <button
                                onClick={() => setViewMode('stocks')}
                                className={clsx(
                                    'px-3 py-2 rounded-[0.85rem] text-[10px] font-black uppercase tracking-[0.24em] transition-all',
                                    viewMode === 'stocks' ? 'bg-fuchsia-500 text-slate-950' : 'text-slate-400 hover:text-slate-200',
                                )}
                            >
                                Stocks
                            </button>
                        </div>

                        {viewMode === 'stocks' && (
                            <select
                                className="bg-slate-950/80 border border-white/10 text-[10px] font-bold text-slate-300 px-3 py-2 rounded-[1rem] focus:outline-none cursor-pointer"
                                value={selectedSector}
                                onChange={(e) => setSelectedSector(e.target.value)}
                            >
                                <option value="">All Sectors</option>
                                {sectorsList.map((sector) => <option key={sector} value={sector}>{sector}</option>)}
                            </select>
                        )}

                        <button
                            aria-label="Refresh sector rotation"
                            onClick={onRefresh}
                            disabled={loading}
                            className="p-2.5 bg-white/[0.03] border border-white/10 hover:bg-white/[0.05] rounded-[1rem] transition disabled:opacity-50"
                        >
                            <RefreshCw className={clsx('w-4 h-4 text-fuchsia-300', loading && 'animate-spin')} />
                        </button>
                    </div>
                }
            />
            {/* Absolute Market Regime & ADV Weighting Banner */}
            <div className="bg-purple-950/20 border border-purple-500/20 rounded-xl p-3 px-4 flex items-center justify-between text-xs text-slate-300">
                <div className="flex items-center space-x-2">
                    <span className="font-bold text-purple-300 uppercase tracking-wider text-[11px]">ADV Volume-Weighted Indices Active</span>
                    <span className="text-slate-500">•</span>
                    <span className="text-slate-400">Component stocks weighted by 20-day average daily turnover (EGP)</span>
                </div>
                <div className="flex items-center space-x-2 font-mono text-[11px]">
                    <span className="text-slate-400">Benchmark Trend:</span>
                    <span className="px-2 py-0.5 rounded font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">EGX30 UPTREND (Valid Dispatches)</span>
                </div>
            </div>

            {children}
        </div>
    );
}
