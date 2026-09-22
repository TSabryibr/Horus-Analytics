'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { apiFetch, readJsonSafe, isIgnorableNetworkError } from '@/lib/api';
import { useLanguage } from '@/context/LanguageContext';
import { ReconciledTrade, SignalStateArchive } from '@/types/domain';
import clsx from 'clsx';
import { CommandHeader } from '@/app/components/custom/CommandHeader';
import { History, Search, ArrowUpDown, ChevronRight, X, AlertTriangle, CheckCircle2, ShieldCheck, TrendingDown, RefreshCw, Activity } from 'lucide-react';
import { formatTimeSince, getPollingStatus, isStale } from '@/utils/telemetry';

export default function ExecutionQualityPage() {
    const { t, isRtl } = useLanguage();
    const [trades, setTrades] = useState<ReconciledTrade[]>([]);
    const [averageSlippage, setAverageSlippage] = useState<number>(0);
    const [reconciledCount, setReconciledCount] = useState<number>(0);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [selectedSignalId, setSelectedSignalId] = useState<string | null>(null);
    const [snapshotDetail, setSnapshotDetail] = useState<SignalStateArchive | null>(null);
    const [loadingSnapshot, setLoadingSnapshot] = useState<boolean>(false);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    const loadReport = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await apiFetch('/api/v1/analytics/slippage-report?limit=100');
            if (!res.ok) {
                throw new Error(`Failed to load slippage report (HTTP ${res.status})`);
            }
            const data = await readJsonSafe<any>(res);
            setTrades(data.trades || []);
            setAverageSlippage(data.average_slippage_pct || 0);
            setReconciledCount(data.reconciled_trades_count || 0);
            setLastUpdated(new Date());
        } catch (e) {
            if (!isIgnorableNetworkError(e)) {
                setError(e instanceof Error ? e.message : 'An unknown error occurred');
            }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadReport();
    }, [loadReport]);

    const loadSnapshot = useCallback(async (signalId: string) => {
        setSelectedSignalId(signalId);
        setLoadingSnapshot(true);
        setSnapshotDetail(null);
        try {
            const res = await apiFetch(`/api/v1/analytics/signal-snapshots/${signalId}`);
            if (!res.ok) {
                throw new Error(`Failed to load signal snapshot (HTTP ${res.status})`);
            }
            const data = await readJsonSafe<SignalStateArchive>(res);
            setSnapshotDetail(data);
        } catch (e) {
            console.error('Error fetching snapshot', e);
        } finally {
            setLoadingSnapshot(false);
        }
    }, []);

    const filteredTrades = trades.filter((t) =>
        t.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.signal_id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="page-shell space-y-6">
            <CommandHeader
                eyebrow="Closed-Loop Verification"
                title={isRtl ? 'جودة التنفيذ والتدقيق' : 'Execution Quality & Audit'}
                description={
                    isRtl
                        ? 'تحليل انحراف الأسعار الفعلي عن الإشارات النظرية وحساب تدهور القيمة.'
                        : 'Closed-loop slippage analysis and post-entry decay tracking against signal snapshots.'
                }
                icon={<History className="h-7 w-7" />}
                iconClassName="border-rose-400/20 bg-rose-500/10 text-rose-200 shadow-[0_16px_34px_rgba(244,63,94,0.16)]"
                statusItems={[
                    getPollingStatus(loading, Boolean(error)),
                    { label: 'Sync', value: formatTimeSince(lastUpdated), tone: isStale(lastUpdated) ? 'warning' : 'muted' },
                    {
                        label: 'Avg Slippage',
                        value: `${averageSlippage > 0 ? '+' : ''}${averageSlippage.toFixed(2)}%`,
                        tone: averageSlippage > 0.5 ? 'danger' : 'success',
                    },
                    { label: 'Audits', value: `${reconciledCount}`, tone: 'primary' },
                ]}
                actions={
                    <button
                        onClick={() => void loadReport()}
                        disabled={loading}
                        className="flex items-center gap-2 rounded-[1rem] border border-white/10 bg-white/[0.04] px-4 py-2 text-[11px] font-black uppercase tracking-[0.24em] text-slate-300 transition hover:bg-white/[0.08]"
                    >
                        <RefreshCw className={clsx('h-3.5 w-3.5', loading && 'animate-spin')} />
                        {isRtl ? 'تحديث البيانات' : 'Refresh Metrics'}
                    </button>
                }
            />

            {/* Error state */}
            {error && (
                <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-200 flex items-start gap-3 shadow-md">
                    <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
                    <div>
                        <h4 className="font-semibold text-rose-300">{isRtl ? 'خطأ في النظام' : 'System Error'}</h4>
                        <p className="text-sm text-rose-400 mt-1">{error}</p>
                    </div>
                </div>
            )}

            {/* Metrics Overview */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Average Slippage */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 relative overflow-hidden group hover:border-slate-700 transition duration-300">
                    <div className="absolute right-4 top-4 opacity-10 group-hover:scale-110 transition duration-300">
                        <Activity className="h-16 w-16 text-rose-500" />
                    </div>
                    <p className="text-sm font-semibold tracking-wider text-slate-400 uppercase">
                        {isRtl ? 'متوسط انزلاق الأسعار الفعلي' : 'Average Execution Slippage'}
                    </p>
                    <div className="mt-3 flex items-baseline gap-2">
                        <span className={`text-4xl font-extrabold ${averageSlippage > 0.5 ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {averageSlippage > 0 ? '+' : ''}{averageSlippage.toFixed(2)}%
                        </span>
                        <span className="text-xs text-slate-500">
                            {isRtl ? 'معدل الانحراف الفعلي' : 'vs. Theoretical'}
                        </span>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
                        <span>
                            {averageSlippage > 0.5
                                ? (isRtl ? '⚠️ انحراف مرتفع - يقوم النظام بتشديد الفروق السعرية المسموحة.' : '⚠️ High slippage detected. Dynamic calibration is tightening spread limits.')
                                : (isRtl ? '✅ انحراف مقبول - ضمن معايير التنفيذ الممتاز.' : '✅ Optimal execution. Within standard liquidity parameters.')}
                        </span>
                        {averageSlippage <= 0.5 && (
                            <span className="ml-2 shrink-0 text-[9px] font-black tracking-wider border border-emerald-400/30 bg-emerald-500/15 text-emerald-300 rounded px-1.5 py-0.5">
                                CALIBRATED ⚡
                            </span>
                        )}
                    </div>
                </div>

                {/* Reconciled Count */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 relative overflow-hidden group hover:border-slate-700 transition duration-300">
                    <div className="absolute right-4 top-4 opacity-10 group-hover:scale-110 transition duration-300">
                        <ShieldCheck className="h-16 w-16 text-emerald-500" />
                    </div>
                    <p className="text-sm font-semibold tracking-wider text-slate-400 uppercase">
                        {isRtl ? 'الصفقات المدققة' : 'Reconciled Audits'}
                    </p>
                    <div className="mt-3 flex items-baseline gap-2">
                        <span className="text-4xl font-extrabold text-slate-100">
                            {reconciledCount}
                        </span>
                        <span className="text-xs text-slate-500">
                            {isRtl ? 'صفقات مكتملة' : 'closed trades'}
                        </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-2">
                        {isRtl
                            ? 'تمت مطابقتها بنجاح مع سجل إثبات الإشارة التاريخي.'
                            : 'Matching execution logs bound to historical signal snapshots.'}
                    </p>
                </div>

                {/* Calibration Status */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 relative overflow-hidden group hover:border-slate-700 transition duration-300">
                    <div className="absolute right-4 top-4 opacity-10 group-hover:scale-110 transition duration-300">
                        <CheckCircle2 className="h-16 w-16 text-amber-500" />
                    </div>
                    <p className="text-sm font-semibold tracking-wider text-slate-400 uppercase">
                        {isRtl ? 'حالة حارس السيولة' : 'Liquidity Guard Calibration'}
                    </p>
                    <div className="mt-3 flex items-baseline gap-2">
                        <span className="text-4xl font-extrabold text-amber-400">
                            {isRtl ? 'نشط' : 'Active'}
                        </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-2">
                        {isRtl
                            ? 'حارس السيولة يقوم بمعايرة حدود الدخول ديناميكياً بناءً على الانزلاق الفعلي.'
                            : 'Liquidity limits dynamically calibrated based on historical execution feeds.'}
                    </p>
                </div>
            </div>

            {/* Controls & Search */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                    <input
                        type="text"
                        placeholder={isRtl ? 'ابحث بالرمز أو بمعرف الإشارة...' : 'Filter by ticker or signal ID...'}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 focus:border-slate-700 focus:ring-0 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 transition duration-200 placeholder-slate-500"
                    />
                </div>
                <div className="text-xs text-slate-500 flex items-center gap-2">
                    <span>{isRtl ? 'عرض أحدث صفقات تمت مطابقتها' : 'Showing latest reconciled trade executions'}</span>
                </div>
            </div>

            {/* Reconciled Trades Table */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-800 bg-slate-900/60 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                <th className="py-4 px-6">{isRtl ? 'الرمز' : 'Ticker'}</th>
                                <th className="py-4 px-6">{isRtl ? 'سعر الدخول الفعلي / النظري' : 'Actual / Theoretical Entry'}</th>
                                <th className="py-4 px-6">{isRtl ? 'الانزلاق الفعلي' : 'Entry Slippage'}</th>
                                <th className="py-4 px-6">{isRtl ? 'سعر الخروج' : 'Actual Exit'}</th>
                                <th className="py-4 px-6">{isRtl ? 'تدهور القيمة بعد الدخول' : 'Post-Entry Decay'}</th>
                                <th className="py-4 px-6">{isRtl ? 'العائد الفعلي' : 'Realized PnL'}</th>
                                <th className="py-4 px-6 text-right">{isRtl ? 'التدقيق' : 'Audit'}</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 text-sm">
                            {loading ? (
                                <tr>
                                    <td colSpan={7} className="py-12 text-center text-slate-500">
                                        <div className="flex flex-col items-center justify-center gap-2">
                                            <div className="h-6 w-6 border-2 border-rose-500 border-t-transparent rounded-full animate-spin" />
                                            <span>{isRtl ? 'جارٍ تحميل البيانات...' : 'Loading audited logs...'}</span>
                                        </div>
                                    </td>
                                </tr>
                            ) : filteredTrades.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="py-12 text-center text-slate-500">
                                        {isRtl ? 'لا توجد صفقات مدققة مطابقة حالياً.' : 'No reconciled trades found.'}
                                    </td>
                                </tr>
                            ) : (
                                filteredTrades.map((t) => {
                                    const slippageColor = t.slippage_pct > 0.5 
                                        ? 'text-rose-400 bg-rose-950/40 border border-rose-900/60' 
                                        : t.slippage_pct <= 0 
                                            ? 'text-emerald-400 bg-emerald-950/40 border border-emerald-900/60'
                                            : 'text-amber-400 bg-amber-950/40 border border-amber-900/60';
                                    
                                    const decayColor = t.decay_pct < -2.0 ? 'text-rose-400' : 'text-slate-300';
                                    const pnlColor = t.actual_pnl_pct >= 0 ? 'text-emerald-400' : 'text-rose-400';

                                    return (
                                        <tr key={t.trade_id} className="hover:bg-slate-900/30 transition duration-150">
                                            <td className="py-4 px-6 font-bold text-slate-100 flex items-center gap-2">
                                                <span>{t.ticker}</span>
                                                <span className="text-[10px] px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded">
                                                    {t.currency}
                                                </span>
                                            </td>
                                            <td className="py-4 px-6 text-slate-300">
                                                <div className="font-semibold">{t.actual_entry.toFixed(2)}</div>
                                                <div className="text-xs text-slate-500">{isRtl ? 'نظري:' : 'theo:'} {t.theoretical_entry.toFixed(2)}</div>
                                            </td>
                                            <td className="py-4 px-6">
                                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${slippageColor}`}>
                                                    {t.slippage_pct > 0 ? '+' : ''}{t.slippage_pct.toFixed(2)}%
                                                </span>
                                            </td>
                                            <td className="py-4 px-6 font-medium text-slate-300">
                                                {t.actual_exit.toFixed(2)}
                                            </td>
                                            <td className={`py-4 px-6 font-semibold ${decayColor}`}>
                                                {t.decay_pct.toFixed(2)}%
                                            </td>
                                            <td className={`py-4 px-6 font-bold ${pnlColor}`}>
                                                {t.actual_pnl_pct >= 0 ? '+' : ''}{t.actual_pnl_pct.toFixed(2)}%
                                            </td>
                                            <td className="py-4 px-6 text-right">
                                                <button
                                                    onClick={() => void loadSnapshot(t.signal_id)}
                                                    className="px-3 py-1.5 bg-slate-800 border border-slate-700 hover:bg-slate-700 rounded text-xs font-medium text-slate-300 hover:text-slate-100 transition duration-150 flex items-center gap-1 inline-flex"
                                                >
                                                    {isRtl ? 'تفاصيل الإشارة' : 'Inspect Signal'}
                                                    <ChevronRight className="h-3 w-3" />
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Snapshot Detail Modal */}
            {selectedSignalId && (
                <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden shadow-2xl flex flex-col animate-in fade-in zoom-in duration-200">
                        {/* Modal Header */}
                        <div className="p-6 border-b border-slate-850 flex items-center justify-between bg-slate-900/80">
                            <div>
                                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                                    {isRtl ? 'تفاصيل حالة إثبات الإشارة' : 'Signal Provenance Audit'}
                                </h3>
                                <p className="text-xs text-slate-400 mt-0.5">
                                    ID: <span className="font-mono text-amber-400 select-all">{selectedSignalId}</span>
                                </p>
                            </div>
                            <button
                                onClick={() => setSelectedSignalId(null)}
                                className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition duration-150"
                            >
                                <X className="h-5 w-5" />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-sm text-slate-300">
                            {loadingSnapshot ? (
                                <div className="flex flex-col items-center justify-center py-16 gap-2">
                                    <div className="h-6 w-6 border-2 border-rose-500 border-t-transparent rounded-full animate-spin" />
                                    <span className="text-slate-500">{isRtl ? 'جارٍ جلب نسخة الإشارة...' : 'Retrieving snapshot database record...'}</span>
                                </div>
                            ) : snapshotDetail ? (
                                <>
                                    {/* Score & Status */}
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                                            <span className="text-xs text-slate-500 block">{isRtl ? 'التقييم الفني' : 'Signal Score'}</span>
                                            <span className="text-2xl font-black text-amber-400">{snapshotDetail.signal_score} / 10</span>
                                        </div>
                                        <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                                            <span className="text-xs text-slate-500 block">{isRtl ? 'تاريخ التوليد' : 'Archived Timestamp'}</span>
                                            <span className="text-sm font-semibold text-slate-200">
                                                {snapshotDetail.timestamp ? new Date(snapshotDetail.timestamp).toLocaleString() : 'N/A'}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Execution Status / Invalidation Reason */}
                                    <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                                        <span className="text-xs text-slate-500 block">{isRtl ? 'الحالة النهائية للماسح' : 'Final Scanner Verdict'}</span>
                                        <span className="text-md font-bold text-slate-200 block mt-1">
                                            {snapshotDetail.final_status}
                                        </span>
                                        {snapshotDetail.kill_reason && (
                                            <div className="mt-3 p-2 bg-rose-950/20 border border-rose-900/60 rounded text-rose-300 text-xs flex items-center gap-2">
                                                <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
                                                <span>
                                                    <strong>{isRtl ? 'سبب الإلغاء:' : 'Kill Reason:'}</strong> {snapshotDetail.kill_reason}
                                                </span>
                                            </div>
                                        )}
                                    </div>

                                    {/* Parameters snapshot details */}
                                    <div>
                                        <h4 className="font-semibold text-slate-400 uppercase tracking-wider text-xs mb-3">
                                            {isRtl ? 'المعطيات اللحظية للتنفيذ' : 'Market Metrics Snapshot'}
                                        </h4>
                                        <div className="bg-slate-950 border border-slate-800 rounded-xl divide-y divide-slate-850 overflow-hidden font-mono text-xs">
                                            {Object.entries(snapshotDetail.filter_snapshot_json ? JSON.parse(snapshotDetail.filter_snapshot_json) : {}).map(([key, val]) => {
                                                let displayVal = String(val);
                                                if (typeof val === 'number') {
                                                    displayVal = val.toFixed(4);
                                                }
                                                return (
                                                    <div key={key} className="flex justify-between p-3 hover:bg-slate-900/20">
                                                        <span className="text-slate-500">{key}</span>
                                                        <span className="text-slate-300 font-semibold">{displayVal}</span>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="text-center py-8 text-slate-500">
                                    {isRtl ? 'فشل تحميل تفاصيل الإشارة.' : 'Failed to display signal snapshot.'}
                                </div>
                            )}
                        </div>

                        {/* Modal Footer */}
                        <div className="p-4 border-t border-slate-850 bg-slate-900/80 flex justify-end">
                            <button
                                onClick={() => setSelectedSignalId(null)}
                                className="px-4 py-2 bg-slate-800 border border-slate-700 hover:bg-slate-700 rounded-lg text-sm font-medium transition duration-150"
                            >
                                {isRtl ? 'إغلاق' : 'Close'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
