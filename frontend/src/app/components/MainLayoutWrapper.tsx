'use client';

import React from 'react';
import { IndustrialNavbar } from './custom/IndustrialNavbar';
import SimulationBanner from './SimulationBanner';

export default function MainLayoutWrapper({ children }: { children: React.ReactNode }) {
    return (
        <div className="relative isolate flex min-h-screen flex-col bg-background text-foreground font-sans selection:bg-primary/30 selection:text-white">
            <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.14),transparent_30%),radial-gradient(circle_at_82%_14%,rgba(56,189,248,0.08),transparent_24%),linear-gradient(180deg,rgba(2,6,23,0),rgba(2,6,23,0.32))]" />
                <div className="absolute -left-24 top-[-7rem] h-[24rem] w-[24rem] rounded-full bg-cyan-400/10 blur-3xl" />
                <div className="absolute right-[8%] top-[8rem] h-[18rem] w-[18rem] rounded-full bg-sky-500/10 blur-3xl" />
            </div>

            {/* Top Navigation */}
            <IndustrialNavbar />

            {/* Global Simulation Banner */}
            <SimulationBanner />

            {/* Main Application Feed */}
            <main className="relative flex flex-1 flex-col overflow-x-clip">
                {/* Background Scan Line Overlay */}
                <div className="pointer-events-none absolute inset-0 overflow-hidden">
                    <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-primary/45 via-primary/10 to-transparent" />
                    <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.02),transparent_16%,transparent_84%,rgba(255,255,255,0.02))] opacity-70" />
                    <div className="absolute inset-0 scan-line opacity-[0.02]" />
                </div>

                {/* Page Content */}
                <div className="relative z-10 flex min-h-0 flex-1 flex-col">
                    {children}
                </div>
            </main>

            {/* Micro Industrial Footer */}
            <footer className="industrial-border flex h-8 shrink-0 items-center border-x-0 border-b-0 border-t bg-slate-950/[0.85] px-3 backdrop-blur-xl sm:px-5 xl:px-6">
                <div className="mx-auto flex w-full max-w-[1700px] items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <span className="text-[8px] font-mono uppercase tracking-[0.34em] text-slate-600">
                            Core System: Ver 10.4.26
                        </span>
                        <span className="text-[8px] font-mono text-slate-700">|</span>
                        <span className="text-[8px] font-mono uppercase tracking-[0.34em] text-slate-600">
                            Encrypted Data Link Active
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-[8px] font-mono uppercase tracking-[0.34em] text-slate-600">EGX</span>
                        <div className="size-1 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.75)]" />
                    </div>
                </div>
            </footer>
        </div>
    );
}
