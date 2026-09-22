import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { OracleMacroPanel } from './OracleMacroPanel';

jest.mock('recharts', () => {
    const MockContainer = ({ children }: any) => <svg data-testid='mock-recharts-container'>{children}</svg>;
    return {
        ComposedChart: MockContainer,
        Area: () => null,
        Line: () => null,
        XAxis: () => null,
        YAxis: () => null,
        Tooltip: () => null,
        CartesianGrid: () => null,
    };
});

describe('OracleMacroPanel', () => {
    it('renders macro state and allows active-index switching', () => {
        const setActiveIndex = jest.fn();

        render(
            <OracleMacroPanel
                activeIndex="EGX30"
                setActiveIndex={setActiveIndex}
                macro={{ signal: 'BULLISH', correlation: 0.74, message: 'Breadth confirms index trend.' }}
                macroSignalColor="text-emerald-500"
            />
        );

        expect(screen.getByText(/Macro Health \(EGX30\)/)).toBeInTheDocument();
        expect(screen.getByText('BULLISH')).toBeInTheDocument();
        expect(screen.getByText(/Correlation: 0.74/)).toBeInTheDocument();

        fireEvent.click(screen.getByText('EGX70'));
        expect(setActiveIndex).toHaveBeenCalledWith('EGX70');
    });

    it('renders the dual-axis chart when price history is present', () => {
        render(
            <OracleMacroPanel
                activeIndex="EGX30"
                setActiveIndex={jest.fn()}
                macro={{
                    signal: 'BULLISH',
                    correlation: 0.74,
                    message: 'Breadth confirms index trend.',
                    price_history: { '1708128000000': 25000 },
                    breadth_history: { '1708128000000': 58.2 }
                }}
                macroSignalColor="text-emerald-500"
            />
        );

        expect(screen.getByTestId('mock-recharts-container')).toBeInTheDocument();
    });
});
