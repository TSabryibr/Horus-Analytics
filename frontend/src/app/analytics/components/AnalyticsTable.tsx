import { ArrowUpDown } from 'lucide-react';

import { AnalyticsItem } from '@/types';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';

import { AnalyticsRow } from './AnalyticsRow';
import { AnalyticsColumnState } from '../lib/analyticsTransforms';
import { SignalDeskLaneKey } from '../../components/signal-desk/PromoteToDeskButtons';

interface AnalyticsTableProps {
    columns: AnalyticsColumnState;
    loading: boolean;
    onBroadcast: (item: AnalyticsItem) => void;
    onPromoteCandidate?: (item: AnalyticsItem, lane: SignalDeskLaneKey) => void | Promise<unknown>;
    onRequestSort: (key: string) => void;
    rows: AnalyticsItem[];
}

export function AnalyticsTable({
    columns,
    loading,
    onBroadcast,
    onPromoteCandidate,
    onRequestSort,
    rows,
}: AnalyticsTableProps) {
    const renderSortButton = (label: string, sortKey: string, accentClassName: string = 'text-slate-400') => (
        <button
            type="button"
            onClick={() => onRequestSort(sortKey)}
            aria-label={`Sort by ${label}`}
            className="group inline-flex items-center gap-1.5 text-left text-[10px] font-black uppercase tracking-[0.22em] text-slate-400 transition hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
        >
            <span className={accentClassName}>{label}</span>
            <ArrowUpDown className="h-3 w-3 text-slate-500 transition group-hover:text-primary" />
        </button>
    );

    return (
        <IndustrialCard
            tone="secondary"
            title="Signal Matrix"
            subtitle="Institutional ranking, execution posture, and tactical filters"
            contentClassName="overflow-x-auto p-0 custom-scrollbar"
        >
                <table className="w-full text-sm text-left">
                    <thead className="border-b border-white/8 bg-white/[0.02]">
                        <tr>
                            {columns.Ticker && (
                                <th scope="col" className="px-6 py-4">
                                    {renderSortButton('Ticker', 'Ticker', 'text-slate-200')}
                                </th>
                            )}
                            {columns.Price && (
                                <th scope="col" className="px-6 py-4">
                                    {renderSortButton('Price', 'Price')}
                                </th>
                            )}
                            {columns.Score && (
                                <th scope="col" className="px-6 py-4">
                                    {renderSortButton('Score', 'Signal_Score')}
                                </th>
                            )}
                            {columns.Status && (
                                <th scope="col" className="px-6 py-4">
                                    {renderSortButton('Status', 'Status')}
                                </th>
                            )}
                            {columns.Trend && (
                                <th scope="col" className="px-6 py-4">
                                    {renderSortButton('Trend', 'Trend')}
                                </th>
                            )}
                            {columns.RSI && (
                                <th scope="col" className="px-6 py-4">
                                    {renderSortButton('RSI', 'RSI')}
                                </th>
                            )}
                            {columns.Target_1 && <th scope="col" className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.22em] text-emerald-300">TP1</th>}
                            {columns.Target_2 && (
                                <th scope="col" className="px-6 py-4">
                                    {renderSortButton('TP2', 'Target_2', 'text-emerald-300')}
                                </th>
                            )}
                            {columns.Risk_Reward && (
                                <th scope="col" className="px-6 py-4">
                                    {renderSortButton('R/R', 'Risk_Reward_Ratio')}
                                </th>
                            )}
                            {columns.Stop_Loss && <th scope="col" className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.22em] text-rose-300">Stop Loss</th>}
                            {columns.Volume && <th scope="col" className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.22em] text-slate-400">Vol (M)</th>}
                            {columns.ATR && <th scope="col" className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.22em] text-slate-400">ATR</th>}
                            <th scope="col" className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.22em] text-slate-400">Desk</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {loading ? (
                            <tr>
                                <td colSpan={13} className="px-6 py-8 text-center text-gray-500">Loading Analytics...</td>
                            </tr>
                        ) : rows.length === 0 ? (
                            <tr>
                                <td colSpan={13} className="px-6 py-8 text-center text-gray-500">No stocks match your filters.</td>
                            </tr>
                        ) : (
                            rows.map((item, i) => (
                                <AnalyticsRow
                                    key={item.Ticker || i}
                                    item={item}
                                    columns={columns}
                                    onBroadcast={onBroadcast}
                                    onPromoteCandidate={onPromoteCandidate}
                                />
                            ))
                        )}
                    </tbody>
                </table>
        </IndustrialCard>
    );
}
