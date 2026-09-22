import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { SettingsMarketHoursSection } from './SettingsMarketHoursSection';

describe('SettingsMarketHoursSection', () => {
    it('renders market-hour controls and wires toggle/input changes', () => {
        const onChange = jest.fn();

        render(
            <SettingsMarketHoursSection
                settings={{
                    RAMADAN_MODE: false,
                    MARKET_START_HHMM_NORMAL: '1000',
                    MARKET_END_HHMM_NORMAL: '1430',
                    MARKET_START_HHMM_RAMADAN: '1000',
                    MARKET_END_HHMM_RAMADAN: '1330',
                    PRE_CLOSE_OFFSET_MINS: 20,
                    DAILY_SIGNAL_OFFSET_MINS: 30,
                    INTRADAY_INTERVAL_MINS: 5,
                }}
                onChange={onChange}
            />
        );

        fireEvent.click(screen.getByRole('checkbox'));
        fireEvent.change(screen.getByLabelText(/Pre-Close Offset/i), { target: { value: '25' } });
        fireEvent.change(screen.getByLabelText(/Daily Signal Offset/i), { target: { value: '35' } });
        fireEvent.change(screen.getByLabelText(/Intraday Interval/i), { target: { value: '10' } });
        fireEvent.change(screen.getAllByPlaceholderText('1000')[0], { target: { value: '1030' } });

        expect(onChange).toHaveBeenCalledWith('RAMADAN_MODE', true);
        expect(onChange).toHaveBeenCalledWith('PRE_CLOSE_OFFSET_MINS', 25);
        expect(onChange).toHaveBeenCalledWith('DAILY_SIGNAL_OFFSET_MINS', 35);
        expect(onChange).toHaveBeenCalledWith('INTRADAY_INTERVAL_MINS', 10);
        expect(onChange).toHaveBeenCalledWith('MARKET_START_HHMM_NORMAL', '1030');
    });
});
