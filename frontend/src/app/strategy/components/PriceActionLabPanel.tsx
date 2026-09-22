import clsx from 'clsx';
import {
    Activity,
    BadgeAlert,
    BarChart3,
    CheckCircle2,
    Loader2,
    PlayCircle,
    Radio,
    ShieldAlert,
    Zap,
} from 'lucide-react';

import type {
    PriceActionBacktestResponse,
    PriceActionCatalogStrategy,
    PriceActionSignalPreview,
} from '@/types/domain';
import type { ScannerStrategyProfileAudit } from '@/types';

type BusyAction = 'evaluate' | 'backtest' | 'promote' | 'activate' | null;

type PriceActionLabPanelProps = {
    actionError: string;
    actionSuccess: string;
    backtestResult: PriceActionBacktestResponse | null;
    busyAction: BusyAction;
    capital: number;
    catalogError: string;
    catalogLoading: boolean;
    dateFrom: string;
    dateTo: string;
    familyFilter: 'ALL' | 'INTRADAY' | 'SWING' | 'POSITION';
    filteredCatalog: PriceActionCatalogStrategy[];
    market: string;
    profileName: string;
    promotedProfile: ScannerStrategyProfileAudit | null;
    selectedStrategy: PriceActionCatalogStrategy | null;
    selectedStrategyId: string;
    signals: PriceActionSignalPreview[];
    ticker: string;
    onActivate: () => void;
    onBacktest: () => void;
    onEvaluate: () => void;
    onPromote: () => void;
    onReloadCatalog: () => void;
    setCapital: (value: number) => void;
    setDateFrom: (value: string) => void;
    setDateTo: (value: string) => void;
    setFamilyFilter: (value: 'ALL' | 'INTRADAY' | 'SWING' | 'POSITION') => void;
    setMarket: (value: string) => void;
    setProfileName: (value: string) => void;
    setSelectedStrategyId: (value: string) => void;
    setTicker: (value: string) => void;
};

const familyOptions: Array<'ALL' | 'INTRADAY' | 'SWING' | 'POSITION'> = ['ALL', 'INTRADAY', 'SWING', 'POSITION'];

function formatPct(value?: number | null) {
    if (value == null || Number.isNaN(value)) return '—';
    return `${value.toFixed(2)}%`;
}

function formatMoney(value?: number | null) {
    if (value == null || Number.isNaN(value)) return '—';
    return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function PriceActionLabPanel({
    actionError,
    actionSuccess,
    backtestResult,
    busyAction,
    capital,
    catalogError,
    catalogLoading,
    dateFrom,
    dateTo,
    familyFilter,
    filteredCatalog,
    market,
    profileName,
    promotedProfile,
    selectedStrategy,
    selectedStrategyId,
    signals,
    ticker,
    onActivate,
    onBacktest,
    onEvaluate,
    onPromote,
    onReloadCatalog,
    setCapital,
    setDateFrom,
    setDateTo,
    setFamilyFilter,
    setMarket,
    setProfileName,
    setSelectedStrategyId,
    setTicker,
}: PriceActionLabPanelProps) {
    return (
        <section className="section-surface industrial-corner rounded-xl p-6 space-y-6">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                <div className="space-y-2">
                    <div className="flex items-center gap-2 text-slate-200">
                        <Zap className="h-5 w-5 text-emerald-300" />
                        <h3 className="text-lg font-bold">Price Action Lab</h3>
                    </div>
                    <p className="max-w-3xl text-sm text-slate-400">
                        Browse the EGX research pack, preview signal behavior, backtest shortlisted setups, and promote a passing profile directly into the scanner.
                    </p>
                </div>
                <button
                    onClick={onReloadCatalog}
                    className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs font-semibold text-slate-200 transition hover:bg-white/[0.05]"
                >
                    <Radio className="h-4 w-4" />
                    Reload Catalog
                </button>
            </div>

            {(catalogError || actionError || actionSuccess) && (
                <div className="grid gap-3 xl:grid-cols-3">
                    {catalogError && (
                        <div className="rounded-lg border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">{catalogError}</div>
                    )}
                    {actionError && (
                        <div className="rounded-lg border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">{actionError}</div>
                    )}
                    {actionSuccess && (
                        <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">{actionSuccess}</div>
                    )}
                </div>
            )}

            <div className="grid gap-6 xl:grid-cols-[1.2fr_0.9fr]">
                <div className="space-y-5">
                    <div className="flex flex-wrap gap-2">
                        {familyOptions.map((option) => (
                            <button
                                key={option}
                                onClick={() => setFamilyFilter(option)}
                                className={clsx(
                                    'rounded-lg border px-3 py-2 text-xs font-semibold transition',
                                    familyFilter === option
                                        ? 'border-emerald-400/40 bg-emerald-500/12 text-emerald-100'
                                        : 'border-white/10 bg-white/[0.03] text-slate-300 hover:bg-white/[0.05]',
                                )}
                            >
                                {option}
                            </button>
                        ))}
                    </div>

                    <div className="rounded-xl border border-white/10 bg-slate-950/45 overflow-hidden">
                        <div className="grid grid-cols-[1.3fr_0.6fr_0.5fr] border-b border-white/10 px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                            <span>Strategy</span>
                            <span>Family</span>
                            <span>Mode</span>
                        </div>
                        {catalogLoading ? (
                            <div className="flex items-center justify-center gap-2 px-4 py-10 text-sm text-slate-400">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Loading catalog…
                            </div>
                        ) : filteredCatalog.length === 0 ? (
                            <div className="px-4 py-10 text-sm text-slate-500">No strategies available for this filter.</div>
                        ) : (
                            <div className="max-h-[360px] overflow-y-auto">
                                {filteredCatalog.map((strategy) => (
                                    <button
                                        key={strategy.strategy_id}
                                        onClick={() => setSelectedStrategyId(strategy.strategy_id)}
                                        className={clsx(
                                            'grid w-full grid-cols-[1.3fr_0.6fr_0.5fr] gap-3 border-b border-white/5 px-4 py-3 text-left transition hover:bg-white/[0.04]',
                                            selectedStrategyId === strategy.strategy_id && 'bg-emerald-500/[0.08]',
                                        )}
                                    >
                                        <div>
                                            <div className="text-sm font-semibold text-slate-100">{strategy.display_name}</div>
                                            <div className="mt-1 text-xs text-slate-400">{strategy.summary}</div>
                                        </div>
                                        <div className="text-xs text-slate-300">{strategy.family}</div>
                                        <div className="text-xs text-slate-400">{strategy.warning_only ? 'Warning' : 'Tradable'}</div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="space-y-4 rounded-xl border border-white/10 bg-slate-950/45 p-4">
                    <div>
                        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Selected Strategy</div>
                        <div className="mt-2 text-base font-semibold text-slate-100">
                            {selectedStrategy?.display_name ?? 'Choose a strategy'}
                        </div>
                        <div className="mt-1 text-sm text-slate-400">{selectedStrategy?.summary ?? 'The selected strategy details will appear here.'}</div>
                    </div>

                    <div className="grid gap-3 md:grid-cols-2">
                        <label className="space-y-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                            <span>Ticker</span>
                            <input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none" />
                        </label>
                        <label className="space-y-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                            <span>Market</span>
                            <select value={market} onChange={(e) => setMarket(e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none">
                                <option value="EGX30">EGX30</option>
                                <option value="EGX70">EGX70</option>
                                <option value="EGX100">EGX100</option>
                                <option value="ALL">ALL</option>
                            </select>
                        </label>
                        <label className="space-y-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                            <span>Date From</span>
                            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none" />
                        </label>
                        <label className="space-y-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                            <span>Date To</span>
                            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none" />
                        </label>
                        <label className="space-y-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                            <span>Capital</span>
                            <input type="number" value={capital} onChange={(e) => setCapital(Number(e.target.value) || 0)} className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none" />
                        </label>
                        <label className="space-y-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                            <span>Profile Name</span>
                            <input value={profileName} onChange={(e) => setProfileName(e.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none" />
                        </label>
                    </div>

                    <div className="grid gap-3 md:grid-cols-2">
                        <button onClick={onEvaluate} disabled={!selectedStrategy || busyAction !== null} className="inline-flex items-center justify-center gap-2 rounded-lg bg-sky-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:opacity-50">
                            {busyAction === 'evaluate' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Activity className="h-4 w-4" />}
                            Evaluate
                        </button>
                        <button onClick={onBacktest} disabled={!selectedStrategy || busyAction !== null || selectedStrategy?.warning_only} className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-50">
                            {busyAction === 'backtest' ? <Loader2 className="h-4 w-4 animate-spin" /> : <BarChart3 className="h-4 w-4" />}
                            Backtest
                        </button>
                        <button onClick={onPromote} disabled={!selectedStrategy || busyAction !== null || selectedStrategy?.warning_only} className="inline-flex items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-violet-500 disabled:opacity-50">
                            {busyAction === 'promote' ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
                            Promote
                        </button>
                        <button onClick={onActivate} disabled={!promotedProfile?.profile_id || busyAction !== null} className="inline-flex items-center justify-center gap-2 rounded-lg bg-amber-500 px-4 py-3 text-sm font-semibold text-black transition hover:bg-amber-400 disabled:opacity-50">
                            {busyAction === 'activate' ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                            Activate
                        </button>
                    </div>
                </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
                <div className="rounded-xl border border-white/10 bg-slate-950/45 p-4">
                    <div className="flex items-center gap-2 text-slate-100">
                        <Activity className="h-4 w-4 text-sky-300" />
                        <h4 className="text-sm font-semibold">Signal Preview</h4>
                    </div>
                    <div className="mt-4 space-y-3">
                        {signals.length === 0 ? (
                            <div className="text-sm text-slate-500">Run Evaluate to preview structured signals and warnings.</div>
                        ) : signals.map((signal) => (
                            <div key={`${signal.strategy_id}-${signal.ticker}-${signal.signal_type}`} className="rounded-lg border border-white/10 bg-slate-950/60 p-4">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <div className="text-sm font-semibold text-slate-100">{signal.setup_name}</div>
                                        <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">{signal.signal_type}</div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="text-sm font-semibold text-emerald-300">{signal.score.toFixed(0)}</div>
                                        {signal.score >= 80 && (
                                            <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 tracking-wider">
                                                HIGH CONFIDENCE ⚡
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <p className="mt-3 text-sm text-slate-300">{signal.explanation}</p>
                                <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-slate-400">
                                    <div>Entry: <span className="text-slate-200">{formatMoney(signal.entry_price ?? undefined)}</span></div>
                                    <div>Stop: <span className="text-slate-200">{formatMoney(signal.stop_loss ?? undefined)}</span></div>
                                    <div>Target: <span className="text-slate-200">{formatMoney(signal.target_1 ?? undefined)}</span></div>
                                </div>
                                {signal.warnings.length > 0 && (
                                    <div className="mt-3 flex items-start gap-2 rounded-lg border border-amber-400/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
                                        <ShieldAlert className="mt-0.5 h-4 w-4" />
                                        <span>{signal.warnings.join(', ')}</span>
                                    </div>
                                )}
                                {signal.avoidance_flags.length > 0 && (
                                    <div className="mt-2 flex items-start gap-2 rounded-lg border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-xs text-rose-100">
                                        <BadgeAlert className="mt-0.5 h-4 w-4" />
                                        <span>{signal.avoidance_flags.join(', ')}</span>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                <div className="rounded-xl border border-white/10 bg-slate-950/45 p-4">
                    <div className="flex items-center gap-2 text-slate-100">
                        <BarChart3 className="h-4 w-4 text-emerald-300" />
                        <h4 className="text-sm font-semibold">Backtest & Promotion</h4>
                    </div>
                    {!backtestResult ? (
                        <div className="mt-4 text-sm text-slate-500">Run Backtest to inspect trade count, drawdown, readiness, and promotion gates.</div>
                    ) : (
                        <div className="mt-4 space-y-4">
                            <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
                                <div className="rounded-lg border border-white/10 bg-slate-950/60 p-3">
                                    <div className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Return</div>
                                    <div className="mt-2 text-lg font-semibold text-emerald-300">{formatPct(backtestResult.metrics.total_return)}</div>
                                </div>
                                <div className="rounded-lg border border-white/10 bg-slate-950/60 p-3">
                                    <div className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Trades</div>
                                    <div className="mt-2 text-lg font-semibold text-slate-100">{backtestResult.metrics.trade_count}</div>
                                </div>
                                <div className="rounded-lg border border-white/10 bg-slate-950/60 p-3">
                                    <div className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Drawdown</div>
                                    <div className="mt-2 text-lg font-semibold text-amber-200">{formatPct(backtestResult.metrics.max_drawdown)}</div>
                                </div>
                                <div className="rounded-lg border border-white/10 bg-slate-950/60 p-3">
                                    <div className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Profit Factor</div>
                                    <div className="mt-2 text-lg font-semibold text-slate-100">{backtestResult.metrics.profit_factor.toFixed(2)}</div>
                                </div>
                                <div className="rounded-lg border border-white/10 bg-slate-950/60 p-3">
                                    <div className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Expectancy</div>
                                    <div className="mt-2 text-lg font-semibold text-slate-100">{formatMoney(backtestResult.metrics.expectancy)}</div>
                                </div>
                                <div className="rounded-lg border border-white/10 bg-slate-950/60 p-3">
                                    <div className="text-[11px] uppercase tracking-[0.16em] text-slate-500">State</div>
                                    <div className="mt-2 text-lg font-semibold text-slate-100">{backtestResult.promotion_summary.profile_state}</div>
                                </div>
                            </div>

                            <div className="rounded-lg border border-white/10 bg-slate-950/60 p-4">
                                <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Promotion Gates</div>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {backtestResult.promotion_summary.failed_gates.length === 0 ? (
                                        <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-100">
                                            All gates passed
                                            <span className="ml-2 text-[9px] font-black tracking-wider border border-emerald-400/30 bg-emerald-500/15 rounded px-1.5 py-0.5">PASSED ⚡</span>
                                        </span>
                                    ) : backtestResult.promotion_summary.failed_gates.map((gate) => (
                                        <span key={gate} className="rounded-full border border-rose-400/20 bg-rose-500/10 px-3 py-1 text-xs text-rose-100">{gate}</span>
                                    ))}
                                </div>
                            </div>

                            {promotedProfile && (
                                <div className="rounded-lg border border-white/10 bg-slate-950/60 p-4">
                                    <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Promoted Profile</div>
                                    <div className="mt-2 text-sm font-semibold text-slate-100">{promotedProfile.profile_name}</div>
                                    <div className="mt-1 text-sm text-slate-400">
                                        {promotedProfile.source_type} · {promotedProfile.profile_state} · {promotedProfile.market}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}
