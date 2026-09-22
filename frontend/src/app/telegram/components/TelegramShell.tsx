'use client';

import type { ReactNode } from 'react';

import { Radio, Settings2 } from 'lucide-react';

type TelegramShellProps = {
    onOpenConfig: () => void;
    statusNode: ReactNode;
    children: ReactNode;
};

export function TelegramShell({ onOpenConfig, statusNode, children }: TelegramShellProps) {
    return (
        <div className="page-shell page-shell-wide flex flex-col gap-8 text-white/90 xl:gap-10">
            <div className="relative overflow-hidden rounded-[1.8rem] border border-white/8 bg-[linear-gradient(180deg,rgba(22,16,8,0.96),rgba(9,10,14,0.98))] px-5 py-5 shadow-[0_30px_100px_rgba(2,6,23,0.32)] md:px-6 md:py-6 xl:px-7 xl:py-7">
                <div className="pointer-events-none absolute inset-x-[18%] top-[-9rem] h-[24rem] rounded-full bg-[radial-gradient(circle,rgba(251,191,36,0.22),transparent_62%)] blur-3xl" />
                <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(135deg,rgba(251,191,36,0.05),transparent_32%),radial-gradient(circle_at_top_right,rgba(251,191,36,0.08),transparent_28%)]" />

                <div className="relative flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
                    <div className="max-w-3xl">
                        <div className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.36em] text-amber-200/70">
                            <span className="inline-flex h-10 w-10 items-center justify-center rounded-[1rem] border border-amber-200/20 bg-amber-300/10 text-amber-100">
                                <Radio className="h-4 w-4" />
                            </span>
                            Royal Release Desk
                        </div>
                        <h1 className="mt-4 font-heading text-[clamp(2rem,4.5vw,4rem)] font-black uppercase tracking-[0.08em] text-white">
                            Telegram Release Chamber
                        </h1>
                        <p className="mt-3 max-w-2xl text-sm leading-6 text-stone-300/85 md:text-[15px]">
                            Official Horus outbound authority for signal dispatch, follow-up stewardship, and premium channel control.
                        </p>
                    </div>

                    <div className="flex flex-col gap-3 xl:min-w-[22rem] xl:items-end">
                        {statusNode}
                        <button
                            onClick={onOpenConfig}
                            className="inline-flex items-center justify-center gap-2 rounded-[1rem] border border-amber-300/20 bg-amber-400/10 px-5 py-3 text-[10px] font-black uppercase tracking-[0.28em] text-amber-50 transition hover:border-amber-300/40 hover:bg-amber-300/14"
                        >
                            <Settings2 className="h-4 w-4" />
                            Configure Channel
                        </button>
                    </div>
                </div>
            </div>
            {children}
        </div>
    );
}
