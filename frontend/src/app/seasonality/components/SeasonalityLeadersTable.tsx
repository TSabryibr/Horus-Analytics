import { Star, BarChart3 } from 'lucide-react';
import clsx from 'clsx';
import { formatReturn } from '../lib/seasonalityTransforms';

interface Performer {
    ticker: string;
    avg_return: number;
    win_rate: number;
    best_month: string;
}

interface SeasonalityLeadersTableProps {
    performers: Performer[] | undefined;
    loading: boolean;
    currentMonthLabel: string;
    onTickerClick: (ticker: string) => void;
}

export function SeasonalityLeadersTable({
    performers,
    loading,
    currentMonthLabel,
    onTickerClick
}: SeasonalityLeadersTableProps) {
    return (
        <div className="lg:col-span-2 section-surface industrial-corner rounded-xl overflow-hidden flex flex-col">
            <div className="p-4 border-b border-white/10 bg-slate-950/50 flex justify-between items-center">
                <h3 className="font-bold text-slate-200 flex items-center capitalize">
                    <Star className="w-4 h-4 mr-2 text-yellow-500" />
                    {currentMonthLabel} Historical Leaders (Top 10)
                </h3>
                <span className="text-[10px] text-slate-500 font-mono">EGX30 Universe</span>
            </div>
            <div className="flex-1 overflow-x-auto custom-scrollbar">
                <table className="w-full text-left text-xs">
                    <thead>
                        <tr className="text-slate-500 border-b border-white/10">
                            <th className="p-4 font-medium uppercase tracking-wider">Ticker</th>
                            <th className="p-4 font-medium uppercase tracking-wider">Avg Return (%)</th>
                            <th className="p-4 font-medium uppercase tracking-wider">Win Rate</th>
                            <th className="p-4 font-medium uppercase tracking-wider">Best Month</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10 font-mono">
                        {performers?.map((p) => (
                            <tr key={p.ticker} className="hover:bg-white/[0.03] cursor-pointer" onClick={() => onTickerClick(p.ticker)}>
                                <td className="p-4 font-bold text-slate-100">
                                    <div className="flex items-center gap-1.5">
                                        <span>{p.ticker}</span>
                                        {Number(p.win_rate || 0) >= 75 && (
                                            <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 tracking-wider">
                                                TOP LEADER ⚡
                                            </span>
                                        )}
                                    </div>
                                </td>
                                <td className="p-4 text-emerald-400">{formatReturn(p.avg_return)}</td>
                                <td className="p-4 text-slate-300">{p.win_rate}%</td>
                                <td className="p-4 text-slate-400 uppercase">{p.best_month}</td>
                            </tr>
                        ))}
                        {loading && Array(5).fill(0).map((_, i) => (
                            <tr key={i} className="">
                                <td colSpan={4} className="p-4 bg-gray-800/10 mb-1 rounded h-10"></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
