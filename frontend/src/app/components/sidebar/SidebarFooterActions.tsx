import { Globe, Clock } from 'lucide-react';
import clsx from 'clsx';

interface SidebarFooterActionsProps {
    isCollapsed: boolean;
    language: string;
    toggleLanguage: () => void;
    startSimulation: () => void;
}

export function SidebarFooterActions({ 
    isCollapsed, 
    language, 
    toggleLanguage, 
    startSimulation 
}: SidebarFooterActionsProps) {
    return (
        <>
            <div className={clsx("pb-3", isCollapsed ? "px-3 flex justify-center" : "px-4")}>
                <button
                    onClick={toggleLanguage}
                    className={clsx(
                        "group flex items-center w-full rounded-sm transition-all duration-300 p-3",
                        isCollapsed ? "justify-center" : "",
                        "bg-white/5 text-slate-400 hover:text-white hover:bg-white/10 border border-white/5 active:scale-95 transition-all"
                    )}
                    title={isCollapsed ? "Toggle Language" : ""}
                >
                    <Globe className={clsx(
                        "h-4 w-4 transition-all duration-500",
                        isCollapsed ? "mr-0" : "mr-4",
                        "group-hover:rotate-12"
                    )} />
                    {!isCollapsed && (
                        <span className="text-[11px] font-black uppercase tracking-[0.2em]">
                            {language === 'en' ? 'Arabic' : 'English'}
                        </span>
                    )}
                </button>
            </div>

            <div className={clsx("pb-6", isCollapsed ? "px-3 flex justify-center" : "px-4")}>
                <button
                    onClick={startSimulation}
                    className={clsx(
                        "group flex items-center w-full rounded-sm transition-all duration-300 p-3",
                        isCollapsed ? "justify-center" : "",
                        "bg-primary text-primary-foreground hover:brightness-125 industrial-corner"
                    )}
                    title={isCollapsed ? "Time Travel Simulation" : ""}
                >
                    <Clock className={clsx(
                        "h-4 w-4 transition-all duration-500",
                        isCollapsed ? "mr-0" : "mr-4",
                        "group-hover:rotate-[-45deg]"
                    )} />
                    {!isCollapsed && (
                        <span className="text-[11px] font-black uppercase tracking-[0.2em]">
                            Matrix Travel
                        </span>
                    )}
                </button>
            </div>
        </>
    );
}
