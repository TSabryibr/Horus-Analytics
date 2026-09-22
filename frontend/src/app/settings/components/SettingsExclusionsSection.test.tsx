import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';

import { SettingsExclusionsSection } from './SettingsExclusionsSection';

describe('SettingsExclusionsSection', () => {
    it('renders blacklist controls and wires input, autocomplete, add, and remove actions', () => {
        const onInputChange = jest.fn();
        const onAddExclusion = jest.fn();
        const onRemoveExclusion = jest.fn();

        render(
            <SettingsExclusionsSection
                excluded={['COMI', 'HRHO']}
                newExclusion="ET"
                autocompleteOptions={['ETEL']}
                onInputChange={onInputChange}
                onAddExclusion={onAddExclusion}
                onRemoveExclusion={onRemoveExclusion}
            />
        );

        const input = screen.getByPlaceholderText('Search Ticker to Blacklist...');
        fireEvent.change(input, { target: { value: 'swdy' } });
        fireEvent.keyDown(input, { key: 'Enter' });
        fireEvent.click(screen.getByText('ETEL'));

        const comiChip = screen.getByText('COMI').closest('span');
        if (!comiChip) {
            throw new Error('COMI chip missing');
        }
        fireEvent.click(within(comiChip).getByRole('button'));

        expect(onInputChange).toHaveBeenCalledWith('SWDY');
        expect(onAddExclusion).toHaveBeenCalledWith('ET');
        expect(onAddExclusion).toHaveBeenCalledWith('ETEL');
        expect(onRemoveExclusion).toHaveBeenCalledWith('COMI');
    });

    it('renders the empty-state copy when no exclusions exist', () => {
        render(
            <SettingsExclusionsSection
                excluded={[]}
                newExclusion=""
                autocompleteOptions={[]}
                onInputChange={jest.fn()}
                onAddExclusion={jest.fn()}
                onRemoveExclusion={jest.fn()}
            />
        );

        expect(screen.getByText('No exclusions set.')).toBeInTheDocument();
    });
});
