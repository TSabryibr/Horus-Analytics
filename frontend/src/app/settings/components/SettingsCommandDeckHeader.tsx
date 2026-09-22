'use client';

import { useEffect, useState } from 'react';
import clsx from 'clsx';
import { History, RefreshCw, RotateCcw, Save } from 'lucide-react';

import { SettingsState } from '../hooks/useSettingsRuntime';

interface SettingsCommandDeckHeaderProps {
    saving: boolean;
    hasChanges: boolean;
    message: string;
    onSave: () => void | Promise<void>;
    onRestoreSuccess?: () => void | Promise<void>;
    settings?: SettingsState;
}

interface SnapshotItem {
    filename: string;
    path: string;
    created_at: string;
    size_bytes: number;
}

const getHeaderState = (saving: boolean, hasChanges: boolean, message: string) => {
    if (saving) return { tag: 'SYNCING', tone: 'text-cyan-300 border-cyan-500/30 bg-cyan-500/10', detail: 'Applying local configuration changes now.' };
    if (hasChanges) return { tag: 'PENDING', tone: 'text-amber-200 border-amber-500/30 bg-amber-500/10', detail: 'Uncommitted edits are waiting in the local workspace.' };
    if (/failed|error/i.test(message)) return { tag: 'FAULT', tone: 'text-orange-200 border-orange-500/30 bg-orange-500/10', detail: 'The last action reported a failure. Review the status banner below.' };
    return { tag: 'SYNCED', tone: 'text-cyan-100 border-cyan-500/20 bg-cyan-500/5', detail: 'The command deck matches the latest saved runtime snapshot.' };
};

const getEnvironmentBadge = (settings?: SettingsState) => {
    if (settings?.AUTO_TRADE_ENABLED && settings?.LIVE_ARM_GUARD_ENABLED) {
        return { label: 'LIVE BROKER', tone: 'text-rose-300 border-rose-500/40 bg-rose-500/20' };
    }
    if (settings?.AUTO_TRADE_ENABLED) {
        return { label: 'AUTOTRADER ARM', tone: 'text-amber-300 border-amber-500/40 bg-amber-500/20' };
    }
    return { label: 'SANDBOX REPLAY', tone: 'text-emerald-300 border-emerald-500/40 bg-emerald-500/20' };
};

export function SettingsCommandDeckHeader({
    saving,
    hasChanges,
    message,
    onSave,
    onRestoreSuccess,
    settings,
}: SettingsCommandDeckHeaderProps) {
    const state = getHeaderState(saving, hasChanges, message);
    const envBadge = getEnvironmentBadge(settings);

    const [isSnapshotOpen, setIsSnapshotOpen] = useState(false);
    const [snapshots, setSnapshots] = useState<SnapshotItem[]>([]);
    const [loadingSnapshots, setLoadingSnapshots] = useState(false);
    const [restoringFile, setRestoringFile] = useState<string | null>(null);

    const fetchSnapshots = async () => {
        setLoadingSnapshots(true);
        try {
            const res = await fetch('/api/v1/settings/snapshots');
            if (res.ok) {
                const data = await res.json();
                setSnapshots(data.snapshots || []);
            }
        } catch (err) {
            console.error('Failed to fetch snapshots', err);
        } finally {
            setLoadingSnapshots(false);
        }
    };

    const handleToggleSnapshots = () => {
        if (!isSnapshotOpen) {
            void fetchSnapshots();
        }
        setIsSnapshotOpen(!isSnapshotOpen);
    };

    const handleRestore = async (filename: string) => {
        setRestoringFile(filename);
        try {
            const res = await fetch('/api/v1/settings/snapshots/restore', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename }),
            });
            if (res.ok) {
                if (onRestoreSuccess) {
                    await onRestoreSuccess();
                } else {
                    window.location.reload();
                }
                setIsSnapshotOpen(false);
            }
        } catch (err) {
            console.error('Failed to restore snapshot', err);
        } finally {
            setRestoringFile(null);
        }
    };

    return (
        <header
            id="header"
            className="section-surface industrial-corner relative overflow-hidden rounded-xl border border-white/10 bg-[linear-gradient(135deg,rgba(8,15,25,0.94),rgba(8,13,20,0.98))] p-5 sm:p-6"
        >
            <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,transparent,rgba(15,23,42,0.55))]" />
            <div className="relative flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
                <div className="max-w-4xl space-y-4">
                    <div className="flex flex-wrap items-center gap-3">
                        <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[10px] font-black uppercase tracking-[0.32em] text-slate-300">
                            Settings // Command Deck
                        </span>
                        <span className={clsx('rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-[0.3em]', envBadge.tone)}>
                            ENVIRONMENT: {envBadge.label}
                        </span>
                        <span className={clsx('rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-[0.3em]', state.tone)}>
                            {state.tag}
                        </span>
                    </div>

                    <div className="space-y-3">
                        <h1 className="heading-title text-3xl font-black uppercase tracking-[0.08em] text-white sm:text-4xl">
                            Settings Command Deck
                        </h1>
                        <p className="max-w-3xl text-sm leading-6 text-slate-400 sm:text-base">
                            Runtime, delivery, and market policy orchestration for the local Horus stack.
                        </p>
                    </div>

                    <div className="grid gap-2 sm:grid-cols-3">
                        <div className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2">
                            <p className="meta-label text-slate-500">Runtime Doctrine</p>
                            <p className="mt-1 text-sm font-semibold text-slate-100">Local-first execution only</p>
                        </div>
                        <div className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2">
                            <p className="meta-label text-slate-500">Operator Priority</p>
                            <p className="mt-1 text-sm font-semibold text-slate-100">Assess readiness before editing</p>
                        </div>
                        <div className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2">
                            <p className="meta-label text-slate-500">Save Discipline</p>
                            <p className="mt-1 text-sm font-semibold text-slate-100">{state.detail}</p>
                        </div>
                    </div>
                </div>

                <div className="relative flex w-full max-w-sm flex-col gap-3 xl:items-end">
                    <div className="w-full rounded-lg border border-white/10 bg-black/20 p-3 xl:max-w-sm">
                        <p className="meta-label text-slate-500">Commit Control</p>
                        <p className="mt-2 font-mono text-xl font-semibold tracking-tight text-white">{state.tag}</p>
                        <p className="mt-1 text-sm leading-6 text-slate-400">{state.detail}</p>
                    </div>

                    <div className="flex w-full items-center gap-2 xl:max-w-sm">
                        <button
                            type="button"
                            onClick={handleToggleSnapshots}
                            className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-4 py-3.5 text-[11px] font-black uppercase tracking-[0.2em] text-slate-300 transition-colors hover:bg-white/10 hover:text-white"
                        >
                            <History className="h-4 w-4 text-cyan-400" />
                            <span>Rollback</span>
                        </button>

                        <button
                            type="button"
                            onClick={() => {
                                void onSave();
                            }}
                            disabled={saving || !hasChanges}
                            className={clsx(
                                'action-primary inline-flex flex-1 items-center justify-center gap-3 rounded-lg px-5 py-3.5 text-[11px] font-black uppercase tracking-[0.28em] transition-colors',
                                hasChanges
                                    ? '!bg-cyan-500 !text-slate-950 hover:!bg-cyan-400'
                                    : 'cursor-not-allowed border border-white/10 !bg-white/[0.04] !text-slate-500'
                            )}
                        >
                            {saving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                            <span>{saving ? 'Committing...' : 'Save Changes'}</span>
                        </button>
                    </div>

                    {isSnapshotOpen && (
                        <div className="absolute top-full z-50 mt-2 w-full rounded-xl border border-white/15 bg-slate-900/95 p-4 shadow-2xl backdrop-blur-md">
                            <div className="mb-3 flex items-center justify-between border-b border-white/10 pb-2">
                                <span className="text-xs font-black uppercase tracking-wider text-cyan-400">
                                    Config Snapshots
                                </span>
                                <button
                                    type="button"
                                    onClick={() => setIsSnapshotOpen(false)}
                                    className="text-xs text-slate-400 hover:text-white"
                                >
                                    Close
                                </button>
                            </div>

                            {loadingSnapshots ? (
                                <div className="py-4 text-center text-xs text-slate-400">Loading snapshots...</div>
                            ) : snapshots.length === 0 ? (
                                <div className="py-4 text-center text-xs text-slate-500">No snapshots found.</div>
                            ) : (
                                <div className="max-h-60 space-y-2 overflow-y-auto pr-1">
                                    {snapshots.map((item) => (
                                        <div
                                            key={item.filename}
                                            className="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.03] p-2.5 text-xs"
                                        >
                                            <div>
                                                <p className="font-mono font-semibold text-slate-200">
                                                    {item.filename.replace('settings_', '').replace('.json', '')}
                                                </p>
                                                <p className="text-[10px] text-slate-400">
                                                    {(item.size_bytes / 1024).toFixed(1)} KB
                                                </p>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => handleRestore(item.filename)}
                                                disabled={restoringFile === item.filename}
                                                className="inline-flex items-center gap-1.5 rounded bg-cyan-500/20 px-2.5 py-1 text-[10px] font-bold text-cyan-300 hover:bg-cyan-500/30 disabled:opacity-50"
                                            >
                                                {restoringFile === item.filename ? (
                                                    <RefreshCw className="h-3 w-3 animate-spin" />
                                                ) : (
                                                    <RotateCcw className="h-3 w-3" />
                                                )}
                                                Restore
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
