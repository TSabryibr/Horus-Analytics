'use client';

import type { MutableRefObject } from 'react';

type TelegramActivityLogProps = {
    log: string[];
    onClear: () => void;
    logEndRef: MutableRefObject<HTMLDivElement | null>;
};

function entryTone(entry: string) {
    if (entry.includes('failed') || entry.includes('error')) {
        return 'text-rose-300';
    }
    if (entry.includes('completed') || entry.includes('processed') || entry.includes('sent')) {
        return 'text-emerald-300';
    }
    return 'text-slate-300';
}

export function TelegramActivityLog({ log, onClear, logEndRef }: TelegramActivityLogProps) {
    return (
        <div className="section-surface flex min-h-[280px] flex-1 flex-col rounded-[1.6rem] p-5">
            <div className="mb-4 flex items-center justify-between">
                <div>
                    <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Operator Ledger</div>
                    <h3 className="mt-2 font-heading text-lg font-black uppercase tracking-[0.12em] text-white">Transmission Log</h3>
                </div>
                <button onClick={onClear} className="text-[9px] font-bold uppercase tracking-[0.2em] text-slate-400 transition-colors hover:text-white">
                    Clear
                </button>
            </div>
            <div
                className="relative flex-1 space-y-2 overflow-y-auto rounded-[1.2rem] border border-white/8 bg-black/20 p-4 font-mono text-[10px] text-slate-400"
                style={{ maxHeight: '300px' }}
            >
                {log.length === 0 ? <span className="absolute inset-0 flex items-center justify-center text-xs opacity-30">Standby...</span> : null}
                {log.map((entry, index) => (
                    <div key={`${index}-${entry}`} className="break-words border-b border-white/5 pb-1.5 last:border-0 last:pb-0">
                        <span className="mr-2 text-slate-500">{entry.split(']')[0]}]</span>
                        <span className={entryTone(entry.toLowerCase())}>{entry.split(']').slice(1).join(']')}</span>
                    </div>
                ))}
                <div ref={logEndRef} />
            </div>
        </div>
    );
}
