import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { TelegramActivityLog } from './TelegramActivityLog';

describe('TelegramActivityLog', () => {
    it('renders log lines and forwards clear action', () => {
        const onClear = jest.fn();

        render(
            <TelegramActivityLog
                log={[
                    '[10:15:00] ✅ Sent successfully',
                    '[10:14:00] ❌ Failed to send',
                ]}
                onClear={onClear}
                logEndRef={{ current: null }}
            />
        );

        expect(screen.getByText(/Sent successfully/i)).toBeInTheDocument();
        expect(screen.getByText(/Failed to send/i)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Clear/i }));

        expect(onClear).toHaveBeenCalled();
    });

    it('renders standby state when log is empty', () => {
        render(<TelegramActivityLog log={[]} onClear={jest.fn()} logEndRef={{ current: null }} />);

        expect(screen.getByText('Standby...')).toBeInTheDocument();
    });
});
