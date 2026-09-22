import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { TelegramBroadcastPanel } from './TelegramBroadcastPanel';

describe('TelegramBroadcastPanel', () => {
    it('renders the broadcast composer and forwards actions', () => {
        const setMessage = jest.fn();
        const setImage = jest.fn();
        const onBroadcast = jest.fn();

        render(
            <TelegramBroadcastPanel
                message="Ready to send"
                image={null}
                sending={false}
                setMessage={setMessage}
                setImage={setImage}
                onBroadcast={onBroadcast}
            />
        );

        fireEvent.change(screen.getByPlaceholderText(/Type an announcement/i), {
            target: { value: 'Broadcast body' },
        });
        fireEvent.click(screen.getByRole('button', { name: /Blast Broadcast/i }));

        expect(setMessage).toHaveBeenCalledWith('Broadcast body');
        expect(onBroadcast).toHaveBeenCalled();
    });
});
