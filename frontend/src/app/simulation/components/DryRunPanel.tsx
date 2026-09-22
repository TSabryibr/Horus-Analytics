'use client';

import clsx from 'clsx';
import { Zap, Send, FileText, Brain, CheckCircle2, XCircle, Clock, Loader2, ArrowRight, FlaskConical, Target } from 'lucide-react';
import type { DryRunStatus, DryRunStep } from '../hooks/useDryRun';
import { MetricBox, ErrorDisplay, GlassCard } from './SimulationPrimitives';

type DryRunPanelProps = {
    dryrunDate: string;
    setDryrunDate: (v: string) => void;
    dryrunNotify: boolean;
    setDryrunNotify: (v: boolean) => void;
    dryrunReport: boolean;
    setDryrunReport: (v: boolean) => void;
    dryrunAiReport: boolean;
    setDryrunAiReport: (v: boolean) => void;
    dryrunLoading: boolean;
    dryrunStatus: DryRunStatus | null;
    dryrunError: string | null;
    selectedProfileLabel: string;
    onStart: () => void | Promise<void>;
};

export function DryRunPanel({
    dryrunDate,
    setDryrunDate,
    dryrunNotify,
    setDryrunNotify,
    dryrunReport,
    setDryrunReport,
    dryrunAiReport,
    setDryrunAiReport,
    dryrunLoading,
    dryrunStatus,
    dryrunError,
    selectedProfileLabel,
    onStart,
}: DryRunPanelProps) {
    const isRunning = dryrunStatus?.status === 'RUNNING';
    const isCompleted = dryrunStatus?.status === 'COMPLETED';
    const isError = dryrunStatus?.status === 'ERROR';
    const effectiveProfileLabel = dryrunStatus?.profile_name || selectedProfileLabel;

    return (
        <div className="animate-in fade-in slide-in-from-bottom-6 duration-700 space-y-8">
            {/* ── Controls ──────────────────────────────────────────── */}
            <div className="group relative">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-500/20 to-blue-500/20 rounded-3xl blur opacity-20 transition duration-1000 group-hover:opacity-40" />
                <div className="relative bg-white/[0.02] border border-white/10 rounded-3xl p-8 space-y-8">
                    {/* Row 1: Date + Toggles */}
                    <div className="flex flex-col md:flex-row gap-8">
                        <div className="flex-1">
                            <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                                Target Date
                            </label>
                            <input
                                type="date"
                                value={dryrunDate}
                                onChange={(e) => setDryrunDate(e.target.value)}
                                disabled={isRunning}
                                placeholder="Last trading day"
                                className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all disabled:opacity-40"
                            />
                            <p className="mt-1.5 text-[10px] text-slate-600 font-medium">
                                Leave empty for last completed trading day
                            </p>
                        </div>
                        <div className="flex-1 flex flex-wrap gap-4">
                            <OptionChip
                                label="Telegram"
                                icon={<Send className="w-3.5 h-3.5" />}
                                enabled={dryrunNotify}
                                onChange={setDryrunNotify}
                                disabled={isRunning}
                                color="violet"
                            />
                            <OptionChip
                                label="Local Reports"
                                icon={<FileText className="w-3.5 h-3.5" />}
                                enabled={dryrunReport}
                                onChange={setDryrunReport}
                                disabled={isRunning}
                                color="violet"
                            />
                            <OptionChip
                                label="AI Report"
                                icon={<Brain className="w-3.5 h-3.5" />}
                                enabled={dryrunAiReport}
                                onChange={setDryrunAiReport}
                                disabled={isRunning}
                                color="violet"
                            />
                        </div>
                    </div>

                    {/* Action Button */}
                    <div className="flex justify-end">
                        <button
                            onClick={onStart}
                            disabled={dryrunLoading || isRunning}
                            className="w-full md:w-auto px-12 py-4 bg-violet-500 text-white font-black tracking-widest rounded-2xl transition-all active:scale-95 disabled:opacity-30 disabled:pointer-events-none uppercase text-xs flex items-center justify-center gap-3 hover:bg-violet-400"
                        >
                            {dryrunLoading || isRunning ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <Zap className="w-5 h-5 fill-current" />
                            )}
                            {isRunning ? 'EXECUTING...' : 'FIRE DRY RUN'}
                        </button>
                    </div>

                    <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-xs text-amber-200">
                        Dry Run persists <span className="font-bold">DRYRUN</span> signals. Telegram and AI Report toggles can trigger real outbound messages.
                    </div>
                </div>
            </div>

            {dryrunError && <ErrorDisplay error={dryrunError} />}

            {/* ── Pipeline Results ───────────────────────────────────── */}
            {(isRunning || isCompleted || isError) && dryrunStatus && (
                <div className="space-y-8 animate-in fade-in fill-mode-both duration-700">
                    <div className="flex items-center justify-between rounded-2xl border border-violet-500/15 bg-violet-500/5 px-5 py-4">
                        <div className="flex items-center gap-3 min-w-0">
                            <Target className="h-4 w-4 text-violet-400 shrink-0" />
                            <span className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">Profile In Use</span>
                            <span className="truncate text-sm font-bold text-violet-300">{effectiveProfileLabel}</span>
                        </div>
                        {isCompleted && (
                            <span className="ml-3 shrink-0 text-[9px] font-black tracking-wider border border-emerald-400/30 bg-emerald-500/15 text-emerald-300 rounded px-2 py-1">
                                DRILL PASSED ⚡
                            </span>
                        )}
                    </div>

                    {/* Metrics Row */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <MetricBox label="Date" value={dryrunStatus.date || 'Auto'} color="slate" />
                        <MetricBox label="Signals" value={String(dryrunStatus.signals_found)} color="cyan" />
                        <MetricBox label="Regime" value={dryrunStatus.regime || '—'} color="orange" />
                        <MetricBox
                            label="Duration"
                            value={dryrunStatus.duration_sec > 0 ? `${dryrunStatus.duration_sec}s` : '…'}
                            color={isCompleted ? 'cyan' : 'yellow'}
                        />
                    </div>

                    {/* Step Pipeline Visualization */}
                    <GlassCard title="Pipeline Execution" icon={<FlaskConical className="text-violet-400" />}>
                        <div className="space-y-1">
                            {dryrunStatus.steps.map((step, i) => (
                                <StepRow key={i} step={step} index={i} isLast={i === dryrunStatus.steps.length - 1} />
                            ))}
                        </div>
                    </GlassCard>

                    {/* Telegram Stats */}
                    {isCompleted && dryrunStatus.telegram_messages_sent > 0 && (
                        <div className="flex items-center gap-3 px-5 py-4 rounded-2xl bg-violet-500/5 border border-violet-500/15">
                            <Send className="w-4 h-4 text-violet-400" />
                            <span className="text-sm font-bold text-violet-300">
                                {dryrunStatus.telegram_messages_sent} Telegram message{dryrunStatus.telegram_messages_sent !== 1 ? 's' : ''} sent
                            </span>
                            <span className="text-xs text-slate-500 ml-auto">with [🧪 DRY RUN] prefix</span>
                        </div>
                    )}

                    {/* Signals Table */}
                    {dryrunStatus.signals.length > 0 && (
                        <GlassCard title="Discovered Signals" icon={<Zap className="text-amber-400" />}>
                            <div className="overflow-hidden rounded-2xl border border-white/5">
                                <table className="w-full text-left text-xs border-collapse">
                                    <thead>
                                        <tr className="bg-white/5 text-slate-500 font-black uppercase tracking-widest">
                                            <th className="p-4">Ticker</th>
                                            <th className="p-4">Type</th>
                                            <th className="p-4">Score</th>
                                            <th className="p-4">Entry</th>
                                            <th className="p-4">Stop Loss</th>
                                            <th className="p-4 text-right">Target</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {dryrunStatus.signals.map((sig, idx) => (
                                            <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition">
                                                <td className="p-4 font-black text-amber-400">{sig.ticker}</td>
                                                <td className="p-4 text-slate-400">{sig.type}</td>
                                                <td className="p-4">
                                                    <span className={clsx(
                                                        'font-mono font-black',
                                                        sig.score >= 8 ? 'text-emerald-400' :
                                                            sig.score >= 6 ? 'text-amber-400' : 'text-slate-400'
                                                    )}>
                                                        {sig.score}/10
                                                    </span>
                                                </td>
                                                <td className="p-4 text-slate-200 font-mono">{Number(sig.entry).toFixed(2)}</td>
                                                <td className="p-4 text-red-400 font-mono">{Number(sig.stop_loss).toFixed(2)}</td>
                                                <td className="p-4 text-right text-emerald-400 font-mono font-bold">{Number(sig.target).toFixed(2)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </GlassCard>
                    )}
                </div>
            )}
        </div>
    );
}


/* ── Step Row ────────────────────────────────────────────────────── */

function StepRow({ step, index, isLast }: { step: DryRunStep; index: number; isLast: boolean }) {
    const statusIcon = {
        running: <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />,
        completed: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
        error: <XCircle className="w-4 h-4 text-red-400" />,
    }[step.status];

    return (
        <div className="flex items-center gap-4">
            {/* Step indicator */}
            <div className="flex flex-col items-center">
                <div className={clsx(
                    'w-8 h-8 rounded-lg flex items-center justify-center border',
                    step.status === 'completed' ? 'bg-emerald-500/10 border-emerald-500/20' :
                        step.status === 'error' ? 'bg-red-500/10 border-red-500/20' :
                            'bg-violet-500/10 border-violet-500/20'
                )}>
                    {statusIcon}
                </div>
                {!isLast && (
                    <div className={clsx(
                        'w-px h-4',
                        step.status === 'completed' ? 'bg-emerald-500/30' : 'bg-white/10'
                    )} />
                )}
            </div>

            {/* Step content */}
            <div className="flex-1 flex items-center gap-4 py-2">
                <span className={clsx(
                    'text-sm font-bold',
                    step.status === 'completed' ? 'text-slate-200' :
                        step.status === 'error' ? 'text-red-400' :
                            'text-violet-300'
                )}>
                    {step.step}
                </span>
                {step.duration_sec > 0 && (
                    <span className="text-[10px] font-mono text-slate-600 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {step.duration_sec}s
                    </span>
                )}
                {step.error && (
                    <span className="text-[10px] text-red-400 truncate max-w-[200px]">{step.error}</span>
                )}
                {!isLast && (
                    <ArrowRight className="w-3 h-3 text-slate-700 ml-auto" />
                )}
            </div>
        </div>
    );
}


/* ── Option Chip ─────────────────────────────────────────────────── */

function OptionChip({
    label,
    icon,
    enabled,
    onChange,
    disabled,
    color = 'violet',
}: {
    label: string;
    icon: React.ReactNode;
    enabled: boolean;
    onChange: (v: boolean) => void;
    disabled?: boolean;
    color?: 'violet' | 'cyan' | 'orange';
}) {
    const colorMap = {
        violet: {
            activeBg: 'bg-violet-500/10',
            activeBorder: 'border-violet-500/30',
            activeText: 'text-violet-400',
            dot: 'bg-violet-400',
        },
        cyan: {
            activeBg: 'bg-cyan-500/10',
            activeBorder: 'border-cyan-500/30',
            activeText: 'text-cyan-400',
            dot: 'bg-cyan-400',
        },
        orange: {
            activeBg: 'bg-orange-500/10',
            activeBorder: 'border-orange-500/30',
            activeText: 'text-orange-400',
            dot: 'bg-orange-400',
        },
    }[color];

    return (
        <button
            onClick={() => onChange(!enabled)}
            disabled={disabled}
            className={clsx(
                'flex items-center gap-2.5 px-4 py-3 rounded-xl border transition-all disabled:opacity-40',
                enabled
                    ? `${colorMap.activeBg} ${colorMap.activeBorder}`
                    : 'bg-white/[0.02] border-white/5 hover:border-white/10'
            )}
        >
            <div className={clsx('p-1 rounded-md', enabled ? `${colorMap.activeBg}` : 'bg-white/5')}>
                {icon}
            </div>
            <span className={clsx(
                'text-xs font-bold',
                enabled ? colorMap.activeText : 'text-slate-500'
            )}>
                {label}
            </span>
            <div className={clsx(
                'w-2 h-2 rounded-full ml-1 transition-all',
                enabled ? colorMap.dot : 'bg-white/10'
            )} />
        </button>
    );
}
