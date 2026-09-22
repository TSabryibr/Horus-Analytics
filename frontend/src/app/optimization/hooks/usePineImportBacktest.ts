'use client';

import { useEffect, useState } from 'react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';

import type { PineLabForm } from './usePineBacktest';

type UiMessage = {
    type: 'error' | 'success';
    text: string;
} | null;

type UsePineImportBacktestOptions = {
    pineForm: PineLabForm;
    importPreviewResult: any;
    showMessage: (message: UiMessage) => void;
    enabled?: boolean;
};

export function usePineImportBacktest({
    pineForm,
    importPreviewResult,
    showMessage,
    enabled = true,
}: UsePineImportBacktestOptions) {
    const [operatorApproved, setOperatorApproved] = useState(false);
    const [importBacktestResult, setImportBacktestResult] = useState<any>(null);
    const [importBacktestLoading, setImportBacktestLoading] = useState(false);

    useEffect(() => {
        setOperatorApproved(false);
        setImportBacktestResult(null);
    }, [importPreviewResult]);

    const runImportBacktest = async () => {
        if (!enabled) {
            return;
        }
        if (!importPreviewResult?.rule_spec) {
            showMessage({ type: 'error', text: 'Extract a Pine logic import rule spec before running import backtest.' });
            return;
        }
        if (!operatorApproved) {
            showMessage({ type: 'error', text: 'Approve the imported rule spec before running import backtest.' });
            return;
        }

        setImportBacktestLoading(true);
        try {
            const res = await apiFetch('/api/v1/strategy/pine/import-backtest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    rule_spec: importPreviewResult.rule_spec,
                    operator_approved: true,
                    market: pineForm.market,
                    timeframe: pineForm.timeframe,
                    date_from: pineForm.dateFrom,
                    date_to: pineForm.dateTo,
                    capital: Number(pineForm.capital),
                    commission_pct: Number(pineForm.commissionPct),
                    slippage_pct: Number(pineForm.slippagePct),
                }),
            });
            const data = await readJsonSafe<any>(res);
            if (!res.ok) {
                showMessage({ type: 'error', text: pickApiMessage(data, 'Pine import backtest failed.') });
                return;
            }
            setImportBacktestResult(data);
            showMessage(null);
        } catch {
            showMessage({ type: 'error', text: 'Network error while running Pine import backtest.' });
        } finally {
            setImportBacktestLoading(false);
        }
    };

    return {
        operatorApproved,
        setOperatorApproved,
        importBacktestResult,
        importBacktestLoading,
        runImportBacktest,
    };
}
