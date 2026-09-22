import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

import type { SimulationBacktestResult } from '../hooks/useSimulationBacktest';
import { StrategyBacktestPanel } from './StrategyBacktestPanel';

jest.mock('recharts', () => {
    const MockContainer = () => <div data-testid="mock-recharts-container" />;
    return {
        ResponsiveContainer: MockContainer,
        LineChart: MockContainer,
        Line: MockContainer,
        XAxis: () => null,
        YAxis: () => null,
        Tooltip: () => null,
        CartesianGrid: () => null,
    };
});

describe('StrategyBacktestPanel', () => {
    const mockProps = {
        loading: false,
        error: null,
        result: null,
        strategyCatalog: [
            { strategy_id: 'strat_1', display_name: 'Ascending Triangle' },
            { strategy_id: 'strat_2', display_name: 'Mean Reversion' },
        ],
        strategyId: 'strat_1',
        setStrategyId: jest.fn(),
        market: 'EGX30',
        setMarket: jest.fn(),
        startDate: '2026-01-01',
        setStartDate: jest.fn(),
        endDate: '2026-06-01',
        setEndDate: jest.fn(),
        capital: '1000000',
        setCapital: jest.fn(),
        commission: '0.1',
        setCommission: jest.fn(),
        slippage: '0.2',
        setSlippage: jest.fn(),
        onRun: jest.fn(),
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders input fields with mock values and triggers state updates', () => {
        render(<StrategyBacktestPanel {...mockProps} />);

        // Test Select Strategy
        const selects = screen.getAllByRole('combobox');
        const stratSelect = selects[0];
        expect(stratSelect).toHaveValue('strat_1');
        fireEvent.change(stratSelect, { target: { value: 'strat_2' } });
        expect(mockProps.setStrategyId).toHaveBeenCalledWith('strat_2');

        // Test Date Inputs
        const startInput = screen.getByLabelText(/Backtest Start Date/i);
        expect(startInput).toHaveValue('2026-01-01');
        fireEvent.change(startInput, { target: { value: '2026-01-02' } });
        expect(mockProps.setStartDate).toHaveBeenCalledWith('2026-01-02');

        // Test Numeric Inputs
        const capitalInput = screen.getByLabelText(/Backtest Capital/i);
        expect(capitalInput).toHaveValue(1000000);
        fireEvent.change(capitalInput, { target: { value: '1500000' } });
        expect(mockProps.setCapital).toHaveBeenCalledWith('1500000');
    });

    it('handles simulate execution triggers', () => {
        render(<StrategyBacktestPanel {...mockProps} />);

        const executeButton = screen.getByRole('button', { name: /EXECUTE_ANALYSIS/i });
        fireEvent.click(executeButton);

        expect(mockProps.onRun).toHaveBeenCalled();
    });

    it('renders simulation metrics and equity curve charts when results exist', () => {
        const mockResult: SimulationBacktestResult = {
            strategy_id: 'strat_1',
            market: 'EGX30',
            start_date: '2026-01-01',
            end_date: '2026-06-01',
            capital: 1000000,
            commission: 0.1,
            slippage: 0.2,
            equity_curve: [1000000, 1050000, 1100000, 1235000],
            trades: [],
            total_return: 23.5,
            sharpe: 1.5,
            sortino: 1.8,
            calmar: 2.0,
            max_drawdown: -8.2,
            profit_factor: 1.85,
            expectancy: 0.15,
            win_rate: 62.4,
            trade_count: 10,
        };

        render(<StrategyBacktestPanel {...mockProps} result={mockResult} />);

        expect(screen.getByText('23.50%')).toBeInTheDocument();
        expect(screen.getByText('-8.20%')).toBeInTheDocument();
        expect(screen.getByText('1.85')).toBeInTheDocument();
        expect(screen.getByText('62.40%')).toBeInTheDocument();
        expect(screen.getByTestId('mock-recharts-container')).toBeInTheDocument();
    });
});
