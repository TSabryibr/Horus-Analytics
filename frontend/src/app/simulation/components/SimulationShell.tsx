'use client';

import type { ReactNode } from 'react';

import clsx from 'clsx';
import { Activity, Flame, Skull, TrendingUp, Play, FlaskConical, History } from 'lucide-react';
import { CommandHeader } from '@/app/components/custom/CommandHeader';

import { formatTimeSince, getStreamStatus, isStale } from '@/utils/telemetry';

export type SimulationTab = 'CRASH' | 'RAGNAROK' | 'STRATEGY' | 'BACKTEST' | 'REPLAY' | 'DRYRUN';

type SimulationShellProps = {
    tab: SimulationTab;
    onSelectTab: (tab: SimulationTab) => void;
    profileControls?: ReactNode;
    children: ReactNode;
    wsConnected?: boolean;
    lastUpdated?: Date | null;
};

type CollectionKey = 'DRILLS' | 'PORTFOLIO' | 'STRATEGY_VALIDATION';

const COLLECTION_TITLES: Record<CollectionKey, string> = {
    DRILLS: 'Operational Fire Drills',
    PORTFOLIO: 'Portfolio Risk Lab',
    STRATEGY_VALIDATION: 'Strategy Validation Lab',
};

const TAB_CONFIG: Record<SimulationTab, {
    label: string;
    icon: typeof Skull;
    color: string;
    activeColor: string;
    title: string;
    description: string;
    chipTone: 'danger' | 'warning' | 'primary' | 'success' | 'muted';
    collection: CollectionKey;
}> = {
    CRASH: {
        label: 'Black Swan Crash',
        icon: Skull,
        color: 'text-slate-500 hover:bg-white/5 hover:text-slate-300',
        activeColor: 'bg-rose-500 text-white ring-1 ring-white/20',
        title: 'Black Swan Crash Simulation',
        description: 'Operational drill: simulate severe market crash scenarios against your portfolio.',
        chipTone: 'danger',
        collection: 'DRILLS',
    },
    RAGNAROK: {
        label: 'Ragnarok Total Liquidation',
        icon: Flame,
        color: 'text-slate-500 hover:bg-white/5 hover:text-slate-300',
        activeColor: 'bg-amber-500 text-white ring-1 ring-white/20',
        title: 'Ragnarok Total Liquidation Simulation',
        description: 'Operational drill: test extreme market stress and total market freeze conditions.',
        chipTone: 'warning',
        collection: 'DRILLS',
    },
    REPLAY: {
        label: 'Historical Session Replay',
        icon: Play,
        color: 'text-slate-500 hover:bg-white/5 hover:text-slate-300',
        activeColor: 'bg-emerald-500 text-white ring-1 ring-white/20',
        title: 'Historical Session Replay',
        description: 'Portfolio stress test: replay historic trading sessions step-by-step to inspect orderflow and rule evaluation.',
        chipTone: 'primary',
        collection: 'PORTFOLIO',
    },
    DRYRUN: {
        label: 'Live Data Dry-Run',
        icon: FlaskConical,
        color: 'text-slate-500 hover:bg-white/5 hover:text-slate-300',
        activeColor: 'bg-indigo-500 text-white ring-1 ring-white/20',
        title: 'Live Data Dry-Run',
        description: 'Portfolio stress test: run real-time market data through paper-trading logic without placing live orders.',
        chipTone: 'primary',
        collection: 'PORTFOLIO',
    },
    STRATEGY: {
        label: 'Trade History Monte Carlo',
        icon: History,
        color: 'text-slate-500 hover:bg-white/5 hover:text-slate-300',
        activeColor: 'bg-cyan-500 text-white ring-1 ring-white/20',
        title: 'Trade History Monte Carlo',
        description: 'Strategy validation: resample closed-trade history to estimate drawdown and threshold ruin risk.',
        chipTone: 'primary',
        collection: 'STRATEGY_VALIDATION',
    },
    BACKTEST: {
        label: 'Backtest',
        icon: TrendingUp,
        color: 'text-slate-500 hover:bg-white/5 hover:text-slate-300',
        activeColor: 'bg-sky-500 text-white ring-1 ring-white/20',
        title: 'Historical Backtest',
        description: 'Strategy validation: run historical strategy backtests with explicit capital, commission, and slippage assumptions.',
        chipTone: 'primary',
        collection: 'STRATEGY_VALIDATION',
    },
};

const COLLECTION_ORDER: CollectionKey[] = ['DRILLS', 'PORTFOLIO', 'STRATEGY_VALIDATION'];

export function SimulationShell({ tab, onSelectTab, profileControls, children, wsConnected, lastUpdated = null }: SimulationShellProps) {
    const config = TAB_CONFIG[tab];
    const Icon = config.icon;
    const streamInfo = getStreamStatus(wsConnected);
    const syncTime = formatTimeSince(lastUpdated);
    const syncStale = isStale(lastUpdated);

    return (
        <div className="page-shell page-shell-wide min-h-screen text-slate-200 selection:bg-cyan-500/30">
            <CommandHeader
                eyebrow="Probabilistic Stress Lab"
                title="Quant Simulator"
                description="Operational drills, portfolio risk stress tests, and strategy validation workflows."
                icon={<Activity className="h-7 w-7" />}
                iconClassName="border-orange-400/20 bg-orange-500/10 text-orange-200 shadow-[0_16px_34px_rgba(249,115,22,0.16)]"
                statusItems={[
                    streamInfo,
                    { label: 'Sync', value: syncTime, tone: syncStale ? 'warning' : 'muted' },
                    { label: 'Engine', value: 'Simulation', tone: 'warning' },
                    { label: 'Vector', value: tab, tone: config.chipTone },
                ]}
                actions={
                    <div className="grid gap-2 rounded-[1rem] border border-white/10 bg-white/[0.03] p-2 md:grid-cols-3">
                        {COLLECTION_ORDER.map((collection) => (
                            <div key={collection} className="space-y-2 rounded-xl border border-white/5 bg-black/20 p-2">
                                <div className="px-2 text-[9px] font-black uppercase tracking-[0.18em] text-slate-500">
                                    {COLLECTION_TITLES[collection]}
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {(Object.entries(TAB_CONFIG) as [SimulationTab, typeof config][])
                                        .filter(([, item]) => item.collection === collection)
                                        .map(([key, item]) => {
                                            const TabIcon = item.icon;
                                            return (
                                                <button
                                                    key={key}
                                                    onClick={() => onSelectTab(key)}
                                                    className={clsx(
                                                        'px-3 py-2 rounded-[0.9rem] text-[9px] font-black uppercase tracking-[0.15em] transition-all duration-300 flex items-center gap-1.5',
                                                        tab === key ? item.activeColor : item.color
                                                    )}
                                                >
                                                    <TabIcon className="w-3.5 h-3.5" />
                                                    {item.label}
                                                </button>
                                            );
                                        })}
                                </div>
                            </div>
                        ))}
                    </div>
                }
            />

            <section className="section-surface industrial-corner overflow-hidden rounded-[1.6rem] p-6 sm:p-8">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(249,115,22,0.12),transparent_36%),radial-gradient(circle_at_85%_18%,rgba(239,68,68,0.1),transparent_30%)] pointer-events-none" />
                <div className="relative z-10 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div className="flex items-start gap-4">
                        <div className="rounded-[1.1rem] border border-white/10 bg-slate-950/80 p-4">
                            <Icon className="h-7 w-7 text-orange-300" />
                        </div>
                        <div className="space-y-2">
                            <div className="meta-label text-orange-200/70">{COLLECTION_TITLES[config.collection]}</div>
                            <h2 className="heading-title text-2xl font-black tracking-[-0.04em] text-white">
                                {config.title}
                            </h2>
                            <p className="max-w-3xl text-sm leading-6 text-slate-300">
                                {config.description}
                            </p>
                        </div>
                    </div>
                </div>
                {profileControls ? <div className="relative z-10 mt-6">{profileControls}</div> : null}
            </section>

            <div className="space-y-12 pb-24">{children}</div>
        </div>
    );
}
