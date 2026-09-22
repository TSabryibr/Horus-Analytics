import { fireEvent, render, screen } from '@testing-library/react';

import { StrategyShell } from './StrategyShell';

describe('StrategyShell', () => {
    it('renders the page chrome and dispatches mode/refresh actions', () => {
        const onToggleManualMode = jest.fn();
        const onRefresh = jest.fn();

        const now = new Date();
        render(
            <StrategyShell
                isLoading={false}
                manualMode={false}
                onRefresh={onRefresh}
                onToggleManualMode={onToggleManualMode}
                activeRegime="Bullish Expansion"
                riskBudget="🛡️ 2.5% ATR"
                wsConnected={true}
                lastUpdated={now}
            >
                <div>strategy-body</div>
            </StrategyShell>,
        );

        expect(screen.getByText('Strategy Configuration')).toBeInTheDocument();
        expect(screen.getByText('⚡ WS LIVE')).toBeInTheDocument();
        expect(screen.getByText('0s ago')).toBeInTheDocument();
        expect(screen.getByText('🟢 BULLISH EXPANSION')).toBeInTheDocument();
        expect(screen.getByText('🛡️ 2.5% ATR')).toBeInTheDocument();
        expect(screen.getByText(/Dynamic strategy adaptation/i)).toBeInTheDocument();
        expect(screen.getByText('strategy-body')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /AI Mode/i }));
        fireEvent.click(screen.getByLabelText('refresh-strategy'));

        expect(onToggleManualMode).toHaveBeenCalledTimes(1);
        expect(onRefresh).toHaveBeenCalledTimes(1);
    });

    it('renders success and error toasts and disables refresh while loading', () => {
        render(
            <StrategyShell
                isLoading
                manualMode
                onRefresh={jest.fn()}
                onToggleManualMode={jest.fn()}
                successMsg="Manual Overrides Applied!"
                errorMsg="Validation failed."
            >
                <div>strategy-body</div>
            </StrategyShell>,
        );

        expect(screen.getByText('Manual Overrides Applied!')).toBeInTheDocument();
        expect(screen.getByText('Validation failed.')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Manual Mode/i })).toBeInTheDocument();
        expect(screen.getByLabelText('refresh-strategy')).toBeDisabled();
    });
});
