import { Radar, AlertTriangle, ShieldAlert } from 'lucide-react';
import { ReactNode } from 'react';
import type { StaleMeta } from '../hooks/useScannerExecution';
import { cn } from '@/lib/utils';
import { CommandHeader } from '@/app/components/custom/CommandHeader';
import { CommandToolbar } from '@/app/components/custom/CommandToolbar';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';

type ScannerShellProps = {
    children: ReactNode;
    controls: ReactNode;
    error?: string;
    errorTitle?: string;
    staleMeta?: StaleMeta | null;
    onBypassStale?: () => void;
    onConfirmHoliday?: () => void;
};

export function ScannerShell({
    children,
    controls,
    error,
    errorTitle = 'Connection Error',
    staleMeta,
    onBypassStale,
    onConfirmHoliday,
}: ScannerShellProps) {
    const isStaleError = errorTitle === 'Read-Only Stale Mode';
    const normalizeDate = (value?: string | null) => value?.split('T')[0]?.split(' ')[0] || null;
    const lastAvailableDate = normalizeDate(staleMeta?.lastUpdated);
    const expectedTradingDate = normalizeDate(staleMeta?.expectedDate);
    const shouldShowHolidayConfirm =
        Boolean(onConfirmHoliday) &&
        (!expectedTradingDate || !lastAvailableDate || expectedTradingDate !== lastAvailableDate);

    return (
        <div className="page-shell page-shell-wide">
            <CommandHeader
                eyebrow="Scanner Command"
                title="Market Scanner"
                description="Real-time technical analysis engine for tactical telemetry, stale-session gates, and execution-ready signal review."
                icon={<Radar className="h-8 w-8" />}
                statusItems={[
                    { label: 'Lane', value: 'Telemetry', tone: 'primary' },
                    { label: 'Session', value: error ? 'Degraded' : 'Active', tone: error ? 'warning' : 'success' },
                ]}
            />

            <CommandToolbar
                label="Scanner Controls"
                description="Filter execution profiles, adjust scanner inputs, and launch the next read without leaving the command frame."
            >
                <div className="w-full">{controls}</div>
            </CommandToolbar>

            {/* Error/Alert Toast */}
            {error && (
                <div className={cn(
                    "section-surface-muted industrial-corner rounded-[1.3rem] border p-4 animate-in fade-in slide-in-from-top-4 duration-500",
                    isStaleError ? "border-amber-500/30 bg-amber-500/10 text-amber-300" : "border-destructive/30 bg-destructive/10 text-destructive"
                )}>
                    <div className="flex items-center gap-4">
                        <div className={cn(
                            "size-8 rounded-sm flex items-center justify-center",
                            isStaleError ? "bg-amber-500/20" : "bg-destructive/20"
                        )}>
                            <AlertTriangle className="size-4" />
                        </div>
                        <div className="flex-1">
                            <h4 className="text-xs font-black uppercase tracking-widest">{errorTitle}</h4>
                            <p className="text-[11px] font-mono leading-relaxed mt-1 opacity-80">{error}</p>
                        </div>
                    </div>

                    {isStaleError && staleMeta && (
                        <div className="mt-4 pt-4 border-t border-white/5 flex flex-wrap items-center justify-between gap-4">
                            <div className="flex items-center gap-3 text-[10px] font-mono text-slate-400">
                                <ShieldAlert className="size-3" />
                                <span>Last Verified Data: <b className="text-amber-400">{staleMeta.lastUpdated || 'Null'}</b></span>
                            </div>
                            <div className="flex gap-2">
                                {onBypassStale && (
                                    <IndustrialButton
                                        type="button"
                                        onClick={onBypassStale}
                                        variant="secondary"
                                        size="sm"
                                        className="border-amber-500/30 bg-amber-500/20 text-amber-200 hover:bg-amber-500/30"
                                    >
                                        Proceed with Current Data
                                    </IndustrialButton>
                                )}
                                {shouldShowHolidayConfirm && (
                                    <IndustrialButton
                                        type="button"
                                        onClick={onConfirmHoliday}
                                        size="sm"
                                    >
                                        Mark as Holiday
                                    </IndustrialButton>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Main Content Feed */}
            <div className="space-y-8">
                {children}
            </div>
        </div>
    );
}
