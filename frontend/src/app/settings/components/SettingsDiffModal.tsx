'use client';

import React, { useMemo } from 'react';
import { AlertTriangle, Check, RefreshCw, X } from 'lucide-react';
import { SettingsState, SignalDeskPolicyState } from '../hooks/useSettingsRuntime';

interface SettingsDiffModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void | Promise<void>;
    saving: boolean;
    settings?: SettingsState;
    originalSettings?: SettingsState;
    excluded?: string[];
    originalExcluded?: string[];
    signalDeskPolicy?: SignalDeskPolicyState;
    originalSignalDeskPolicy?: SignalDeskPolicyState;
}

export function SettingsDiffModal({
    isOpen,
    onClose,
    onConfirm,
    saving,
    settings,
    originalSettings,
    excluded,
    originalExcluded,
    signalDeskPolicy,
    originalSignalDeskPolicy,
}: SettingsDiffModalProps) {
    const settingDiffs = useMemo(() => {
        if (!settings || !originalSettings) return [];
        const diffs: { key: string; oldVal: string; newVal: string }[] = [];
        const allKeys = Array.from(new Set([...Object.keys(settings), ...Object.keys(originalSettings)]));
        for (const key of allKeys) {
            if (key.endsWith('_CONFIGURED') || key.endsWith('_PREVIEW')) continue;
            const oldVal = originalSettings[key];
            const newVal = settings[key];
            if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
                diffs.push({
                    key,
                    oldVal: oldVal !== undefined && oldVal !== null ? String(oldVal) : '(unset)',
                    newVal: newVal !== undefined && newVal !== null ? String(newVal) : '(unset)',
                });
            }
        }
        return diffs;
    }, [settings, originalSettings]);

    const addedExclusions = useMemo(() => {
        if (!excluded || !originalExcluded) return [];
        return excluded.filter((x) => !originalExcluded.includes(x));
    }, [excluded, originalExcluded]);

    const removedExclusions = useMemo(() => {
        if (!excluded || !originalExcluded) return [];
        return originalExcluded.filter((x) => !excluded.includes(x));
    }, [excluded, originalExcluded]);

    const policyDiffs = useMemo(() => {
        if (!signalDeskPolicy || !originalSignalDeskPolicy) return [];
        const diffs: { key: string; oldVal: string; newVal: string }[] = [];
        for (const key of Object.keys(signalDeskPolicy) as (keyof SignalDeskPolicyState)[]) {
            const oldVal = originalSignalDeskPolicy[key];
            const newVal = signalDeskPolicy[key];
            if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
                diffs.push({
                    key,
                    oldVal: JSON.stringify(oldVal),
                    newVal: JSON.stringify(newVal),
                });
            }
        }
        return diffs;
    }, [signalDeskPolicy, originalSignalDeskPolicy]);

    if (!isOpen) return null;

    const totalChanges = settingDiffs.length + addedExclusions.length + removedExclusions.length + policyDiffs.length;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-in fade-in duration-150">
            <div
                className="relative w-full max-w-2xl rounded-2xl border border-cyan-500/30 bg-slate-900 p-6 shadow-2xl space-y-6"
                role="dialog"
                aria-modal="true"
                aria-labelledby="settings-diff-title"
            >
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-slate-400 hover:text-white transition"
                    type="button"
                    aria-label="Close dialog"
                >
                    <X size={20} />
                </button>

                <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-300">
                        <AlertTriangle size={24} />
                    </div>
                    <div>
                        <div className="text-xs font-semibold tracking-wider text-cyan-400 uppercase">Pre-Commit Audit</div>
                    <h2 id="settings-diff-title" className="text-xl font-bold text-white">Review Pending Configuration Changes</h2>
                        <p className="mt-1 text-xs text-slate-400">
                            {totalChanges} parameter {totalChanges === 1 ? 'change' : 'changes'} detected. Verify modified values before committing to runtime.
                        </p>
                    </div>
                </div>

                <div className="max-h-[340px] overflow-y-auto space-y-4 pr-1">
                    {settingDiffs.length > 0 && (
                        <div className="space-y-2">
                            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">System Parameters ({settingDiffs.length})</h3>
                            <div className="rounded-xl border border-slate-800 bg-slate-950/70 overflow-hidden text-xs">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 font-semibold">
                                            <th className="py-2.5 px-3">Parameter</th>
                                            <th className="py-2.5 px-3">Current Saved Value</th>
                                            <th className="py-2.5 px-3">Pending New Value</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-800/60 font-mono">
                                        {settingDiffs.map(({ key, oldVal, newVal }) => (
                                            <tr key={key} className="hover:bg-slate-900/40">
                                                <td className="py-2 px-3 font-sans font-medium text-slate-200">{key}</td>
                                                <td className="py-2 px-3 text-rose-300/80 line-through">{oldVal}</td>
                                                <td className="py-2 px-3 text-emerald-400 font-bold">{newVal}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {(addedExclusions.length > 0 || removedExclusions.length > 0) && (
                        <div className="space-y-2">
                            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Blacklist Exclusions</h3>
                            <div className="flex flex-wrap gap-2 text-xs">
                                {addedExclusions.map((ticker) => (
                                    <span key={ticker} className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-emerald-300 font-medium">
                                        + Blacklisted: {ticker}
                                    </span>
                                ))}
                                {removedExclusions.map((ticker) => (
                                    <span key={ticker} className="rounded-md border border-rose-500/30 bg-rose-500/10 px-2.5 py-1 text-rose-300 font-medium line-through">
                                        - Restored: {ticker}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {policyDiffs.length > 0 && (
                        <div className="space-y-2">
                            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Signal Desk Policy ({policyDiffs.length})</h3>
                            <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3 space-y-1 text-xs">
                                {policyDiffs.map(({ key, oldVal, newVal }) => (
                                    <div key={key} className="flex justify-between font-mono">
                                        <span className="text-slate-300 font-sans">{key}:</span>
                                        <span>
                                            <span className="text-rose-300 line-through mr-2">{oldVal}</span>
                                            <span className="text-emerald-400 font-bold">{newVal}</span>
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {totalChanges === 0 && (
                        <div className="p-4 text-center text-slate-500 text-xs">No pending parameter differences found.</div>
                    )}
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                    <button
                        type="button"
                        onClick={onClose}
                        disabled={saving}
                        className="rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-xs font-semibold text-slate-300 hover:bg-slate-700 hover:text-white transition disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        onClick={async () => {
                            await onConfirm();
                            onClose();
                        }}
                        disabled={saving}
                        className="inline-flex items-center gap-2 rounded-lg bg-cyan-500 px-5 py-2.5 text-xs font-black uppercase tracking-wider text-slate-950 hover:bg-cyan-400 transition disabled:opacity-50"
                    >
                        {saving ? <RefreshCw size={14} className="animate-spin" /> : <Check size={14} />}
                        <span>{saving ? 'Saving...' : 'Confirm & Apply Changes'}</span>
                    </button>
                </div>
            </div>
        </div>
    );
}
