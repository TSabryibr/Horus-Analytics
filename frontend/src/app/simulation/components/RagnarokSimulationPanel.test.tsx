import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import type { RagnarokResult } from '../hooks/useRagnarokSimulation';
import { RagnarokSimulationPanel } from './RagnarokSimulationPanel';

jest.mock('recharts', () => {
    const MockContainer = () => <div data-testid="mock-recharts-container" />;
    return {
        ResponsiveContainer: MockContainer,
        LineChart: MockContainer,
        Line: () => null,
        XAxis: () => null,
        YAxis: () => null,
        Tooltip: () => null,
        CartesianGrid: () => null,
    };
});

describe('RagnarokSimulationPanel', () => {
    it('forwards control changes and renders result metrics', () => {
        const setTickerInput = jest.fn();
        const setRagnarokIterations = jest.fn();
        const setRagnarokDays = jest.fn();
        const setRagnarokStartingValue = jest.fn();
        const setRagnarokRuinThresholdPct = jest.fn();
        const onSimulate = jest.fn();
        const result: RagnarokResult = {
            expected_value: 1050000,
            var_95: 820000,
            loss_probability: 22.5,
            ruin_probability: 15.5,
            starting_value: 1000000,
            ruin_threshold_pct: 50,
            ruin_floor: 500000,
            iterations: 1000,
            days: 20,
            assets_count: 2,
            assets_used: ['COMI', 'ETEL'],
            plot_paths: [[1, 2, 3]],
        };

        render(
            <RagnarokSimulationPanel
                ragnarokLoading={false}
                ragnarokResult={result}
                ragnarokError={null}
                ragnarokIterations="1000"
                setRagnarokIterations={setRagnarokIterations}
                ragnarokDays="20"
                setRagnarokDays={setRagnarokDays}
                ragnarokStartingValue=""
                setRagnarokStartingValue={setRagnarokStartingValue}
                ragnarokRuinThresholdPct="50"
                setRagnarokRuinThresholdPct={setRagnarokRuinThresholdPct}
                tickerInput=""
                setTickerInput={setTickerInput}
                ragnarokChartData={[{ name: 0, p0: 1 }]}
                onSimulate={onSimulate}
            />
        );

        fireEvent.change(screen.getByLabelText(/Universe Tickers/i), { target: { value: 'COMI, ETEL' } });
        fireEvent.change(screen.getByLabelText(/^Cycles$/i), { target: { value: '500' } });
        fireEvent.change(screen.getByLabelText(/Horizon \(Days\)/i), { target: { value: '10' } });
        fireEvent.change(screen.getByLabelText(/Starting Value \(EGP\)/i), { target: { value: '2500000' } });
        fireEvent.change(screen.getByLabelText(/Ruin Threshold \(%\)/i), { target: { value: '40' } });
        fireEvent.click(screen.getByRole('button', { name: /EXECUTE_ANALYSIS/i }));

        expect(setTickerInput).toHaveBeenCalledWith('COMI, ETEL');
        expect(setRagnarokIterations).toHaveBeenCalledWith('500');
        expect(setRagnarokDays).toHaveBeenCalledWith('10');
        expect(setRagnarokStartingValue).toHaveBeenCalledWith('2500000');
        expect(setRagnarokRuinThresholdPct).toHaveBeenCalledWith('40');
        expect(onSimulate).toHaveBeenCalled();
        expect(screen.getByText('Expected Value')).toBeInTheDocument();
        expect(screen.getByText('Probabilistic Trajectories')).toBeInTheDocument();
    });
});
