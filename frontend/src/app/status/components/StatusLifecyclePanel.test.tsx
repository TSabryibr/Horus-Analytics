import { render, screen } from '@testing-library/react';

import { StatusLifecyclePanel } from './StatusLifecyclePanel';

describe('StatusLifecyclePanel', () => {
    it('renders lifecycle monitor summary values', () => {
        render(
            <StatusLifecyclePanel
                signalDesk={{
                    queued_candidate_count: 60,
                    lanes: { intraday: 52, swing: 8, position: 0 },
                }}
                lifecycle={{
                    total: 18,
                    active_count: 5,
                    ambiguous_count: 2,
                    stale_active_count: 1,
                    monitor_status: 'ATTENTION',
                    latest_published_at: '2026-04-22T12:00:00',
                }}
                followups={{
                    total: 9,
                    pending_count: 2,
                    ready_count: 1,
                    failed_count: 1,
                    suppressed_count: 1,
                    stale_pending_count: 1,
                    destination_counts: { SUBSCRIBER: 6, MAIN_CHANNEL: 3 },
                    service_tier_counts: { SIGNALS_ONLY: 9 },
                    latest_created_at: '2026-04-22T13:00:00',
                }}
            />
        );

        expect(screen.getByText('Signal Lifecycle + Queue')).toBeInTheDocument();
        expect(screen.getByText('ATTENTION')).toBeInTheDocument();
        expect(screen.getByText('Candidate Queue')).toBeInTheDocument();
        expect(screen.getByText('60')).toBeInTheDocument();
        expect(screen.getByText(/Intraday 52 \/ Swing 8 \/ Position 0/i)).toBeInTheDocument();
        expect(screen.getAllByText('18').length).toBeGreaterThan(0);
        expect(screen.getAllByText('5').length).toBeGreaterThan(0);
        expect(screen.getAllByText('2').length).toBeGreaterThan(0);
        expect(screen.getAllByText('1').length).toBeGreaterThan(0);
        expect(screen.getByText(/2026-04-22T12:00:00/)).toBeInTheDocument();
        expect(screen.getByText('Follow-Up Queue')).toBeInTheDocument();
        expect(screen.getByText('9 Jobs')).toBeInTheDocument();
        expect(screen.getByText(/2026-04-22T13:00:00/)).toBeInTheDocument();
        expect(screen.getByText(/Destinations: SUBSCRIBER 6/i)).toBeInTheDocument();
        expect(screen.getByText(/Service tiers: SIGNALS ONLY 9/i)).toBeInTheDocument();
    });

    it('surfaces disabled follow-up processing as an explicit queue state', () => {
        render(
            <StatusLifecyclePanel
                signalDesk={{ queued_candidate_count: 0 }}
                lifecycle={{ configured: true, total: 0, monitor_status: 'READY' }}
                followups={{
                    configured: false,
                    total: 0,
                    pending_count: 0,
                    ready_count: 0,
                    failed_count: 0,
                    suppressed_count: 0,
                    stale_pending_count: 0,
                }}
            />
        );

        expect(screen.getByText('FOLLOWUPS_DISABLED')).toBeInTheDocument();
        expect(screen.getByText(/Follow-up processing is not configured/i)).toBeInTheDocument();
    });
});
