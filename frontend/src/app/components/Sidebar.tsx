'use client';

import clsx from 'clsx';
import { SidebarRuntimeState, useSidebarRuntime } from './hooks/useSidebarRuntime';
import { SidebarHeader } from './sidebar/SidebarHeader';
import { SidebarNavMenu } from './sidebar/SidebarNavMenu';
import { SidebarDataStatus } from './sidebar/SidebarDataStatus';
import { SidebarFooterActions } from './sidebar/SidebarFooterActions';

interface SidebarProps {
    runtime?: SidebarRuntimeState;
}

export default function Sidebar({ runtime }: SidebarProps) {
    const defaultRuntime = useSidebarRuntime();
    const sidebarRuntime = runtime ?? defaultRuntime;
    const {
        isCollapsed,
        hydrated,
        pathname,
        t,
        language,
        toggleLanguage,
        toggleSidebar,
        startSimulation,
        backendSourceLabel,
        feedModeLabel,
        lastSyncDisplay,
        systemStatus
    } = sidebarRuntime;

    return (
        <div className={clsx(
            "flex flex-col h-full  bg-[#0A0D14] border border-white/10  border-r border-white/5   overflow-y-auto custom-scrollbar transition-all duration-500 relative",
            isCollapsed ? "w-20" : "w-64"
        )}>
            <SidebarHeader 
                isCollapsed={isCollapsed} 
                toggleSidebar={toggleSidebar} 
            />

            <div className={clsx("pb-6 pt-11 flex-1 flex flex-col", isCollapsed ? "px-3" : "px-4")}>
                <SidebarNavMenu 
                    isCollapsed={isCollapsed}
                    pathname={pathname}
                    t={t}
                />
            </div>

            <SidebarDataStatus 
                isCollapsed={isCollapsed}
                hydrated={hydrated}
                systemStatus={systemStatus}
                backendSourceLabel={backendSourceLabel}
                feedModeLabel={feedModeLabel}
                lastSyncDisplay={lastSyncDisplay}
            />

            <SidebarFooterActions 
                isCollapsed={isCollapsed}
                language={language}
                toggleLanguage={toggleLanguage}
                startSimulation={startSimulation}
            />
        </div>
    );
}
