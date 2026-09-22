'use client';

import React from 'react';
import clsx from 'clsx';
import {
    AlertCircle,
    PauseCircle,
    PlayCircle,
    Radar,
    RefreshCw,
    Search,
    ShieldAlert,
    Zap,
} from 'lucide-react';
import { CommandHeader } from '@/app/components/custom/CommandHeader';
import { CommandToolbar } from '@/app/components/custom/CommandToolbar';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';

interface SovereignAlert {
    Type: string;
    Message: string;
}

interface LiveShellProps {
    lastUpdate: string;
    liveRunning: boolean;
    marketOpen: boolean;
    pollOptions: number[];
    autoRefreshMs: number;
    autoRefreshEnabled: boolean;
    ticker: string;
    tickers: string[];
    radarCount: number;
    showRadar: boolean;
    refreshing: boolean;
    wsConnected: boolean;
    error: string | null;
    sovereignAlerts: SovereignAlert[];
    onToggleRadar: () => void;
    onChangeTicker: (ticker: string) => void;
    onChangeAutoRefreshMs: (value: number) => void;
    onToggleAutoRefresh: () => void;
    onRefresh: () => void;
    onToggleLiveFeed: () => void;
    onDismissSovereignAlert: (index: number) => void;
    children: React.ReactNode;
}

export function LiveShell({
    lastUpdate,
    liveRunning,
    marketOpen,
    pollOptions,
    autoRefreshMs,
    autoRefreshEnabled,
    ticker,
    tickers,
    radarCount,
    showRadar,
    refreshing,
    wsConnected,
    error,
    sovereignAlerts,
    onToggleRadar,
    onChangeTicker,
    onChangeAutoRefreshMs,
    onToggleAutoRefresh,
    onRefresh,
    onToggleLiveFeed,
    onDismissSovereignAlert,
    children,
}: LiveShellProps) {
    return (
        <div className="page-shell page-shell-wide relative text-white">
            <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
                <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-cyan-500/10" />
                <div className="absolute bottom-0 right-0 h-96 w-96 rounded-full bg-emerald-500/10" />
            </div>

            <div className="flex flex-col gap-6">
                <CommandHeader
                    eyebrow="Live Monitoring"
                    title="Live Terminal"
                    description="Intraday telemetry, radar watchlists, and feed execution control for the active market session."
                    icon={<Zap className="h-8 w-8" />}
                    statusItems={[
                        { label: 'Transport', value: wsConnected ? '⚡ WS Live' : '🔄 HTTP Poll', tone: wsConnected ? 'success' : 'warning' },
                        { label: 'Focus', value: ticker || 'COMI', tone: 'info' },
                        { label: 'Feed', value: liveRunning ? 'Live' : 'Idle', tone: liveRunning ? 'success' : 'warning' },
                        { label: 'Market', value: marketOpen ? 'Open' : 'Closed', tone: marketOpen ? 'success' : 'muted' },
                        { label: 'Sync', value: lastUpdate || 'Pending', tone: 'primary' },
                    ]}
                />

                <CommandToolbar
                    label="Feed Controls"
                    description="Toggle radar visibility, switch ticker focus, tune polling cadence, and control live feed execution."
                >
                    <IndustrialButton
                        type="button"
                        variant={showRadar ? 'primary' : 'secondary'}
                        size="sm"
                        onClick={onToggleRadar}
                    >
                        <Radar className="h-4 w-4" />
                        Radar
                        <span className="rounded-full bg-black/40 px-1.5 py-0.5 text-[10px]">{radarCount}</span>
                    </IndustrialButton>

                    <div className="h-8 w-px bg-white/10" />

                    <div className="section-surface-muted industrial-corner flex items-center gap-2 rounded-[1rem] px-3">
                        <Search className="h-4 w-4 text-gray-500" />
                        <select
                            value={ticker}
                            onChange={(e) => onChangeTicker(e.target.value)}
                            className="min-w-[120px] bg-transparent py-3 text-sm font-black uppercase tracking-tight text-white outline-none cursor-pointer"
                        >
                            {tickers.length === 0 && <option className="bg-gray-900">COMI</option>}
                            {tickers.map((item) => (
                                <option key={item} value={item} className="bg-gray-900">{item}</option>
                            ))}
                        </select>
                    </div>

                    <div className="h-8 w-px bg-white/10" />

                    <select
                        value={autoRefreshMs}
                        onChange={(e) => onChangeAutoRefreshMs(Number(e.target.value))}
                        className="section-surface-muted industrial-corner rounded-[1rem] px-3 py-3 text-[11px] font-black uppercase tracking-widest text-gray-300 outline-none cursor-pointer"
                        title="Polling interval"
                    >
                        {pollOptions.map((value) => (
                            <option key={value} value={value} className="bg-gray-900">
                                {value >= 60000 ? `${value / 60000}m` : `${value / 1000}s`}
                            </option>
                        ))}
                    </select>

                    <IndustrialButton
                        type="button"
                        variant={autoRefreshEnabled ? 'primary' : 'ghost'}
                        size="sm"
                        onClick={onToggleAutoRefresh}
                        title={autoRefreshEnabled ? 'Pause auto refresh' : 'Resume auto refresh'}
                    >
                        {autoRefreshEnabled ? 'Auto On' : 'Auto Off'}
                    </IndustrialButton>

                    <IndustrialButton
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={onRefresh}
                        title="Force refresh"
                    >
                        <RefreshCw className={clsx('h-4 w-4', refreshing && 'animate-spin')} />
                        Refresh
                    </IndustrialButton>

                    <IndustrialButton
                        type="button"
                        variant={liveRunning ? 'secondary' : 'primary'}
                        size="sm"
                        onClick={onToggleLiveFeed}
                        disabled={!marketOpen && !liveRunning}
                    >
                        {liveRunning ? <PauseCircle className="h-4 w-4" /> : <PlayCircle className="h-4 w-4" />}
                        {liveRunning ? 'Stop Feed' : marketOpen ? 'Start Feed' : 'Market Closed'}
                    </IndustrialButton>
                </CommandToolbar>

                {!wsConnected && (
                    <div className="flex items-center gap-2 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
                        <AlertCircle className="h-4 w-4" />
                        Sovereign alerts offline — attempting reconnection
                    </div>
                )}

                {error && (
                    <div className="flex items-center gap-2 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                        <AlertCircle className="h-4 w-4" />
                        {error}
                    </div>
                )}

                {sovereignAlerts.length > 0 && (
                    <div className="flex flex-col gap-3">
                        {sovereignAlerts.map((alert, idx) => (
                            <div
                                key={`${alert.Type}-${idx}`}
                                className="animate-in fade-in zoom-in slide-in-from-right-8 duration-500 flex items-center justify-between gap-4 rounded-2xl border border-amber-500/40 bg-gradient-to-r from-amber-500/20 to-transparent px-4 py-3"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-xl bg-amber-500/20 text-amber-300">
                                        <ShieldAlert className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-black text-amber-200 tracking-tight uppercase">
                                            {alert.Type.replace(/_/g, ' ')}
                                        </p>
                                        <p className="text-[11px] text-amber-100/70 font-mono">
                                            {alert.Message}
                                        </p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => onDismissSovereignAlert(idx)}
                                    className="text-amber-500/60 hover:text-amber-400 transition"
                                >
                                    Dismiss
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                {children}
            </div>
        </div>
    );
}
