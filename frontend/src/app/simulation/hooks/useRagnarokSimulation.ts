'use client';

import { useState } from 'react';

export type RagnarokResult = {
    expected_value: number;
    var_95: number;
    loss_probability: number;
    ruin_probability: number;
    starting_value: number;
    ruin_threshold_pct: number;
    ruin_floor: number;
    iterations: number;
    days: number;
    assets_count: number;
    assets_used: string[];
    plot_paths: number[][];
};

type UseRagnarokSimulationOptions = {
    apiBase: string;
};

export function useRagnarokSimulation({ apiBase }: UseRagnarokSimulationOptions) {
    const [ragnarokLoading, setRagnarokLoading] = useState(false);
    const [ragnarokResult, setRagnarokResult] = useState<RagnarokResult | null>(null);
    const [ragnarokError, setRagnarokError] = useState<string | null>(null);
    const [ragnarokIterations, setRagnarokIterations] = useState('1000');
    const [ragnarokDays, setRagnarokDays] = useState('20');
    const [ragnarokStartingValue, setRagnarokStartingValue] = useState('');
    const [ragnarokRuinThresholdPct, setRagnarokRuinThresholdPct] = useState('50');
    const [tickerInput, setTickerInput] = useState('');

    const runRagnarokSimulation = async () => {
        setRagnarokLoading(true);
        setRagnarokError(null);
        try {
            const parsedTickers = tickerInput
                .split(',')
                .map((ticker) => ticker.trim().toUpperCase())
                .filter(Boolean);

            const res = await fetch(`${apiBase}/api/v1/ragnarok`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    iterations: parseInt(ragnarokIterations, 10) || 1000,
                    days: parseInt(ragnarokDays, 10) || 20,
                    tickers: parsedTickers.length ? parsedTickers : undefined,
                    starting_value: ragnarokStartingValue ? parseFloat(ragnarokStartingValue) : undefined,
                    ruin_threshold_pct: parseFloat(ragnarokRuinThresholdPct) || 50,
                }),
            });
            const json = await res.json();
            if (json.status === 'success') {
                setRagnarokResult(json.data);
            } else {
                setRagnarokError(json.message || 'Ragnarok simulation failed.');
            }
        } catch (error) {
            setRagnarokError('Ragnarok simulation failed.');
            console.error('Ragnarok error:', error);
        } finally {
            setRagnarokLoading(false);
        }
    };

    return {
        ragnarokLoading,
        ragnarokResult,
        ragnarokError,
        ragnarokIterations,
        setRagnarokIterations,
        ragnarokDays,
        setRagnarokDays,
        ragnarokStartingValue,
        setRagnarokStartingValue,
        ragnarokRuinThresholdPct,
        setRagnarokRuinThresholdPct,
        tickerInput,
        setTickerInput,
        runRagnarokSimulation,
    };
}
