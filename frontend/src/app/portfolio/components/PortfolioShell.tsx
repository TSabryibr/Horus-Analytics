'use client';

import React from 'react';
import Link from 'next/link';
import {
    Activity,
    Coins,
    DollarSign,
    Download,
    FileText,
    HardDrive,
    Plus,
    RefreshCw,
    Scale,
    Shield,
    TrendingUp,
    Upload,
    Radio,
} from 'lucide-react';
import clsx from 'clsx';

import { PortfolioTable, PriceTick } from '@/components/PortfolioTable';
import { CommandHeader } from '@/app/components/custom/CommandHeader';
import { CommandToolbar } from '@/app/components/custom/CommandToolbar';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';
import dynamic from 'next/dynamic';
import { PortfolioHealth, Position } from '@/types';

const PortfolioReportSection = dynamic(
    () => import('./PortfolioReportSection'),
    { ssr: false, loading: () => <div className="flex h-[400px] items-center justify-center bg-slate-950/50 rounded-xl border border-white/5 text-slate-500">Loading Portfolio Report...</div> }
);
import { HoardData, PortfolioAnalysisReport, PortfolioReportBundle, CurrencyMode, FeeMode } from '../hooks/usePortfolioRuntime';
import { SystemComparisonResult, SystemPerformance, ExecutionHistoryItem } from '../hooks/useSystemPerformance';
import { SystemComparisonSection } from './SystemComparisonSection';
import { PortfolioAnalyticsDeck } from './PortfolioAnalyticsDeck';

type UiMessage = { type: 'error' | 'success'; text: string } | null;

interface PortfolioShellProps {
    hoard: HoardData | null;
    health: PortfolioHealth | null;
    analysis: PortfolioAnalysisReport | null;
    report: PortfolioReportBundle | null;
    systemPerformance?: SystemPerformance | null;
    systemComparison?: SystemComparisonResult | null;
    executionHistory?: ExecutionHistoryItem[];
    loading: boolean;
    uiMessage: UiMessage;
    importLoading: boolean;
    activePortfolioId: number | null;
    isSystemPortfolio?: boolean;
    importFileInputRef: React.RefObject<HTMLInputElement | null>;
    reportingSectionRef: React.RefObject<HTMLDivElement | null>;
    currencyMode?: CurrencyMode;
    setCurrencyMode?: (mode: CurrencyMode) => void;
    feeMode?: FeeMode;
    setFeeMode?: (mode: FeeMode) => void;
    usdRate?: number;
    displayNetWorth?: number;
    displayFloatingPnl?: number;
    displaySettledPnl?: number;
    floatingFees?: number;
    settledFees?: number;
    livePrices?: Record<string, PriceTick>;
    wsConnected?: boolean;
    onImportCsv: React.ChangeEventHandler<HTMLInputElement>;
    onRefresh: () => void | Promise<void>;
    onExport: () => void;
    onExportExcel?: () => void;
    onDownloadTemplate?: (format?: 'xlsx' | 'csv') => void;
    onTriggerImportPicker: () => void;
    onOpenGenesis: () => void;
    onUpdateBalances: () => void;
    onOpenAddPosition: () => void;
    onOpenManagement: () => void | Promise<void>;
    onOpenAnalysis: () => void;
    onOpenRebalance?: () => void;
    onBatchMoveBreakeven?: (tickers: string[]) => void;
    onBatchScaleOut50?: (tickers: string[]) => void;
    onBatchFlatten?: (tickers: string[]) => void;
    onEditPosition: (position: Position) => void;
    onClosePosition: (ticker: string) => void;
    onReplicatePortfolio?: (sourcePortfolioId: number) => Promise<void> | void;
    genesisModal?: React.ReactNode;
    traps?: { bull_traps?: any[]; bear_traps?: any[] } | null;
}

export function PortfolioShell({
    hoard,
    health,
    analysis,
    report,
    systemPerformance,
    systemComparison,
    executionHistory,
    loading,
    uiMessage,
    importLoading,
    activePortfolioId,
    isSystemPortfolio = false,
    importFileInputRef,
    reportingSectionRef,
    currencyMode = 'EGP',
    setCurrencyMode,
    feeMode = 'GROSS',
    setFeeMode,
    usdRate = 50.0,
    displayNetWorth,
    displayFloatingPnl,
    displaySettledPnl,
    floatingFees = 0,
    settledFees = 0,
    livePrices = {},
    wsConnected = false,
    onImportCsv,
    onRefresh,
    onExport,
    onExportExcel,
    onDownloadTemplate,
    onTriggerImportPicker,
    onOpenGenesis,
    onUpdateBalances,
    onOpenAddPosition,
    onOpenManagement,
    onOpenAnalysis,
    onOpenRebalance,
    onBatchMoveBreakeven,
    onBatchScaleOut50,
    onBatchFlatten,
    onEditPosition,
    onClosePosition,
    onReplicatePortfolio,
    genesisModal,
    traps = null,
}: PortfolioShellProps) {
    const positions = hoard?.positions;
    const bullTraps = traps?.bull_traps;
    const bullTrapAlerts = React.useMemo(() => {
        if (!positions || !bullTraps || bullTraps.length === 0) return [];
        const heldTickers = new Set(positions.map((p) => String(p.ticker || '').toUpperCase()));
        return bullTraps.filter((bt: any) => heldTickers.has(String(bt.Ticker || '').toUpperCase()));
    }, [positions, bullTraps]);

    if (!hoard) {
        return (
            <div className="page-shell page-shell-wide">
                <CommandHeader
                    eyebrow="Portfolio Desk"
                    title="Portfolio Setup Required"
                    description="This portfolio has no starting cash or holdings yet. Add balances or import a known book before using live portfolio telemetry."
                    icon={<HardDrive className="h-7 w-7" />}
                    iconClassName="border-amber-400/25 bg-amber-500/12 text-amber-200 shadow-[0_16px_34px_rgba(245,158,11,0.18)]"
                    statusItems={[
                        { label: 'State', value: 'Uninitialized', tone: 'warning' },
                        { label: 'Mode', value: 'Capital Setup', tone: 'muted' },
                    ]}
                />

                {uiMessage && (
                    <div
                        className={clsx(
                            'command-chip w-fit rounded-[999px]',
                            uiMessage.type === 'error' ? 'command-chip-danger' : 'command-chip-success'
                        )}
                    >
                        <span>{uiMessage.type === 'error' ? 'Alert' : 'Ready'}</span>
                        <span>{uiMessage.text}</span>
                    </div>
                )}

                <section className="section-surface industrial-corner overflow-hidden rounded-[1.6rem] p-6 sm:p-8">
                    <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-amber-400/55 via-amber-200/10 to-transparent" />
                    <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-center">
                        <div className="flex min-w-0 items-start gap-5">
                            <div className="flex size-18 shrink-0 items-center justify-center rounded-[1.5rem] border border-amber-400/20 bg-[radial-gradient(circle_at_top,rgba(251,191,36,0.26),rgba(120,53,15,0.18))] shadow-[0_24px_60px_rgba(245,158,11,0.16)]">
                                <HardDrive className="h-9 w-9 text-amber-200" />
                            </div>
                            <div className="min-w-0 space-y-3">
                                <div className="meta-label text-amber-200/70">Reserve Authority</div>
                                <div className="space-y-2">
                                    <h2 className="heading-title text-3xl font-black tracking-[-0.04em] text-white sm:text-4xl">
                                        Treasury Bootstrap
                                    </h2>
                                    <p className="max-w-2xl text-sm leading-6 text-slate-300 sm:text-[15px]">
                                        Initialize starting cash and holdings, or import a filled subscriber template (.xlsx / .csv) to connect this portfolio to the live command system.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="flex w-full flex-col gap-3 xl:w-[18rem]">
                            <input
                                ref={importFileInputRef}
                                type="file"
                                accept=".xlsx,.xls,.csv,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                data-testid="csv-import-input"
                                className="hidden"
                                onChange={onImportCsv}
                            />
                            <button
                                onClick={onOpenGenesis}
                                className="rounded-[1rem] border border-amber-300/35 bg-[linear-gradient(135deg,rgba(245,158,11,0.92),rgba(251,191,36,0.76))] px-5 py-3 text-[11px] font-black uppercase tracking-[0.28em] text-slate-950 transition hover:brightness-105"
                            >
                                Initialize Treasury
                            </button>
                            <button
                                onClick={onTriggerImportPicker}
                                className="rounded-[1rem] border border-cyan-400/30 bg-cyan-500/10 px-5 py-3 text-[11px] font-black uppercase tracking-[0.24em] text-cyan-200 transition hover:border-cyan-400/50 hover:bg-cyan-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
                                disabled={importLoading}
                            >
                                {importLoading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5 text-cyan-400" />}
                                {importLoading ? 'Importing File...' : 'Import Subscriber File (.xlsx / .csv)'}
                            </button>
                            {onDownloadTemplate && (
                                <button
                                    onClick={() => onDownloadTemplate('xlsx')}
                                    className="rounded-[1rem] border border-emerald-500/30 bg-emerald-500/10 px-5 py-2.5 text-[11px] font-black uppercase tracking-[0.24em] text-emerald-300 transition hover:border-emerald-400/50 hover:bg-emerald-500/20 flex items-center justify-center gap-2"
                                >
                                    <Download className="h-3.5 w-3.5 text-emerald-400" /> Download Template (.xlsx)
                                </button>
                            )}
                            <button
                                onClick={() => {
                                    void onRefresh();
                                }}
                                className="rounded-[1rem] border border-white/10 bg-white/[0.04] px-5 py-2.5 text-[11px] font-black uppercase tracking-[0.24em] text-slate-300 transition hover:border-white/20 hover:text-white"
                            >
                                Refresh Telemetry
                            </button>
                        </div>
                    </div>
                </section>

                {genesisModal}
            </div>
        );
    }

    const currUnit = currencyMode;
    const finalNetWorth = displayNetWorth !== undefined ? displayNetWorth : hoard.net_worth_egp;
    const finalFloatingPnl = displayFloatingPnl !== undefined ? displayFloatingPnl : (hoard.positions ? hoard.positions.reduce((acc, pos) => acc + (pos.pnl || 0), 0) : 0);
    const finalSettledPnl = displaySettledPnl !== undefined ? displaySettledPnl : (report?.metrics?.total_pnl ?? 0);

    return (
        <div className="page-shell page-shell-wide">
            <CommandHeader
                eyebrow="Portfolio Desk"
                title="Portfolio Manager"
                description={
                    isSystemPortfolio 
                        ? "Algorithmic System Fleet benchmark telemetry (Read-Only Simulation). Replicate to personal book to execute trades." 
                        : "Institutional command suite with real-time telemetry, FX switching, rebalancing desk, and stress testing."
                }
                icon={<Coins className="h-7 w-7" />}
                iconClassName={clsx(
                    "shadow-[0_16px_34px_rgba(245,158,11,0.15)]",
                    isSystemPortfolio ? "border-purple-400/20 bg-purple-500/10 text-purple-200" : "border-amber-400/20 bg-amber-500/10 text-amber-200"
                )}
                statusItems={[
                    { label: 'Route', value: 'Portfolio Live', tone: 'primary' },
                    { 
                        label: isSystemPortfolio ? 'Book Class' : 'Portfolio', 
                        value: isSystemPortfolio ? 'System Fleet' : (activePortfolioId !== null ? `#${activePortfolioId}` : 'Unbound'), 
                        tone: isSystemPortfolio ? 'warning' : (activePortfolioId !== null ? 'success' : 'warning') 
                    },
                    { 
                        label: isSystemPortfolio ? 'Mode' : 'Telemetry', 
                        value: isSystemPortfolio ? 'Simulation Benchmark' : (wsConnected ? 'Live Feed' : 'Connected'), 
                        tone: 'success' 
                    },
                ]}
            />

            <CommandToolbar
                label="Command Actions"
                description="Execute portfolio operations, export multi-sheet audit sheets, intake subscriber books, and manage positions."
            >
                <input
                    ref={importFileInputRef}
                    type="file"
                    accept=".xlsx,.xls,.csv,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    data-testid="csv-import-input"
                    className="hidden"
                    onChange={onImportCsv}
                />

                {/* 1. Multi-Currency & Fee Toggles */}
                {setCurrencyMode && (
                    <div className="flex items-center bg-slate-900 border border-slate-700/80 rounded-xl p-1 shadow-sm">
                        <button
                            type="button"
                            onClick={() => setCurrencyMode('EGP')}
                            className={clsx(
                                "px-2.5 py-1 text-xs font-mono font-bold rounded-lg transition-all",
                                currencyMode === 'EGP' ? "bg-cyan-500 text-slate-950 shadow-sm" : "text-slate-400 hover:text-slate-200"
                            )}
                        >
                            EGP
                        </button>
                        <button
                            type="button"
                            onClick={() => setCurrencyMode('USD')}
                            className={clsx(
                                "px-2.5 py-1 text-xs font-mono font-bold rounded-lg transition-all",
                                currencyMode === 'USD' ? "bg-cyan-500 text-slate-950 shadow-sm" : "text-slate-400 hover:text-slate-200"
                            )}
                            title={`Parallel USD/EGP: ${usdRate.toFixed(2)}`}
                        >
                            USD
                        </button>
                    </div>
                )}

                {setFeeMode && (
                    <div className="flex items-center bg-slate-900 border border-slate-700/80 rounded-xl p-1 shadow-sm">
                        <button
                            type="button"
                            onClick={() => setFeeMode('GROSS')}
                            className={clsx(
                                "px-2.5 py-1 text-xs font-mono font-bold rounded-lg transition-all",
                                feeMode === 'GROSS' ? "bg-slate-700 text-slate-100 shadow-sm" : "text-slate-400 hover:text-slate-200"
                            )}
                        >
                            Gross
                        </button>
                        <button
                            type="button"
                            onClick={() => setFeeMode('NET')}
                            className={clsx(
                                "px-2.5 py-1 text-xs font-mono font-bold rounded-lg transition-all",
                                feeMode === 'NET' ? "bg-amber-500 text-slate-950 shadow-sm" : "text-slate-400 hover:text-slate-200"
                            )}
                            title="Deducts EGX brokerage, clearing, FRA, and stamp duty (0.30% round-trip)"
                        >
                            Net PnL
                        </button>
                    </div>
                )}

                <div className="h-8 w-px bg-white/10 hidden sm:block" />

                {/* 2. Trading Desk */}
                {onOpenRebalance && (
                    <IndustrialButton
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={onOpenRebalance}
                        className="text-cyan-300 hover:border-cyan-400/50"
                        title="Open Institutional Rebalancing Desk"
                    >
                        <Scale className="h-3.5 w-3.5 text-cyan-400" /> Rebalance Desk
                    </IndustrialButton>
                )}

                {isSystemPortfolio && onReplicatePortfolio && activePortfolioId ? (
                    <IndustrialButton
                        type="button"
                        variant="primary"
                        size="sm"
                        onClick={() => void onReplicatePortfolio(activePortfolioId)}
                        className="border-purple-400/40 bg-[linear-gradient(135deg,rgba(168,85,247,0.25),rgba(88,28,135,0.2))] text-purple-100 hover:border-purple-400/60 hover:bg-purple-500/30"
                        title="Replicate this System Fleet to your active user trading book"
                    >
                        <Radio className="h-3.5 w-3.5 text-purple-300" /> Replicate Fleet
                    </IndustrialButton>
                ) : (
                    <>
                        <IndustrialButton
                            type="button"
                            variant="primary"
                            size="sm"
                            onClick={onOpenAddPosition}
                            className="border-amber-400/40 bg-[linear-gradient(135deg,rgba(245,158,11,0.22),rgba(120,53,15,0.2))] text-amber-100 hover:border-amber-400/60 hover:bg-amber-500/25"
                        >
                            <Plus className="h-3.5 w-3.5 text-amber-300" /> Add Position
                        </IndustrialButton>

                        <IndustrialButton
                            type="button"
                            variant="secondary"
                            size="sm"
                            onClick={onUpdateBalances}
                        >
                            <DollarSign className="h-3.5 w-3.5 text-emerald-400" /> Update Balances
                        </IndustrialButton>
                    </>
                )}

                <div className="h-8 w-px bg-white/10 hidden sm:block" />

                {/* 3. Data & Export Hub */}
                {onExportExcel && (
                    <IndustrialButton
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={onExportExcel}
                        className="text-emerald-300 hover:border-emerald-500/50"
                        title="Download Multi-Sheet Excel audit report"
                    >
                        <Download className="h-3.5 w-3.5 text-emerald-400" /> Export Excel (.xlsx)
                    </IndustrialButton>
                )}

                <IndustrialButton
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={onExport}
                    disabled={importLoading}
                    title="Export CSV"
                >
                    <Download className="h-3.5 w-3.5" /> Export CSV
                </IndustrialButton>

                {!isSystemPortfolio && (
                    <IndustrialButton
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={onTriggerImportPicker}
                        disabled={importLoading}
                        title="Import Subscriber Template (.xlsx / .csv) or Horus Backup"
                    >
                        {importLoading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5 text-cyan-400" />}
                        Import File (.xlsx / .csv)
                    </IndustrialButton>
                )}

                <div className="h-8 w-px bg-white/10 hidden sm:block" />

                {/* 4. Advisory Services & Management */}
                {onDownloadTemplate && (
                    <IndustrialButton
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => onDownloadTemplate('xlsx')}
                        className="text-cyan-300 hover:border-cyan-500/50"
                        title="Download Subscriber Intake Excel template"
                    >
                        <FileText className="h-3.5 w-3.5 text-cyan-400" /> Subscriber Template
                    </IndustrialButton>
                )}

                <IndustrialButton
                    type="button"
                    variant="primary"
                    size="sm"
                    onClick={() => {
                        void onOpenManagement();
                    }}
                >
                    <FileText className="h-3.5 w-3.5" /> Management Service
                </IndustrialButton>

                <IndustrialButton
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => void onRefresh()}
                    disabled={loading}
                    className="size-9 px-0"
                    title="Refresh Telemetry"
                >
                    <RefreshCw className={clsx('h-3.5 w-3.5 text-gray-300', loading && 'animate-spin')} />
                </IndustrialButton>
            </CommandToolbar>

            {uiMessage && (
                <div
                    className={clsx(
                        'command-chip w-fit rounded-[999px]',
                        uiMessage.type === 'error' ? 'command-chip-danger' : 'command-chip-success'
                    )}
                >
                    <span>{uiMessage.type === 'error' ? 'Alert' : 'Ready'}</span>
                    <span>{uiMessage.text}</span>
                </div>
            )}

            {bullTrapAlerts.length > 0 && (
                <div className="section-surface industrial-corner border-rose-500/50 bg-rose-950/40 p-4 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border shadow-[0_0_20px_rgba(244,63,94,0.15)]">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400">
                            <Shield className="w-6 h-6" />
                        </div>
                        <div>
                            <h4 className="text-sm font-bold text-rose-200 uppercase tracking-wider flex items-center gap-2">
                                🛡️ Defensive Shield Alert: Bull Trap on {bullTrapAlerts.map((a: any) => a.Ticker).join(', ')}
                            </h4>
                            <p className="text-xs text-rose-300/80 mt-0.5">
                                Resistance failure / upthrust detected on open portfolio position(s). Consider tightening stop-loss or scaling out.
                            </p>
                        </div>
                    </div>
                    <Link
                        href="/traps"
                        className="shrink-0 px-4 py-2 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-200 text-xs font-bold hover:bg-rose-500/30 transition uppercase tracking-wider"
                    >
                        Inspect Traps &rarr;
                    </Link>
                </div>
            )}

            {/* Council Verdict First Priority: Dual PnL Telemetry Card */}
            <div className="section-surface industrial-corner border-cyan-500/20 bg-slate-900/60 p-5 rounded-2xl">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-4 mb-4">
                    <div className="flex items-center gap-3">
                        <div>
                            <div className="text-xs font-semibold tracking-wider text-cyan-400 uppercase flex items-center gap-1.5">
                                <Radio size={12} className="text-cyan-400 animate-pulse" />
                                Council Risk Telemetry ({currencyMode})
                            </div>
                            <h3 className="text-lg font-bold text-white">Mark-to-Market vs. Settled PnL</h3>
                        </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyan-400"></span> Floating = Open Positions</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400"></span> Settled = Closed Trades</span>
                        {feeMode === 'NET' && (
                            <span className="text-amber-400 font-mono text-[11px] bg-amber-950/40 px-2 py-0.5 rounded border border-amber-500/30">
                                Friction: -{(floatingFees + settledFees).toFixed(2)} EGP
                            </span>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
                        <div className="text-slate-400 text-xs font-medium mb-1 flex justify-between">
                            <span>Floating MTM PnL ({hoard.positions ? hoard.positions.length : 0} Open Positions)</span>
                            {feeMode === 'NET' && <span className="text-amber-400 text-[10px] font-mono font-bold">NET</span>}
                        </div>
                        <div className={clsx("text-2xl font-black font-mono", finalFloatingPnl >= 0 ? "text-emerald-400" : "text-rose-400")}>
                            {finalFloatingPnl >= 0 ? '+' : ''}
                            {finalFloatingPnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} <span className="text-xs text-slate-500">{currUnit}</span>
                        </div>
                        <div className="text-[11px] text-slate-500 mt-1">Unrealized profit/loss across active holdings</div>
                    </div>

                    <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
                        <div className="text-slate-400 text-xs font-medium mb-1 flex justify-between">
                            <span>Settled Realized PnL ({report?.metrics?.total_trades ?? 0} Closed Trades)</span>
                            {feeMode === 'NET' && <span className="text-amber-400 text-[10px] font-mono font-bold">NET</span>}
                        </div>
                        <div className={clsx("text-2xl font-black font-mono", finalSettledPnl >= 0 ? "text-emerald-400" : "text-rose-400")}>
                            {finalSettledPnl >= 0 ? '+' : ''}
                            {finalSettledPnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} <span className="text-xs text-slate-500">{currUnit}</span>
                        </div>
                        <div className="text-[11px] text-slate-500 mt-1">Win Rate: {report?.metrics?.win_rate ?? 0}% | Fully closed trade performance</div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="section-surface industrial-corner border-amber-500/15 p-6 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
                        <TrendingUp className="w-12 h-12 text-amber-300" />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium mb-1">Total Net Worth</h3>
                    <div className="text-3xl font-bold text-white font-mono">
                        {finalNetWorth.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} <span className="text-xs text-slate-500">{currUnit}</span>
                    </div>
                    <div className="text-xs text-slate-400 mt-2 flex items-center justify-between">
                        <span>Cash Drag: <strong className="text-amber-300">{hoard.net_worth_egp > 0 ? Math.round((hoard.cash_egp / hoard.net_worth_egp) * 100) : 0}%</strong></span>
                        <span>Invested: <strong className="text-cyan-300">{hoard.net_worth_egp > 0 ? Math.max(0, 100 - Math.round((hoard.cash_egp / hoard.net_worth_egp) * 100)) : 0}%</strong></span>
                    </div>
                </div>

                <div className="section-surface industrial-corner p-6 group">
                    <h3 className="text-slate-400 text-sm font-medium mb-1 flex items-center">
                        <DollarSign className="w-4 h-4 mr-1 text-emerald-400" /> Buy Power (EGP)
                    </h3>
                    <div className="text-3xl font-bold text-white font-mono">{hoard.cash_egp.toLocaleString()}</div>
                    <div className="text-xs text-slate-500 mt-2">Free Margin (Available)</div>
                </div>

                <div className="section-surface industrial-corner p-6 group">
                    <h3 className="text-slate-400 text-sm font-medium mb-1 flex items-center">
                        <DollarSign className="w-4 h-4 mr-1 text-cyan-400" /> Buy Power (USD)
                    </h3>
                    <div className="text-3xl font-bold text-white font-mono">{hoard.cash_usd.toLocaleString()}</div>
                    <div className="text-xs text-slate-500 mt-2">Parallel Rate: {usdRate.toFixed(2)} EGP</div>
                </div>

                <button
                    type="button"
                    onClick={onOpenAnalysis}
                    className="section-surface industrial-corner p-6 group cursor-pointer hover:border-cyan-500/35 transition relative overflow-hidden text-left"
                >
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
                        <Shield className={clsx('w-12 h-12', analysis?.status === 'RISK' ? 'text-red-400' : 'text-cyan-300')} />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium mb-1 flex items-center">
                        <Activity className="w-4 h-4 mr-1 text-cyan-400" /> Risk Score
                    </h3>
                    <div
                        className={clsx(
                            'text-3xl font-bold font-mono',
                            analysis?.status === 'RISK'
                                ? 'text-red-400'
                                : analysis?.status === 'WARNING'
                                    ? 'text-amber-300'
                                    : 'text-emerald-300'
                        )}
                    >
                        {analysis ? analysis.health_score : '--'}
                        <span className="text-lg text-slate-500">/100</span>
                    </div>
                    <div className="text-xs text-slate-500 mt-2 flex items-center justify-between">
                        <span>Status: {analysis?.status || 'HEALTHY'}</span>
                        <span className="text-cyan-300 font-bold group-hover:underline">VIEW REPORT &rarr;</span>
                    </div>
                </button>
            </div>

            {/* Quantitative Risk & Asset Allocation Desk */}
            <PortfolioAnalyticsDeck
                hoard={hoard}
                report={report}
                usdRate={usdRate}
                currencyMode={currencyMode}
            />

            <PortfolioTable
                positions={hoard.positions}
                health={health}
                onEdit={onEditPosition}
                onClose={onClosePosition}
                livePrices={livePrices}
                feeMode={feeMode}
                currencyMode={currencyMode}
                usdRate={usdRate}
                onBatchMoveBreakeven={onBatchMoveBreakeven}
                onBatchScaleOut50={onBatchScaleOut50}
                onBatchFlatten={onBatchFlatten}
            />

            {activePortfolioId !== null && (
                <div id="reporting-section" ref={reportingSectionRef}>
                    <PortfolioReportSection
                        portfolioId={activePortfolioId}
                        report={report}
                        performance={systemPerformance}
                        executionHistory={executionHistory}
                        loading={loading}
                        compact
                        showPrint
                    />
                </div>
            )}

            <SystemComparisonSection 
                comparison={systemComparison || null} 
                loading={loading} 
                activePortfolioId={activePortfolioId} 
                onReplicatePortfolio={onReplicatePortfolio}
            />

            <Link
                href="/whales"
                className="section-surface industrial-corner mt-10 flex flex-col gap-4 border-cyan-500/15 bg-gradient-to-r from-cyan-950/40 to-slate-950/40 p-6 transition hover:border-cyan-500/35 cursor-pointer group sm:flex-row sm:items-center sm:justify-between"
            >
                <div className="flex min-w-0 items-start sm:items-center">
                    <div className="mr-4 rounded-[1rem] bg-cyan-500/15 p-3 transition group-hover:scale-110">
                        <Activity className="w-6 h-6 text-cyan-400" />
                    </div>
                    <div className="min-w-0">
                        <h4 className="text-lg font-bold text-white">Smart Money Tracking</h4>
                        <p className="text-sm text-slate-400">Scan for Whale Accumulation using OBV Divergence logic from the Smart Money Accumulation Engine.</p>
                    </div>
                </div>
                <div className="self-start rounded-[0.95rem] border border-cyan-400/25 bg-cyan-500/14 px-6 py-2 text-[10px] font-black uppercase tracking-[0.24em] text-cyan-100 transition group-hover:border-cyan-300/40 group-hover:bg-cyan-500/18 sm:self-auto">
                    Open Whisperer
                </div>
            </Link>
        </div>
    );
}
