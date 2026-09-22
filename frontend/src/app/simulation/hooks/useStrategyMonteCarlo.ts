'use client';

import { useState } from 'react';

export type MonteCarloResult = {
    simulations: number;
    median_equity: number;
    worst_case_equity: number;
    best_case_equity: number;
    avg_max_drawdown: number;
    median_max_drawdown: number;
    worst_max_drawdown: number;
    loss_probability: number;
    ruin_probability: number;
    ruin_threshold_pct: number;
    ruin_floor: number;
    drawdown_probability_20: number;
    drawdown_probability_50: number;
    plot_paths: number[][];
};

type UseStrategyMonteCarloOptions = {
    apiBase: string;
};

export function useStrategyMonteCarlo({ apiBase }: UseStrategyMonteCarloOptions) {
    const [mcLoading, setMcLoading] = useState(false);
    const [mcResult, setMcResult] = useState<MonteCarloResult | null>(null);
    const [mcError, setMcError] = useState<string | null>(null);
    const [mcCapital, setMcCapital] = useState('100000');
    const [mcSims, setMcSims] = useState('2000');
    const [mcRuinThreshold, setMcRuinThreshold] = useState('50');

    const runStrategyMonteCarlo = async () => {
        setMcLoading(true);
        setMcError(null);
        try {
            const res = await fetch(`${apiBase}/api/v1/montecarlo`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    initial_capital: parseFloat(mcCapital) || 100000,
                    simulations: parseInt(mcSims, 10) || 2000,
                    ruin_threshold_pct: parseFloat(mcRuinThreshold) || 50,
                }),
            });
            const json = await res.json();
            if (json.status === 'success') {
                setMcResult(json.data);
            } else if (json.status === 'warning') {
                setMcError(json.message);
            }
        } catch (error) {
            setMcError('Monte Carlo simulation failed.');
            console.error('Monte Carlo error:', error);
        } finally {
            setMcLoading(false);
        }
    };

    return {
        mcLoading,
        mcResult,
        mcError,
        mcCapital,
        setMcCapital,
        mcSims,
        setMcSims,
        mcRuinThreshold,
        setMcRuinThreshold,
        runStrategyMonteCarlo,
    };
}
