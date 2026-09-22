import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { TelegramFollowUpsPanel } from './TelegramFollowUpsPanel';

describe('TelegramFollowUpsPanel', () => {
    it('renders queue summary and dispatches row actions', () => {
        const onProcessReady = jest.fn();
        const onAction = jest.fn();

        render(
            <TelegramFollowUpsPanel
                summary={{
                    configured: true,
                    total: 4,
                    pending_count: 1,
                    ready_count: 1,
                    sent_count: 1,
                    failed_count: 1,
                    suppressed_count: 0,
                    stale_pending_count: 0,
                    destination_counts: { SUBSCRIBER: 1, MAIN_CHANNEL: 1 },
                    service_tier_counts: { SIGNALS_ONLY: 2 },
                    latest_created_at: '2026-04-22T11:00:00',
                }}
                records={[
                    {
                        id: 1,
                        ticker: 'COMI',
                        side: 'BUY',
                        lane: 'swing',
                        trigger_state: 'TP1_HIT',
                        message_type: 'UPDATE',
                        queue_state: 'READY',
                        retry_count: 0,
                        service_tier: 'SIGNALS_ONLY',
                        destination_type: 'SUBSCRIBER',
                        destination_name: 'Type One Client',
                        draft_message: 'HORUS UPDATE COMI TP1 reached.',
                    },
                    {
                        id: 2,
                        ticker: 'HRHO',
                        side: 'BUY',
                        lane: 'intraday',
                        trigger_state: 'STOP_LOSS_HIT',
                        message_type: 'CLOSE',
                        queue_state: 'FAILED',
                        retry_count: 1,
                        service_tier: 'SIGNALS_ONLY',
                        destination_type: 'MAIN_CHANNEL',
                        destination_name: 'Main Telegram Channel',
                        last_error: 'transport down',
                    },
                ]}
                loading={false}
                onProcessReady={onProcessReady}
                onAction={onAction}
            />,
        );

        expect(screen.getByText('Lifecycle Follow-Ups')).toBeInTheDocument();
        expect(screen.getByText('Process Ready Queue')).toBeInTheDocument();
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
        expect(screen.getByText(/SUBSCRIBER: Type One Client/i)).toBeInTheDocument();
        expect(screen.getByText(/MAIN CHANNEL: Main Telegram Channel/i)).toBeInTheDocument();
        expect(screen.getByText(/Destinations: SUBSCRIBER 1/i)).toBeInTheDocument();
        expect(screen.getByText(/Service tiers: SIGNALS ONLY 2/i)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Process Ready Queue/i }));
        fireEvent.click(screen.getByRole('button', { name: /Send Now/i }));
        fireEvent.click(screen.getByRole('button', { name: /Retry/i }));

        expect(onProcessReady).toHaveBeenCalled();
        expect(onAction).toHaveBeenCalledWith(1, 'SEND_NOW');
        expect(onAction).toHaveBeenCalledWith(2, 'RETRY');
    });
});
