'use client';

import { Download, FileText, Plus, RefreshCw, Scale, Send, Trash2, Upload, X } from 'lucide-react';
import clsx from 'clsx';
import React, { useRef } from 'react';

import { ManagedHoldingForm, ManagementReport } from '../hooks/usePortfolioManagement';

interface PortfolioManagementModalProps {
    open: boolean;
    managementLoading: boolean;
    managementMessage: string;
    managementReport: ManagementReport | null;
    managementSendResult: {
        status: string;
        chunks_total: number;
        chunks_sent: number;
        chunks_failed: number;
    } | null;
    managedHoldings: ManagedHoldingForm[];
    reportControls: {
        include_positions: string;
        chat_id: string;
        refresh_prices: boolean;
    };
    actionItemsPreviewLimit: number;
    onClose: () => void;
    onAddHolding: () => void;
    onRemoveHolding: (id: number) => void;
    onUpdateHolding: (id: number, field: keyof ManagedHoldingForm, value: string) => void;
    onClearRows: () => void;
    onRunIntake: () => void;
    onUploadFile?: (
        file: File,
        options?: {
            mode?: 'create_new' | 'sandbox' | 'overwrite';
            portfolioName?: string;
            cashEgp?: number;
            cashUsd?: number;
        }
    ) => void | Promise<void>;
    onDownloadTemplate?: (format?: 'xlsx' | 'csv') => void;
    onOpenRebalance?: () => void;
    onGenerateReport: () => void;
    onSendReport: () => void;
    onSetReportControls: (value: { include_positions: string; chat_id: string; refresh_prices: boolean }) => void;
    truncatePrice: (value: unknown, decimals?: number) => string;
}

export function PortfolioManagementModal({
    open,
    managementLoading,
    managementMessage,
    managementReport,
    managementSendResult,
    managedHoldings,
    reportControls,
    actionItemsPreviewLimit,
    onClose,
    onAddHolding,
    onRemoveHolding,
    onUpdateHolding,
    onClearRows,
    onRunIntake,
    onUploadFile,
    onDownloadTemplate,
    onOpenRebalance,
    onGenerateReport,
    onSendReport,
    onSetReportControls,
    truncatePrice,
}: PortfolioManagementModalProps) {
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const [intakeMode, setIntakeMode] = React.useState<'create_new' | 'sandbox' | 'overwrite'>('create_new');
    const [clientPortfolioName, setClientPortfolioName] = React.useState('');
    const [startingCashEgp, setStartingCashEgp] = React.useState('');
    const [isDragOver, setIsDragOver] = React.useState(false);

    if (!open) return null;

    const handleFileProcess = (file: File) => {
        if (!onUploadFile) return;
        const cashVal = Number(startingCashEgp.replace(/,/g, ''));
        void onUploadFile(file, {
            mode: intakeMode,
            portfolioName: clientPortfolioName.trim() || undefined,
            cashEgp: Number.isFinite(cashVal) && cashVal > 0 ? cashVal : undefined,
        });
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            handleFileProcess(file);
        }
        e.target.value = '';
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragOver(false);
        const file = e.dataTransfer.files?.[0];
        if (file) {
            handleFileProcess(file);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 z-[120] flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Portfolio management service">
            <div className="section-surface w-full max-w-6xl overflow-hidden rounded-[2rem] animate-in zoom-in-95 duration-200 max-h-[92vh] flex flex-col">
                <div className="p-8 border-b border-white/5 flex justify-between items-center bg-gradient-to-r from-blue-900/20 to-transparent flex-shrink-0">
                    <div>
                        <h3 className="text-xl font-black text-white uppercase tracking-tighter">Subscriber Portfolio Desk</h3>
                        <p className="text-xs text-gray-400 font-mono">EXCEL INTAKE • HEALTH DIAGNOSIS • MODEL REBALANCE • TELEGRAM DISPATCH</p>
                    </div>
                    <button type="button" onClick={onClose} aria-label="Close" className="text-gray-500 hover:text-white transition">
                        <X size={20} />
                    </button>
                </div>

                <div className="overflow-y-auto flex-1 p-8 space-y-8">
                    {managementMessage && (
                        <div
                            className={clsx(
                                'p-4 rounded-xl border text-sm',
                                managementMessage.toLowerCase().includes('failed') || managementMessage.toLowerCase().includes('error')
                                    ? 'bg-red-500/10 border-red-500/20 text-red-300'
                                    : managementMessage.toLowerCase().includes('partial') || managementMessage.toLowerCase().includes('blocked')
                                        ? 'bg-amber-500/10 border-amber-500/20 text-amber-200'
                                        : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200'
                            )}
                        >
                            {managementMessage}
                        </div>
                    )}

                    {/* Subscriber Ingestion Mode Bar & Dropzone */}
                    <div className="section-surface rounded-2xl p-6 border border-cyan-500/20 bg-[linear-gradient(135deg,rgba(6,182,212,0.05),rgba(15,23,42,0.6))] space-y-4">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/10 pb-4">
                            <div>
                                <h4 className="text-sm font-black text-cyan-200 uppercase tracking-widest flex items-center gap-2">
                                    <Upload size={16} className="text-cyan-400" /> 1. Subscriber File Ingestion
                                </h4>
                                <p className="text-xs text-gray-400 mt-0.5">
                                    Upload filled client Excel/CSV sheet. Select intake destination to protect or expand your books.
                                </p>
                            </div>
                            {onDownloadTemplate && (
                                <button
                                    type="button"
                                    onClick={() => onDownloadTemplate('xlsx')}
                                    className="action-secondary text-xs !text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/10 px-3.5 py-1.5 gap-1.5 self-start md:self-auto"
                                    title="Download guided subscriber Excel template"
                                >
                                    <Download size={13} className="text-emerald-400" /> Download Template (.xlsx)
                                </button>
                            )}
                        </div>

                        {/* Mode Switcher */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
                            <button
                                type="button"
                                onClick={() => setIntakeMode('create_new')}
                                className={clsx(
                                    'p-3.5 rounded-xl border text-left transition-all',
                                    intakeMode === 'create_new'
                                        ? 'border-cyan-400/60 bg-cyan-950/40 shadow-[0_0_15px_rgba(6,182,212,0.15)] text-white'
                                        : 'border-white/10 bg-white/[0.02] text-gray-400 hover:border-white/20'
                                )}
                            >
                                <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-cyan-300">
                                    <span className="size-2 rounded-full bg-cyan-400" /> Create New Client Book
                                </div>
                                <div className="text-[11px] text-gray-400 mt-1">
                                    Isolates client in a new portfolio under your Switcher.
                                </div>
                            </button>

                            <button
                                type="button"
                                onClick={() => setIntakeMode('sandbox')}
                                className={clsx(
                                    'p-3.5 rounded-xl border text-left transition-all',
                                    intakeMode === 'sandbox'
                                        ? 'border-amber-400/60 bg-amber-950/40 shadow-[0_0_15px_rgba(245,158,11,0.15)] text-white'
                                        : 'border-white/10 bg-white/[0.02] text-gray-400 hover:border-white/20'
                                )}
                            >
                                <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-amber-300">
                                    <span className="size-2 rounded-full bg-amber-400" /> Sandbox Audit (No Save)
                                </div>
                                <div className="text-[11px] text-gray-400 mt-1">
                                    Evaluate health & Telegram preview with zero database changes.
                                </div>
                            </button>

                            <button
                                type="button"
                                onClick={() => setIntakeMode('overwrite')}
                                className={clsx(
                                    'p-3.5 rounded-xl border text-left transition-all',
                                    intakeMode === 'overwrite'
                                        ? 'border-rose-400/60 bg-rose-950/40 shadow-[0_0_15px_rgba(244,63,94,0.15)] text-white'
                                        : 'border-white/10 bg-white/[0.02] text-gray-400 hover:border-white/20'
                                )}
                            >
                                <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-rose-300">
                                    <span className="size-2 rounded-full bg-rose-400" /> Overwrite Active Book
                                </div>
                                <div className="text-[11px] text-gray-400 mt-1">
                                    Replaces positions in currently selected portfolio.
                                </div>
                            </button>
                        </div>

                        {/* Optional Client Metadata when creating new book */}
                        {intakeMode === 'create_new' && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                                <div>
                                    <label className="block text-[10px] text-gray-400 font-bold uppercase tracking-wider mb-1">
                                        Client / Portfolio Name (Optional)
                                    </label>
                                    <input
                                        value={clientPortfolioName}
                                        onChange={(e) => setClientPortfolioName(e.target.value)}
                                        placeholder="e.g. Subscriber - Karim Mansour (or auto from file)"
                                        className="control-input w-full text-xs"
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] text-gray-400 font-bold uppercase tracking-wider mb-1">
                                        Starting Cash Reserve (EGP)
                                    </label>
                                    <input
                                        value={startingCashEgp}
                                        onChange={(e) => setStartingCashEgp(e.target.value)}
                                        placeholder="e.g. 50,000"
                                        className="control-input w-full text-xs"
                                    />
                                </div>
                            </div>
                        )}

                        {/* Drag and Drop Zone */}
                        <div
                            onDragOver={(e) => {
                                e.preventDefault();
                                setIsDragOver(true);
                            }}
                            onDragLeave={() => setIsDragOver(false)}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                            className={clsx(
                                'border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all',
                                isDragOver
                                    ? 'border-cyan-400 bg-cyan-500/10 scale-[1.01]'
                                    : 'border-white/15 bg-slate-950/40 hover:border-cyan-500/40 hover:bg-white/[0.02]'
                            )}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".xlsx,.xls,.csv"
                                className="hidden"
                                onChange={handleFileChange}
                            />
                            <Upload className="mx-auto mb-2 text-cyan-400" size={24} />
                            <div className="text-sm font-bold text-white">
                                {managementLoading ? 'Processing & Auditing Excel File...' : 'Drop Subscriber Excel (.xlsx / .csv) Here or Click to Browse'}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">
                                Auto-resolves EGX aliases &bull; Auto-calculates risk stop levels &bull; Pre-computes Kelly allocations
                            </div>
                        </div>
                    </div>

                    <div className="section-surface rounded-xl p-6 space-y-4">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-3">
                            <div>
                                <h4 className="text-sm font-black text-gray-300 uppercase tracking-widest">Manual Holdings Editor</h4>
                                <p className="text-xs text-gray-500">Fine-tune individual positions manually if needed.</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <button type="button" onClick={onAddHolding} className="action-secondary !text-yellow-500 px-3 py-1.5 text-xs gap-1 border-yellow-500/20">
                                    <Plus size={12} /> Add Holding
                                </button>
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs min-w-[960px]">
                                <thead>
                                    <tr className="text-gray-500 border-b border-white/10">
                                        <th className="py-2 px-2">Ticker</th>
                                        <th className="py-2 px-2">Shares</th>
                                        <th className="py-2 px-2">Entry Price</th>
                                        <th className="py-2 px-2">Total Cost</th>
                                        <th className="py-2 px-2">SL</th>
                                        <th className="py-2 px-2">TP1</th>
                                        <th className="py-2 px-2">TP2</th>
                                        <th className="py-2 px-2">Currency</th>
                                        <th className="py-2 px-2">Sector</th>
                                        <th className="py-2 px-2">Notes</th>
                                        <th className="py-2 px-2"></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {managedHoldings.map((row) => (
                                        <tr key={row.id} className="border-b border-white/5">
                                            <td className="py-2 px-2">
                                                <input value={row.ticker} onChange={(e) => onUpdateHolding(row.id, 'ticker', e.target.value.toUpperCase())} className="control-input w-20 px-2 py-1 text-white" placeholder="COMI" />
                                            </td>
                                            <td className="py-2 px-2">
                                                <input value={row.shares} onChange={(e) => onUpdateHolding(row.id, 'shares', e.target.value)} className="control-input w-20 px-2 py-1 text-white" placeholder="100" />
                                            </td>
                                            <td className="py-2 px-2">
                                                <input value={row.entry_price} onChange={(e) => onUpdateHolding(row.id, 'entry_price', e.target.value)} className="control-input w-24 px-2 py-1 text-white" placeholder="10.50" />
                                            </td>
                                            <td className="py-2 px-2">
                                                <input value={row.total_cost} onChange={(e) => onUpdateHolding(row.id, 'total_cost', e.target.value)} className="control-input w-24 px-2 py-1 text-white" placeholder="1050" />
                                            </td>
                                            <td className="py-2 px-2">
                                                <input value={row.stop_loss} onChange={(e) => onUpdateHolding(row.id, 'stop_loss', e.target.value)} className="control-input w-24 px-2 py-1 text-white" placeholder="9.80" />
                                            </td>
                                            <td className="py-2 px-2">
                                                <input value={row.target_price} onChange={(e) => onUpdateHolding(row.id, 'target_price', e.target.value)} className="control-input w-24 px-2 py-1 text-white" placeholder="11.20" />
                                            </td>
                                            <td className="py-2 px-2">
                                                <input value={row.target_price_2 || ''} onChange={(e) => onUpdateHolding(row.id, 'target_price_2', e.target.value)} className="control-input w-24 px-2 py-1 text-white" placeholder="12.00" />
                                            </td>
                                            <td className="py-2 px-2">
                                                <input value={row.currency} onChange={(e) => onUpdateHolding(row.id, 'currency', e.target.value.toUpperCase())} className="control-input w-16 px-2 py-1 text-white" placeholder="EGP" />
                                            </td>
                                            <td className="py-2 px-2">
                                                <input value={row.sector} onChange={(e) => onUpdateHolding(row.id, 'sector', e.target.value)} className="control-input w-24 px-2 py-1 text-white" placeholder="Banking" />
                                            </td>
                                            <td className="py-2 px-2">
                                                <input value={row.notes} onChange={(e) => onUpdateHolding(row.id, 'notes', e.target.value)} className="control-input w-44 px-2 py-1 text-white" placeholder="Client note" />
                                            </td>
                                            <td className="py-2 px-2 text-right">
                                                <button type="button" onClick={() => onRemoveHolding(row.id)} className="p-1 text-gray-500 hover:text-red-400">
                                                    <Trash2 size={14} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {managedHoldings.length === 0 && (
                                        <tr>
                                            <td colSpan={10} className="py-6 text-center text-gray-500 italic">
                                                No holdings added yet. Click &quot;Add Holding&quot;.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        <div className="flex gap-3">
                            <button type="button" onClick={onRunIntake} disabled={managementLoading} className="action-primary !bg-yellow-500 hover:!bg-yellow-400 !text-black disabled:opacity-50">
                                {managementLoading ? <RefreshCw className="animate-spin w-4 h-4" /> : 'Run Intake'}
                            </button>
                            <button type="button" onClick={onClearRows} className="action-secondary">
                                Clear Rows
                            </button>
                        </div>
                    </div>

                    <div className="section-surface rounded-xl p-6 space-y-4">
                        <h4 className="text-sm font-black text-gray-300 uppercase tracking-widest">2. Report & Delivery</h4>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                            <div>
                                <label className="block text-[10px] text-gray-500 mb-1 uppercase">Include Positions</label>
                                <input
                                    value={reportControls.include_positions}
                                    onChange={(e) => onSetReportControls({ ...reportControls, include_positions: e.target.value })}
                                    className="control-input w-full"
                                />
                            </div>
                            <div className="md:col-span-2">
                                <label className="block text-[10px] text-gray-500 mb-1 uppercase">Telegram Chat Override (Optional)</label>
                                <input
                                    value={reportControls.chat_id}
                                    onChange={(e) => onSetReportControls({ ...reportControls, chat_id: e.target.value })}
                                    className="control-input w-full"
                                    placeholder="-100xxxxxxxx"
                                />
                            </div>
                            <div className="flex items-end">
                                <label className="flex items-center gap-2 text-sm text-gray-300">
                                    <input
                                        type="checkbox"
                                        checked={reportControls.refresh_prices}
                                        onChange={(e) => onSetReportControls({ ...reportControls, refresh_prices: e.target.checked })}
                                        className="h-4 w-4 accent-blue-500"
                                    />
                                    Refresh Live Prices
                                </label>
                            </div>
                        </div>

                        <div className="flex flex-wrap gap-3">
                            <button type="button" onClick={onGenerateReport} disabled={managementLoading} className="action-primary !bg-blue-600 hover:!bg-blue-500 disabled:opacity-50 flex items-center gap-2">
                                <FileText size={16} /> Generate Report
                            </button>
                            <button type="button" onClick={onSendReport} disabled={managementLoading} className="action-primary !bg-emerald-600 hover:!bg-emerald-500 disabled:opacity-50 flex items-center gap-2">
                                <Send size={16} /> Send To Telegram
                            </button>
                        </div>

                        {managementSendResult && (
                            <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-200 text-sm">
                                Send status `{managementSendResult.status}` | sent `{managementSendResult.chunks_sent}` / `{managementSendResult.chunks_total}` | failed `{managementSendResult.chunks_failed}`
                            </div>
                        )}

                        {managementReport && (
                            <div className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                                    <div className="p-3 rounded-lg bg-black/20 border border-white/10">
                                        <div className="text-[10px] text-gray-500 uppercase">Open</div>
                                        <div className="text-lg font-bold">{managementReport.summary.open_positions}</div>
                                    </div>
                                    <div className="p-3 rounded-lg bg-black/20 border border-white/10">
                                        <div className="text-[10px] text-gray-500 uppercase">Unrealized PnL</div>
                                        <div className={clsx('text-lg font-bold', managementReport.summary.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-red-400')}>
                                            {managementReport.summary.unrealized_pnl.toFixed(2)}
                                        </div>
                                    </div>
                                    <div className="p-3 rounded-lg bg-black/20 border border-white/10">
                                        <div className="text-[10px] text-gray-500 uppercase">PnL %</div>
                                        <div className={clsx('text-lg font-bold', managementReport.summary.unrealized_pnl_pct >= 0 ? 'text-emerald-400' : 'text-red-400')}>
                                            {managementReport.summary.unrealized_pnl_pct.toFixed(2)}%
                                        </div>
                                    </div>
                                    <div className="p-3 rounded-lg bg-black/20 border border-white/10">
                                        <div className="text-[10px] text-gray-500 uppercase">Risk Score</div>
                                        <div className="text-lg font-bold">{managementReport.risk.health_score}</div>
                                    </div>
                                    <div className="p-3 rounded-lg bg-black/20 border border-white/10">
                                        <div className="text-[10px] text-gray-500 uppercase">Risk Heat</div>
                                        <div className="text-lg font-bold">{managementReport.risk.heat}%</div>
                                    </div>
                                </div>

                                <div className="p-4 rounded-xl border border-white/10 bg-black/20">
                                    <div className="flex justify-between items-center mb-2">
                                        <div className="flex items-center gap-3">
                                            <h5 className="text-sm font-bold text-white">Action Items</h5>
                                            {onOpenRebalance && (
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        onClose();
                                                        onOpenRebalance();
                                                    }}
                                                    className="text-[10px] font-bold text-cyan-300 bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 px-2.5 py-0.5 rounded-lg flex items-center gap-1 transition"
                                                    title="Open rebalancing desk to execute model allocations"
                                                >
                                                    <Scale size={11} className="text-cyan-400" /> Send to Rebalance Desk
                                                </button>
                                            )}
                                        </div>
                                        <span className="text-[10px] text-cyan-400 font-mono uppercase bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                                            Kelly Sizing Engine Active
                                        </span>
                                    </div>
                                    {!managementReport.action_items || managementReport.action_items.length === 0 ? (
                                        <p className="text-sm text-gray-400">No urgent action items. Hold and monitor.</p>
                                    ) : (
                                        <div className="space-y-2 max-h-48 overflow-y-auto">
                                            {managementReport.action_items.slice(0, Math.max(1, actionItemsPreviewLimit)).map((item, idx) => (
                                                <div key={`${item.ticker}-${idx}`} className="text-sm border border-white/10 rounded-lg p-2.5 bg-white/5 space-y-1">
                                                    <div className="flex justify-between items-center">
                                                        <div className="font-bold text-blue-300">{item.ticker} - {item.action}</div>
                                                        {item.kelly_pct !== undefined && item.kelly_pct > 0 && (
                                                            <div className="text-[11px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                                                                Kelly Rec: {item.recommended_shares} sh ({item.kelly_pct}%) | R:R {item.risk_reward_ratio}x
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="text-gray-300">
                                                        SL {item.stop_loss ? truncatePrice(item.stop_loss) : 'N/A'} | TP1 {item.target_price ? truncatePrice(item.target_price) : 'N/A'} | TP2 {item.target_price_2 ? truncatePrice(item.target_price_2) : 'N/A'}
                                                    </div>
                                                    <div className="text-gray-400 text-xs">{item.action_reason}</div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
