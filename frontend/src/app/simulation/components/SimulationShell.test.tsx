import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { SimulationShell } from './SimulationShell';

describe('SimulationShell', () => {
    it('renders the header, tab buttons, and forwards tab changes', () => {
        const onSelectTab = jest.fn();

        const now = new Date();
        render(
            <SimulationShell tab="CRASH" onSelectTab={onSelectTab} wsConnected={true} lastUpdated={now}>
                <div data-testid="simulation-shell-children" />
            </SimulationShell>
        );

        expect(screen.getByRole('heading', { name: /Quant Simulator/i })).toBeInTheDocument();
        expect(screen.getByText('⚡ WS LIVE')).toBeInTheDocument();
        expect(screen.getByText('0s ago')).toBeInTheDocument();
        expect(screen.getAllByText('Operational Fire Drills').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Portfolio Risk Lab').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Strategy Validation Lab').length).toBeGreaterThan(0);
        expect(screen.getByRole('button', { name: /Black Swan Crash/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Ragnarok Total Liquidation/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Trade History Monte Carlo/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /^Backtest$/i })).toBeInTheDocument();
        expect(screen.getByTestId('simulation-shell-children')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Ragnarok Total Liquidation/i }));
        fireEvent.click(screen.getByRole('button', { name: /Trade History Monte Carlo/i }));

        expect(onSelectTab).toHaveBeenCalledWith('RAGNAROK');
        expect(onSelectTab).toHaveBeenCalledWith('STRATEGY');
    });
});
