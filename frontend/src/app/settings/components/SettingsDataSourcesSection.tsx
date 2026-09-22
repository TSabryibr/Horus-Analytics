'use client';

import React from 'react';
import { Activity } from 'lucide-react';

import type { SettingsState } from '../hooks/useSettingsRuntime';

interface SettingsDataSourcesSectionProps {
    settings: SettingsState;
    onChange: (key: string, value: string | boolean) => void;
}

const FieldGroup = ({
    label,
    desc,
    children,
}: {
    label: string;
    desc: string;
    children: React.ReactNode;
}) => (
    <div className="mb-6">
        <label className="block text-sm font-medium text-gray-300 mb-1">{label}</label>
        <p className="text-xs text-gray-500 mb-2">{desc}</p>
        {children}
    </div>
);

type SourceCard = {
    label: string;
    ready: boolean;
    path: string;
    detail?: string;
};

const SourceReadinessCard = ({ card }: { card: SourceCard }) => (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
        <div className="flex items-center justify-between gap-3">
            <span className="text-sm font-semibold text-white">{card.label}</span>
            <span className={`rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.2em] ${card.ready ? 'border-cyan-500/30 bg-cyan-500/10 text-cyan-100' : 'border-orange-500/30 bg-orange-500/10 text-orange-100'}`}>
                {card.ready ? 'Ready' : 'Missing'}
            </span>
        </div>
        {card.detail ? <p className="mt-3 text-xs leading-5 text-slate-400">{card.detail}</p> : null}
        <p className="mt-3 break-all font-mono text-xs leading-5 text-slate-500">{card.path}</p>
    </div>
);

export function SettingsDataSourcesSection({
    settings,
    onChange,
}: SettingsDataSourcesSectionProps) {
    const historicalTradeDetails = [
        `Latest: ${settings.MUBASHER_HISTORICAL_TRADE_LATEST_DATE || 'none'}`,
        `DB files: ${Number(settings.MUBASHER_HISTORICAL_TRADE_DB_COUNT ?? 0)}`,
    ].join(' | ');

    const mubasherCards: SourceCard[] = [
        {
            label: 'Mubasher History DB',
            ready: Boolean(settings.MUBASHER_HISTORY_DB_AVAILABLE),
            path: settings.MUBASHER_HISTORY_DB_PATH || settings.MUBASHER_ROOT_DIR || 'not configured',
            detail: 'Daily OHLCV source used by history ingest and historical backfill.',
        },
        {
            label: 'Mubasher Intraday DB',
            ready: Boolean(settings.MUBASHER_INTRADAY_DB_AVAILABLE),
            path: settings.MUBASHER_INTRADAY_DB_PATH || settings.MUBASHER_ROOT_DIR || 'not configured',
            detail: 'Minute-bar archive used by ingest_intraday.',
        },
        {
            label: 'HistoricalTrade Ticks',
            ready: Boolean(settings.MUBASHER_HISTORICAL_TRADE_AVAILABLE),
            path: settings.MUBASHER_HISTORICAL_TRADE_FOLDER || settings.MUBASHER_ROOT_DIR || 'not configured',
            detail: historicalTradeDetails,
        },
    ];

    const fallbackMountCards: SourceCard[] = [
        {
            label: 'History DAT',
            ready: Boolean(settings.METASTOCK_DAT_HISTORY_AVAILABLE),
            path: settings.METASTOCK_DAT_HISTORY_FOLDER || 'not configured',
        },
        {
            label: 'Intraday DAT',
            ready: Boolean(settings.METASTOCK_DAT_INTRADAY_AVAILABLE),
            path: settings.METASTOCK_DAT_INTRADAY_FOLDER || 'not configured',
        },
        {
            label: 'Intraday CSV',
            ready: Boolean(settings.METASTOCK_INTRADAY_AVAILABLE),
            path: settings.METASTOCK_INTRADAY_FOLDER || 'not configured',
        },
    ];

    return (
        <div className="section-surface p-6 rounded-xl md:col-span-2">
            <div className="flex items-center mb-6">
                <div className="p-2 bg-amber-500/20 rounded-lg mr-2">
                    <Activity className="h-5 w-5 text-amber-300" />
                </div>
                <div>
                    <h2 className="text-xl font-bold">Local Data Source Policy</h2>
                    <p className="text-xs text-gray-400">
                        Set provider policy per timeframe. Mubasher DB is the default high-precision source.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                <FieldGroup label="History Provider" desc="AUTO, MetaStock DAT, CSV, Mubasher DB, or DirectFN feed">
                    <select
                        value={settings.LOCAL_HISTORY_PROVIDER || 'MUBASHER_DB'}
                        onChange={(e) => onChange('LOCAL_HISTORY_PROVIDER', e.target.value)}
                        className="control-input w-full focus:border-amber-500"
                    >
                        <option value="METASTOCK_DAT">METASTOCK_DAT</option>
                        <option value="MUBASHER_DB">MUBASHER_DB</option>
                        <option value="AUTO">AUTO</option>
                        <option value="CSV">CSV</option>
                        <option value="DIRECTFN">DIRECTFN</option>
                    </select>
                </FieldGroup>

                <FieldGroup label="Intraday Provider" desc="MetaStock DAT/CSV options require their paths to be mounted">
                    <select
                        value={settings.LOCAL_INTRADAY_PROVIDER || 'MUBASHER_DB'}
                        onChange={(e) => onChange('LOCAL_INTRADAY_PROVIDER', e.target.value)}
                        className="control-input w-full focus:border-amber-500"
                    >
                        <option value="METASTOCK_DAT" disabled={!Boolean(settings.METASTOCK_DAT_INTRADAY_AVAILABLE)}>
                            METASTOCK_DAT {!Boolean(settings.METASTOCK_DAT_INTRADAY_AVAILABLE) ? '(mount missing)' : ''}
                        </option>
                        <option value="MUBASHER_DB">MUBASHER_DB</option>
                        <option value="AUTO">AUTO</option>
                        <option value="DIRECTFN">DIRECTFN</option>
                        <option value="CSV" disabled={!Boolean(settings.METASTOCK_INTRADAY_AVAILABLE)}>
                            CSV {!Boolean(settings.METASTOCK_INTRADAY_AVAILABLE) ? '(mount missing)' : ''}
                        </option>
                    </select>
                    <p className="text-xs text-gray-500 mt-2">
                        Intraday DAT path: {settings.METASTOCK_DAT_INTRADAY_FOLDER || 'not configured'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                        Intraday CSV path: {settings.METASTOCK_INTRADAY_FOLDER || 'not configured'}
                    </p>
                </FieldGroup>

                <FieldGroup label="Ticks Provider" desc="HistoricalTrade ticks are read from Mubasher DB files">
                    <select
                        value={settings.LOCAL_TICKS_PROVIDER || 'MUBASHER_DB'}
                        onChange={(e) => onChange('LOCAL_TICKS_PROVIDER', e.target.value)}
                        className="control-input w-full focus:border-amber-500"
                    >
                        <option value="MUBASHER_DB">MUBASHER_DB</option>
                        <option value="AUTO">AUTO</option>
                    </select>
                    <label className="mt-3 flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-slate-300">
                        <input
                            type="checkbox"
                            checked={Boolean(settings.TICK_SYNC_ENABLED ?? true)}
                            onChange={(e) => onChange('TICK_SYNC_ENABLED', e.target.checked)}
                            className="h-4 w-4 accent-amber-400"
                        />
                        Sync HistoricalTrade ticks
                    </label>
                </FieldGroup>
            </div>

            <div className="mt-2 space-y-4">
                <div>
                    <p className="meta-label text-slate-500">Mubasher streams</p>
                    <div className="mt-3 grid gap-4 md:grid-cols-3">
                        {mubasherCards.map((card) => (
                            <SourceReadinessCard key={card.label} card={card} />
                        ))}
                    </div>
                    {settings.MUBASHER_STREAM_DISCOVERY_ERROR ? (
                        <p className="mt-3 rounded-xl border border-orange-500/20 bg-orange-500/10 px-3 py-2 text-xs text-orange-100">
                            {settings.MUBASHER_STREAM_DISCOVERY_ERROR}
                        </p>
                    ) : null}
                </div>

                <div>
                    <p className="meta-label text-slate-500">Fallback mounts</p>
                    <div className="mt-3 grid gap-4 md:grid-cols-3">
                        {fallbackMountCards.map((card) => (
                            <SourceReadinessCard key={card.label} card={card} />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
