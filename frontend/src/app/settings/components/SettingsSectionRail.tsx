'use client';

import clsx from 'clsx';
import { useEffect, useState } from 'react';

import type { SettingsAttentionItem } from '../lib/settingsCommandDeck';

export interface SettingsRailSection {
    id: string;
    label: string;
    detail: string;
}

interface SettingsSectionRailProps {
    sections: SettingsRailSection[];
    attentionItems: SettingsAttentionItem[];
}

export function SettingsSectionRail({ sections, attentionItems }: SettingsSectionRailProps) {
    const [activeId, setActiveId] = useState(sections[0]?.id ?? '');

    useEffect(() => {
        if (typeof window === 'undefined' || typeof IntersectionObserver === 'undefined') return;
        const observer = new IntersectionObserver(
            (entries) => {
                const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
                if (visible?.target.id) setActiveId(visible.target.id);
            },
            { rootMargin: '-20% 0px -55% 0px', threshold: [0.15, 0.35, 0.6] }
        );

        sections.forEach((section) => {
            const node = document.getElementById(section.id);
            if (node) observer.observe(node);
        });

        return () => observer.disconnect();
    }, [sections]);

    return (
        <>
            <div className="sticky top-3 z-20 -mx-1 overflow-x-auto px-1 pb-2 lg:hidden">
                <div className="flex min-w-max gap-2 rounded-[1.25rem] border border-white/10 bg-[#07111b]/95 p-2 backdrop-blur">
                    {sections.map((section) => (
                        <a
                            key={section.id}
                            href={`#${section.id}`}
                            aria-label={`Open settings section: ${section.label}`}
                            onClick={() => setActiveId(section.id)}
                            className={clsx(
                                'rounded-xl px-3 py-2 text-[10px] font-black uppercase tracking-[0.2em] transition-colors',
                                activeId === section.id ? 'bg-cyan-500 text-slate-950' : 'bg-white/[0.04] text-slate-400'
                            )}
                        >
                            {section.label}
                        </a>
                    ))}
                </div>
            </div>

            <aside className="hidden lg:block">
                <div className="sticky top-6 space-y-6">
                    <div className="rounded-[1.75rem] border border-white/10 bg-[#06101a] p-5">
                        <div className="space-y-1">
                            <p className="meta-label text-slate-500">Section Rail</p>
                            <h2 className="heading-title text-xl font-bold text-white">Operator Focus</h2>
                        </div>

                        <nav aria-label="Settings section navigation" className="mt-5 space-y-2">
                            {sections.map((section) => (
                                <a
                                    key={section.id}
                                    href={`#${section.id}`}
                                    onClick={() => setActiveId(section.id)}
                                    className={clsx(
                                        'group block rounded-2xl border px-4 py-3 transition-colors',
                                        activeId === section.id
                                            ? 'border-cyan-500/30 bg-cyan-500/10'
                                            : 'border-white/10 bg-white/[0.03] hover:border-white/15 hover:bg-white/[0.05]'
                                    )}
                                >
                                    <div className="flex items-center justify-between gap-3">
                                        <span className="text-xs font-black uppercase tracking-[0.22em] text-white">{section.label}</span>
                                        <span className={clsx('h-2 w-2 rounded-full transition-colors', activeId === section.id ? 'bg-cyan-300' : 'bg-slate-600 group-hover:bg-slate-400')} />
                                    </div>
                                    <p className="mt-2 text-xs leading-5 text-slate-500">{section.detail}</p>
                                </a>
                            ))}
                        </nav>
                    </div>

                    <div className="rounded-[1.75rem] border border-white/10 bg-[#06101a] p-5">
                        <div className="space-y-1">
                            <p className="meta-label text-slate-500">Intervention Queue</p>
                            <h2 className="heading-title text-xl font-bold text-white">Attention</h2>
                        </div>

                        {attentionItems.length ? (
                            <div className="mt-5 space-y-3">
                                {attentionItems.map((item) => (
                                    <a
                                        key={item.id}
                                        href={`#${item.targetId}`}
                                        className={clsx(
                                            'block rounded-2xl border px-4 py-3 transition-colors',
                                            item.tone === 'danger'
                                                ? 'border-orange-500/20 bg-orange-500/[0.07]'
                                                : item.tone === 'warning'
                                                    ? 'border-amber-500/20 bg-amber-500/[0.07]'
                                                    : 'border-cyan-500/20 bg-cyan-500/[0.07]'
                                        )}
                                    >
                                        <p className="text-xs font-black uppercase tracking-[0.18em] text-white">{item.label}</p>
                                        <p className="mt-2 text-xs leading-5 text-slate-400">{item.detail}</p>
                                    </a>
                                ))}
                            </div>
                        ) : (
                            <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-500">
                                No active intervention queue. Runtime posture is nominal.
                            </div>
                        )}
                    </div>
                </div>
            </aside>
        </>
    );
}
