'use client';

import { Crown, Send, Share2, Zap } from 'lucide-react';

type SignalForm = {
    ticker: string;
    entry: string;
    sl: string;
    tp1: string;
    tp2: string;
    caption: string;
};

type TelegramSignalPanelProps = {
    signalForm: SignalForm;
    sending: boolean;
    activeRunId?: number | null;
    autopilotReady?: boolean;
    failedDeliveryCount?: number;
    setSignalForm: (next: SignalForm) => void;
    onDeskRelease: () => void | Promise<void>;
    onAutopilotRun: () => void | Promise<void>;
    onRetryFailedDeliveries: () => void | Promise<void>;
    onSignalBroadcast: () => void | Promise<void>;
    onAiDailyReport: () => void | Promise<void>;
    onAnalysisReport: (period: 'weekly' | 'monthly') => void | Promise<void>;
    onScan: (type: 'DAILY' | 'INTRADAY') => void | Promise<void>;
};

export function TelegramSignalPanel({
    signalForm,
    sending,
    activeRunId,
    autopilotReady,
    failedDeliveryCount = 0,
    setSignalForm,
    onDeskRelease,
    onAutopilotRun,
    onRetryFailedDeliveries,
    onSignalBroadcast,
    onAiDailyReport,
    onAnalysisReport,
    onScan,
}: TelegramSignalPanelProps) {
    return (
        <div className="section-surface rounded-[1.75rem] p-5 md:p-6">
            <div className="flex flex-col gap-4 border-b border-white/8 pb-5 md:flex-row md:items-center md:justify-between">
                <div>
                    <div className="text-[10px] font-black uppercase tracking-[0.32em] text-slate-500">Release Composition</div>
                    <h2 className="mt-2 font-heading text-2xl font-black uppercase tracking-[0.12em] text-white">
                        Signal Issuance Desk
                    </h2>
                    <p className="mt-2 max-w-2xl text-sm text-slate-400">
                        Compose the royal signal card, trigger desk dispatch, and govern the major outbound broadcasts from one chamber.
                    </p>
                </div>
                <div className="inline-flex items-center gap-2 rounded-full border border-amber-300/20 bg-amber-500/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.24em] text-amber-100">
                    <Crown className="h-3.5 w-3.5" />
                    Release Composition
                </div>
            </div>

            <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1.08fr)_19rem]">
                <div className="rounded-[1.4rem] border border-amber-200/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.02))] p-4 md:p-5">
                    <div className="mb-5 flex items-center justify-between">
                        <div>
                            <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Manual Composition</div>
                            <div className="mt-2 text-lg font-black uppercase tracking-[0.12em] text-white">Premium Broadcaster</div>
                        </div>
                        <Zap className="h-4 w-4 text-amber-200" />
                    </div>

                    <div className="space-y-5">
                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Ticker</label>
                                <input
                                    type="text"
                                    placeholder="e.g. COMI"
                                    value={signalForm.ticker}
                                    onChange={(event) =>
                                        setSignalForm({
                                            ...signalForm,
                                            ticker: event.target.value.toUpperCase(),
                                        })
                                    }
                                    className="control-input w-full p-3 font-mono focus:border-primary focus:ring-1 focus:ring-primary"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Entry Range</label>
                                <input
                                    type="number"
                                    placeholder="85.50"
                                    value={signalForm.entry}
                                    onChange={(event) => setSignalForm({ ...signalForm, entry: event.target.value })}
                                    className="control-input w-full p-3 font-mono focus:border-primary focus:ring-1 focus:ring-primary"
                                />
                            </div>
                        </div>

                        <div className="grid gap-4 md:grid-cols-3">
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-rose-500">Stop Loss</label>
                                <input
                                    type="number"
                                    placeholder="82.00"
                                    value={signalForm.sl}
                                    onChange={(event) => setSignalForm({ ...signalForm, sl: event.target.value })}
                                    className="control-input w-full border-rose-500/20 p-3 font-mono focus:border-rose-500"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-emerald-500">TP 1</label>
                                <input
                                    type="number"
                                    placeholder="92.00"
                                    value={signalForm.tp1}
                                    onChange={(event) => setSignalForm({ ...signalForm, tp1: event.target.value })}
                                    className="control-input w-full border-emerald-500/20 p-3 font-mono focus:border-emerald-500"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-emerald-600">TP 2 (Opt)</label>
                                <input
                                    type="number"
                                    placeholder="+4.0%"
                                    value={signalForm.tp2}
                                    onChange={(event) => setSignalForm({ ...signalForm, tp2: event.target.value })}
                                    className="control-input w-full p-3 font-mono focus:border-emerald-500"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Caption / Analysis Override</label>
                            <textarea
                                placeholder="Leave blank for auto-generated caption..."
                                value={signalForm.caption}
                                onChange={(event) => setSignalForm({ ...signalForm, caption: event.target.value })}
                                className="control-input h-24 w-full p-3 text-xs focus:border-primary"
                            />
                        </div>

                        <button
                            onClick={onSignalBroadcast}
                            disabled={sending || !signalForm.ticker || !signalForm.entry}
                            className="action-primary w-full py-4 text-[10px] tracking-[0.2em] disabled:scale-100 disabled:opacity-50"
                        >
                            <Zap className="mr-2 h-4 w-4" />
                            {sending ? 'Broadcasting Card...' : 'Blast Horus Signal Card'}
                        </button>
                    </div>
                </div>

                <div className="grid gap-3">
                    <div className="rounded-[1.35rem] border border-white/8 bg-white/[0.03] p-4">
                        <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Chamber Triggers</div>
                        <div className="mt-4 space-y-3">
                            <button onClick={onAutopilotRun} disabled={sending || !autopilotReady} className="action-secondary group w-full py-4 text-[10px] tracking-widest disabled:opacity-50">
                                <Zap className="mr-2 h-3 w-3 transition-transform duration-300 group-hover:scale-110" /> Run Autopilot Dispatch
                            </button>
                            <button onClick={onDeskRelease} disabled={sending || !activeRunId} className="action-secondary group w-full py-4 text-[10px] tracking-widest disabled:opacity-50">
                                <Send className="mr-2 h-3 w-3 transition-transform duration-300 group-hover:translate-x-1" /> Dispatch Latest Desk Run
                            </button>
                            <button onClick={onRetryFailedDeliveries} disabled={sending || !activeRunId || failedDeliveryCount < 1} className="action-secondary group w-full py-4 text-[10px] tracking-widest disabled:opacity-50">
                                <Send className="mr-2 h-3 w-3 transition-transform duration-300 group-hover:translate-x-1" /> Retry Failed Deliveries
                            </button>
                        </div>
                    </div>

                    <div className="rounded-[1.35rem] border border-white/8 bg-white/[0.03] p-4">
                        <div className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">Broadcast Triggers</div>
                        <div className="mt-4 space-y-3">
                            <button onClick={() => onScan('INTRADAY')} disabled={sending} className="action-secondary group w-full py-4 text-[10px] tracking-widest disabled:opacity-50">
                                <Send className="mr-2 h-3 w-3 transition-transform duration-300 group-hover:translate-x-1" /> Broadcast Intraday
                            </button>
                            <button onClick={() => onScan('DAILY')} disabled={sending} className="action-secondary group w-full py-4 text-[10px] tracking-widest disabled:opacity-50">
                                <Send className="mr-2 h-3 w-3 transition-transform duration-300 group-hover:translate-x-1" /> Broadcast Daily Close
                            </button>
                            <button onClick={onAiDailyReport} disabled={sending} className="action-secondary group w-full py-4 text-[10px] tracking-widest disabled:opacity-50">
                                <Share2 className="mr-2 h-3 w-3 transition-transform duration-300 group-hover:scale-110" /> Broadcast AI Daily Report
                            </button>
                            <button onClick={() => onAnalysisReport('weekly')} disabled={sending} className="action-secondary group w-full py-4 text-[10px] tracking-widest disabled:opacity-50">
                                <Share2 className="mr-2 h-3 w-3 transition-transform duration-300 group-hover:scale-110" /> Broadcast Weekly Report
                            </button>
                            <button onClick={() => onAnalysisReport('monthly')} disabled={sending} className="action-secondary group w-full py-4 text-[10px] tracking-widest disabled:opacity-50">
                                <Share2 className="mr-2 h-3 w-3 transition-transform duration-300 group-hover:scale-110" /> Broadcast Monthly Report
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
