import { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import clsx from 'clsx';
import { ChevronLeft, ChevronRight, HelpCircle } from 'lucide-react';

import { TerminalManual } from '../TerminalManual';

interface SidebarHeaderProps {
    isCollapsed: boolean;
    toggleSidebar: () => void;
}

export function SidebarHeader({ isCollapsed, toggleSidebar }: SidebarHeaderProps) {
    const [isManualOpen, setIsManualOpen] = useState(false);

    return (
        <>
            {/* HELP TRIGGER */}
            <button
                onClick={() => setIsManualOpen(true)}
                aria-label="Open Terminal Manual"
                className="absolute top-2 right-2 text-slate-700 hover:text-primary transition-colors z-50 p-1"
            >
                <HelpCircle size={14} />
            </button>

            <TerminalManual isOpen={isManualOpen} onClose={() => setIsManualOpen(false)} />
            
            {/* COLLAPSE TOGGLE */}
            <button
                onClick={toggleSidebar}
                aria-label="Toggle Sidebar"
                className="absolute left-1/2 -translate-x-1/2 top-4 bg-primary text-primary-foreground rounded-sm p-1 z-50 hover:scale-110 transition-transform active:scale-95"
            >
                {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
            </button>

            <Link
                href="/"
                prefetch={false}
                className={clsx("flex items-center mb-10 group transition-all", isCollapsed ? "justify-center" : "px-2")}
            >
                <div className={clsx("relative flex-shrink-0 transition-all duration-500", isCollapsed ? "w-10 h-10 mr-0" : "w-12 h-12 mr-4")}>
                    <Image
                        src="/android-chrome-192x192.png"
                        alt="Horus Logo"
                        width={48}
                        height={49}
                        className="h-auto w-full object-contain transition-all duration-700 group-hover:scale-110 group-hover:rotate-3 horus-logo-float filter"
                        style={{ height: 'auto' }}
                    />
                </div>
                {!isCollapsed && (
                    <div className="flex flex-col">
                        <h1 className="text-sm font-heading font-black tracking-[0.2em] text-white uppercase group-hover:text-primary transition-colors">
                            HORUS <span className="text-amber-200/70">ANALYTICS</span>
                        </h1>
                        <span className="text-[9px] font-mono text-slate-500 tracking-tighter uppercase">EGX Command Shell</span>
                    </div>
                )}
            </Link>
        </>
    );
}
