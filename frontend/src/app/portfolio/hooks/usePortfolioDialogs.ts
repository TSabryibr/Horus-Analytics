import { useRef, useState } from 'react';
import { Position } from '@/types';
import { formatPrice, toNumber } from '../lib/forms';

interface UsePortfolioDialogsProps {
    hoard: any;
    showUiMessage: (type: 'error' | 'success', message: string) => void;
    submitClosePosition: (position: Position, shares: number, price: number) => Promise<void>;
}

export function usePortfolioDialogs({ hoard, showUiMessage, submitClosePosition }: UsePortfolioDialogsProps) {
    const nextGenesisHoldingId = useRef(1);

    // Basic Modal Toggles
    const [isAnalysisModalOpen, setIsAnalysisModalOpen] = useState(false);
    const [isManagementModalOpen, setIsManagementModalOpen] = useState(false);

    // Genesis Modal State
    const [isGenesisModalOpen, setIsGenesisModalOpen] = useState(false);
    const [genesisData, setGenesisData] = useState({
        egp_balance: '',
        usd_balance: '',
        holdings: [] as { id: number; ticker: string; shares: string; price: string }[]
    });

    const handleGenesisFieldChange = (field: 'egp_balance' | 'usd_balance', value: string) => {
        setGenesisData((prev) => ({ ...prev, [field]: value }));
    };

    const addGenesisHoldingRow = () => {
        const rowId = nextGenesisHoldingId.current;
        nextGenesisHoldingId.current += 1;
        setGenesisData((prev) => ({
            ...prev,
            holdings: [...prev.holdings, { id: rowId, ticker: '', shares: '', price: '' }],
        }));
    };

    const removeGenesisHoldingRow = (id: number) => {
        setGenesisData((prev) => ({
            ...prev,
            holdings: prev.holdings.filter((holding) => holding.id !== id),
        }));
    };

    const updateGenesisHoldingRow = (id: number, field: 'ticker' | 'shares' | 'price', value: string) => {
        setGenesisData((prev) => ({
            ...prev,
            holdings: prev.holdings.map((holding) => (
                holding.id === id ? { ...holding, [field]: value } : holding
            )),
        }));
    };

    // Close Dialog State
    const [closeConfirmOpen, setCloseConfirmOpen] = useState(false);
    const [pendingClosePosition, setPendingClosePosition] = useState<Position | null>(null);
    const [pendingCloseShares, setPendingCloseShares] = useState<string>('');
    const [pendingClosePrice, setPendingClosePrice] = useState<string>('');

    const getMaxSellableShares = (position: Position | null) => {
        const rawShares = toNumber(position?.shares);
        if (!Number.isFinite(rawShares) || rawShares <= 0) return 0;
        return Math.max(1, Math.trunc(rawShares));
    };

    const resetCloseDialog = () => {
        setCloseConfirmOpen(false);
        setPendingClosePosition(null);
        setPendingCloseShares('');
        setPendingClosePrice('');
    };

    const requestClosePosition = (ticker: string) => {
        if (!hoard) {
            showUiMessage('error', "Position data is not loaded yet.");
            return;
        }
        const position = hoard.positions.find((p: Position) => p.ticker === ticker) || null;
        if (!position) {
            showUiMessage('error', "Position not found or data not loaded");
            return;
        }
        const maxShares = getMaxSellableShares(position);
        if (maxShares <= 0) {
            showUiMessage('error', `Position ${ticker} has no sellable shares.`);
            return;
        }
        setPendingClosePosition(position);
        setPendingCloseShares(String(maxShares));
        setPendingClosePrice(formatPrice(position.current_price));
        setCloseConfirmOpen(true);
    };

    const setQuickCloseShares = (percent: number) => {
        const maxShares = getMaxSellableShares(pendingClosePosition);
        if (maxShares <= 0) return;
        const quickShares = Math.max(1, Math.round((maxShares * percent) / 100));
        setPendingCloseShares(String(Math.min(maxShares, quickShares)));
    };

    const confirmClosePosition = async () => {
        if (!pendingClosePosition) {
            resetCloseDialog();
            return;
        }
        const maxShares = getMaxSellableShares(pendingClosePosition);
        const requestedShares = Number(pendingCloseShares);
        const requestedPrice = Number(pendingClosePrice);

        if (!Number.isInteger(requestedShares) || requestedShares <= 0) {
            showUiMessage('error', "Shares to sell must be a positive whole number.");
            return;
        }
        if (!Number.isFinite(requestedPrice) || requestedPrice <= 0) {
            showUiMessage('error', "Selling price must be a number greater than zero.");
            return;
        }
        if (requestedShares > maxShares) {
            showUiMessage('error', `Cannot sell more than ${maxShares} shares for ${pendingClosePosition.ticker}.`);
            return;
        }

        const positionToClose = pendingClosePosition;
        resetCloseDialog();
        await submitClosePosition(positionToClose, requestedShares, requestedPrice);
    };

    return {
        isAnalysisModalOpen,
        setIsAnalysisModalOpen,
        isManagementModalOpen,
        setIsManagementModalOpen,

        isGenesisModalOpen,
        setIsGenesisModalOpen,
        genesisData,
        setGenesisData,
        handleGenesisFieldChange,
        addGenesisHoldingRow,
        removeGenesisHoldingRow,
        updateGenesisHoldingRow,

        closeConfirmOpen,
        pendingClosePosition,
        pendingCloseShares,
        pendingClosePrice,
        getMaxSellableShares,
        resetCloseDialog,
        requestClosePosition,
        setPendingClosePrice,
        setPendingCloseShares,
        setQuickCloseShares,
        confirmClosePosition,
    };
}
