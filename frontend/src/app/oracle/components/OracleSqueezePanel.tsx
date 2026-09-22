import { Activity } from 'lucide-react';

import { truncatePrice } from '../lib/oracleTransforms';

type OracleSqueezePanelProps = {
    squeeze: any;
    candidates: any[];
};

export function OracleSqueezePanel({ squeeze, candidates }: OracleSqueezePanelProps) {
    return (
        <div className="bg-slate-950 border border-slate-800/80 rounded-none p-4 flex flex-col font-mono select-none">
            <div className="flex items-center gap-1 mb-4">
                <span className="w-1.5 h-1.5 bg-amber-500 animate-pulse" />
                <span className="text-[9px] text-slate-500 font-bold uppercase tracking-widest">{'// ORACLE::VOLATILITY_COIL'}</span>
            </div>
            <div className="mb-4 space-y-1">
                <h3 className="text-sm font-bold text-slate-100">The Coil (Squeezes)</h3>
                <p className="text-[10px] uppercase tracking-tight text-slate-600">
                    Volatility compression scanner
                </p>
            </div>

            {squeeze && squeeze.status === 'found' ? (
                <div className="space-y-2 overflow-y-auto max-h-[400px] pr-2 custom-scrollbar">
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter mb-3">
                        SCANNER_DETECTION: {squeeze.count} CANDIDATES_READY
                    </p>
                    <p className="text-[10px] text-slate-400">
                        Found {squeeze.count} stocks preparing for an explosive move.
                    </p>
                    {candidates.map((c: any, idx: number) => (
                        <div key={idx} className="bg-slate-900/30 p-2 rounded-none border border-slate-800 hover:border-amber-500/50 hover:bg-slate-900/50 transition-all flex justify-between items-center group">
                            <div className="flex flex-col">
                                <div className="text-xs font-bold text-slate-200 group-hover:text-amber-400 transition-colors">{c.Ticker}</div>
                                <div className="text-[9px] text-slate-600 uppercase tracking-tight">{c.Sector}</div>
                            </div>
                            <div className="text-right">
                                <div className="text-[11px] font-bold text-slate-400 tabular-nums">{truncatePrice(c.Price)}</div>
                                <div className="text-[9px] text-amber-600/80 font-black uppercase tabular-nums">
                                    BW_{truncatePrice(c.BandWidth)}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="flex-1 flex flex-col items-center justify-center p-8 border border-slate-800/40 bg-black/20 group">
                    <Activity className="w-12 h-12 mb-3 text-slate-800 group-hover:text-slate-700 transition-colors" />
                    <p className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">Market is expanded.</p>
                    <p className="text-[9px] text-slate-700 mt-1 uppercase">No volatility squeezes detected.</p>
                </div>
            )}
        </div>
    );
}
