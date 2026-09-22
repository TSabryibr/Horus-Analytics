'use client';

import { useEffect, useMemo, useState } from 'react';

import { clsx } from 'clsx';
import { Activity, AlertTriangle, Database, Play, RotateCw, Sliders } from 'lucide-react';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';

import type { BacktestSource, PineRunConfig } from '../hooks/useBacktestLab';
import type { PineProfileRecord } from '../hooks/usePineProfilePromotion';

const SIMULATION_FIELDS = [
    { label: 'RSI Entry', key: 'RSI_MIN', min: 30, max: 60, step: 1 },
    { label: 'RSI Overbought', key: 'RSI_MAX', min: 65, max: 90, step: 1 },
    { label: 'Vol Threshold', key: 'VOL_SPIKE', min: 1.0, max: 5.0, step: 0.1, unit: 'X' },
    { label: 'Momentum %', key: 'MOMENTUM', min: 0.5, max: 5.0, step: 0.1, unit: '%' },
    { label: 'Stop Loss', key: 'SL_PCT', min: 0.5, max: 5.0, step: 0.1, unit: '%' },
    { label: 'Target 1', key: 'TP1_PCT', min: 1.0, max: 10.0, step: 0.5, unit: '%' },
    { label: 'Max Slots', key: 'MAX_POSITIONS', min: 1, max: 20, step: 1 },
] as const;

const MARKET_OPTIONS = ['EGX30', 'EGX70', 'EGX100', 'ALL'] as const;
const TIMEFRAME_OPTIONS = ['1D', '1W', '1M'] as const;

const backtestFieldClass =
    'section-surface-muted industrial-corner w-full cursor-pointer appearance-none border border-white/10 px-4 py-3.5 text-[11px] font-black tracking-[0.2em] text-slate-200 transition-all hover:border-white/16 focus:border-primary/50 focus:outline-none';

const rangeTrackClass = 'absolute inset-0 rounded-full bg-white/[0.06]';

type SimulationParams = {
    RSI_MIN: number;
    RSI_MAX: number;
    VOL_SPIKE: number;
    MOMENTUM: number;
    SL_PCT: number;
    TP1_PCT: number;
    MAX_POSITIONS: number;
    TRAILING_STOP_ENABLED: boolean;
    TRAILING_STOP_TYPE: string;
    TRAILING_STOP_VALUE: number;
};

type BacktestLabPanelProps = {
    optIndex: string;
    simParams: SimulationParams;
    simLoading: boolean;
    backtestSource: BacktestSource;
    pineProfiles: PineProfileRecord[];
    pineProfilesLoading: boolean;
    selectedPineProfileId: number | null;
    pineRunConfig: PineRunConfig;
    onSelectIndex: (value: string) => void;
    onChangeParam: (nextParams: SimulationParams) => void;
    onRunSimulation: (profileIdOverride?: number | null) => void | Promise<void>;
    onChangeBacktestSource: (source: BacktestSource) => void;
    onSelectPineProfile: (profileId: number | null) => void;
    onChangePineRunConfig: (nextConfig: PineRunConfig) => void;
};

function FieldHeader({ label, value }: { label: string; value?: string | number | null }) {
    return (
        <div className="mb-4 flex justify-between text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">
            <span>{label}</span>
            {value !== undefined && value !== null && <span className="font-mono font-bold text-white">{value}</span>}
        </div>
    );
}

function ProfileStateBadge({ state }: { state: string }) {
    const normalizedState = String(state || 'UNKNOWN').toUpperCase();
    return (
        <span
            className={clsx(
                'industrial-corner inline-flex items-center border px-2 py-1 text-[9px] font-black uppercase tracking-[0.25em]',
                normalizedState === 'ACTIVE' && 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
                normalizedState === 'READY' && 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300',
                normalizedState === 'DRAFT' && 'border-amber-500/40 bg-amber-500/10 text-amber-300',
                !['ACTIVE', 'READY', 'DRAFT'].includes(normalizedState) && 'border-white/10 bg-white/[0.06] text-slate-300'
            )}
        >
            {normalizedState}
        </span>
    );
}

export function BacktestLabPanel({
    optIndex,
    simParams,
    simLoading,
    backtestSource,
    pineProfiles,
    pineProfilesLoading,
    selectedPineProfileId,
    pineRunConfig,
    onSelectIndex,
    onChangeParam,
    onRunSimulation,
    onChangeBacktestSource,
    onSelectPineProfile,
    onChangePineRunConfig,
}: BacktestLabPanelProps) {
    const [pineProfileSelection, setPineProfileSelection] = useState(selectedPineProfileId?.toString() ?? '');
    const isPineMode = backtestSource === 'PINE_PROFILE';
    const effectiveSelectedPineProfileId = pineProfileSelection ? Number(pineProfileSelection) : selectedPineProfileId;
    const selectedPineProfile = useMemo(
        () => pineProfiles.find((profile) => profile.profile_id === effectiveSelectedPineProfileId) ?? null,
        [effectiveSelectedPineProfileId, pineProfiles]
    );
    const runDisabled = simLoading || (isPineMode && !effectiveSelectedPineProfileId);

    useEffect(() => {
        setPineProfileSelection(selectedPineProfileId?.toString() ?? '');
    }, [selectedPineProfileId]);

    const updatePineConfig = (key: keyof PineRunConfig, rawValue: string) => {
        const numericKeys: Array<keyof PineRunConfig> = ['capital', 'commissionPct', 'slippagePct'];
        onChangePineRunConfig({
            ...pineRunConfig,
            [key]: numericKeys.includes(key) ? Number(rawValue) : rawValue,
        });
    };

    return (
        <IndustrialCard
            tone="secondary"
            className="group relative h-fit overflow-hidden"
            contentClassName="p-8"
        >
            <div className="absolute right-0 top-0 p-2 opacity-20">
                <Sliders size={40} className="text-primary transition-transform duration-700 group-hover:rotate-12" />
            </div>

            <div className="mb-10 flex items-center gap-4">
                <div className="h-1 w-1 bg-primary" />
                <h2 className="font-heading text-xs font-black uppercase tracking-[0.3em] text-white">System_Configuration</h2>
            </div>

            <div className="space-y-10">
                <div className="section-surface-muted industrial-corner border border-white/8 p-5">
                    <FieldHeader label="Backtest Source" />
                    <div className="grid grid-cols-2 gap-3">
                        <IndustrialButton
                            type="button"
                            aria-pressed={backtestSource === 'HORUS'}
                            onClick={() => onChangeBacktestSource('HORUS')}
                            variant={backtestSource === 'HORUS' ? 'primary' : 'secondary'}
                            className="w-full px-4 py-3 text-[10px] tracking-[0.25em]"
                        >
                            Horus Strategy
                        </IndustrialButton>
                        <IndustrialButton
                            type="button"
                            aria-pressed={backtestSource === 'PINE_PROFILE'}
                            onClick={() => onChangeBacktestSource('PINE_PROFILE')}
                            variant={backtestSource === 'PINE_PROFILE' ? 'primary' : 'secondary'}
                            className="w-full px-4 py-3 text-[10px] tracking-[0.25em]"
                        >
                            Pine Profile
                        </IndustrialButton>
                    </div>
                </div>

                {!isPineMode && (
                    <>
                        <div className="group/field">
                            <div className="mb-3 flex justify-between text-[9px] font-black uppercase tracking-[0.3em] text-slate-500 transition-colors group-hover/field:text-primary">
                                <span>Market_Matrix</span>
                                <Activity className="h-3 w-3 text-primary/40" />
                            </div>
                            <div className="relative">
                                <select
                                    value={optIndex}
                                    onChange={(event) => onSelectIndex(event.target.value)}
                                    className={backtestFieldClass}
                                >
                                    <option value="EGX30" className="bg-slate-950">
                                        EGX 30 Blue Chips
                                    </option>
                                    <option value="EGX70" className="bg-slate-950">
                                        EGX 70 Mid-Cap
                                    </option>
                                    <option value="EGX100" className="bg-slate-950">
                                        EGX 100 Index
                                    </option>
                                    <option value="ALL" className="bg-slate-950">
                                        Full Market Matrix
                                    </option>
                                </select>
                                <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 opacity-40">
                                    <div className="h-0 w-0 border-l-[4px] border-r-[4px] border-t-[4px] border-l-transparent border-r-transparent border-t-white" />
                                </div>
                            </div>
                        </div>

                        {SIMULATION_FIELDS.map((field) => (
                            <div key={field.key} className="group/field">
                                <div className="mb-4 flex justify-between text-[9px] font-black uppercase tracking-[0.3em] text-slate-500 transition-colors group-hover/field:text-primary">
                                    <span>{field.label.replace(' ', '_')}</span>
                                    <span className="font-mono font-bold text-white">
                                        {simParams[field.key]}
                                        {'unit' in field ? field.unit : ''}
                                    </span>
                                </div>
                                <div className="relative flex h-1.5 items-center">
                                    <div className={rangeTrackClass} />
                                    <input
                                        type="range"
                                        min={field.min}
                                        max={field.max}
                                        step={field.step}
                                        value={simParams[field.key]}
                                        onChange={(event) =>
                                            onChangeParam({
                                                ...simParams,
                                                [field.key]: parseFloat(event.target.value),
                                            })
                                        }
                                        aria-label={field.label}
                                        className="relative z-10 h-1.5 w-full cursor-pointer appearance-none rounded-full bg-transparent accent-primary"
                                    />
                                </div>
                            </div>
                        ))}

                        <div className="section-surface-muted industrial-corner border border-white/8 p-6">
                            <div className="mb-6 flex items-center justify-between">
                                <span className="text-[9px] font-black uppercase tracking-[0.3em] text-slate-400">Trailing_Stop</span>
                                <button
                                    onClick={() =>
                                        onChangeParam({
                                            ...simParams,
                                            TRAILING_STOP_ENABLED: !simParams.TRAILING_STOP_ENABLED,
                                        })
                                    }
                                    type="button"
                                    aria-label="Toggle trailing stop"
                                    className={clsx(
                                        'industrial-corner relative h-6 w-12 border transition-all',
                                        simParams.TRAILING_STOP_ENABLED
                                            ? 'border-primary/50 bg-primary'
                                            : 'border-white/10 bg-white/[0.06]'
                                    )}
                                >
                                    <div
                                        className={clsx(
                                            'industrial-corner absolute top-1/2 h-4 w-4 -translate-y-1/2 transition-all duration-300',
                                            simParams.TRAILING_STOP_ENABLED ? 'left-7 bg-white' : 'left-1 bg-slate-600'
                                        )}
                                    />
                                </button>
                            </div>
                            {simParams.TRAILING_STOP_ENABLED && (
                                <div className="animate-in slide-in-from-top-2 duration-300">
                                    <div className="mb-4 flex justify-between text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">
                                        <span>Trail_Buffer</span>
                                        <span className="font-mono font-bold text-white">{simParams.TRAILING_STOP_VALUE}%</span>
                                    </div>
                                    <div className="relative flex h-1.5 items-center">
                                        <div className={rangeTrackClass} />
                                        <input
                                            type="range"
                                            min={0.5}
                                            max={5.0}
                                            step={0.1}
                                            value={simParams.TRAILING_STOP_VALUE}
                                            onChange={(event) =>
                                                onChangeParam({
                                                    ...simParams,
                                                    TRAILING_STOP_VALUE: parseFloat(event.target.value),
                                                })
                                            }
                                            aria-label="Trailing stop value"
                                            className="relative z-10 h-1.5 w-full cursor-pointer appearance-none rounded-full bg-transparent accent-primary"
                                        />
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                )}

                {isPineMode && (
                    <>
                        <div className="group/field">
                            <div className="mb-3 flex justify-between text-[9px] font-black uppercase tracking-[0.3em] text-slate-500 transition-colors group-hover/field:text-primary">
                                <span>Saved_Pine_Profile</span>
                                <Database className="h-3 w-3 text-primary/40" />
                            </div>
                            <div className="relative">
                                <label htmlFor="backtester-pine-profile" className="sr-only">
                                    Saved Pine Profile
                                </label>
                                <select
                                    id="backtester-pine-profile"
                                    aria-label="Saved Pine Profile"
                                    value={pineProfileSelection}
                                    onChange={(event) => {
                                        setPineProfileSelection(event.target.value);
                                        onSelectPineProfile(event.target.value ? Number(event.target.value) : null);
                                    }}
                                    className={backtestFieldClass}
                                >
                                    <option value="" className="bg-slate-950">
                                        {pineProfilesLoading ? 'Loading Pine registry...' : 'Select a saved Pine profile'}
                                    </option>
                                    {pineProfiles.map((profile) => (
                                        <option key={profile.profile_id} value={profile.profile_id} className="bg-slate-950">
                                            {profile.profile_name} [{profile.profile_state}]
                                        </option>
                                    ))}
                                </select>
                                <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 opacity-40">
                                    <div className="h-0 w-0 border-l-[4px] border-r-[4px] border-t-[4px] border-l-transparent border-r-transparent border-t-white" />
                                </div>
                            </div>
                            {!pineProfilesLoading && pineProfiles.length === 0 && (
                                <p className="mt-3 text-[11px] text-slate-500">No saved Pine profiles yet. Create one from Pine Lab first.</p>
                            )}
                        </div>

                        {selectedPineProfile && (
                            <>
                        <div className="section-surface-muted industrial-corner border border-white/8 p-5">
                                    <div className="mb-4 flex items-center justify-between gap-4">
                                        <div className="space-y-1">
                                            <p className="text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">Logic Source</p>
                                            <p className="text-sm font-black uppercase tracking-[0.18em] text-white">
                                                Logic Source: {selectedPineProfile.profile_name}
                                            </p>
                                        </div>
                                        <ProfileStateBadge state={selectedPineProfile.profile_state} />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4 text-[10px] uppercase tracking-[0.25em] text-slate-400">
                                        <div>Stored Market: {selectedPineProfile.market ?? 'EGX30'}</div>
                                        <div>Stored Timeframe: {selectedPineProfile.timeframe ?? '1D'}</div>
                                    </div>
                                </div>

                                {selectedPineProfile.profile_state === 'DRAFT' ? (
                                    <div className="industrial-corner flex items-start gap-3 border border-amber-500/30 bg-amber-500/10 p-4 text-amber-200">
                                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                                        <div className="space-y-1">
                                            <p className="text-[10px] font-black uppercase tracking-[0.25em]">Draft Profile</p>
                                            <p className="text-sm">Draft profile: this Pine strategy has not passed promotion gates yet.</p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="industrial-corner border border-cyan-500/20 bg-cyan-500/5 p-4 text-cyan-100">
                                        <p className="text-[10px] font-black uppercase tracking-[0.25em]">
                                            {selectedPineProfile.profile_state === 'ACTIVE' ? 'Active Scanner Profile' : 'Ready Research Profile'}
                                        </p>
                                        <p className="mt-1 text-sm text-slate-300">
                                            Pine logic stays read-only here. These run settings only affect the current Backtester session.
                                        </p>
                                    </div>
                                )}
                            </>
                        )}

                        <div className="section-surface-muted industrial-corner border border-white/8 p-6">
                            <FieldHeader label="Run Settings" />
                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                <div>
                                    <label htmlFor="pine-run-market" className="mb-2 block text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">
                                        Market
                                    </label>
                                    <select
                                        id="pine-run-market"
                                        aria-label="Pine run market"
                                        value={pineRunConfig.market}
                                        onChange={(event) => updatePineConfig('market', event.target.value)}
                                        className={backtestFieldClass}
                                    >
                                        {MARKET_OPTIONS.map((option) => (
                                            <option key={option} value={option} className="bg-slate-950">
                                                {option}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label htmlFor="pine-run-timeframe" className="mb-2 block text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">
                                        Timeframe
                                    </label>
                                    <select
                                        id="pine-run-timeframe"
                                        aria-label="Pine run timeframe"
                                        value={pineRunConfig.timeframe}
                                        onChange={(event) => updatePineConfig('timeframe', event.target.value)}
                                        className={backtestFieldClass}
                                    >
                                        {TIMEFRAME_OPTIONS.map((option) => (
                                            <option key={option} value={option} className="bg-slate-950">
                                                {option}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label htmlFor="pine-run-date-from" className="mb-2 block text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">
                                        Date From
                                    </label>
                                    <input
                                        id="pine-run-date-from"
                                        aria-label="Pine run date from"
                                        type="date"
                                        value={pineRunConfig.dateFrom}
                                        onChange={(event) => updatePineConfig('dateFrom', event.target.value)}
                                        className={backtestFieldClass}
                                    />
                                </div>
                                <div>
                                    <label htmlFor="pine-run-date-to" className="mb-2 block text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">
                                        Date To
                                    </label>
                                    <input
                                        id="pine-run-date-to"
                                        aria-label="Pine run date to"
                                        type="date"
                                        value={pineRunConfig.dateTo}
                                        onChange={(event) => updatePineConfig('dateTo', event.target.value)}
                                        className={backtestFieldClass}
                                    />
                                </div>
                                <div>
                                    <label htmlFor="pine-run-capital" className="mb-2 block text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">
                                        Capital
                                    </label>
                                    <input
                                        id="pine-run-capital"
                                        aria-label="Pine run capital"
                                        type="number"
                                        min={1}
                                        step={1000}
                                        value={pineRunConfig.capital}
                                        onChange={(event) => updatePineConfig('capital', event.target.value)}
                                        className={backtestFieldClass}
                                    />
                                </div>
                                <div>
                                    <label htmlFor="pine-run-commission" className="mb-2 block text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">
                                        Commission %
                                    </label>
                                    <input
                                        id="pine-run-commission"
                                        aria-label="Pine run commission percent"
                                        type="number"
                                        min={0}
                                        step={0.01}
                                        value={pineRunConfig.commissionPct}
                                        onChange={(event) => updatePineConfig('commissionPct', event.target.value)}
                                        className={backtestFieldClass}
                                    />
                                </div>
                                <div className="md:col-span-2">
                                    <label htmlFor="pine-run-slippage" className="mb-2 block text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">
                                        Slippage %
                                    </label>
                                    <input
                                        id="pine-run-slippage"
                                        aria-label="Pine run slippage percent"
                                        type="number"
                                        min={0}
                                        step={0.1}
                                        value={pineRunConfig.slippagePct}
                                        onChange={(event) => updatePineConfig('slippagePct', event.target.value)}
                                        className={backtestFieldClass}
                                    />
                                </div>
                            </div>
                        </div>
                    </>
                )}

                <IndustrialButton
                    type="button"
                    onClick={() => onRunSimulation(isPineMode ? effectiveSelectedPineProfileId ?? null : undefined)}
                    disabled={runDisabled}
                    variant={runDisabled ? 'secondary' : 'primary'}
                    size="lg"
                    className="group/btn relative w-full overflow-hidden py-5 text-[11px] tracking-[0.3em]"
                >
                    <div className="absolute inset-0 -translate-x-full skew-x-12 bg-white/20 transition-transform duration-1000 group-hover/btn:translate-x-full" />
                    {simLoading ? <RotateCw className="h-4 w-4 animate-spin" /> : <Play size={16} fill="currentColor" />}
                    {simLoading ? 'Engaging_Engines' : 'Init_Backtest'}
                </IndustrialButton>
            </div>
        </IndustrialCard>
    );
}
