'use client';

import React from 'react';
import { AlertTriangle, DatabaseBackup, RefreshCw } from 'lucide-react';

import type { BackfillStatus } from '../hooks/useSettingsOperations';

interface SettingsOperationsSectionProps {
    saving: boolean;
    operationLoading: boolean;
    backfillTradingDays: number;
    backfillUniverseChoice: 'EGX30' | 'EGX70' | 'EGX100' | 'FULL';
    backfill: BackfillStatus;
    includeDangerZone?: boolean;
    onBackfillTradingDaysChange: (value: number) => void;
    onBackfillUniverseChoiceChange: (value: 'EGX30' | 'EGX70' | 'EGX100' | 'FULL') => void;
    onBackfill: () => void | Promise<void>;
    onHardReset: () => void | Promise<void>;
}

export function SettingsOperationsSection({
    saving,
    operationLoading,
    backfillTradingDays,
    backfillUniverseChoice,
    backfill,
    includeDangerZone = true,
    onBackfillTradingDaysChange,
    onBackfillUniverseChoiceChange,
    onBackfill,
    onHardReset,
}: SettingsOperationsSectionProps) {
    const busy = saving || operationLoading;
    const visibleUniverseChoice = String(backfill.universe_choice || backfillUniverseChoice || 'EGX30').toUpperCase();

    return (
        <>
            <div className="section-surface p-6 rounded-xl md:col-span-2">
                <div className="flex items-center mb-4">
                    <div className="p-2 bg-cyan-500/20 rounded-lg mr-2">
                        <DatabaseBackup className="h-5 w-5 text-cyan-400" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold">Historical Backfill</h2>
                        <p className="text-xs text-gray-400">Choose how many trading days of historical signal context to rebuild, then run backfill manually when needed.</p>
                    </div>
                </div>

                <div className="flex flex-col md:flex-row items-center justify-between p-4 bg-cyan-500/5 rounded-lg border border-cyan-500/20">
                    <div className="mb-4 md:mb-0 flex-1">
                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="max-w-xs">
                                <label className="block text-xs font-medium uppercase tracking-[0.2em] text-cyan-300/80 mb-2">
                                    Backfill Trading Days
                                </label>
                                <input
                                    type="number"
                                    min={1}
                                    max={365}
                                    value={backfillTradingDays}
                                    disabled={busy || backfill.status === 'RUNNING'}
                                    onChange={(e) => onBackfillTradingDaysChange(Math.max(1, Math.min(parseInt(e.target.value || '252', 10) || 252, 365)))}
                                    className="control-input w-full focus:border-cyan-500"
                                />
                            </div>
                            <div className="max-w-xs">
                                <label className="block text-xs font-medium uppercase tracking-[0.2em] text-cyan-300/80 mb-2">
                                    Backfill Universe
                                </label>
                                <select
                                    value={backfillUniverseChoice}
                                    disabled={busy || backfill.status === 'RUNNING'}
                                    onChange={(e) => onBackfillUniverseChoiceChange(e.target.value as 'EGX30' | 'EGX70' | 'EGX100' | 'FULL')}
                                    className="control-input w-full focus:border-cyan-500"
                                >
                                    <option value="EGX30">EGX30</option>
                                    <option value="EGX70">EGX70</option>
                                    <option value="EGX100">EGX100</option>
                                    <option value="FULL">FULL</option>
                                </select>
                            </div>
                        </div>
                        {backfill.status === 'RUNNING' ? (
                            <div className="space-y-2">
                                <div className="flex items-center gap-3">
                                    <RefreshCw className="h-4 w-4 text-cyan-400 animate-spin" />
                                    <span className="text-sm text-gray-200">
                                        Analyzing <span className="font-mono text-cyan-300">{backfill.current_day || '...'}</span>
                                        {' '} - trading day {backfill.progress + 1} of {backfill.total_days} - universe {visibleUniverseChoice}
                                    </span>
                                </div>
                                <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                                    <div
                                        className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full rounded-full transition-all"
                                        style={{ width: backfill.total_days ? `${((backfill.progress + 1) / backfill.total_days) * 100}%` : '0%' }}
                                    />
                                </div>
                                <p className="text-xs text-gray-400">{backfill.signals_found} signals found so far</p>
                            </div>
                        ) : backfill.status === 'COMPLETED' ? (
                            <p className="text-sm text-emerald-400">Backfill complete - {visibleUniverseChoice} - {backfill.signals_found} signals across {backfill.total_days} trading days.</p>
                        ) : backfill.status === 'COMPLETED_WITH_WARNINGS' ? (
                            <div className="space-y-1">
                                <p className="text-sm text-amber-300">Backfill complete with limited coverage - {visibleUniverseChoice} - {backfill.signals_found} signals across {backfill.total_days} trading days.</p>
                                <p className="text-xs text-amber-200/80">{backfill.error || `Historical coverage is shorter than the ${backfillTradingDays}-trading-day target.`}</p>
                            </div>
                        ) : backfill.status === 'ERROR' ? (
                            <p className="text-sm text-red-400">Backfill failed for {visibleUniverseChoice}: {backfill.error}</p>
                        ) : (
                            <p className="text-sm text-gray-400">Startup no longer runs historical backfill automatically. Save a trading-day target here, then run backfill manually when reports need deeper history.</p>
                        )}
                    </div>
                    <button
                        onClick={() => {
                            void onBackfill();
                        }}
                        disabled={busy || backfill.status === 'RUNNING'}
                        className="action-primary !bg-cyan-600 hover:!bg-cyan-500 whitespace-nowrap px-6 py-3 ml-4"
                    >
                        {backfill.status === 'RUNNING'
                            ? <><RefreshCw className="animate-spin h-5 w-5 mr-2 inline" />Running...</>
                            : <><DatabaseBackup className="h-5 w-5 mr-2 inline" />Run Backfill</>}
                    </button>
                </div>
            </div>

            {includeDangerZone ? (
                <div className="section-surface p-6 rounded-xl md:col-span-2 border border-red-500/30">
                    <div className="flex items-center mb-4">
                        <div className="p-2 bg-red-500/20 rounded-lg mr-2">
                            <AlertTriangle className="h-5 w-5 text-red-500" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-red-400">Danger Zone</h2>
                            <p className="text-xs text-red-300/80">Irreversible, destructive system operations.</p>
                        </div>
                    </div>

                    <div className="flex flex-col md:flex-row items-center justify-between p-4 bg-red-500/5 rounded-lg border border-red-500/20">
                        <div className="mb-4 md:mb-0">
                            <h3 className="text-lg font-medium text-white">Hard Reset System</h3>
                            <p className="text-sm text-gray-400 max-w-xl mt-1">
                                This action deletes the underlying <code className="text-xs bg-black/30 px-1 rounded">horus.db</code> database and all cached Parquet flat files.
                                All signals, portfolios, metrics, and accumulated market data will be permanently destroyed.
                                The system will come back online on the next startup, and you can rebuild deeper history manually from this Settings page when needed.
                            </p>
                        </div>
                        <button
                            onClick={() => {
                                void onHardReset();
                            }}
                            disabled={busy}
                            className="action-primary !bg-red-600 hover:!bg-red-500 whitespace-nowrap px-6 py-3"
                        >
                            {busy ? <RefreshCw className="animate-spin h-5 w-5 mr-2 inline" /> : <AlertTriangle className="h-5 w-5 mr-2 inline" />}
                            Hard Reset Data
                        </button>
                    </div>
                </div>
            ) : null}
        </>
    );
}
