'use client';

import React from 'react';
import { clsx } from 'clsx';
import { X, ShieldCheck, AlertTriangle, Lightbulb, TrendingUp, ChevronRight, Zap } from 'lucide-react';

interface StrategyAuditDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    auditResult: any;
    onCommit: (result: any) => void;
    committing: boolean;
}

export default function StrategyAuditDrawer({ isOpen, onClose, auditResult, onCommit, committing }: StrategyAuditDrawerProps) {
    if (!isOpen) return null;

    const analysis = auditResult?.analysis || {};
    const score = analysis.robustness_score || 0;
    
    const getScoreColor = (s: number) => {
        if (s >= 80) return 'text-emerald-400';
        if (s >= 60) return 'text-amber-400';
        return 'text-rose-400';
    };

    return (
        <div className="fixed inset-0 z-[100] flex justify-end">
            {/* Backdrop */}
            <div 
                className="absolute inset-0 bg-black/60 animate-in fade-in duration-300" 
                onClick={onClose}
            />
            
            {/* Panel */}
            <div className={clsx(
                "relative w-full max-w-lg h-full bg-[#0a0f18] border-l border-white/10   flex flex-col",
                "animate-in slide-in-from-right duration-500 ease-out"
            )}>
                {/* Header */}
                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg border border-primary/20">
                            <ShieldCheck className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                            <h2 className="text-lg font-black uppercase tracking-widest text-white italic">AI Strategy Audit</h2>
                            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Statistical Integrity Report</p>
                        </div>
                    </div>
                    <button 
                        onClick={onClose}
                        className="p-2 hover:bg-white/5 rounded-full transition-colors"
                    >
                        <X className="w-5 h-5 text-slate-400" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8 space-y-10 custom-scrollbar">
                    
                    {/* Robustness Score */}
                    <div className="text-center space-y-4">
                        <div className="relative inline-block">
                            <svg className="w-32 h-32 transform -rotate-90">
                                <circle
                                    className="text-white/5"
                                    strokeWidth="8"
                                    stroke="currentColor"
                                    fill="transparent"
                                    r="58"
                                    cx="64"
                                    cy="64"
                                />
                                <circle
                                    className={clsx("transition-all duration-1000 ease-out", getScoreColor(score))}
                                    strokeWidth="8"
                                    strokeDasharray={364}
                                    strokeDashoffset={364 - (364 * score) / 100}
                                    strokeLinecap="round"
                                    stroke="currentColor"
                                    fill="transparent"
                                    r="58"
                                    cx="64"
                                    cy="64"
                                />
                            </svg>
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className={clsx("text-4xl font-black font-mono tracking-tighter", getScoreColor(score))}>
                                    {score}
                                </span>
                                <span className="text-[8px] font-black uppercase text-slate-500 tracking-widest">Score</span>
                            </div>
                        </div>
                        <h3 className="text-xs font-black uppercase tracking-[0.3em] text-slate-400">Robustness Rating</h3>
                    </div>

                    {/* Critique */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-primary">
                            <Lightbulb className="w-3 h-3" />
                            <span>Executive Summary</span>
                        </div>
                        <div className="p-5 bg-white/[0.03] border border-white/5 rounded-xl text-sm leading-relaxed text-slate-300 italic">
                            &ldquo;{analysis.critique || 'No analysis available.'}&rdquo;
                        </div>
                    </div>

                    {/* Risk Warnings */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-rose-400">
                            <AlertTriangle className="w-3 h-3" />
                            <span>Critical Warnings</span>
                        </div>
                        <div className="space-y-3">
                            {analysis.risk_warnings?.map((warning: string, i: number) => (
                                <div key={i} className="flex gap-3 text-xs text-rose-300/80 bg-rose-500/5 p-4 rounded-lg border border-rose-500/10">
                                    <div className="mt-0.5">•</div>
                                    <span>{warning}</span>
                                </div>
                            ))}
                            {(!analysis.risk_warnings || analysis.risk_warnings.length === 0) && (
                                <div className="text-xs text-slate-500 italic">No significant risks detected in simulation.</div>
                            )}
                        </div>
                    </div>

                    {/* Parameter Suggestions */}
                    <div className="space-y-6">
                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-emerald-400">
                            <Zap className="w-3 h-3" />
                            <span>Suggested Adjustments</span>
                        </div>
                        <div className="grid grid-cols-1 gap-2">
                            {Object.entries(analysis.suggested_parameters || {}).map(([key, value]) => (
                                <div key={key} className="flex justify-between items-center p-4 bg-white/[0.02] border border-white/5 rounded-lg group hover:bg-white/[0.04] transition-colors">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 group-hover:text-slate-300">{key.replace('_', ' ')}</span>
                                    <span className="font-mono font-bold text-emerald-400">{String(value)}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>

                {/* Footer */}
                <div className="p-8 border-t border-white/5 bg-white/[0.01]">
                    <button
                        onClick={() => onCommit(auditResult)}
                        disabled={committing || !analysis.suggested_parameters}
                        className={clsx(
                            "w-full py-5 rounded-xl text-[11px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 transition-all duration-300",
                            committing || !analysis.suggested_parameters
                                ? "bg-white/5 text-slate-600 grayscale"
                                : "bg-primary text-primary-foreground hover:scale-[1.02]   active:scale-95"
                        )}
                    >
                        {committing ? "Processing_Deployment" : "Commit to Strategy Core"}
                        {!committing && <ChevronRight className="w-4 h-4" />}
                    </button>
                    <p className="mt-4 text-[8px] text-center text-slate-600 uppercase tracking-widest font-bold">
                        Authorization required to push optimized parameters to production.
                    </p>
                </div>
            </div>
        </div>
    );
}
