import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { TelegramConfigModal } from './TelegramConfigModal';

describe('TelegramConfigModal', () => {
    it('renders config toggles and forwards submit/close actions', () => {
        const setConfigForm = jest.fn();
        const onClose = jest.fn();
        const onSubmit = jest.fn((event) => event.preventDefault());

        render(
            <TelegramConfigModal
                isOpen
                sending={false}
                configForm={{
                    auto_intraday: true,
                    auto_daily: true,
                    auto_horus_eye: true,
                    auto_ai_daily_report: true,
                    auto_weekly_report: false,
                    auto_monthly_report: false,
                }}
                setConfigForm={setConfigForm}
                onClose={onClose}
                onSubmit={onSubmit}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /Close telegram configuration/i }));
        fireEvent.click(screen.getByText(/Broadcast Intraday Scans/i));
        fireEvent.click(screen.getByRole('button', { name: /Establish Connection/i }));

        expect(onClose).toHaveBeenCalled();
        expect(setConfigForm).toHaveBeenCalledWith(
            expect.objectContaining({
                auto_intraday: false,
            })
        );
        expect(onSubmit).toHaveBeenCalled();
    });
});
