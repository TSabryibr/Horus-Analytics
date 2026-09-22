import { ReactNode } from 'react';
import {
    AlertTriangle,
    CheckCircle,
    GanttChart,
    RefreshCw,
} from 'lucide-react';
import clsx from 'clsx';
import { CommandHeader } from '@/app/components/custom/CommandHeader';
import { formatTimeSince, getStreamStatus, isStale } from '@/utils/telemetry';

type StrategyShellProps = {
    children: ReactNode;
    errorMsg?: string;
    isLoading: boolean;
    manualMode: boolean;
    onRefresh: () => void;
    onToggleManualMode: () => void;
    successMsg?: string;
    activeRegime?: string;
    riskBudget?: string;
    wsConnected?: boolean;
    lastUpdated?: Date | null;
};

export function StrategyShell({
    children,
    errorMsg,
    isLoading,
    manualMode,
    onRefresh,
    onToggleManualMode,
    successMsg,
    activeRegime,
    riskBudget = '🛡️ 2.5% ATR',
    wsConnected,
    lastUpdated = null,
}: StrategyShellProps) {
    const streamInfo = getStreamStatus(wsConnected, isLoading);
    const syncTime = formatTimeSince(lastUpdated);
    const syncStale = isStale(lastUpdated);

    return (
        <div className="page-shell">
            <CommandHeader
                eyebrow="Adaptive Logic"
                title="Strategy Configuration"
                description="Dynamic strategy adaptation, operator overrides, and regime-aware rule control for the live command environment."
                icon={<GanttChart className="h-7 w-7" />}
                iconClassName="border-slate-300/15 bg-white/[0.04] text-slate-100 shadow-[0_16px_34px_rgba(148,163,184,0.12)]"
                statusItems={[
                    streamInfo,
                    { label: 'Sync', value: syncTime, tone: syncStale ? 'warning' : 'muted' },
                    {
                        label: 'Regime',
                        value: activeRegime ? `🟢 ${activeRegime.toUpperCase()}` : 'MARKET TERRAIN',
                        tone: 'success',
                    },
                    {
                        label: 'Risk Cap',
                        value: riskBudget,
                        tone: 'primary',
                    },
                    { label: 'Mode', value: manualMode ? 'Manual' : 'AI Mode', tone: manualMode ? 'warning' : 'info' },
                    { label: 'State', value: isLoading ? 'Refreshing' : 'Ready', tone: isLoading ? 'warning' : 'muted' },
                ]}
                actions={
                    <div className="flex items-center gap-4">
                        <button
                            onClick={onToggleManualMode}
                            className={clsx(
                                'rounded-[1rem] border px-4 py-2 text-[10px] font-black uppercase tracking-[0.24em] transition',
                                manualMode
                                    ? 'border-amber-400/30 bg-amber-500/12 text-amber-100'
                                    : 'border-white/10 bg-white/[0.03] text-slate-300 hover:bg-white/[0.05]',
                            )}
                        >
                            {manualMode ? 'Manual Mode' : 'AI Mode'}
                        </button>
                        <button
                            aria-label="refresh-strategy"
                            onClick={onRefresh}
                            disabled={isLoading}
                            className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-2.5 transition hover:bg-white/[0.05] disabled:opacity-50"
                        >
                            <RefreshCw className={clsx('h-5 w-5 text-slate-300', isLoading && 'animate-spin')} />
                        </button>
                    </div>
                }
            />

            {successMsg && (
                <div className="command-chip command-chip-success w-fit rounded-[999px]">
                    <CheckCircle className="h-4 w-4" />
                    <span>{successMsg}</span>
                </div>
            )}
            {errorMsg && (
                <div className="command-chip command-chip-danger w-fit rounded-[999px]">
                    <AlertTriangle className="h-4 w-4" />
                    <span>{errorMsg}</span>
                </div>
            )}

            {children}
        </div>
    );
}
