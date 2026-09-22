import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import type { MonteCarloResult } from '../hooks/useStrategyMonteCarlo';
import { StrategyMonteCarloPanel } from './StrategyMonteCarloPanel';

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

describe('StrategyMonteCarloPanel', () => {
    it('forwards control changes and renders Monte Carlo results', () => {
        const setMcCapital = jest.fn();
        const setMcSims = jest.fn();
        const onSimulate = jest.fn();
        const result: MonteCarloResult = {
            simulations: 5000,
            median_equity: 110000,
            worst_case_equity: 70000,
            best_case_equity: 180000,
            avg_max_drawdown: 12,
            median_max_drawdown: 10,
            worst_max_drawdown: 24,
            loss_probability: 12,
            ruin_probability: 4.5,
            ruin_threshold_pct: 50,
            ruin_floor: 50000,
            drawdown_probability_20: 15,
            drawdown_probability_50: 1.2,
            plot_paths: [[1, 2, 3]],
        };

        render(
            <StrategyMonteCarloPanel
                mcLoading={false}
                mcResult={result}
                mcError={null}
                mcCapital="100000"
                setMcCapital={setMcCapital}
                mcSims="2000"
                setMcSims={setMcSims}
                mcRuinThreshold="50"
                setMcRuinThreshold={jest.fn()}
                mcChartData={[{ name: 0, p0: 1 }]}
                onSimulate={onSimulate}
            />
        );

        fireEvent.change(screen.getByLabelText(/Strategy Capital/i), { target: { value: '250000' } });
        fireEvent.change(screen.getByLabelText(/Sim Cycles/i), { target: { value: '5000' } });
        fireEvent.click(screen.getByRole('button', { name: /EXECUTE_ANALYSIS/i }));

        expect(setMcCapital).toHaveBeenCalledWith('250000');
        expect(setMcSims).toHaveBeenCalledWith('5000');
        expect(onSimulate).toHaveBeenCalled();
        expect(screen.getByText('Monte Carlo Strategy Paths')).toBeInTheDocument();
        expect(screen.getByText('Simulation Metadata')).toBeInTheDocument();
        expect(screen.queryByText('OPTIMIZED')).not.toBeInTheDocument();
        expect(screen.queryByText('99.8%')).not.toBeInTheDocument();
    });
});
