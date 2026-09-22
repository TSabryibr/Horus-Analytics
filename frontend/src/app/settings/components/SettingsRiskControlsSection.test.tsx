import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';

import { SettingsRiskControlsSection } from './SettingsRiskControlsSection';

describe('SettingsRiskControlsSection', () => {
    it('renders risk controls and wires numeric/toggle updates', () => {
        const onChange = jest.fn();

        render(
            <SettingsRiskControlsSection
                settings={{
                    SL_PCT: 1.5,
                    SLIPPAGE_PCT: 0.5,
                    COMMISSION_PCT: 0.05,
                    TP1_PCT: 4,
                    MIN_TURNOVER: 2000000,
                    MAX_POSITIONS: 10,
                    RISK_PER_TRADE: 2,
                    MIN_RISK_REWARD: 1,
                    MAX_DAILY_TRADES: 3,
                    MAX_PORTFOLIO_HEAT: 6,
                    PENDING_ENTRY_MAX_GAP_PCT: 2.2,
                    USE_ATR_EXITS: false,
                    AUTO_TRADE_ENABLED: false,
                    SIGNAL_AUTO_EXECUTION_ENABLED: false,
                    LIVE_ARM_GUARD_ENABLED: false,
                    TRAILING_STOP_ENABLED: false,
                    REGIME_FILTER_ENABLED: false,
                    SECTOR_LIMIT_ENABLED: false,
                }}
                onChange={onChange}
            />
        );

        fireEvent.change(screen.getByDisplayValue('1.5'), { target: { value: '2.0' } });
        fireEvent.change(screen.getByDisplayValue('0.5'), { target: { value: '0.7' } });
        fireEvent.change(screen.getByDisplayValue('4'), { target: { value: '5' } });
        fireEvent.change(screen.getByDisplayValue('2000000'), { target: { value: '2500000' } });
        fireEvent.change(screen.getByDisplayValue('0.05'), { target: { value: '0.08' } });
        fireEvent.change(screen.getByDisplayValue('1'), { target: { value: '1.6' } });
        fireEvent.change(screen.getByDisplayValue('3'), { target: { value: '5' } });
        fireEvent.change(screen.getByDisplayValue('6'), { target: { value: '7.5' } });
        fireEvent.change(screen.getByDisplayValue('2.2'), { target: { value: '1.8' } });

        const atrContainer = screen.getByText('Use ATR Exits').closest('.flex.items-center.justify-between');
        const autoContainer = screen.getByText('Auto Trading').closest('.flex.items-center.justify-between');
        const signalExecutionContainer = screen.getByText('Signal Auto Execution').closest('.flex.items-center.justify-between');
        const liveGuardContainer = screen.getByText('Require Daily Manual Arm').closest('.flex.items-center.justify-between');
        const trailingContainer = screen.getByText('Trailing Stop').closest('.flex.items-center.justify-between');
        const regimeContainer = screen.getByText('Regime Filter').closest('.flex.items-center.justify-between');
        const sectorContainer = screen.getByText('Sector Limit').closest('.flex.items-center.justify-between');
        if (!atrContainer || !autoContainer || !signalExecutionContainer || !liveGuardContainer || !trailingContainer || !regimeContainer || !sectorContainer) {
            throw new Error('Toggle containers missing');
        }
        fireEvent.click(within(atrContainer).getByRole('checkbox'));
        fireEvent.click(within(autoContainer).getByRole('checkbox'));
        fireEvent.click(within(signalExecutionContainer).getByRole('checkbox'));
        fireEvent.click(within(liveGuardContainer).getByRole('checkbox'));
        fireEvent.click(within(trailingContainer).getByRole('checkbox'));
        fireEvent.click(within(regimeContainer).getByRole('checkbox'));
        fireEvent.click(within(sectorContainer).getByRole('checkbox'));

        expect(onChange).toHaveBeenCalledWith('SL_PCT', 2);
        expect(onChange).toHaveBeenCalledWith('SLIPPAGE_PCT', 0.7);
        expect(onChange).toHaveBeenCalledWith('TP1_PCT', 5);
        expect(onChange).toHaveBeenCalledWith('MIN_TURNOVER', 2500000);
        expect(onChange).toHaveBeenCalledWith('COMMISSION_PCT', 0.08);
        expect(onChange).toHaveBeenCalledWith('MIN_RISK_REWARD', 1.6);
        expect(onChange).toHaveBeenCalledWith('MAX_DAILY_TRADES', 5);
        expect(onChange).toHaveBeenCalledWith('MAX_PORTFOLIO_HEAT', 7.5);
        expect(onChange).toHaveBeenCalledWith('PENDING_ENTRY_MAX_GAP_PCT', 1.8);
        expect(onChange).toHaveBeenCalledWith('USE_ATR_EXITS', true);
        expect(onChange).toHaveBeenCalledWith('AUTO_TRADE_ENABLED', true);
        expect(onChange).toHaveBeenCalledWith('SIGNAL_AUTO_EXECUTION_ENABLED', true);
        expect(onChange).toHaveBeenCalledWith('LIVE_ARM_GUARD_ENABLED', true);
        expect(onChange).toHaveBeenCalledWith('TRAILING_STOP_ENABLED', true);
        expect(onChange).toHaveBeenCalledWith('REGIME_FILTER_ENABLED', true);
        expect(onChange).toHaveBeenCalledWith('SECTOR_LIMIT_ENABLED', true);
    });

    it('shows that signal auto execution blocks entries even when auto trading is enabled', () => {
        render(
            <SettingsRiskControlsSection
                settings={{
                    AUTO_TRADE_ENABLED: true,
                    SIGNAL_AUTO_EXECUTION_ENABLED: false,
                    LIVE_ARM_GUARD_ENABLED: false,
                }}
                onChange={jest.fn()}
            />
        );

        expect(screen.getAllByText('SIGNAL_EXEC_OFF').length).toBeGreaterThan(0);
        expect(screen.getByText(/Execution monitor will skip signal entries/i)).toBeInTheDocument();
    });

    it('shows ATR fields when ATR exits are enabled', () => {
        render(
            <SettingsRiskControlsSection
                settings={{
                    USE_ATR_EXITS: true,
                    ATR_TP_MULTIPLIER: 2,
                    ATR_SL_MULTIPLIER: 1,
                }}
                onChange={jest.fn()}
            />
        );

        expect(screen.getByText('ATR TP Mult.')).toBeInTheDocument();
        expect(screen.getByText('ATR SL Mult.')).toBeInTheDocument();
    });

    it('shows trailing and sector fields when toggles are enabled', () => {
        render(
            <SettingsRiskControlsSection
                settings={{
                    TRAILING_STOP_ENABLED: true,
                    TRAILING_STOP_TYPE: 'FIXED',
                    TRAILING_STOP_VALUE: 2.0,
                    SECTOR_LIMIT_ENABLED: true,
                    MAX_PER_SECTOR: 2,
                }}
                onChange={jest.fn()}
            />
        );

        expect(screen.getByText('Trailing Type')).toBeInTheDocument();
        expect(screen.getByText('Trailing Value')).toBeInTheDocument();
        expect(screen.getByText('Max Per Sector')).toBeInTheDocument();
    });
});
