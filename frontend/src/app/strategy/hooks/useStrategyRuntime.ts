import { useEffect, useState } from 'react';

import { useStrategyData } from '../../context/GlobalDataContext';

import {
    buildStrategyApplyPayload,
    defaultManualParams,
    getStrategyRegimeColor,
} from '../lib/strategyTransforms';

export function useStrategyRuntime() {
    const { strategy: proposal, strategyLoading, refreshStrategy } = useStrategyData();
    const [successMsg, setSuccessMsg] = useState('');
    const [errorMsg, setErrorMsg] = useState('');
    const [manualMode, setManualMode] = useState(false);
    const [manualParams, setManualParams] = useState(defaultManualParams);

    useEffect(() => {
        if (proposal?.proposed_settings) {
            const updated = { ...defaultManualParams };
            Object.entries(proposal.proposed_settings).forEach(([k, v]) => {
                if (k in updated && typeof v === 'number') {
                    (updated as Record<string, number>)[k] = v;
                }
            });
            setManualParams(updated);
        }
    }, [proposal]);

    const toggleManualMode = () => setManualMode((current) => !current);

    const updateManualParam = (key: keyof typeof defaultManualParams, value: number) => {
        setManualParams((current) => ({
            ...current,
            [key]: value,
        }));
    };

    const buildApplyPayload = () =>
        buildStrategyApplyPayload({
            manualMode,
            manualParams,
            proposal,
        });

    return {
        proposal,
        isLoading: strategyLoading,
        refreshStrategy,
        successMsg,
        setSuccessMsg,
        errorMsg,
        setErrorMsg,
        manualMode,
        manualParams,
        setManualParams,
        toggleManualMode,
        updateManualParam,
        buildApplyPayload,
        getRegimeColor: getStrategyRegimeColor,
    };
}
