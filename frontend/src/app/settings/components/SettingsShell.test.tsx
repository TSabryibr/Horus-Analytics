import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import { SettingsShell } from './SettingsShell';

describe('SettingsShell', () => {
    it('renders the loading state before the settings shell is ready', () => {
        render(
            <SettingsShell loading={true} message="" saving={false} hasChanges={false} onSave={jest.fn()}>
                <div>ignored</div>
            </SettingsShell>
        );

        expect(screen.getByText('Loading configuration...')).toBeInTheDocument();
        expect(screen.queryByText('Settings Command Deck')).not.toBeInTheDocument();
    });

    it('renders the shell chrome, message banner, and save action', async () => {
        const onSave = jest.fn();

        render(
            <SettingsShell
                loading={false}
                message="Configuration Saved Successfully!"
                saving={false}
                hasChanges={true}
                onSave={onSave}
            >
                <div data-testid="settings-content">Settings content</div>
            </SettingsShell>
        );

        expect(screen.getByRole('heading', { name: 'Settings Command Deck' })).toBeInTheDocument();
        expect(screen.getByText('Runtime, delivery, and market policy orchestration for the local Horus stack.')).toBeInTheDocument();
        expect(screen.getByText('Configuration Saved Successfully!')).toBeInTheDocument();
        expect(screen.getByTestId('settings-content')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
        expect(screen.getByRole('dialog')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: /Confirm & Apply Changes/i }));

        await waitFor(() => expect(onSave).toHaveBeenCalled());
        await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    });

    it('disables the save button when nothing changed or a save is in progress', () => {
        const { rerender } = render(
            <SettingsShell loading={false} message="" saving={false} hasChanges={false} onSave={jest.fn()}>
                <div />
            </SettingsShell>
        );

        expect(screen.getByRole('button', { name: /Save Changes/i })).toBeDisabled();

        rerender(
            <SettingsShell loading={false} message="" saving={true} hasChanges={true} onSave={jest.fn()}>
                <div />
            </SettingsShell>
        );

        expect(screen.getByRole('button', { name: /Committing/i })).toBeDisabled();
    });
});
