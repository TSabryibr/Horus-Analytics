'use client';

import clsx from 'clsx';

import { Position } from '@/types';

interface PortfolioCloseDialogProps {
    position: Position;
    sharesValue: string;
    priceValue: string;
    maxShares: number;
    loading: boolean;
    onCancel: () => void;
    onConfirm: () => void;
    onPriceChange: (value: string) => void;
    onSharesChange: (value: string) => void;
    onPercentClick: (percent: number) => void;
}

export function PortfolioCloseDialog({
    position,
    sharesValue,
    priceValue,
    maxShares,
    loading,
    onCancel,
    onConfirm,
    onPriceChange,
    onSharesChange,
    onPercentClick,
}: PortfolioCloseDialogProps) {
    return (
        <div className="fixed inset-0 z-[130] flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true" aria-label={`Close ${position.ticker}`}>
            <div className="section-surface w-full max-w-md p-6">
                <div className="mb-5">
                    <h2 className="text-base font-bold text-white">Sell {position.ticker}</h2>
                    <p className="mt-1 text-sm text-slate-300">Current shares: {maxShares.toLocaleString()}.</p>
                </div>

                <div className="mb-4 space-y-3">
                    <label htmlFor="close-sell-price" className="block text-[10px] font-black text-gray-500 uppercase tracking-widest">Selling Price</label>
                    <input
                        id="close-sell-price"
                        type="number"
                        min={0.0001}
                        step={0.0001}
                        value={priceValue}
                        onChange={(event) => onPriceChange(event.target.value)}
                        className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-rose-500/50"
                        placeholder={String(position.current_price ?? '')}
                    />
                    <p className="text-[10px] text-slate-500">Enter the exact execution price you sold at.</p>

                    <label htmlFor="close-sell-shares" className="block text-[10px] font-black text-gray-500 uppercase tracking-widest">Shares to Sell</label>
                    <input
                        id="close-sell-shares"
                        type="number"
                        min={1}
                        max={maxShares}
                        step={1}
                        value={sharesValue}
                        onChange={(event) => onSharesChange(event.target.value)}
                        className="control-input w-full px-4 py-3 focus:ring-2 focus:ring-rose-500/50"
                        placeholder="Enter shares"
                    />
                    <div className="grid grid-cols-4 gap-2">
                        {[25, 50, 75, 100].map((percent) => (
                            <button
                                key={percent}
                                type="button"
                                className="action-secondary text-xs"
                                onClick={() => onPercentClick(percent)}
                                disabled={loading}
                            >
                                {percent}%
                            </button>
                        ))}
                    </div>
                </div>

                <div className="flex items-center justify-end gap-3">
                    <button type="button" className="action-secondary" onClick={onCancel} disabled={loading}>
                        Keep Position
                    </button>
                    <button
                        type="button"
                        className={clsx('action-primary !bg-rose-600 hover:!bg-rose-500 !text-white', loading && 'opacity-70')}
                        onClick={onConfirm}
                        disabled={loading}
                    >
                        {loading ? 'Working...' : 'Sell Shares'}
                    </button>
                </div>
            </div>
        </div>
    );
}
