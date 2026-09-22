import { RefreshCw, Zap, Clock, Link as LinkIcon } from 'lucide-react';
import clsx from 'clsx';
import {
    getZScoreClass,
    getConfidenceClass,
    getEchoTypeClass,
    getActionStatusClass,
} from '../lib/arbitrageTransforms';
import type { ActionStatus } from '../hooks/useArbitrageRuntime';

interface ArbitrageMirrorCardProps {
    mirror: any;
    idx: number;
    isExecuting: boolean;
    actionStatus: ActionStatus;
    onExecute: (mirror: any, idx: number) => void;
}

export function ArbitrageMirrorCard({
    mirror,
    idx,
    isExecuting,
    actionStatus,
    onExecute,
}: ArbitrageMirrorCardProps) {
    return (
        <div className="section-surface industrial-corner hover:border-emerald-500/35 rounded-xl p-6 transition group relative overflow-hidden flex flex-col justify-between">
            <div>
                {/* Lag Indicator Background */}
                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition">
                    <Clock className="w-16 h-16 text-emerald-500" />
                </div>

                {/* Leader / Follower */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                        <div className="p-2 bg-emerald-950/30 rounded-lg border border-emerald-500/20">
                            <span className="font-bold text-emerald-400 text-lg uppercase">{mirror.Leader}</span>
                        </div>
                        <LinkIcon className="w-4 h-4 text-slate-600" />
                        <div className="p-2 bg-slate-950/80 rounded-lg border border-white/10">
                            <span className="font-bold text-slate-100 text-lg uppercase">{mirror.Follower}</span>
                        </div>
                    </div>
                    {Number(mirror.Correlation || 0) >= 85 && (
                        <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 tracking-wider">
                            HIGH CORRELATION ⚡
                        </span>
                    )}
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-3 gap-2">
                    <div>
                        <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Mirror Lag</div>
                        <div className="text-xl font-bold text-white flex items-baseline">
                            {mirror.Lag} <span className="text-xs text-slate-500 ml-1">Days</span>
                        </div>
                    </div>
                    <div className="text-center">
                        <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Z-Score</div>
                        <div className={clsx('text-xl font-bold', getZScoreClass(mirror.ZScore || 0))}>
                            {mirror.ZScore !== undefined ? mirror.ZScore.toFixed(2) : 'N/A'}
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Confidence</div>
                        <div className={clsx('text-xl font-bold', getConfidenceClass(mirror.Confidence))}>
                            {mirror.Confidence?.toFixed(1)}%
                        </div>
                    </div>
                </div>

                {/* Echo Type Badge & Bracket Parameters */}
                <div className="mt-4 flex flex-col space-y-2">
                    <div className="flex justify-between items-center">
                        <div className={clsx('text-xs font-bold px-2 py-1 rounded uppercase', getEchoTypeClass(mirror.Type))}>
                            {mirror.Type} Echo
                        </div>
                        <div className="text-[10px] font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
                            Unhedged Single-Leg
                        </div>
                    </div>
                    <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono bg-slate-950/40 px-2.5 py-1 rounded border border-white/5">
                        <span>Bracket Targets:</span>
                        <span className="text-emerald-400">SL -{mirror.StopLossPct || 1.5}% | TP +{mirror.TakeProfitPct || 2.5}%</span>
                    </div>
                </div>
            </div>

            {/* Execute */}
            <div className="mt-6 pt-4 border-t border-white/10 space-y-3">
                <button
                    onClick={() => onExecute(mirror, idx)}
                    disabled={isExecuting}
                    className="w-full flex justify-center items-center gap-2 py-2 px-4 rounded-lg text-sm font-bold transition bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isExecuting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                    {isExecuting ? 'Routing Execution...' : 'Execute Lead-Lag Trade'}
                </button>

                {actionStatus?.id === idx && (
                    <div className={clsx('text-xs px-3 py-2 rounded border', getActionStatusClass(actionStatus.type))}>
                        {actionStatus.msg}
                    </div>
                )}
            </div>
        </div>
    );
}
