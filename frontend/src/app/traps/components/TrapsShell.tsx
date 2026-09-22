import { Target, RefreshCw } from 'lucide-react';
import clsx from 'clsx';
import { ReactNode } from 'react';
import { CommandHeader } from '@/app/components/custom/CommandHeader';

interface TrapsShellProps {
    loading: boolean;
    onRefresh: () => void;
    dominantBias?: string;
    maxDepth?: number;
    trapCount?: number;
    children: ReactNode;
}

export function TrapsShell({ loading, onRefresh, dominantBias, maxDepth, trapCount, children }: TrapsShellProps) {
    return (
        <div className="page-shell">
            <CommandHeader
                eyebrow="Failure Patterns"
                title="Bull Trap Detector"
                description="False breakout and breakdown detection for failed conviction moves, liquidity grabs, and reversal traps."
                icon={<Target className="h-7 w-7" />}
                iconClassName="border-rose-400/20 bg-rose-500/10 text-rose-200 shadow-[0_16px_34px_rgba(244,63,94,0.16)]"
                statusItems={[
                    { label: 'Scan', value: loading ? 'Refreshing' : 'Live Stream', tone: loading ? 'warning' : 'danger' },
                    { label: 'Dominant Bias', value: dominantBias || 'Failure Radar', tone: dominantBias?.includes('BULL') ? 'danger' : 'success' },
                    { label: 'Max Rejection', value: maxDepth !== undefined ? `${maxDepth.toFixed(1)}% ${maxDepth >= 4.0 ? 'SEVERE' : 'MODERATE'}` : 'Scanning Depth', tone: 'warning' },
                    { label: 'Active Traps', value: trapCount !== undefined ? `${trapCount} Staged` : 'Live Stream', tone: 'muted' },
                ]}
                actions={
                    <button
                        onClick={onRefresh}
                        disabled={loading}
                        aria-label="Refresh trap detection"
                        className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-2.5 transition hover:border-rose-400/25 hover:bg-white/[0.05] disabled:opacity-50"
                    >
                        <RefreshCw className={clsx('h-5 w-5 text-slate-300', loading && 'animate-spin')} />
                    </button>
                }
            />
            {children}
        </div>
    );
}
