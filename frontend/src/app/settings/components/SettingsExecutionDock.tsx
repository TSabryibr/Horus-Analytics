'use client';

import clsx from 'clsx';
import { ArrowRight, CircleDot } from 'lucide-react';

import type { SettingsState } from '../hooks/useSettingsRuntime';
import type { SettingsDeckCard } from '../lib/settingsCommandDeck';

interface SettingsExecutionDockProps {
    settings: SettingsState;
    executionCard?: SettingsDeckCard;
    schedulerCard?: SettingsDeckCard;
}

const toneClasses: Record<SettingsDeckCard['tone'], string> = {
    ready: 'border-cyan-500/30 bg-cyan-500/[0.09] text-cyan-50',
    warning: 'border-amber-500/30 bg-amber-500/[0.09] text-amber-50',
    danger: 'border-orange-500/30 bg-orange-500/[0.1] text-orange-50',
    neutral: 'border-white/10 bg-white/[0.04] text-slate-300',
    active: 'border-cyan-400/35 bg-cyan-400/[0.12] text-cyan-50',
};

export function SettingsExecutionDock({ settings, executionCard, schedulerCard }: SettingsExecutionDockProps) {
    const autoTradingTag = settings.AUTO_TRADE_ENABLED ? 'ON' : 'OFF';
    const signalExecutionTag = settings.SIGNAL_AUTO_EXECUTION_ENABLED ? 'ON' : 'OFF';
    const manualArmTag = settings.LIVE_ARM_GUARD_ENABLED ? 'REQUIRED' : 'BYPASSED';
    const gateTag = executionCard?.tag || (!settings.AUTO_TRADE_ENABLED ? 'AUTO_OFF' : !settings.SIGNAL_AUTO_EXECUTION_ENABLED ? 'SIGNAL_EXEC_OFF' : 'AUTO_ENTRY');
    const tone = executionCard?.tone || (!settings.AUTO_TRADE_ENABLED || !settings.SIGNAL_AUTO_EXECUTION_ENABLED ? 'danger' : 'ready');

    return (
        <section
            aria-label="Execution command strip"
            className="industrial-corner overflow-hidden rounded-xl border border-cyan-500/20 bg-[linear-gradient(135deg,rgba(6,16,24,0.96),rgba(3,7,18,0.98))]"
        >
            <div className="grid gap-px bg-white/[0.07] lg:grid-cols-[minmax(0,1.15fr)_repeat(4,minmax(8rem,0.55fr))_auto]">
                <div className="bg-slate-950/90 p-4">
                    <p className="meta-label text-slate-500">Live Policy</p>
                    <h2 className="mt-1 text-xl font-black uppercase tracking-[0.08em] text-white">Execution Gate</h2>
                    <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
                        {executionCard?.detail || 'Live entry state mirrors Auto Trading and daily manual arm policy.'}
                    </p>
                </div>

                <div className="bg-slate-950/88 p-4">
                    <p className="meta-label text-slate-500">Trading Flag</p>
                    <p className="mt-2 font-mono text-lg font-semibold text-white">{autoTradingTag}</p>
                </div>

                <div className="bg-slate-950/88 p-4">
                    <p className="meta-label text-slate-500">Entry Mode</p>
                    <p className={clsx('mt-2 inline-flex rounded-full border px-3 py-1 font-mono text-xs font-black uppercase tracking-[0.18em]', toneClasses[tone])}>
                        {gateTag}
                    </p>
                </div>

                <div className="bg-slate-950/88 p-4">
                    <p className="meta-label text-slate-500">Signal Exec</p>
                    <p className={clsx('mt-2 font-mono text-lg font-semibold', settings.SIGNAL_AUTO_EXECUTION_ENABLED ? 'text-white' : 'text-orange-200')}>
                        {signalExecutionTag}
                    </p>
                </div>

                <div className="bg-slate-950/88 p-4">
                    <p className="meta-label text-slate-500">Manual Arm</p>
                    <p className="mt-2 font-mono text-lg font-semibold text-white">{manualArmTag}</p>
                    {schedulerCard?.meta ? <p className="mt-1 truncate text-xs text-slate-500">{schedulerCard.meta}</p> : null}
                </div>

                <a
                    href="#strategy-risk"
                    aria-label="Jump to Strategy & Risk"
                    className="group flex min-h-[5.5rem] items-center justify-between gap-4 bg-cyan-500 px-4 py-3 text-slate-950 transition-colors hover:bg-cyan-400 lg:min-w-[13rem]"
                >
                    <span className="text-[11px] font-black uppercase tracking-[0.22em]">Jump to Strategy & Risk</span>
                    <CircleDot className="h-4 w-4 shrink-0" />
                    <ArrowRight className="h-4 w-4 shrink-0 transition-transform group-hover:translate-x-0.5" />
                </a>
            </div>
        </section>
    );
}
