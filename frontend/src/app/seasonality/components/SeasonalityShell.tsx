import { CalendarDays, Search, RefreshCw } from 'lucide-react';
import clsx from 'clsx';
import { CommandHeader } from '@/app/components/custom/CommandHeader';

interface SeasonalityShellProps {
    searchTicker: string;
    onSearchChange: (value: string) => void;
    onSearch: () => void;
    onRefresh: () => void;
    loading: boolean;
    children: React.ReactNode;
    currentMonthLabel?: string;
    activeBias?: string;
}

export function SeasonalityShell({
    searchTicker,
    onSearchChange,
    onSearch,
    onRefresh,
    loading,
    children,
    currentMonthLabel,
    activeBias,
}: SeasonalityShellProps) {
    return (
        <div className="page-shell">
            <CommandHeader
                eyebrow="Pattern Intelligence"
                title="Seasonal Pattern Analysis"
                description="Historical seasonality and time-cycle behavior for the active symbol or market scope."
                icon={<CalendarDays className="h-7 w-7" />}
                iconClassName="border-rose-400/20 bg-rose-500/10 text-rose-200 shadow-[0_16px_34px_rgba(244,63,94,0.16)]"
                statusItems={[
                    {
                        label: 'Cycle',
                        value: currentMonthLabel ? `📅 ${currentMonthLabel.toUpperCase()} CYCLE` : 'CALENDAR STREAM',
                        tone: 'primary',
                    },
                    { label: 'Ticker', value: searchTicker || 'Universe Scope', tone: 'warning' },
                    {
                        label: 'Bias',
                        value: activeBias || 'Historical Matrix',
                        tone: (activeBias || '').toUpperCase().includes('BEAR') ? 'danger' : 'success',
                    },
                    { label: 'Mode', value: 'Historical Patterns', tone: 'muted' },
                ]}
                actions={
                    <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center lg:w-auto lg:justify-end">
                        <div className="relative w-full sm:flex-1 lg:w-72">
                            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                            <input
                                type="text"
                                placeholder="Search specific ticker..."
                                value={searchTicker}
                                onChange={(e) => onSearchChange(e.target.value.toUpperCase())}
                                onKeyDown={(e) => e.key === 'Enter' && onSearch()}
                                className="w-full rounded-[1rem] border border-white/10 bg-slate-950/80 py-2.5 pl-10 pr-4 text-sm text-slate-100 transition focus:border-rose-500/40 focus:outline-none"
                            />
                        </div>
                        <button
                            onClick={onRefresh}
                            aria-label="Refresh seasonality data"
                            className="self-end rounded-[1rem] border border-white/10 bg-white/[0.03] p-2.5 transition hover:border-rose-400/25 hover:bg-white/[0.05] sm:self-auto"
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
