'use client';

import clsx from 'clsx';

import type { SettingsDeckCard } from '../lib/settingsCommandDeck';

interface SettingsStatusMatrixProps {
    cards: SettingsDeckCard[];
}

const toneMap: Record<SettingsDeckCard['tone'], { border: string; tag: string; dot: string }> = {
    ready: { border: 'border-cyan-500/20 bg-cyan-500/[0.07]', tag: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-100', dot: 'bg-cyan-300' },
    warning: { border: 'border-amber-500/20 bg-amber-500/[0.07]', tag: 'border-amber-500/30 bg-amber-500/10 text-amber-100', dot: 'bg-amber-300' },
    danger: { border: 'border-orange-500/20 bg-orange-500/[0.08]', tag: 'border-orange-500/30 bg-orange-500/10 text-orange-100', dot: 'bg-orange-300' },
    neutral: { border: 'border-white/10 bg-white/[0.04]', tag: 'border-white/10 bg-white/[0.04] text-slate-300', dot: 'bg-slate-400' },
    active: { border: 'border-cyan-500/25 bg-cyan-500/[0.1]', tag: 'border-cyan-500/40 bg-cyan-500/15 text-cyan-50', dot: 'bg-cyan-200' },
};

export function SettingsStatusMatrix({ cards }: SettingsStatusMatrixProps) {
    return (
        <section aria-labelledby="settings-status-matrix" className="space-y-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <p className="meta-label text-slate-500">Runtime Snapshot</p>
                    <h2 id="settings-status-matrix" className="heading-title text-2xl font-bold text-white">
                        Operational Posture
                    </h2>
                </div>
                <p className="max-w-2xl text-sm leading-6 text-slate-500">
                    Deterministic state tags mirror the current frontend and local runtime signals without introducing a new backend status endpoint.
                </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {cards.map((card) => {
                    const tone = toneMap[card.tone];

                    return (
                        <article key={card.id} className={clsx('industrial-corner min-h-[136px] rounded-xl border p-4 transition-colors', tone.border)}>
                            <div className="flex items-start justify-between gap-3">
                                <div>
                                    <p className="meta-label text-slate-500">Status Node</p>
                                    <h3 className="mt-2 text-base font-semibold text-white">{card.title}</h3>
                                </div>
                                <span className={clsx('shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em]', tone.tag)}>
                                    {card.tag}
                                </span>
                            </div>

                            <div className="mt-5 space-y-3">
                                <div className="flex items-center gap-2">
                                    <span className={clsx('h-2.5 w-2.5 rounded-full', tone.dot)} />
                                    <span className="text-[11px] font-black uppercase tracking-[0.25em] text-slate-500">Operator Readout</span>
                                </div>
                                <p className="text-sm leading-6 text-slate-300">{card.detail}</p>
                                {card.meta ? <p className="font-mono text-xs text-slate-500">{card.meta}</p> : null}
                            </div>
                        </article>
                    );
                })}
            </div>
        </section>
    );
}
