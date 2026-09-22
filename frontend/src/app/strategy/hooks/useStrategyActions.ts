'use client';

import { useState } from 'react';
import { getBaseUrl } from '@/lib/api';

import { StrategyProposal } from '@/types/domain';

type UseStrategyActionsOptions = {
    manualMode: boolean;
    proposal: StrategyProposal | null;
    refreshStrategy: () => void;
    buildApplyPayload: () => Record<string, unknown> | null;
    setErrorMsg: (message: string) => void;
    setSuccessMsg: (message: string) => void;
};

export function useStrategyActions({
    manualMode,
    proposal,
    refreshStrategy,
    buildApplyPayload,
    setErrorMsg,
    setSuccessMsg,
}: UseStrategyActionsOptions) {
    const [applying, setApplying] = useState(false);

    const applyStrategy = async () => {
        if (!proposal && !manualMode) {
            return;
        }

        setApplying(true);
        setErrorMsg('');

        try {
            const payload = buildApplyPayload();

            if (!payload) {
                setErrorMsg('No strategy parameters available to apply.');
                return;
            }

            const res = await fetch(
                `${getBaseUrl()}/api/v1/strategy/apply`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                },
            );
            const json = await res.json();

            if (res.ok && (json.status === 'applied' || json.status === 'success')) {
                setSuccessMsg(
                    manualMode
                        ? 'Manual Overrides Applied!'
                        : 'Strategy Updated Successfully! Fenrir is active.',
                );
                refreshStrategy();
                setTimeout(() => setSuccessMsg(''), 5000);
            } else {
                setErrorMsg(json?.detail || json?.message || 'Failed to apply strategy changes.');
            }
        } catch (error) {
            console.error('Apply Error:', error);
            setErrorMsg('Network error while applying strategy changes.');
        } finally {
            setApplying(false);
        }
    };

    return {
        applying,
        applyStrategy,
        refresh: refreshStrategy,
    };
}
