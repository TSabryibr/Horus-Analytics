'use client';

import { useState } from 'react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';

import type { PineLabForm } from './usePineBacktest';

type UiMessage = {
    type: 'error' | 'success';
    text: string;
} | null;

type UsePineLogicImportOptions = {
    pineForm: PineLabForm;
    showMessage: (message: UiMessage) => void;
    enabled?: boolean;
};

export function usePineLogicImport({ pineForm, showMessage, enabled = true }: UsePineLogicImportOptions) {
    const [importPreviewResult, setImportPreviewResult] = useState<any>(null);
    const [importPreviewLoading, setImportPreviewLoading] = useState(false);
    const [signalOverrides, setSignalOverrides] = useState<Record<string, string>>({});

    const setSignalOverride = (role: string, sourceName: string) => {
        setSignalOverrides((current) => ({
            ...current,
            [role]: sourceName,
        }));
    };

    const runImportPreview = async () => {
        if (!enabled) {
            return;
        }
        if (!pineForm.scriptSource.trim()) {
            showMessage({ type: 'error', text: 'Pine Script Source is required.' });
            return;
        }

        setImportPreviewLoading(true);
        try {
            const payload: Record<string, unknown> = {
                script_source: pineForm.scriptSource,
                market: pineForm.market,
                timeframe: pineForm.timeframe,
                date_from: pineForm.dateFrom,
                date_to: pineForm.dateTo,
            };
            if (Object.keys(signalOverrides).length > 0) {
                payload.signal_overrides = signalOverrides;
            }
            const res = await apiFetch('/api/v1/strategy/pine/import-preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await readJsonSafe<any>(res);
            if (!res.ok) {
                showMessage({ type: 'error', text: pickApiMessage(data, 'Pine logic import preview failed.') });
                return;
            }
            setImportPreviewResult(data);
            if (data?.signal_overrides && typeof data.signal_overrides === 'object') {
                setSignalOverrides(data.signal_overrides);
            }
            showMessage(null);
        } catch {
            showMessage({ type: 'error', text: 'Network error while running Pine logic import preview.' });
        } finally {
            setImportPreviewLoading(false);
        }
    };

    return {
        importPreviewResult,
        importPreviewLoading,
        signalOverrides,
        setSignalOverride,
        runImportPreview,
    };
}
