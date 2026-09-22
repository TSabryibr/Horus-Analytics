import { fireEvent, render, screen } from '@testing-library/react';

import { AuditFollowUpsPanel } from './AuditFollowUpsPanel';

describe('AuditFollowUpsPanel', () => {
    it('renders follow-up rows and dispatches queue actions', () => {
        const onAction = jest.fn();

        render(
            <AuditFollowUpsPanel
                loading={false}
                summary={{
                    pending_count: 1,
                    ready_count: 1,
                    failed_count: 1,
                    suppressed_count: 1,
                    destination_counts: { SUBSCRIBER: 1, MAIN_CHANNEL: 1 },
                    service_tier_counts: { SIGNALS_ONLY: 2 },
                }}
                rows={[
                    { id: 1, ticker: 'COMI', trigger_state: 'TP1_HIT', queue_state: 'READY', message_type: 'UPDATE', lane: 'swing', retry_count: 0, service_tier: 'SIGNALS_ONLY', destination_type: 'SUBSCRIBER', destination_name: 'Type One Client' },
                    { id: 2, ticker: 'HRHO', trigger_state: 'STOP_LOSS_HIT', queue_state: 'FAILED', message_type: 'CLOSE', lane: 'intraday', retry_count: 1, last_error: 'transport down', service_tier: 'SIGNALS_ONLY', destination_type: 'MAIN_CHANNEL', destination_name: 'Main Telegram Channel' },
                ]}
                onAction={onAction}
            />,
        );

        expect(screen.getByText('Follow-Up Delivery Ledger')).toBeInTheDocument();
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
        expect(screen.getByText(/Destinations: SUBSCRIBER 1/i)).toBeInTheDocument();
        expect(screen.getByText(/SUBSCRIBER: Type One Client/i)).toBeInTheDocument();
        expect(screen.getByText(/MAIN CHANNEL: Main Telegram Channel/i)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Send Now/i }));
        fireEvent.click(screen.getByRole('button', { name: /Retry/i }));

        expect(onAction).toHaveBeenCalledWith(1, 'SEND_NOW');
        expect(onAction).toHaveBeenCalledWith(2, 'RETRY');
    });
});
