import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { BacktestLabPanel } from './BacktestLabPanel';

describe('BacktestLabPanel', () => {
    const baseProps = {
        optIndex: 'ALL',
        simLoading: false,
        simParams: {
            RSI_MIN: 55,
            RSI_MAX: 85,
            VOL_SPIKE: 1.5,
            MOMENTUM: 2.5,
            SL_PCT: 1.5,
            TP1_PCT: 4,
            MAX_POSITIONS: 10,
            TRAILING_STOP_ENABLED: false,
            TRAILING_STOP_TYPE: 'PERCENT',
            TRAILING_STOP_VALUE: 2,
        },
        backtestSource: 'HORUS' as const,
        pineProfiles: [],
        pineProfilesLoading: false,
        selectedPineProfileId: null,
        pineRunConfig: {
            market: 'EGX30',
            timeframe: '1D',
            dateFrom: '2026-01-01',
            dateTo: '2026-04-01',
            capital: 100000,
            commissionPct: 0.05,
            slippagePct: 0.1,
        },
        onSelectIndex: jest.fn(),
        onChangeParam: jest.fn(),
        onRunSimulation: jest.fn(),
        onChangeBacktestSource: jest.fn(),
        onSelectPineProfile: jest.fn(),
        onChangePineRunConfig: jest.fn(),
    };

    it('forwards index, parameter, trailing-stop, and run actions', () => {
        const onSelectIndex = jest.fn();
        const onChangeParam = jest.fn();
        const onRunSimulation = jest.fn();

        render(
            <BacktestLabPanel
                {...baseProps}
                onSelectIndex={onSelectIndex}
                onChangeParam={onChangeParam}
                onRunSimulation={onRunSimulation}
            />
        );

        fireEvent.change(screen.getByDisplayValue(/Full Market Matrix/i), { target: { value: 'EGX30' } });
        fireEvent.change(screen.getByLabelText(/RSI Entry/i), { target: { value: '50' } });
        fireEvent.click(screen.getByRole('button', { name: /Toggle trailing stop/i }));
        fireEvent.click(screen.getByRole('button', { name: /Init_Backtest/i }));

        expect(onSelectIndex).toHaveBeenCalledWith('EGX30');
        expect(onChangeParam).toHaveBeenCalledWith(
            expect.objectContaining({
                RSI_MIN: 50,
            })
        );
        expect(onChangeParam).toHaveBeenCalledWith(
            expect.objectContaining({
                TRAILING_STOP_ENABLED: true,
            })
        );
        expect(onRunSimulation).toHaveBeenCalled();
    });

    it('renders Pine profile controls, requires a selection, and shows a draft warning', () => {
        const onSelectPineProfile = jest.fn();
        const pineProfiles = [
            {
                profile_id: 7,
                profile_name: 'Draft Pine Breakout',
                profile_state: 'DRAFT',
                market: 'EGX70',
                timeframe: '1W',
            },
        ];

        const { rerender } = render(
            <BacktestLabPanel
                {...baseProps}
                backtestSource="PINE_PROFILE"
                pineProfiles={pineProfiles}
                onSelectPineProfile={onSelectPineProfile}
            />
        );

        expect(screen.getByText(/Backtest Source/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Pine Profile/i })).toHaveAttribute('aria-pressed', 'true');
        expect(screen.getByLabelText(/Saved Pine Profile/i)).toBeInTheDocument();
        expect(screen.queryByLabelText(/RSI Entry/i)).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Init_Backtest/i })).toBeDisabled();

        fireEvent.change(screen.getByLabelText(/Saved Pine Profile/i), { target: { value: '7' } });
        expect(onSelectPineProfile).toHaveBeenCalledWith(7);

        rerender(
            <BacktestLabPanel
                {...baseProps}
                backtestSource="PINE_PROFILE"
                pineProfiles={pineProfiles}
                selectedPineProfileId={7}
                pineRunConfig={{
                    ...baseProps.pineRunConfig,
                    market: 'EGX70',
                    timeframe: '1W',
                }}
                onSelectPineProfile={onSelectPineProfile}
            />
        );

        expect(screen.getByText(/Draft profile: this Pine strategy has not passed promotion gates yet./i)).toBeInTheDocument();
        expect(screen.getByText(/Logic Source: Draft Pine Breakout/i)).toBeInTheDocument();
        expect(screen.getByDisplayValue(/EGX70/i)).toBeInTheDocument();
        expect(screen.getByDisplayValue(/1W/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Init_Backtest/i })).not.toBeDisabled();
    });
});
