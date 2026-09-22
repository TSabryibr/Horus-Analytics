import { BarChart3 } from 'lucide-react';
import clsx from 'clsx';
import { formatReturn } from '../lib/seasonalityTransforms';

interface MonthData {
    label: string;
    average_return: number;
    win_rate: number;
    count: number;
}

interface SeasonalityMonthlyGridProps {
    months: MonthData[] | undefined;
    ticker: string;
}

export function SeasonalityMonthlyGrid({ months, ticker }: SeasonalityMonthlyGridProps) {
    if (!months) return null;

    return (
        <div className="section-surface industrial-corner rounded-xl p-6">
            <h3 className="font-bold text-slate-200 mb-6 flex items-center">
                <BarChart3 className="w-5 h-5 mr-3 text-rose-500" />
                Full Monthly Breakdown: {ticker}
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {months.map((m) => (
                    <div key={m.label} className="bg-slate-950/60 border border-white/10 rounded-lg p-4 group hover:border-rose-500/30 transition">
                        <div className="text-xs font-bold text-slate-500 uppercase mb-2">{m.label}</div>
                        <div className={clsx("text-lg font-bold mb-1", m.average_return >= 0 ? "text-emerald-500" : "text-rose-500")}>
                            {formatReturn(m.average_return)}
                        </div>
                        <div className="flex justify-between items-center text-[10px]">
                            <span className="text-slate-600">WR: {m.win_rate}%</span>
                            <span className="text-slate-700">N={m.count}</span>
                        </div>
                        {/* Small Visual Bar */}
                        <div className="mt-3 h-1 bg-slate-800 rounded-full overflow-hidden">
                            <div
                                className={clsx("h-full", m.average_return >= 0 ? "bg-emerald-500" : "bg-rose-500")}
                                style={{ width: `${Math.min(Math.abs(m.average_return) * 10, 100)}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
