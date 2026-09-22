import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import type { StressResult } from '../hooks/useCrashSimulation';
import { CrashSimulationPanel } from './CrashSimulationPanel';

jest.mock('recharts', () => {
    const MockContainer = () => <div data-testid="mock-recharts-container" />;
    return {
        ResponsiveContainer: MockContainer,
        BarChart: MockContainer,
        Bar: MockContainer,
        XAxis: () => null,
        YAxis: () => null,
        Tooltip: () => null,
        Cell: () => null,
    };
});

describe('CrashSimulationPanel', () => {
    it('forwards control changes and renders crash result sections', () => {
        const setIndexChoice = jest.fn();
        const setStartDate = jest.fn();
        const setInitialCapital = jest.fn();
        const onSimulate = jest.fn();
        const stressResult: StressResult = {
            crash_date: '2020-03-15',
            market_impact: -12.8,
            worst_affected: [{ Ticker: 'COMI', 'Total_Drop_%': -18.2 }],
            least_affected: [{ Ticker: 'HRHO', Current_Price: 37.2, Final_Price: 35.9, 'Total_Drop_%': -3.5 }],
            initial_capital: 2500000,
            ending_capital: 2180000,
        };

        render(
            <CrashSimulationPanel
                stressLoading={false}
                stressResult={stressResult}
                indexChoice="EGX30"
                setIndexChoice={setIndexChoice}
                startDate=""
                setStartDate={setStartDate}
                initialCapital="1000000"
                setInitialCapital={setInitialCapital}
                onSimulate={onSimulate}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'EGX70' }));
        fireEvent.change(screen.getByLabelText(/Ref Date/i), { target: { value: '2020-03-15' } });
        fireEvent.change(screen.getByLabelText(/Base Capital \(EGP\)/i), { target: { value: '2500000' } });
        fireEvent.click(screen.getByRole('button', { name: /EXECUTE_ANALYSIS/i }));

        expect(setIndexChoice).toHaveBeenCalledWith('EGX70');
        expect(setStartDate).toHaveBeenCalledWith('2020-03-15');
        expect(setInitialCapital).toHaveBeenCalledWith('2500000');
        expect(onSimulate).toHaveBeenCalled();
        expect(screen.getByText('Vulnerability Spectrum')).toBeInTheDocument();
        expect(screen.getByText('Defensive Outliers')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
        expect(screen.getByText('Base Capital')).toBeInTheDocument();
        expect(screen.getByText('Projected Ending Capital')).toBeInTheDocument();
    });
});
