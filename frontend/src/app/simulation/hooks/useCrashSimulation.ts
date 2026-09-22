'use client';

import { useState } from 'react';

export type StressResult = {
    crash_date: string;
    market_impact: number;
    worst_affected: Array<Record<string, any>>;
    least_affected: Array<Record<string, any>>;
    estimated_loss_egp?: number;
    ending_capital?: number;
    initial_capital?: number;
    lookback_days?: number;
    simulation_days?: number;
    ref_date?: string | null;
};

type UseCrashSimulationOptions = {
    apiBase: string;
};

export function useCrashSimulation({ apiBase }: UseCrashSimulationOptions) {
    const [stressLoading, setStressLoading] = useState(false);
    const [stressResult, setStressResult] = useState<StressResult | null>(null);
    const [indexChoice, setIndexChoice] = useState('EGX30');
    const [startDate, setStartDate] = useState('');
    const [initialCapital, setInitialCapital] = useState('1000000');

    const runCrashSimulation = async () => {
        setStressLoading(true);
        try {
            const res = await fetch(`${apiBase}/api/v1/stress-test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index: indexChoice,
                    ref_date: startDate || null,
                    initial_capital: parseFloat(initialCapital) || 1000000,
                    lookback_days: 365,
                    simulation_days: 5,
                }),
            });
            const json = await res.json();
            if (json.status === 'success') {
                setStressResult(json.data);
            }
        } catch (error) {
            console.error('Simulation error:', error);
        } finally {
            setStressLoading(false);
        }
    };

    return {
        stressLoading,
        stressResult,
        indexChoice,
        setIndexChoice,
        startDate,
        setStartDate,
        initialCapital,
        setInitialCapital,
        runCrashSimulation,
    };
}
