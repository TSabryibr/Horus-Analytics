'use client';

import type { ReactNode } from 'react';

interface SettingsOperatorModuleProps {
    id: string;
    label: string;
    title: string;
    description: string;
    aside?: ReactNode;
    children: ReactNode;
}

export function SettingsOperatorModule({
    id,
    label,
    title,
    description,
    aside,
    children,
}: SettingsOperatorModuleProps) {
    return (
        <section id={id} className="scroll-mt-28 space-y-5">
            <div className="flex flex-col gap-4 border-b border-white/10 pb-5 xl:flex-row xl:items-end xl:justify-between">
                <div className="space-y-2">
                    <p className="meta-label text-slate-500">{label}</p>
                    <h2 className="heading-title text-3xl font-bold text-white">{title}</h2>
                    <p className="max-w-3xl text-sm leading-6 text-slate-400">{description}</p>
                </div>
                {aside ? <div className="shrink-0">{aside}</div> : null}
            </div>
            {children}
        </section>
    );
}
