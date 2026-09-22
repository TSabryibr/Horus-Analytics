'use client';

import { useState } from 'react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';

type UiMessage = {
    type: 'error' | 'success';
    text: string;
} | null;

export type PineLabForm = {
    scriptSource: string;
    market: string;
    timeframe: string;
    dateFrom: string;
    dateTo: string;
    capital: number;
    commissionPct: number;
    slippagePct: number;
    profileName: string;
};

type UsePineBacktestOptions = {
    showMessage: (message: UiMessage) => void;
};

function buildDefaultDateRange() {
    const now = new Date();
    const currentYear = now.getFullYear();
    return {
        dateFrom: `${currentYear}-01-01`,
        dateTo: now.toISOString().slice(0, 10),
    };
}

export function usePineBacktest({ showMessage }: UsePineBacktestOptions) {
    const { dateFrom, dateTo } = buildDefaultDateRange();
    const [pineForm, setPineForm] = useState<PineLabForm>({
        scriptSource: '',
        market: 'EGX30',
        timeframe: '1D',
        dateFrom,
        dateTo,
        capital: 100000,
        commissionPct: 0.05,
        slippagePct: 0.1,
        profileName: '',
    });
    const [backtestResult, setBacktestResult] = useState<any>(null);
    const [backtestLoading, setBacktestLoading] = useState(false);

    const buildPayload = () => ({
        script_source: pineForm.scriptSource,
        market: pineForm.market,
        timeframe: pineForm.timeframe,
        date_from: pineForm.dateFrom,
        date_to: pineForm.dateTo,
        capital: Number(pineForm.capital),
        commission_pct: Number(pineForm.commissionPct),
        slippage_pct: Number(pineForm.slippagePct),
    });

    const runBacktest = async () => {
        if (!pineForm.scriptSource.trim()) {
            showMessage({ type: 'error', text: 'Pine Script Source is required.' });
            return;
        }

        setBacktestLoading(true);
        try {
            const res = await apiFetch('/api/v1/strategy/pine/backtest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(buildPayload()),
            });
            const data = await readJsonSafe<any>(res);
            if (!res.ok) {
                showMessage({ type: 'error', text: pickApiMessage(data, 'Pine backtest failed.') });
                return;
            }
            setBacktestResult(data);
            showMessage(null);
        } catch {
            showMessage({ type: 'error', text: 'Network error while running Pine backtest.' });
        } finally {
            setBacktestLoading(false);
        }
    };

    return {
        pineForm,
        setPineForm,
        buildPayload,
        backtestResult,
        backtestLoading,
        runBacktest,
    };
}
