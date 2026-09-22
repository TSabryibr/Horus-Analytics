import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { SettingsOperationsSection } from './SettingsOperationsSection';

describe('SettingsOperationsSection', () => {
    it('renders operations UI and wires backfill/reset actions', () => {
        const onBackfill = jest.fn();
        const onHardReset = jest.fn();

        render(
            <SettingsOperationsSection
                saving={false}
                operationLoading={false}
                backfillTradingDays={126}
                backfill={{ status: 'IDLE', current_day: null, progress: 0, total_days: 0, signals_found: 0, universe_choice: 'FULL', error: null }}
                backfillUniverseChoice="FULL"
                onBackfillUniverseChoiceChange={jest.fn()}
                onBackfillTradingDaysChange={jest.fn()}
                onBackfill={onBackfill}
                onHardReset={onHardReset}
            />
        );

        expect(screen.getByRole('heading', { name: /Historical Backfill/i })).toBeInTheDocument();
        expect(screen.getByDisplayValue('126')).toBeInTheDocument();
        expect(screen.getByDisplayValue('FULL')).toBeInTheDocument();
        expect(screen.getByText(/run backfill manually when needed/i)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Run Backfill/i }));
        fireEvent.click(screen.getByRole('button', { name: /Hard Reset Data/i }));

        expect(onBackfill).toHaveBeenCalled();
        expect(onHardReset).toHaveBeenCalled();
    });

    it('shows running and error states with correct button disabling', () => {
        const { rerender } = render(
            <SettingsOperationsSection
                saving={false}
                operationLoading={false}
                backfillTradingDays={252}
                backfill={{ status: 'RUNNING', current_day: '2026-03-01', progress: 1, total_days: 3, signals_found: 4, universe_choice: 'EGX100', error: null }}
                backfillUniverseChoice="EGX100"
                onBackfillUniverseChoiceChange={jest.fn()}
                onBackfillTradingDaysChange={jest.fn()}
                onBackfill={jest.fn()}
                onHardReset={jest.fn()}
            />
        );

        expect(screen.getByText(/Analyzing/i)).toBeInTheDocument();
        expect(screen.getByText(/universe EGX100/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Running/i })).toBeDisabled();

        rerender(
            <SettingsOperationsSection
                saving={false}
                operationLoading={true}
                backfillTradingDays={252}
                backfill={{ status: 'ERROR', current_day: null, progress: 0, total_days: 0, signals_found: 0, universe_choice: 'EGX100', error: 'boom' }}
                backfillUniverseChoice="EGX100"
                onBackfillUniverseChoiceChange={jest.fn()}
                onBackfillTradingDaysChange={jest.fn()}
                onBackfill={jest.fn()}
                onHardReset={jest.fn()}
            />
        );

        expect(screen.getByText(/Backfill failed for EGX100:/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Hard Reset Data/i })).toBeDisabled();
    });

    it('shows warning state when provisioning completes with reduced coverage', () => {
        render(
            <SettingsOperationsSection
                saving={false}
                operationLoading={false}
                backfillTradingDays={252}
                backfill={{
                    status: 'COMPLETED_WITH_WARNINGS',
                    current_day: '2026-03-02',
                    progress: 199,
                    total_days: 200,
                    signals_found: 7,
                    universe_choice: 'EGX70',
                    error: 'Short historical coverage',
                }}
                backfillUniverseChoice="EGX70"
                onBackfillUniverseChoiceChange={jest.fn()}
                onBackfillTradingDaysChange={jest.fn()}
                onBackfill={jest.fn()}
                onHardReset={jest.fn()}
            />
        );

        expect(screen.getByText(/complete with limited coverage - EGX70/i)).toBeInTheDocument();
        expect(screen.getByText(/Short historical coverage/i)).toBeInTheDocument();
        expect(screen.queryByText(/completed with warnings/i)).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Run Backfill/i })).toBeEnabled();
    });
});
