'use client';

import { RefreshCw, X } from 'lucide-react';

import { Position } from '@/types';
import { PortfolioFormData } from '../hooks/usePortfolioActions';

interface PortfolioPositionModalProps {
    mode: 'add' | 'update';
    actionLoading: boolean;
    formData: PortfolioFormData;
    position?: Position | null;
    onClose: () => void;
    onSubmit: (event: React.FormEvent) => void;
    onFieldChange: (field: keyof PortfolioFormData, value: string) => void;
}

export function PortfolioPositionModal({
    mode,
    actionLoading,
    formData,
    position,
    onClose,
    onSubmit,
    onFieldChange,
}: PortfolioPositionModalProps) {
    if (mode === 'update' && !position) return null;

    const isAdd = mode === 'add';

    return (
        <div
            className="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
            aria-label={isAdd ? 'Add position' : 'Update position'}
        >
            <div className="section-surface w-full max-w-md overflow-hidden rounded-[2rem] animate-in zoom-in-95 duration-200">
                <div className={`p-8 border-b border-white/5 flex justify-between items-center ${isAdd ? 'bg-gradient-to-r from-yellow-500/10 to-transparent' : 'bg-gradient-to-r from-cyan-500/10 to-transparent'}`}>
                    <div>
                        <h3 className="text-xl font-black text-white uppercase tracking-tighter">
                            {isAdd ? 'Forge New Position' : `Recalibrate ${position?.ticker}`}
                        </h3>
                        <p className="text-xs text-gray-500 font-mono">
                            {isAdd ? 'DRAUPNIR PROTOCOL MK-1' : 'RISK MITIGATION MODULE'}
                        </p>
                    </div>
                    <button type="button" onClick={onClose} aria-label="Close" className="text-gray-500 hover:text-white transition">
                        <X size={20} />
                    </button>
                </div>
                <form onSubmit={onSubmit} className="p-8 space-y-6">
                    {isAdd ? (
                        <div className="space-y-4">
                            <div>
                                <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2">Ticker Symbol</label>
                                <input
                                    required
                                    type="text"
                                    placeholder="e.g. COMI"
                                    className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-yellow-500/50"
                                    value={formData.ticker}
                                    onChange={(e) => onFieldChange('ticker', e.target.value)}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2">Shares</label>
                                    <input
                                        required
                                        type="number"
                                        placeholder="100"
                                        className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-yellow-500/50"
                                        value={formData.shares}
                                        onChange={(e) => onFieldChange('shares', e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2">Entry Price</label>
                                    <input
                                        required
                                        type="number"
                                        step="0.0001"
                                        placeholder="0.0000"
                                        className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-yellow-500/50"
                                        value={formData.price}
                                        onChange={(e) => onFieldChange('price', e.target.value)}
                                    />
                                </div>
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-[10px] font-black text-emerald-500/50 uppercase tracking-widest mb-2">Stop Loss</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        placeholder="Optional"
                                        className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500/50"
                                        value={formData.sl}
                                        onChange={(e) => onFieldChange('sl', e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black text-rose-500/50 uppercase tracking-widest mb-2">Target TP 1</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        placeholder="Optional"
                                        className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-rose-500/50"
                                        value={formData.tp}
                                        onChange={(e) => onFieldChange('tp', e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black text-fuchsia-500/50 uppercase tracking-widest mb-2">Target TP 2</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        placeholder="Optional"
                                        className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-fuchsia-500/50"
                                        value={formData.tp2}
                                        onChange={(e) => onFieldChange('tp2', e.target.value)}
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Entry Date (Optional)</label>
                                <input
                                    type="date"
                                    className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-yellow-500/50 opacity-80"
                                    value={formData.date}
                                    onChange={(e) => onFieldChange('date', e.target.value)}
                                />
                                <p className="text-[9px] text-gray-600 mt-1 italic">Leave blank for TODAY. Use past dates to backfill history.</p>
                            </div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 gap-6">
                            <div>
                                <label className="block text-[10px] font-black text-emerald-500/50 uppercase tracking-widest mb-2">Stop Loss</label>
                                <input
                                    type="number"
                                    step="0.0001"
                                    className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500/50"
                                    value={formData.sl}
                                    onChange={(e) => onFieldChange('sl', e.target.value)}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] font-black text-rose-500/50 uppercase tracking-widest mb-2">Take Profit 1</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-rose-500/50"
                                        value={formData.tp}
                                        onChange={(e) => onFieldChange('tp', e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black text-fuchsia-500/50 uppercase tracking-widest mb-2">Take Profit 2</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-fuchsia-500/50"
                                        value={formData.tp2}
                                        onChange={(e) => onFieldChange('tp2', e.target.value)}
                                    />
                                </div>
                            </div>
                        </div>
                    )}
                    <button
                        type="submit"
                        disabled={actionLoading}
                        className={`action-primary w-full py-4 disabled:opacity-50   ${isAdd ? '!bg-yellow-500 hover:!bg-yellow-400 !text-black  ' : '!bg-cyan-600 hover:!bg-cyan-500  '}`}
                    >
                        {actionLoading ? <RefreshCw className="animate-spin mx-auto" /> : isAdd ? 'Authorize Entry' : 'Apply Risk Patch'}
                    </button>
                </form>
            </div>
        </div>
    );
}
