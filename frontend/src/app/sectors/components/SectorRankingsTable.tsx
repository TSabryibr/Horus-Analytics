import { Activity } from 'lucide-react';
import clsx from 'clsx';

import {
    getSectorStatusColor,
    SectorQuadrantCounts,
    SectorRrgRow,
    SectorViewMode,
} from '../lib/sectorTransforms';

interface SectorRankingsTableProps {
    dataCount: number;
    quadrantCounts: SectorQuadrantCounts;
    rows: SectorRrgRow[];
    viewMode: SectorViewMode;
}

export function SectorRankingsTable({
    dataCount,
    quadrantCounts,
    rows,
    viewMode,
}: SectorRankingsTableProps) {
    return (
        <div className="bg-slate-900/30 border border-white/5 rounded-2xl overflow-hidden">
            <div className="p-4 border-b border-white/5 flex items-center justify-between">
                <h4 className="text-sm font-black text-white uppercase tracking-tight flex items-center gap-2">
                    <Activity className="w-4 h-4 text-purple-400" />
                    Rankings ({dataCount})
                </h4>
                <div className="flex gap-4 text-[10px] font-bold">
                    <span className="text-emerald-400">LEAD: {quadrantCounts.LEADING}</span>
                    <span className="text-blue-400">IMPR: {quadrantCounts.IMPROVING}</span>
                    <span className="text-yellow-400">WEAK: {quadrantCounts.WEAKENING}</span>
                    <span className="text-rose-400">LAG: {quadrantCounts.LAGGING}</span>
                </div>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead className="bg-slate-900/50">
                        <tr className="text-slate-500">
                            <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest">#</th>
                            <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest">Ticker / Sector</th>
                            {viewMode === 'stocks' && <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest">Sector</th>}
                            <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest text-center">Status</th>
                            <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest text-right">RS Ratio</th>
                            <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest text-right">Momentum</th>
                            <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest text-right">Velocity</th>
                            <th className="px-4 py-3 text-[10px] font-black uppercase tracking-widest text-right">Top Driver</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {rows.map((item, idx) => (
                            <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                                <td className="px-4 py-2 text-[10px] text-slate-400 font-mono">{idx + 1}</td>
                                <td className="px-4 py-2">
                                    <div className="flex items-center gap-1.5">
                                        <span className="text-xs font-black text-white uppercase">{item.ticker || item.Sector}</span>
                                        {String(item.Status || '').toUpperCase().includes('LEADING') && (
                                            <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 tracking-wider">
                                                LEADING 🚀
                                            </span>
                                        )}
                                    </div>
                                </td>
                                {viewMode === 'stocks' && (
                                    <td className="px-4 py-2">
                                        <span className="text-[10px] text-slate-500 truncate max-w-[150px] block">{item.Sector}</span>
                                    </td>
                                )}
                                <td className="px-4 py-2 text-center">
                                    <span className={clsx(
                                        'text-[9px] px-2 py-0.5 rounded border font-black uppercase inline-block',
                                        getSectorStatusColor(item.Status),
                                    )}>
                                        {item.Status}
                                    </span>
                                </td>
                                <td className="px-4 py-2 text-right">
                                    <span className={clsx(
                                        'text-xs font-bold font-mono',
                                        item.y > 0 ? 'text-emerald-400' : 'text-rose-400',
                                    )}>
                                        {item.y > 0 ? '+' : ''}{item.y?.toFixed(2)}%
                                    </span>
                                </td>
                                <td className="px-4 py-2 text-right">
                                    <span className={clsx(
                                        'text-xs font-bold font-mono',
                                        item.x > 0 ? 'text-emerald-400' : 'text-rose-400',
                                    )}>
                                        {item.x > 0 ? '+' : ''}{item.x?.toFixed(2)}
                                    </span>
                                </td>
                                <td className="px-4 py-2 text-right">
                                    <span className="text-xs font-mono font-semibold text-purple-300">
                                        {item.Velocity !== undefined ? item.Velocity.toFixed(2) : 'N/A'}
                                    </span>
                                </td>
                                <td className="px-4 py-2 text-right">
                                    <span className="text-xs font-mono font-bold text-emerald-400 uppercase">
                                        {item.TopDriver || 'N/A'}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
