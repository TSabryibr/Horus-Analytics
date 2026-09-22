'use client';

import { Plus, RefreshCw, Trash2, X } from 'lucide-react';

interface GenesisHoldingRow {
    id: number;
    ticker: string;
    shares: string;
    price: string;
}

interface PortfolioGenesisModalProps {
    actionLoading: boolean;
    genesisData: {
        egp_balance: string;
        usd_balance: string;
        holdings: GenesisHoldingRow[];
    };
    onClose: () => void;
    onSubmit: (event: React.FormEvent) => void;
    onFieldChange: (field: 'egp_balance' | 'usd_balance', value: string) => void;
    onAddHolding: () => void;
    onRemoveHolding: (id: number) => void;
    onUpdateHolding: (id: number, field: 'ticker' | 'shares' | 'price', value: string) => void;
}

export function PortfolioGenesisModal({
    actionLoading,
    genesisData,
    onClose,
    onSubmit,
    onFieldChange,
    onAddHolding,
    onRemoveHolding,
    onUpdateHolding,
}: PortfolioGenesisModalProps) {
    return (
        <div className="fixed inset-0 bg-black/60 z-[110] flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Treasury genesis">
            <div className="section-surface w-full max-w-2xl overflow-hidden rounded-[2rem] animate-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col">
                <div className="p-8 border-b border-white/5 flex justify-between items-center bg-gradient-to-r from-yellow-500/10 to-transparent flex-shrink-0">
                    <div>
                        <h3 className="text-xl font-black text-white uppercase tracking-tighter">Treasury Genesis</h3>
                        <p className="text-xs text-gray-500 font-mono">CALIBRATE RESERVES & HOLDINGS</p>
                    </div>
                    <button type="button" onClick={onClose} aria-label="Close" className="text-gray-500 hover:text-white transition">
                        <X size={20} />
                    </button>
                </div>

                <div className="overflow-y-auto flex-1 p-8">
                    <form id="genesis-form" onSubmit={onSubmit} className="space-y-8">
                        <div className="space-y-4">
                            <h4 className="text-sm font-black text-gray-400 uppercase tracking-widest border-b border-white/5 pb-2">1. Starting Cash Reserves</h4>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] font-black text-emerald-500/50 uppercase tracking-widest mb-2">EGP Balance</label>
                                    <div className="relative">
                                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-emerald-500/50 font-bold">EGP</div>
                                        <input
                                            required
                                            type="number"
                                            placeholder="0.00"
                                            className="control-input w-full pl-14 pr-4 py-3 focus:ring-2 focus:ring-emerald-500/50"
                                            value={genesisData.egp_balance}
                                            onChange={(e) => onFieldChange('egp_balance', e.target.value)}
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black text-cyan-500/50 uppercase tracking-widest mb-2">USD Balance</label>
                                    <div className="relative">
                                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-cyan-500/50 font-bold">USD</div>
                                        <input
                                            required
                                            type="number"
                                            placeholder="0.00"
                                            className="control-input w-full pl-14 pr-4 py-3 focus:ring-2 focus:ring-cyan-500/50"
                                            value={genesisData.usd_balance}
                                            onChange={(e) => onFieldChange('usd_balance', e.target.value)}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="flex justify-between items-center border-b border-white/5 pb-2">
                                <h4 className="text-sm font-black text-gray-400 uppercase tracking-widest">2. Existing Holdings (Optional)</h4>
                                <button
                                    type="button"
                                    onClick={onAddHolding}
                                    className="action-secondary text-xs !text-yellow-500 px-3 py-1 border-yellow-500/20 gap-1"
                                >
                                    <Plus size={12} /> Add Ticker
                                </button>
                            </div>

                            <div className="space-y-2">
                                {genesisData.holdings.length === 0 && (
                                    <div className="rounded-xl border border-dashed border-white/10 bg-slate-950/45 py-4 text-center text-xs italic text-slate-600">
                                        No holdings added. You can start with just cash.
                                    </div>
                                )}

                                {genesisData.holdings.map((holding, idx) => (
                                    <div key={holding.id} className="flex gap-2 items-center animate-in slide-in-from-left-2 duration-200">
                                        <div className="w-8 text-[10px] text-gray-600 font-mono text-center">#{idx + 1}</div>
                                        <input
                                            type="text"
                                            placeholder="Ticker"
                                            className="control-input flex-1 px-3 py-2 text-sm focus:ring-1 focus:ring-yellow-500/50 uppercase"
                                            value={holding.ticker}
                                            onChange={(e) => onUpdateHolding(holding.id, 'ticker', e.target.value)}
                                        />
                                        <input
                                            type="number"
                                            placeholder="Shares"
                                            className="control-input w-24 px-3 py-2 text-sm focus:ring-1 focus:ring-yellow-500/50"
                                            value={holding.shares}
                                            onChange={(e) => onUpdateHolding(holding.id, 'shares', e.target.value)}
                                        />
                                        <input
                                            type="number"
                                            placeholder="Avg Price"
                                            className="control-input w-32 px-3 py-2 text-sm focus:ring-1 focus:ring-yellow-500/50"
                                            value={holding.price}
                                            onChange={(e) => onUpdateHolding(holding.id, 'price', e.target.value)}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => onRemoveHolding(holding.id)}
                                            aria-label={`Remove holding ${holding.ticker || idx + 1}`}
                                            className="p-2 text-gray-600 hover:text-red-500 transition"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </form>
                </div>

                <div className="p-8 border-t border-white/5 flex-shrink-0">
                    <button
                        form="genesis-form"
                        type="submit"
                        disabled={actionLoading}
                        className="action-primary w-full !bg-yellow-500 hover:!bg-yellow-400 !text-black py-4 disabled:opacity-50"
                    >
                        {actionLoading ? <RefreshCw className="animate-spin mx-auto" /> : 'Authorize Treasury Genesis'}
                    </button>
                </div>
            </div>
        </div>
    );
}
