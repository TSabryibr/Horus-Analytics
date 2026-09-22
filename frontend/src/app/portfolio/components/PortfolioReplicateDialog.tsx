'use client';

import React from 'react';
import { Copy, AlertTriangle, RefreshCw } from 'lucide-react';
import { Position } from '@/types';

interface PortfolioReplicateDialogProps {
    open: boolean;
    loading: boolean;
    sourcePortfolioId: number;
    sourcePortfolioName?: string;
    targetPortfolioId: number;
    sourcePositions: Position[];
    onClose: () => void;
    onConfirm: () => Promise<void> | void;
}

export function PortfolioReplicateDialog({
    open,
    loading,
    sourcePortfolioId,
    sourcePortfolioName,
    targetPortfolioId,
    sourcePositions,
    onClose,
    onConfirm,
}: PortfolioReplicateDialogProps) {
    if (!open) return null;

    return (
        <div
            className="fixed inset-0 z-[130] flex items-center justify-center bg-black/70 p-4 backdrop-blur-xs"
            role="dialog"
            aria-labelledby="replicate-dialog-title"
            onClick={(e) => {
                if (e.target === e.currentTarget && !loading) onClose();
            }}
        >
            <div className="bg-slate-900 border border-cyan-500/30 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
                <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                    <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                        <Copy className="w-6 h-6 text-amber-400" />
                    </div>
                    <div>
                        <h3 id="replicate-dialog-title" className="text-lg font-black text-white uppercase tracking-tight">
                            Confirm Fleet Replication
                        </h3>
                        <p className="text-xs text-gray-400">
                            Copy holdings from {sourcePortfolioName || `System Fleet #${sourcePortfolioId}`} to Active Portfolio #{targetPortfolioId}
                        </p>
                    </div>
                </div>

                <div className="space-y-3 bg-slate-800/60 p-4 rounded-xl border border-white/5 text-sm">
                    <div className="flex justify-between items-center text-xs">
                        <span className="text-gray-400">Source Fleet:</span>
                        <span className="font-bold text-white">{sourcePortfolioName || `Fleet #${sourcePortfolioId}`}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                        <span className="text-gray-400">Destination Portfolio:</span>
                        <span className="font-bold text-cyan-400">Portfolio #{targetPortfolioId}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                        <span className="text-gray-400">Positions to Replicate:</span>
                        <span className="font-bold text-amber-300">{sourcePositions.length} position(s)</span>
                    </div>
                </div>

                <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3.5 flex gap-3 items-start">
                    <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                    <div className="text-xs text-amber-200/90 space-y-1">
                        <p className="font-bold text-amber-300">Replacement Semantics Notice:</p>
                        <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-200/80">
                            <li>Matching open positions in destination will be <strong>REPLACED</strong>.</li>
                            <li>New source positions will be <strong>CREATED</strong>.</li>
                            <li>Unrelated destination positions will remain <strong>UNCHANGED</strong>.</li>
                            <li>Source shares will <strong>NEVER be added</strong> to existing shares.</li>
                        </ul>
                    </div>
                </div>

                <div className="flex justify-end gap-3 pt-2">
                    <button
                        type="button"
                        onClick={onClose}
                        disabled={loading}
                        className="px-4 py-2 text-xs font-bold uppercase tracking-wider text-gray-300 bg-white/5 hover:bg-white/10 rounded-lg transition disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        onClick={onConfirm}
                        disabled={loading}
                        className="flex items-center gap-2 px-5 py-2 text-xs font-bold uppercase tracking-wider text-black bg-amber-400 hover:bg-amber-300 rounded-lg shadow-md transition disabled:opacity-50"
                    >
                        {loading ? (
                            <>
                                <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Replicating...
                            </>
                        ) : (
                            'Confirm Replication'
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
