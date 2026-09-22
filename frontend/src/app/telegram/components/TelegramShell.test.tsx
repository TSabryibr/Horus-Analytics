import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { TelegramShell } from './TelegramShell';

describe('TelegramShell', () => {
    it('renders the shell chrome and forwards the config action', () => {
        const onOpenConfig = jest.fn();

        render(
            <TelegramShell
                onOpenConfig={onOpenConfig}
                statusNode={<div>CHANNEL ONLINE</div>}
            >
                <div>telegram body</div>
            </TelegramShell>
        );

        expect(screen.getByText('Telegram Release Chamber')).toBeInTheDocument();
        expect(screen.getByText('Royal Release Desk')).toBeInTheDocument();
        expect(screen.getByText(/Official Horus outbound authority/i)).toBeInTheDocument();
        expect(screen.getByText('CHANNEL ONLINE')).toBeInTheDocument();
        expect(screen.getByText('telegram body')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Configure Channel/i }));

        expect(onOpenConfig).toHaveBeenCalled();
    });
});
