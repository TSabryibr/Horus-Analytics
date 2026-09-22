'use client';

import { useState } from 'react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';

type UiMessage = {
    type: 'error' | 'success';
    text: string;
} | null;

type UsePinePreflightOptions = {
    buildPayload: () => {
        script_source: string;
        market: string;
        timeframe: string;
        date_from: string;
        date_to: string;
    };
    showMessage: (message: UiMessage) => void;
};

export function usePinePreflight({ buildPayload, showMessage }: UsePinePreflightOptions) {
    const [preflightResult, setPreflightResult] = useState<any>(null);
    const [preflightLoading, setPreflightLoading] = useState(false);

    const runPreflight = async () => {
        const payload = buildPayload();
        if (!payload.script_source.trim()) {
            showMessage({ type: 'error', text: 'Pine Script Source is required.' });
            return;
        }

        setPreflightLoading(true);
        try {
            const res = await apiFetch('/api/v1/strategy/pine/preflight', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await readJsonSafe<any>(res);
            if (!res.ok) {
                showMessage({ type: 'error', text: pickApiMessage(data, 'Pine preflight failed.') });
                return;
            }
            setPreflightResult(data);
            showMessage(null);
        } catch {
            showMessage({ type: 'error', text: 'Network error while running Pine preflight.' });
        } finally {
            setPreflightLoading(false);
        }
    };

    return {
        preflightResult,
        preflightLoading,
        runPreflight,
    };
}
