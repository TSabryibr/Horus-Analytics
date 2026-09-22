'use client';

import type { ReactNode } from 'react';
import { RefreshCw, Search, Waves } from 'lucide-react';
import clsx from 'clsx';
import { CommandHeader } from '@/app/components/custom/CommandHeader';

interface WhalesShellProps {
    children: ReactNode;
    filter: string;
    isLoading: boolean;
    onFilterChange: (value: string) => void;
    onRefresh: () => void;
    netFlowBias?: string;
    leadSector?: string;
    candidateCount?: number;
}

export function WhalesShell({
    children,
    filter,
    isLoading,
    onFilterChange,
    onRefresh,
    netFlowBias,
    leadSector,
    candidateCount,
}: WhalesShellProps) {
    return (
        <div className="page-shell">
            <CommandHeader
                eyebrow="Flow Intelligence"
                title="Institutional Flow Tracker"
                description="Smart-money accumulation and distribution surveillance across live candidates and sector flow."
                icon={<Waves className="h-7 w-7" />}
                iconClassName="border-cyan-400/20 bg-cyan-500/10 text-cyan-200 shadow-[0_16px_34px_rgba(34,211,238,0.16)]"
                statusItems={[
                    { label: 'Filter', value: filter.trim() || 'All Flow', tone: 'primary' },
                    { label: 'Net Flow', value: netFlowBias || '🟢 Accumulation Lead', tone: netFlowBias?.includes('Distribution') ? 'danger' : 'success' },
                    { label: 'Lead Sector', value: leadSector || 'Market Scope', tone: 'info' },
                    { label: 'Setups', value: candidateCount !== undefined ? `${candidateCount} Candidates` : 'Smart Money Stream', tone: 'muted' },
                ]}
                actions={
                    <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center lg:w-auto lg:justify-end">
                        <div className="relative w-full sm:flex-1 lg:w-72">
                            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                            <input
                                type="text"
                                placeholder="Filter by ticker or sector..."
                                value={filter}
                                onChange={(event) => onFilterChange(event.target.value)}
                                className="w-full rounded-[1rem] border border-white/10 bg-slate-950/80 py-2.5 pl-10 pr-4 text-sm text-slate-100 transition focus:border-cyan-500/40 focus:outline-none"
                            />
                        </div>
                        <button
                            onClick={onRefresh}
                            disabled={isLoading}
                            aria-label="Refresh whale data"
                            className="self-end rounded-[1rem] border border-white/10 bg-white/[0.03] p-2.5 transition hover:border-cyan-400/25 hover:bg-white/[0.05] disabled:opacity-50 sm:self-auto"
                        >
                            <RefreshCw className={clsx('h-5 w-5 text-slate-300', isLoading && 'animate-spin')} />
                        </button>
                    </div>
                }
            />
            {children}
        </div>
    );
}
