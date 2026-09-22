'use client';

import { useState } from 'react';

import { Position } from '@/types';
import { apiFetch, apiUrl, pickApiMessage, readJsonSafe } from '@/lib/api';

export interface PortfolioFormData {
    ticker: string;
    shares: string;
    price: string;
    sl: string;
    tp: string;
    tp2: string;
    date: string;
}

export interface GenesisHoldingInput {
    id: number;
    ticker: string;
    shares: string;
    price: string;
}

export interface GenesisFormData {
    egp_balance: string;
    usd_balance: string;
    holdings: GenesisHoldingInput[];
}

function buildGenesisHoldingsPayload(holdings: GenesisHoldingInput[]) {
    const byTicker = new Map<string, { ticker: string; shares: number; totalCost: number }>();

    holdings
        .filter((holding) => holding.ticker && holding.shares && holding.price)
        .forEach((holding) => {
            const ticker = holding.ticker.trim().toUpperCase();
            const shares = Number(holding.shares);
            const price = Number(holding.price);
            if (!ticker || !Number.isFinite(shares) || !Number.isFinite(price) || shares <= 0 || price <= 0) {
                return;
            }

            const current = byTicker.get(ticker) || { ticker, shares: 0, totalCost: 0 };
            current.shares += shares;
            current.totalCost += shares * price;
            byTicker.set(ticker, current);
        });

    return Array.from(byTicker.values()).map((holding) => ({
        ticker: holding.ticker,
        shares: holding.shares,
        price: holding.totalCost / holding.shares,
    }));
}

interface UsePortfolioActionsArgs {
    activePortfolioId: number | null;
    refreshData: () => Promise<void> | void;
    showUiMessage: (type: 'error' | 'success', text: string) => void;
    clearUiMessage: () => void;
    importFileInputRef: React.RefObject<HTMLInputElement | null>;
}

export function usePortfolioActions({
    activePortfolioId,
    refreshData,
    showUiMessage,
    clearUiMessage,
    importFileInputRef,
}: UsePortfolioActionsArgs) {
    const [actionLoading, setActionLoading] = useState(false);
    const [closeActionLoading, setCloseActionLoading] = useState(false);
    const [importLoading, setImportLoading] = useState(false);

    const handleGenesis = async (
        genesisData: GenesisFormData,
        callbacks: { closeModal: () => void }
    ) => {
        setActionLoading(true);
        if (!activePortfolioId) {
            showUiMessage('error', 'No active user portfolio selected.');
            setActionLoading(false);
            return;
        }

        try {
            const validHoldings = buildGenesisHoldingsPayload(genesisData.holdings);

            const res = await apiFetch('/api/v1/portfolio/genesis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    egp_balance: Number(genesisData.egp_balance),
                    usd_balance: Number(genesisData.usd_balance),
                    holdings: validHoldings,
                }),
            });

            const data = await readJsonSafe<any>(res);
            if (res.ok && data.status === 'success') {
                callbacks.closeModal();
                clearUiMessage();
                await refreshData();
                if (data.errors && data.errors.length > 0) {
                    showUiMessage('error', `Portfolio initialized with issues: ${data.errors.join(' | ')}`);
                } else {
                    showUiMessage('success', 'Portfolio initialized successfully.');
                }
            } else {
                showUiMessage('error', pickApiMessage(data, 'Failed to initialize portfolio.'));
            }
        } catch (_error) {
            showUiMessage('error', 'Network error while initializing portfolio.');
        } finally {
            setActionLoading(false);
        }
    };

    const handleAddPosition = async (
        formData: PortfolioFormData,
        callbacks: { closeModal: () => void; resetForm: () => void }
    ) => {
        setActionLoading(true);
        if (!activePortfolioId) {
            showUiMessage('error', 'No active user portfolio selected.');
            setActionLoading(false);
            return;
        }

        try {
            const res = await apiFetch('/api/v1/portfolio/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker: formData.ticker.toUpperCase(),
                    shares: Number(formData.shares),
                    price: Number(formData.price),
                    sl: formData.sl ? Number(formData.sl) : null,
                    target_price: formData.tp ? Number(formData.tp) : null,
                    target_price_2: formData.tp2 ? Number(formData.tp2) : null,
                    date: formData.date || null,
                    portfolio_id: activePortfolioId,
                }),
            });

            const data = await readJsonSafe<any>(res);
            const status = typeof data.status === 'string' ? data.status : '';

            if (res.ok && status === 'success') {
                callbacks.closeModal();
                callbacks.resetForm();
                showUiMessage('success', `Position ${formData.ticker.toUpperCase()} added.`);
                await refreshData();
            } else if (res.status === 403) {
                showUiMessage('error', `Blocked by WFA gate: ${pickApiMessage(data, 'This ticker is blocked for new entries.')}`);
            } else {
                showUiMessage('error', pickApiMessage(data, 'Failed to add position'));
            }
        } catch (_error) {
            showUiMessage('error', 'Network error while adding position.');
        } finally {
            setActionLoading(false);
        }
    };

    const handleUpdatePosition = async (
        selectedPosition: Position | null,
        formData: Pick<PortfolioFormData, 'sl' | 'tp' | 'tp2'>,
        callbacks: { onComplete: () => void }
    ) => {
        if (!selectedPosition) return;

        setActionLoading(true);
        if (!activePortfolioId) {
            showUiMessage('error', 'No active user portfolio selected.');
            setActionLoading(false);
            return;
        }

        try {
            const res = await apiFetch('/api/v1/portfolio/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker: selectedPosition.ticker,
                    sl: formData.sl ? Number(formData.sl) : null,
                    target_price: formData.tp ? Number(formData.tp) : null,
                    target_price_2: formData.tp2 ? Number(formData.tp2) : null,
                    portfolio_id: activePortfolioId,
                }),
            });

            const data = await readJsonSafe<any>(res);
            if (res.ok && data.status === 'success') {
                callbacks.onComplete();
                showUiMessage('success', `Position ${selectedPosition.ticker} updated.`);
                await refreshData();
            } else {
                showUiMessage('error', pickApiMessage(data, 'Failed to update position'));
            }
        } catch (_error) {
            showUiMessage('error', 'Network error while updating position.');
        } finally {
            setActionLoading(false);
        }
    };

    const handleClosePosition = async (position: Position, sharesToSell: number, sellPrice: number) => {
        setCloseActionLoading(true);
        if (!activePortfolioId) {
            showUiMessage('error', 'No active user portfolio selected.');
            setCloseActionLoading(false);
            return;
        }

        try {
            const ticker = position.ticker;
            const rawShares = Number(position.shares);
            const maxShares = Number.isFinite(rawShares) && rawShares > 0 ? Math.max(1, Math.trunc(rawShares)) : 0;

            const res = await apiFetch('/api/v1/portfolio/close', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker,
                    shares: sharesToSell,
                    price: sellPrice,
                    reason: 'MANUAL_UI',
                    portfolio_id: activePortfolioId,
                }),
            });

            const data = await readJsonSafe<any>(res);
            const status = typeof data.status === 'string' ? data.status : '';
            if (res.ok && status === 'success') {
                if (sharesToSell < maxShares) {
                    showUiMessage('success', `Sold ${sharesToSell}/${maxShares} shares of ${ticker}.`);
                } else {
                    showUiMessage('success', `Position ${ticker} closed.`);
                }
                await refreshData();
            } else {
                const fallback = `Failed to close position${res.status ? ` (HTTP ${res.status})` : ''}`;
                showUiMessage('error', pickApiMessage(data, fallback));
            }
        } catch (_error) {
            showUiMessage('error', 'Network error while closing position.');
        } finally {
            setCloseActionLoading(false);
        }
    };

    const handleExport = () => {
        window.open(apiUrl(`/api/v1/portfolio/export?portfolio_id=${activePortfolioId}`), '_blank');
    };

    const handleExportExcel = () => {
        window.open(apiUrl(`/api/v1/portfolio/export/excel?portfolio_id=${activePortfolioId}`), '_blank');
    };

    const handleDownloadTemplate = (format: 'xlsx' | 'csv' = 'xlsx') => {
        window.open(apiUrl(`/api/v1/portfolio/template?format=${format}`), '_blank');
    };

    const triggerImportPicker = () => {
        if (importLoading) return;
        importFileInputRef.current?.click();
    };

    const handleImportCsv = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0] || null;
        event.target.value = '';
        if (!selectedFile) return;
        if (!activePortfolioId) {
            showUiMessage('error', 'No active user portfolio selected.');
            return;
        }

        const proceed = window.confirm(
            'Import will load holdings from your Subscriber Template (.xlsx / .csv) or restore a Horus backup into this portfolio. Continue?'
        );
        if (!proceed) return;

        setImportLoading(true);
        try {
            const body = new FormData();
            body.append('file', selectedFile);
            const response = await apiFetch(
                `/api/v1/portfolio/import?portfolio_id=${activePortfolioId}&replace_existing=true`,
                { method: 'POST', body }
            );
            const json = await readJsonSafe<any>(response);
            if (!response.ok) {
                showUiMessage('error', pickApiMessage(json, 'File import failed.'));
                return;
            }

            const imported = json?.imported || {};
            if (json?.message) {
                showUiMessage('success', json.message);
            } else {
                showUiMessage(
                    'success',
                    `Import complete: profile ${imported.profile || 0}, positions ${imported.positions || 0}, trades ${imported.trades || 0}, snapshots ${imported.snapshots || 0}.`
                );
            }
            await refreshData();
        } catch (_error) {
            showUiMessage('error', 'Network error while importing file.');
        } finally {
            setImportLoading(false);
        }
    };

    const handleBatchAction = async (action: 'MOVE_STOPS_BREAKEVEN' | 'SCALE_OUT_50' | 'FLATTEN', tickers: string[]) => {
        if (!activePortfolioId) {
            showUiMessage('error', 'No active user portfolio selected.');
            return;
        }
        if (!tickers || tickers.length === 0) {
            showUiMessage('error', 'No holdings selected for batch action.');
            return;
        }

        setActionLoading(true);
        try {
            const res = await apiFetch('/api/v1/portfolio/positions/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    portfolio_id: activePortfolioId,
                    action,
                    tickers,
                }),
            });
            const data = await readJsonSafe<any>(res);
            if (res.ok && (data.status === 'success' || data.status === 'partial')) {
                const label =
                    action === 'MOVE_STOPS_BREAKEVEN'
                        ? 'Stops moved to breakeven'
                        : action === 'SCALE_OUT_50'
                        ? 'Scaled out 50%'
                        : 'Flattened';
                showUiMessage('success', `${label} for ${data.processed_count} position(s).`);
                await refreshData();
            } else {
                showUiMessage('error', pickApiMessage(data, 'Batch action failed.'));
            }
        } catch (_err) {
            showUiMessage('error', 'Network error during batch execution.');
        } finally {
            setActionLoading(false);
        }
    };

    const handleApplyRebalance = async (model: string, callbacks?: { onSuccess?: () => void }) => {
        if (!activePortfolioId) {
            showUiMessage('error', 'No active user portfolio selected.');
            return;
        }

        setActionLoading(true);
        try {
            const res = await apiFetch('/api/v1/portfolio/rebalance/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    portfolio_id: activePortfolioId,
                    model,
                }),
            });
            const data = await readJsonSafe<any>(res);
            if (res.ok && data.status !== 'error') {
                showUiMessage('success', `Rebalance applied: ${data.executed_count || 0} order(s) processed.`);
                callbacks?.onSuccess?.();
                await refreshData();
            } else {
                showUiMessage('error', pickApiMessage(data, 'Rebalance execution failed.'));
            }
        } catch (_err) {
            showUiMessage('error', 'Network error applying rebalance.');
        } finally {
            setActionLoading(false);
        }
    };

    return {
        actionLoading,
        closeActionLoading,
        importLoading,
        handleGenesis,
        handleAddPosition,
        handleUpdatePosition,
        handleClosePosition,
        handleExport,
        handleExportExcel,
        handleDownloadTemplate,
        triggerImportPicker,
        handleImportCsv,
        handleBatchAction,
        handleApplyRebalance,
    };
}
