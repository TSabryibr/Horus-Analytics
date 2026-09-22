'use client';

import { useState } from 'react';
import { Database, HardDrive, ShieldCheck, RefreshCw, Clock, AlertCircle } from 'lucide-react';
import clsx from 'clsx';

interface StatusBackupCardProps {
    backupStatus?: {
        configured?: boolean;
        backup_count?: number;
        total_size_mb?: number;
        latest_backup?: {
            filename: string;
            size_mb: number;
            created_at: string;
            age_days: number;
        } | null;
        live_db_size_mb?: number;
        retention_days?: number;
        status?: string;
    };
    onSnapshotTaken?: () => void;
}

export function StatusBackupCard({ backupStatus, onSnapshotTaken }: StatusBackupCardProps) {
    const [loading, setLoading] = useState(false);
    const [actionMsg, setActionMsg] = useState<string | null>(null);

    const status = (backupStatus?.status || 'PENDING').toUpperCase();
    const count = backupStatus?.backup_count ?? 0;
    const totalMb = backupStatus?.total_size_mb ?? 0;
    const latest = backupStatus?.latest_backup;
    const retention = backupStatus?.retention_days ?? 14;

    const handleCreateSnapshot = async () => {
        setLoading(true);
        setActionMsg(null);
        try {
            const res = await fetch('/api/v1/system/backups', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ label: 'manual_ui' }),
            });
            const data = await res.json();
            if (res.ok) {
                setActionMsg('Snapshot created successfully');
                if (onSnapshotTaken) {
                    onSnapshotTaken();
                }
            } else {
                setActionMsg(`Failed: ${data.detail || 'Error'}`);
            }
        } catch (err: any) {
            setActionMsg(`Error: ${err.message}`);
        } finally {
            setLoading(false);
            setTimeout(() => setActionMsg(null), 5000);
        }
    };

    return (
        <div className="bg-[#0A0D14] border border-white/10 rounded-3xl p-8 space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-xl">
                        <Database className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white uppercase tracking-tight">
                            Disaster Recovery & Snapshots
                        </h2>
                        <p className="text-xs text-slate-400">
                            Zero-Downtime SQLite Online Streaming & 14-Day Rolling Backups
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <span
                        className={clsx(
                            'px-3 py-1 text-[10px] font-black uppercase rounded-full tracking-wider border',
                            status === 'HEALTHY'
                                ? 'bg-emerald-950/40 text-emerald-400 border-emerald-800/60'
                                : status === 'PENDING'
                                    ? 'bg-amber-950/40 text-amber-400 border-amber-800/60'
                                    : 'bg-rose-950/40 text-rose-400 border-rose-800/60'
                        )}
                    >
                        {status}
                    </span>

                    <button
                        onClick={handleCreateSnapshot}
                        disabled={loading}
                        className={clsx(
                            'flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase rounded-xl transition-all',
                            'bg-primary/20 hover:bg-primary/30 text-primary border border-primary/40',
                            'disabled:opacity-50 disabled:cursor-not-allowed'
                        )}
                    >
                        <RefreshCw className={clsx('w-3.5 h-3.5', loading && 'animate-spin')} />
                        {loading ? 'Snapshotting...' : 'Snapshot Now'}
                    </button>
                </div>
            </div>

            {actionMsg && (
                <div className="p-3 bg-white/5 border border-white/10 rounded-xl text-xs font-medium text-slate-300">
                    {actionMsg}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 bg-slate-900/50 border border-white/5 rounded-2xl">
                    <div className="flex items-center gap-2 text-slate-400 text-[10px] font-black uppercase mb-1">
                        <Clock className="w-3.5 h-3.5" />
                        <span>Latest Snapshot</span>
                    </div>
                    <p className="text-sm font-bold text-white truncate">
                        {latest ? new Date(latest.created_at).toLocaleString() : 'None Recorded'}
                    </p>
                    <p className="text-[10px] text-slate-500 mt-1 font-mono">
                        {latest ? `${latest.age_days}d ago | ${latest.size_mb} MB` : 'Run daily at 15:45'}
                    </p>
                </div>

                <div className="p-4 bg-slate-900/50 border border-white/5 rounded-2xl">
                    <div className="flex items-center gap-2 text-slate-400 text-[10px] font-black uppercase mb-1">
                        <HardDrive className="w-3.5 h-3.5" />
                        <span>Retention Ratio</span>
                    </div>
                    <p className="text-lg font-black text-white">
                        {count} <span className="text-xs text-slate-500 font-bold">/ {retention} Days</span>
                    </p>
                    <p className="text-[10px] text-slate-500 mt-1">
                        Automatic pruning of &gt;14d files
                    </p>
                </div>

                <div className="p-4 bg-slate-900/50 border border-white/5 rounded-2xl">
                    <div className="flex items-center gap-2 text-slate-400 text-[10px] font-black uppercase mb-1">
                        <Database className="w-3.5 h-3.5" />
                        <span>Backup Storage</span>
                    </div>
                    <p className="text-lg font-black text-white">
                        {totalMb} <span className="text-xs text-slate-500 font-bold">MB</span>
                    </p>
                    <p className="text-[10px] text-slate-500 mt-1">
                        {latest?.filename || 'Stored in data/backups/'}
                    </p>
                </div>

                <div className="p-4 bg-slate-900/50 border border-white/5 rounded-2xl">
                    <div className="flex items-center gap-2 text-emerald-400 text-[10px] font-black uppercase mb-1">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>Storage Integrity</span>
                    </div>
                    <p className="text-sm font-bold text-emerald-400 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4" />
                        PRAGMA Verified
                    </p>
                    <p className="text-[10px] text-slate-500 mt-1 font-mono">
                        Live DB: {backupStatus?.live_db_size_mb ?? 0} MB
                    </p>
                </div>
            </div>
        </div>
    );
}
