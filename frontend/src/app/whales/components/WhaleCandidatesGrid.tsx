'use client';

import { Maximize2, RefreshCw, TrendingDown, TrendingUp } from 'lucide-react';
import clsx from 'clsx';

import { WhaleCandidate } from '../../../types';
import { PromoteToDeskButtons, SignalDeskLaneKey } from '../../components/signal-desk/PromoteToDeskButtons';

interface WhaleCandidatesGridProps {
    candidates: WhaleCandidate[];
    isLoading: boolean;
    onSelectTicker: (ticker: string) => void;
    onPromoteCandidate?: (candidate: WhaleCandidate, lane: SignalDeskLaneKey) => void | Promise<unknown>;
    truncatePrice: (value: number | undefined) => string;
}

export function WhaleCandidatesGrid({
    candidates,
    isLoading,
    onSelectTicker,
    onPromoteCandidate,
    truncatePrice,
}: WhaleCandidatesGridProps) {
    if (isLoading) {
        return (
            <div role="status" className="flex-1 flex justify-center items-center">
                <RefreshCw className="w-10 h-10 text-cyan-600 animate-spin" />
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {candidates.map((candidate, idx) => (
                <div
                    key={idx}
                    onClick={() => onSelectTicker(candidate.Ticker)}
                    className="section-surface industrial-corner hover:border-cyan-500/35 rounded-xl p-6 transition group relative overflow-hidden cursor-pointer"
                >
                    <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition">
                        <Maximize2 className="w-4 h-4 text-cyan-400" />
                    </div>

                    <div className="absolute -bottom-4 -right-4 opacity-5 group-hover:opacity-10 transition">
                        {candidate.Signal === 'ACCUMULATION' ? (
                            <TrendingUp className="w-24 h-24 text-emerald-500" />
                        ) : (
                            <TrendingDown className="w-24 h-24 text-rose-500" />
                        )}
                    </div>

                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="text-xl font-bold text-slate-100 group-hover:text-cyan-400">{candidate.Ticker}</h3>
                            <p className="text-xs text-slate-500 font-medium">{candidate.Sector}</p>
                        </div>
                        <div className="flex items-center gap-1.5">
                            {Number(candidate.Strength || 0) >= 2.0 && (
                                <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 tracking-wider">
                                    HIGH CONVICTION ⚡
                                </span>
                            )}
                            <div
                                className={clsx(
                                    'text-[10px] font-bold px-2 py-1 rounded uppercase',
                                    candidate.Signal === 'ACCUMULATION'
                                        ? 'bg-emerald-950/30 text-emerald-500 border border-emerald-500/20'
                                        : 'bg-rose-950/30 text-rose-500 border border-rose-500/20',
                                )}
                            >
                                {candidate.Signal}
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-between items-end">
                        <div>
                            <div className="text-2xl font-bold text-white">{truncatePrice(candidate.Last_Price)}</div>
                            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Current Price</div>
                        </div>
                        <div className="text-right">
                            <div
                                className={clsx(
                                    'text-xs font-bold',
                                    candidate.Signal === 'ACCUMULATION' ? 'text-emerald-400' : 'text-rose-400',
                                )}
                            >
                                {candidate.Signal === 'ACCUMULATION' ? 'Whales Buying' : 'Whales Selling'}
                            </div>
                            <div className="text-[10px] text-slate-600">Strength: {candidate.Strength?.toFixed(2) || 'N/A'}</div>
                        </div>
                    </div>

                    {(candidate.Flow_EGP_Millions !== undefined || candidate.Support_Anchor !== undefined) && (
                        <div className="mt-3 grid grid-cols-2 gap-2 bg-slate-900/60 p-2.5 rounded-lg border border-white/5 text-[11px]">
                            {candidate.Flow_EGP_Millions !== undefined && (
                                <div>
                                    <span className="text-slate-500 text-[9px] uppercase tracking-wider block">Est. 20D Net Flow</span>
                                    <span className={clsx('font-bold', candidate.Flow_EGP_Millions >= 0 ? 'text-emerald-400' : 'text-rose-400')}>
                                        {candidate.Flow_EGP_Millions >= 0 ? `+${candidate.Flow_EGP_Millions}M` : `${candidate.Flow_EGP_Millions}M`} EGP
                                    </span>
                                </div>
                            )}
                            {candidate.Support_Anchor !== undefined && (
                                <div className="text-right">
                                    <span className="text-slate-500 text-[9px] uppercase tracking-wider block">20D Support Anchor</span>
                                    <span className="font-bold text-cyan-300 font-mono">
                                        {truncatePrice(candidate.Support_Anchor)}
                                    </span>
                                </div>
                            )}
                        </div>
                    )}

                    <div className="mt-3 pt-3 border-t border-white/10">
                        <p className="text-[11px] text-slate-400 leading-relaxed italic">
                            {candidate.Signal === 'ACCUMULATION'
                                ? 'Price is trapped or dropping, but OBV is surging. This is hidden accumulation before a breakout.'
                                : 'Price is grinding up, but OBV is leaking. Whales are distributing to retail during the rally.'}
                        </p>
                        {onPromoteCandidate ? (
                            <div
                                className="mt-4 border-t border-white/10 pt-4"
                                onClick={(event) => event.stopPropagation()}
                            >
                                <p className="mb-2 text-[9px] font-black uppercase tracking-[0.2em] text-slate-500">Promote To Desk</p>
                                <PromoteToDeskButtons compact onPromote={(lane) => onPromoteCandidate(candidate, lane)} />
                            </div>
                        ) : null}
                    </div>
                </div>
            ))}
        </div>
    );
}
