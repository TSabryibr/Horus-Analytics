import Link from 'next/link';
import clsx from 'clsx';

interface SidebarDataStatusProps {
    isCollapsed: boolean;
    hydrated: boolean;
    systemStatus: {
        code: string;
        label: string;
        dotClass: string;
        textClass: string;
    };
    backendSourceLabel: string;
    feedModeLabel?: string | null;
    lastSyncDisplay: string;
}

export function SidebarDataStatus({ 
    isCollapsed, 
    hydrated, 
    systemStatus, 
    backendSourceLabel, 
    feedModeLabel,
    lastSyncDisplay 
}: SidebarDataStatusProps) {
    return (
        <div className={clsx("py-4 border-t border-white/5", isCollapsed ? "px-3 flex justify-center" : "px-4")}>
            <Link href="/status" prefetch={false} className={clsx(
                " bg-[#0A0D14] border border-white/10  industrial-corner scan-line rounded-sm relative overflow-hidden group transition-all hover:bg-white/5 block",
                isCollapsed ? "p-2.5" : "p-3 w-full"
            )}>
                <div className="flex items-center gap-2.5 mb-3">
                    <div className={clsx(
                        "rounded-full transition-all flex-shrink-0  ",
                        isCollapsed ? "w-2 h-2" : "w-2.5 h-2.5",
                        systemStatus.dotClass,
                        systemStatus.code === 'FRESH' ? " " : " -none"
                    )} />
                    {!isCollapsed && (
                        <div className="flex flex-col">
                            <p className="text-[9px] font-black text-slate-500 tracking-[0.2em] uppercase">LINK_STATUS</p>
                            <p className={clsx(
                                "text-[10px] font-heading font-black uppercase tracking-tight",
                                systemStatus.textClass
                            )}>
                                {systemStatus.label}
                            </p>
                        </div>
                    )}
                </div>

                {!isCollapsed && (
                    <div className="space-y-2">
                        <div className="flex justify-between items-center text-[9px] font-mono">
                            <span className="text-slate-600 uppercase">SYNC_TIME</span>
                            <span className="text-slate-300 font-bold" suppressHydrationWarning>
                                {hydrated ? lastSyncDisplay : '--:--'}
                            </span>
                        </div>
                        <div className="flex justify-between items-center text-[9px] font-mono">
                            <span className="text-slate-600 uppercase">FEED_SRC</span>
                            <span className="text-slate-300 font-bold">
                                {backendSourceLabel}
                            </span>
                        </div>
                        {feedModeLabel && (
                            <div className="flex justify-between items-start gap-3 text-[9px] font-mono">
                                <span className="text-slate-600 uppercase">FEED_MODE</span>
                                <span className="max-w-[8.5rem] text-right font-bold leading-tight text-amber-200/90">
                                    {feedModeLabel}
                                </span>
                            </div>
                        )}
                    </div>
                )}
            </Link>
        </div>
    );
}
