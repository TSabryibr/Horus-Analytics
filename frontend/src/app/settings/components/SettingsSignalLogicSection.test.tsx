import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { SettingsSignalLogicSection } from './SettingsSignalLogicSection';

describe('SettingsSignalLogicSection', () => {
    it('renders signal logic controls and wires updates', () => {
        const onChange = jest.fn();

        render(
            <SettingsSignalLogicSection
                settings={{
                    LOOKBACK: 40,
                    RSI_MIN: 55,
                    RSI_MAX: 85,
                    MOMENTUM: 2.5,
                    VOL_SPIKE: 1.5,
                    MIN_SIGNAL_SCORE: 0,
                    MIN_SIGNAL_CONFIDENCE: 0,
                    TRICKSTER_RSI_MAX: 30,
                    TRICKSTER_REL_VOL_MIN: 1.2,
                    TRICKSTER_STRETCH_ATR: 2,
                }}
                onChange={onChange}
            />
        );

        fireEvent.change(screen.getByDisplayValue('40'), { target: { value: '55' } });
        fireEvent.change(screen.getByDisplayValue('55'), { target: { value: '60' } });
        fireEvent.change(screen.getByDisplayValue('85'), { target: { value: '90' } });
        fireEvent.change(screen.getByDisplayValue('2.5'), { target: { value: '3.1' } });
        fireEvent.change(screen.getByDisplayValue('1.5'), { target: { value: '2.0' } });
        const zeroFields = screen.getAllByDisplayValue('0');
        fireEvent.change(zeroFields[0], { target: { value: '6.5' } });
        fireEvent.change(zeroFields[1], { target: { value: '72.5' } });
        fireEvent.change(screen.getByDisplayValue('30'), { target: { value: '28' } });
        fireEvent.change(screen.getByDisplayValue('1.2'), { target: { value: '1.4' } });
        fireEvent.change(screen.getByDisplayValue('2'), { target: { value: '2.3' } });

        expect(onChange).toHaveBeenCalledWith('LOOKBACK', 55);
        expect(onChange).toHaveBeenCalledWith('RSI_MIN', 60);
        expect(onChange).toHaveBeenCalledWith('RSI_MAX', 90);
        expect(onChange).toHaveBeenCalledWith('MOMENTUM', 3.1);
        expect(onChange).toHaveBeenCalledWith('VOL_SPIKE', 2);
        expect(onChange).toHaveBeenCalledWith('MIN_SIGNAL_SCORE', 6.5);
        expect(onChange).toHaveBeenCalledWith('MIN_SIGNAL_CONFIDENCE', 72.5);
        expect(onChange).toHaveBeenCalledWith('TRICKSTER_RSI_MAX', 28);
        expect(onChange).toHaveBeenCalledWith('TRICKSTER_REL_VOL_MIN', 1.4);
        expect(onChange).toHaveBeenCalledWith('TRICKSTER_STRETCH_ATR', 2.3);
    });
});
