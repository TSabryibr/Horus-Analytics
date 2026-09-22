import React from 'react';
import clsx from 'clsx';
import { InfoTooltip } from './InfoTooltip';

interface SignalCardProps {
    ticker: string;
    signal_type: 'BUY' | 'SELL' | string;
    price: number | string;
    score: number;
    date: string;
}

const formatPrice = (priceVal: number | string) => {
    const n = Number(priceVal);
    if (!Number.isFinite(n)) return '00.000';
    return n.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 3 });
};

const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }).toUpperCase();
};

export const SignalCard = React.memo(({ ticker, signal_type, price, score, date }: SignalCardProps) => {
    const isBuy = signal_type === 'BUY';

    return (
        <div 
            role="region"
            aria-label={`${ticker} ${signal_type} Signal`}
            tabIndex={0}
            className="group relative flex items-center justify-between p-5 bg-[#0A0D14] border border-white/10 industrial-corner scan-line transition-all duration-300 hover:border-primary/40 hover:-translate-x-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:border-primary" 
            data-testid="signal-card"
        >
            <div className="flex items-center space-x-6 w-full">
                <div className={clsx("h-14 w-full max-w-[3.5rem] flex items-center justify-center font-heading font-black text-xs border-2 transition-all duration-700 shrink-0",
                    isBuy
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 group-hover:bg-emerald-500 group-hover:text-black group-hover:border-emerald-400  "
                        : "bg-rose-500/10 text-rose-400 border-rose-500/20 group-hover:bg-rose-500 group-hover:text-black group-hover:border-rose-400  "
                )}>
                    {ticker?.slice(0, 3).toUpperCase()}
                </div>
                <div>
                    <h4 className="text-[15px] font-heading font-black text-white group-hover:text-primary transition-colors tracking-widest leading-none mb-1.5 uppercase">
                        {ticker}
                    </h4>
                    <div className="flex items-center gap-2">
                        <span className={clsx("text-[9px] font-black uppercase tracking-[0.2em] px-2 py-0.5 border",
                            isBuy ? "bg-emerald-500/5 text-emerald-500/80 border-emerald-500/10" : "bg-rose-500/5 text-rose-500/80 border-rose-500/10")}>
                            {signal_type}
                        </span>
                        <div className="h-[1px] w-4 bg-white/10" />
                        <span className="font-mono text-[10px] text-slate-500 font-bold tabular-nums">
                            {formatPrice(price)}
                        </span>
                    </div>
                </div>
            </div>
            <div className="text-right flex flex-col items-end gap-2">
                <InfoTooltip content="Composite signal score (0-5) based on momentum, accumulation, and trap detection confluence.">
                    <div className="text-[10px] font-black font-mono text-white/50 bg-white/5 border border-white/5 px-2.5 py-1 industrial-corner group-hover:text-primary transition-colors cursor-help">
                        MTRX_{score}/5
                    </div>
                </InfoTooltip>
                <div className="flex items-center gap-2">
                    <span className="text-[9px] font-mono text-slate-600">TIMESTAMP:</span>
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">
                        {formatDate(date)}
                    </span>
                </div>
            </div>
        </div>
    );
});

SignalCard.displayName = 'SignalCard';
