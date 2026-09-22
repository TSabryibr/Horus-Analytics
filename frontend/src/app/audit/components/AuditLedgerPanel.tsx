'use client';

import { Fragment } from 'react';
import { CheckCircle2, ChevronRight, Filter, History, ShieldAlert, Zap } from 'lucide-react';
import clsx from 'clsx';

import { AuditLog, Strategy } from '@/types/domain';

interface AuditLedgerPanelProps {
    strategies: Strategy[];
    logs: AuditLog[];
    filter: string;
    setFilter: (filter: string) => void;
    expandedRow: number | null;
    setExpandedRow: (row: number | null) => void;
}

function getReturnTone(value?: number) {
    if (value == null) return 'text-slate-500';
    if (value > 0) return 'text-emerald-400';
    if (value < 0) return 'text-rose-400';
    return 'text-slate-500';
}

function formatReturn(value?: number) {
    if (value == null) return '-';
    return `${value > 0 ? '+' : ''}${value}%`;
}

function ReturnPill({ label, value, emphasis = false }: { label: string; value?: number; emphasis?: boolean }) {
    return (
        <div
            className={clsx(
                'flex min-w-[4.35rem] flex-col gap-1 rounded-lg border px-2.5 py-2',
                emphasis ? 'border-white/10 bg-white/[0.04]' : 'border-white/6 bg-slate-950/35'
            )}
        >
            <span className="text-[8px] font-black uppercase tracking-[0.22em] text-slate-600">{label}</span>
            <span className={clsx('font-mono text-[11px] font-black', getReturnTone(value))}>{formatReturn(value)}</span>
        </div>
    );
}

function OutcomeBadge({ pnl5d }: { pnl5d: number }) {
    if (pnl5d > 1) {
        return (
            <div className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-400/20 bg-emerald-500/10 px-3 py-2 text-[9px] font-black uppercase tracking-[0.16em] text-emerald-300">
                <Zap size={10} /> Profit <span className="ml-1 text-[8px] bg-emerald-500/20 px-1 py-0.5 rounded border border-emerald-400/30">REALIZED ⚡</span>
            </div>
        );
    }

    if (pnl5d < -1) {
        return (
            <div className="inline-flex items-center gap-1.5 rounded-lg border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-[9px] font-black uppercase tracking-[0.16em] text-rose-300">
                <ShieldAlert size={10} /> Loss
            </div>
        );
    }

    return (
        <div className="inline-flex items-center gap-1.5 rounded-lg border border-white/8 bg-slate-900/70 px-3 py-2 text-[9px] font-black uppercase tracking-[0.16em] text-slate-500">
            Neutral
        </div>
    );
}

export function AuditLedgerPanel({
    strategies,
    logs,
    filter,
    setFilter,
    expandedRow,
    setExpandedRow,
}: AuditLedgerPanelProps) {
    const filteredLogs = logs
        .filter((log) => filter === 'ALL' || log.strategy === filter)
        .reverse();

    return (
        <div id="intelligence-log" className="col-span-12 flex flex-col overflow-hidden rounded-[1.6rem] border border-white/8 bg-slate-950/55">
            <div className="flex flex-col gap-5 border-b border-white/8 bg-slate-900/50 p-6 lg:flex-row lg:items-center lg:justify-between">
                <div className="min-w-0">
                    <h3 className="flex items-center gap-3 text-xl font-black uppercase tracking-tight text-white">
                        <History className="h-6 w-6 text-blue-400" />
                        Performance Ledger
                    </h3>
                    <p className="mt-1 text-xs font-medium text-slate-500">Detailed verification of past strategic signals</p>
                </div>

                <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center lg:w-auto">
                    <div className="grid grid-cols-2 overflow-hidden rounded-xl border border-white/8 bg-slate-950/40 sm:w-[16rem]">
                        <div className="border-r border-white/8 px-4 py-3">
                            <div className="text-[9px] font-black uppercase tracking-[0.24em] text-slate-600">Visible</div>
                            <div className="mt-1 font-mono text-sm font-black text-cyan-200">{filteredLogs.length}</div>
                        </div>
                        <div className="px-4 py-3">
                            <div className="text-[9px] font-black uppercase tracking-[0.24em] text-slate-600">Stored</div>
                            <div className="mt-1 font-mono text-sm font-black text-slate-300">{logs.length}</div>
                        </div>
                    </div>

                    <div className="flex w-full items-center gap-3 rounded-xl border border-white/8 bg-slate-950/40 p-1.5 sm:w-auto">
                        <div className="px-3">
                            <Filter size={14} className="text-slate-500" />
                        </div>
                        <select
                            className="w-full cursor-pointer bg-transparent py-2 pr-8 text-[10px] font-black uppercase tracking-[0.16em] text-slate-300 focus:outline-none"
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                        >
                            <option value="ALL">All Strategies</option>
                            {strategies.map((strategy) => (
                                <option key={strategy.name} value={strategy.name}>{strategy.name}</option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full min-w-[1080px] table-fixed text-left">
                    <colgroup>
                        <col className="w-[10.5rem]" />
                        <col className="w-[12rem]" />
                        <col className="w-[13rem]" />
                        <col className="w-[17rem]" />
                        <col className="w-[9rem]" />
                        <col className="w-[9rem]" />
                        <col className="w-[5rem]" />
                    </colgroup>
                    <thead className="bg-[#0f172a]/80">
                        <tr className="text-slate-500">
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em]">Entry Date</th>
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em]">Signal</th>
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em]">Origin</th>
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em]">Return Path</th>
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em]">Outcome</th>
                            <th className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em]">Execution</th>
                            <th className="px-6 py-4 text-right text-[10px] font-black uppercase tracking-[0.2em]">Details</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {filteredLogs.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="px-6 py-14 text-center">
                                    <div className="mx-auto max-w-xl space-y-3">
                                        <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">No Ledger Entries</div>
                                        <p className="text-sm leading-6 text-slate-400">
                                            No strategic signals match the current ledger filter.
                                        </p>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            filteredLogs.map((log, index) => {
                                const pnl5d = log.pnl_history?.['5D'] || log.pnl_history?.['1D'] || 0;
                                const isExpanded = expandedRow === index;
                                const rowKey = `${log.date}-${log.ticker}-${log.strategy}-${index}`;

                                return (
                                    <Fragment key={rowKey}>
                                        <tr className="group cursor-pointer align-top transition-colors hover:bg-white/[0.02]" onClick={() => setExpandedRow(isExpanded ? null : index)}>
                                            <td className="px-6 py-5">
                                                <div className="font-mono text-[11px] font-black uppercase tracking-[0.14em] text-slate-400">{log.date}</div>
                                                <div className="mt-1 text-[9px] font-black uppercase tracking-[0.18em] text-slate-600">{log.action || 'SIGNAL'}</div>
                                            </td>
                                            <td className="px-6 py-5">
                                                <div className="text-sm font-black uppercase tracking-tight text-white transition-colors group-hover:text-blue-400">{log.ticker}</div>
                                                <div className="mt-1 truncate text-[10px] font-medium text-slate-600">{log.details || 'No detail note'}</div>
                                            </td>
                                            <td className="px-6 py-5">
                                                <div className="inline-flex max-w-full rounded-lg border border-white/8 bg-slate-900/70 px-3 py-2 text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">
                                                    <span className="truncate">{log.strategy || 'Unassigned'}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-5">
                                                <div className="flex items-center gap-2">
                                                    <ReturnPill label="1D" value={log.pnl_history?.['1D']} />
                                                    <ReturnPill label="3D" value={log.pnl_history?.['3D']} />
                                                    <ReturnPill label="5D" value={log.pnl_history?.['5D']} emphasis />
                                                </div>
                                            </td>
                                            <td className="px-6 py-5">
                                                <OutcomeBadge pnl5d={pnl5d} />
                                            </td>
                                            <td className="px-6 py-5 uppercase">
                                                {log.converted ? (
                                                    <div className="inline-flex items-center gap-1.5 rounded-lg border border-blue-400/20 bg-blue-500/10 px-3 py-2 text-[9px] font-black tracking-[0.16em] text-blue-300">
                                                        <CheckCircle2 size={12} /> Traded
                                                    </div>
                                                ) : (
                                                    <div className="inline-flex rounded-lg border border-white/6 bg-slate-900/45 px-3 py-2 text-[9px] font-black tracking-[0.16em] text-slate-500">Ignored</div>
                                                )}
                                            </td>
                                            <td className="px-6 py-5 text-right">
                                                <button
                                                    type="button"
                                                    aria-label={`${isExpanded ? 'Collapse' : 'Expand'} ${log.ticker} ledger details`}
                                                    onClick={(event) => {
                                                        event.stopPropagation();
                                                        setExpandedRow(isExpanded ? null : index);
                                                    }}
                                                    className={clsx('rounded-xl p-2 text-slate-500 transition-all hover:bg-white/5 hover:text-blue-400', isExpanded ? 'rotate-90 bg-white/5 text-blue-400' : 'opacity-70 group-hover:opacity-100')}
                                                >
                                                    <ChevronRight size={16} />
                                                </button>
                                            </td>
                                        </tr>
                                        {isExpanded ? (
                                            <tr className="bg-slate-900/60">
                                                <td colSpan={7} className="px-6 py-6">
                                                    <div className="grid animate-in grid-cols-2 gap-4 rounded-xl border border-white/8 bg-slate-950/35 p-4 duration-300 fade-in slide-in-from-top-2 md:grid-cols-6">
                                                        <div>
                                                            <div className="mb-1 text-[10px] font-black uppercase tracking-widest text-slate-500">Entry Price</div>
                                                            <div className="text-sm font-bold text-white">EGP {log.entry_price?.toFixed(2) ?? 'N/A'}</div>
                                                        </div>
                                                        <div>
                                                            <div className="mb-1 text-[10px] font-black uppercase tracking-widest text-slate-500">1-Day Return</div>
                                                            <div className={clsx('text-sm font-bold', getReturnTone(log.pnl_history?.['1D']))}>
                                                                {formatReturn(log.pnl_history?.['1D'])}
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <div className="mb-1 text-[10px] font-black uppercase tracking-widest text-slate-500">3-Day Return</div>
                                                            <div className={clsx('text-sm font-bold', getReturnTone(log.pnl_history?.['3D']))}>
                                                                {formatReturn(log.pnl_history?.['3D'])}
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <div className="mb-1 text-[10px] font-black uppercase tracking-widest text-slate-500">5-Day Return</div>
                                                            <div className={clsx('text-sm font-bold', getReturnTone(log.pnl_history?.['5D']))}>
                                                                {formatReturn(log.pnl_history?.['5D'])}
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <div className="mb-1 text-[10px] font-black uppercase tracking-widest text-slate-500">Action</div>
                                                            <div className="text-sm font-bold uppercase text-white">{log.action || 'SIGNAL'}</div>
                                                        </div>
                                                        <div>
                                                            <div className="mb-1 text-[10px] font-black uppercase tracking-widest text-slate-500">Details</div>
                                                            <div className="text-sm leading-6 text-slate-300">{log.details || 'No detail note'}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                            </tr>
                                        ) : null}
                                    </Fragment>
                                );
                            })
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
