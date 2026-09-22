import clsx from 'clsx';
import { 
    formatFakeoutDepth, 
    getTrapCardClasses, 
    getTickerClasses, 
    getDetailBoxClasses 
} from '../lib/trapsTransforms';

interface TrapCardProps {
    ticker: string;
    date: string;
    price: string | number;
    depth: number;
    details: string;
    type: 'bull' | 'bear';
    isHeldInPortfolio?: boolean;
}

export function TrapCard({ ticker, date, price, depth, details, type, isHeldInPortfolio }: TrapCardProps) {
    return (
        <div className={clsx(
            "section-surface industrial-corner rounded-lg p-4 group transition", 
            getTrapCardClasses(type),
            isHeldInPortfolio && type === 'bull' && "border-rose-500/60 shadow-[0_0_15px_rgba(244,63,94,0.15)]"
        )}>
            <div className="flex justify-between items-start">
                <div>
                    <div className="flex items-center gap-2 flex-wrap">
                        <h4 className={clsx("text-lg font-bold text-slate-100", getTickerClasses(type))}>
                            {ticker}
                        </h4>
                        {isHeldInPortfolio && (
                            <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 tracking-wider">
                                🛡️ HELD IN PORTFOLIO
                            </span>
                        )}
                        {Math.abs(Number(depth || 0)) >= 4.0 && (
                            <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/30 tracking-wider">
                                SEVERE TRAP ⚡
                            </span>
                        )}
                    </div>
                    <p className="text-xs text-slate-400 font-mono">{date}</p>
                </div>
                <div className="text-right">
                    <div className="text-xl font-bold text-slate-200">{price}</div>
                    <div className={clsx("text-xs font-bold", type === 'bull' ? 'text-rose-500' : 'text-emerald-500')}>
                        {formatFakeoutDepth(depth, type)}
                    </div>
                </div>
            </div>
            <div className={clsx("mt-3 text-xs p-2 rounded border", getDetailBoxClasses(type))}>
                {details}
            </div>
        </div>
    );
}
