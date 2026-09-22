import { ReactNode } from 'react';
import { BarChart3, RefreshCcw } from 'lucide-react';
import clsx from 'clsx';
import { CommandHeader } from '@/app/components/custom/CommandHeader';

interface AnalyticsShellProps {
    children: ReactNode;
    dataCount: number;
    isScanning: boolean;
    lastUpdatedLabel: string;
    onRunScan: () => void;
    bullCount?: number;
    bearCount?: number;
    highConvictionCount?: number;
}

export function AnalyticsShell({
    children,
    dataCount,
    isScanning,
    lastUpdatedLabel,
    onRunScan,
    bullCount,
    bearCount,
    highConvictionCount,
}: AnalyticsShellProps) {
    return (
        <div className="page-shell text-white">
            <CommandHeader
                eyebrow="Market Intelligence"
                title="Full Market Analytics"
                description={`Deep scan results across ${dataCount} tickers. Last updated: ${lastUpdatedLabel}.`}
                icon={<BarChart3 className="h-7 w-7" />}
                iconClassName="border-cyan-400/20 bg-cyan-500/10 text-cyan-200 shadow-[0_16px_34px_rgba(34,211,238,0.16)]"
                statusItems={[
                    { label: 'Coverage', value: `${dataCount} Tickers`, tone: 'primary' },
                    {
                        label: 'Market Breadth',
                        value: bullCount !== undefined && bearCount !== undefined ? `🟢 ${bullCount} Bull / 🔴 ${bearCount} Bear` : 'Full Scope',
                        tone: (bullCount || 0) >= (bearCount || 0) ? 'success' : 'danger',
                    },
                    {
                        label: 'High Conviction',
                        value: highConvictionCount !== undefined ? `${highConvictionCount} Setups` : 'Matrix Stream',
                        tone: 'info',
                    },
                    { label: 'Sync', value: lastUpdatedLabel, tone: 'muted' },
                ]}
                actions={
                    <button
                        onClick={onRunScan}
                        disabled={isScanning}
                        className={clsx(
                            'flex items-center rounded-[1rem] border px-4 py-2 text-[11px] font-black uppercase tracking-[0.24em] transition',
                            isScanning
                                ? 'cursor-not-allowed border-white/10 bg-white/[0.03] text-slate-500'
                                : 'border-cyan-400/25 bg-cyan-500/12 text-cyan-100 hover:border-cyan-300/40 hover:bg-cyan-500/18',
                        )}
                    >
                        <RefreshCcw className={clsx('mr-2 h-4 w-4', isScanning && 'animate-spin')} />
                        {isScanning ? 'Scanning...' : 'Run Fresh Scan'}
                    </button>
                }
            />
            {children}
        </div>
    );
}
