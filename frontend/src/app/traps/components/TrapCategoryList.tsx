import { TrendingUp, TrendingDown } from 'lucide-react';
import clsx from 'clsx';
import { TrapCard } from './TrapCard';
import { PromoteToDeskButtons, SignalDeskLaneKey } from '../../components/signal-desk/PromoteToDeskButtons';
import { Trap } from '../../../types';

interface TrapCategoryListProps {
    type: 'bull' | 'bear';
    items: Trap[];
    heldTickers?: Set<string>;
    onPromoteCandidate?: (type: 'bull' | 'bear', item: Trap, lane: SignalDeskLaneKey) => void | Promise<unknown>;
}

export function TrapCategoryList({ type, items, heldTickers, onPromoteCandidate }: TrapCategoryListProps) {
    const isBull = type === 'bull';
    const Icon = isBull ? TrendingDown : TrendingUp;
    const title = isBull ? 'Bull Traps (Defensive / Sell)' : 'Bear Traps (Springboard / Buy)';
    const colorClass = isBull ? 'text-rose-400' : 'text-emerald-400';
    const borderClass = isBull ? 'border-rose-500/30' : 'border-emerald-500/30';
    const subtitle = isBull 
        ? 'Failed Breakouts / Upthrusts. Major risk of aggressive distribution.'
        : 'Failed Breakdowns / Springs. High probability institutional reversal bounce.';
    const emptyMsg = isBull ? 'No Bull Traps found' : 'No Bear Traps found';

    return (
        <div className="space-y-4">
            <h3 className={clsx("text-xl font-bold flex items-center border-b pb-2", colorClass, borderClass)}>
                <Icon className="w-5 h-5 mr-2" />
                {title}
            </h3>
            <p className="text-xs text-gray-500">{subtitle}</p>

            {items.map((t, idx) => (
                <div key={idx} className="space-y-3">
                    <TrapCard
                        type={type}
                        ticker={t.Ticker}
                        date={t.Date}
                        price={t.Price}
                        depth={t['Fakeout_Depth_%']}
                        details={t.Details || ''}
                        isHeldInPortfolio={heldTickers ? heldTickers.has(t.Ticker) : false}
                    />
                    {onPromoteCandidate ? (
                        <div className="rounded-2xl border border-white/5 bg-slate-950/40 px-4 py-3">
                            <p className="mb-2 text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">
                                {isBull ? 'Stage Defensive Exit / Trim' : 'Promote Springboard (Buy)'}
                            </p>
                            <PromoteToDeskButtons compact onPromote={(lane) => onPromoteCandidate(type, t, lane)} />
                        </div>
                    ) : null}
                </div>
            ))}

            {items.length === 0 && (
                <div className="text-gray-500 text-sm italic text-center py-10 opacity-50">
                    {emptyMsg}
                </div>
            )}
        </div>
    );
}
