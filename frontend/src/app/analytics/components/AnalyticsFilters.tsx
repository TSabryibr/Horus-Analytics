import { Search, ChevronDown } from 'lucide-react';
import clsx from 'clsx';

import { IndustrialButton } from '@/app/components/custom/IndustrialButton';
import { IndustrialInput } from '@/app/components/custom/IndustrialInput';
import { AnalyticsColumnState } from '../lib/analyticsTransforms';

interface AnalyticsFiltersProps {
    columns: AnalyticsColumnState;
    filterStatus: string;
    minScore: number;
    search: string;
    setFilterStatus: (value: string) => void;
    setMinScore: (value: number) => void;
    setSearch: (value: string) => void;
    setShowColMenu: (value: boolean) => void;
    showColMenu: boolean;
    toggleColumn: (key: string) => void;
}

export function AnalyticsFilters({
    columns,
    filterStatus,
    minScore,
    search,
    setFilterStatus,
    setMinScore,
    setSearch,
    setShowColMenu,
    showColMenu,
    toggleColumn,
}: AnalyticsFiltersProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <IndustrialInput
                type="text"
                placeholder="Search Ticker..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                shellClassName="min-h-[3.5rem]"
                leadingSlot={<Search className="h-4 w-4" />}
                aria-label="Search ticker"
            />

            <div className="relative">
                <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    disabled={search.length > 0}
                    aria-label="Filter by status"
                    className={clsx(
                        'section-surface-muted industrial-corner min-h-[3.5rem] w-full appearance-none border border-white/10 bg-transparent pl-4 pr-10 py-2.5 text-sm font-black uppercase tracking-[0.16em] text-slate-100 outline-none transition focus:border-primary/40 focus-visible:outline-none hover:border-white/16',
                        search.length > 0 && 'opacity-50 cursor-not-allowed',
                    )}
                >
                    <option value="ALL" className="bg-[#1A1A2E] text-white">All Statuses</option>
                    <option value="BUY" className="bg-[#1A1A2E] text-white">All Buys</option>
                    <option value="HIGH CONVICTION" className="bg-[#1A1A2E] text-white">High Conviction</option>
                    <option value="INSTITUTIONAL" className="bg-[#1A1A2E] text-white">Institutional Activity</option>
                    <option value="BREAKOUT" className="bg-[#1A1A2E] text-white">Breakouts</option>
                    <option value="WATCHLIST" className="bg-[#1A1A2E] text-white">Watchlist</option>
                </select>
                <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            </div>

            <div className={clsx('section-surface-muted industrial-corner flex min-h-[3.5rem] items-center gap-3 rounded-[1rem] border border-white/10 px-4 py-2', search.length > 0 && 'opacity-50')}>
                <span className="shrink-0 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Min Score: {minScore}</span>
                <input
                    type="range"
                    min="0"
                    max="10"
                    value={minScore}
                    onChange={(e) => setMinScore(parseInt(e.target.value, 10))}
                    disabled={search.length > 0}
                    className="flex-1"
                />
            </div>

            <div className="relative">
                <IndustrialButton
                    type="button"
                    onClick={() => setShowColMenu(!showColMenu)}
                    aria-expanded={showColMenu}
                    aria-haspopup="menu"
                    aria-controls="analytics-column-picker"
                    variant="secondary"
                    className="w-full justify-between"
                >
                    <span>Columns</span>
                    <ChevronDown className="h-4 w-4" />
                </IndustrialButton>

                {showColMenu && (
                    <div
                        id="analytics-column-picker"
                        role="menu"
                        aria-label="Analytics columns"
                        className="section-surface absolute top-full right-0 z-50 mt-2 grid w-[280px] grid-cols-2 gap-2 rounded-[1rem] border border-white/15 bg-slate-950/98 p-3 shadow-[0_24px_54px_rgba(0,0,0,0.72)]"
                    >
                        {Object.keys(columns).map((col) => (
                            <label key={col} role="menuitemcheckbox" aria-checked={columns[col as keyof AnalyticsColumnState]} className="flex items-center space-x-2 rounded-[0.8rem] px-2 py-2 text-xs text-slate-300 cursor-pointer hover:bg-white/[0.03] hover:text-white">
                                <input
                                    type="checkbox"
                                    checked={columns[col as keyof AnalyticsColumnState]}
                                    onChange={() => toggleColumn(col)}
                                    className="rounded bg-white/10 border-white/20"
                                />
                                <span>{col.replace('_', ' ')}</span>
                            </label>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
