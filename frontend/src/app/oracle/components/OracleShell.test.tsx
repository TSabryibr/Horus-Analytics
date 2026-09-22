import { fireEvent, render, screen } from '@testing-library/react';

import { OracleShell } from './OracleShell';

describe('OracleShell', () => {
    it('renders the page chrome and dispatches refresh clicks', () => {
        const onRefresh = jest.fn();

        render(
            <OracleShell isLoading={false} onRefresh={onRefresh} selectedTicker="CIIC" isHistorical={false}>
                <div>oracle-body</div>
            </OracleShell>
        );

        expect(screen.getByText('AI Price Forecast')).toBeInTheDocument();
        expect(screen.getByText('CIIC')).toBeInTheDocument();
        expect(screen.getByText('oracle-body')).toBeInTheDocument();

        fireEvent.click(screen.getByLabelText('refresh-oracle'));
        expect(onRefresh).toHaveBeenCalledTimes(1);
    });

    it('disables refresh while loading', () => {
        render(
            <OracleShell isLoading onRefresh={jest.fn()} selectedTicker="CIIC" isHistorical>
                <div>oracle-body</div>
            </OracleShell>
        );

        expect(screen.getByLabelText('refresh-oracle')).toBeDisabled();
    });
});
