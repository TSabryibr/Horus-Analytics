import { render, screen } from '@testing-library/react';

import { StatusDiagnosticsPanel } from './StatusDiagnosticsPanel';

describe('StatusDiagnosticsPanel', () => {
    it('renders engine metrics and diagnostics console output', () => {
        render(
            <StatusDiagnosticsPanel
                status={{
                    system_ready: true,
                    message: 'Running...',
                    metrics: { total_signals: 314, last_signal_date: '2026-03-17' },
                }}
                lastRefresh={new Date('2026-03-18T12:00:00Z')}
            />
        );

        expect(screen.getByText('Engine Stats')).toBeInTheDocument();
        expect(screen.getByText('314')).toBeInTheDocument();
        expect(screen.getByText('Diagnostics Console')).toBeInTheDocument();
        expect(screen.getByText(/Core State: READY/)).toBeInTheDocument();
        expect(screen.getByText(/Message: Running/)).toBeInTheDocument();
    });

    it('surfaces provisioning failure details in the diagnostics console', () => {
        render(
            <StatusDiagnosticsPanel
                status={{
                    system_ready: false,
                    message: 'Startup provisioning failed.',
                    provisioning_status: 'ERROR',
                    provisioning_error: 'Insufficient historical data coverage',
                    metrics: { total_signals: 0, last_signal_date: null },
                }}
                lastRefresh={new Date('2026-03-18T12:00:00Z')}
            />
        );

        expect(screen.getByText(/Core State: PROVISIONING_ERROR/)).toBeInTheDocument();
        expect(screen.getByText(/Provisioning Error: Insufficient historical data coverage/i)).toBeInTheDocument();
        expect(screen.queryByText(/System readiness check passed/i)).not.toBeInTheDocument();
    });

    it('surfaces last manual backfill as historical context after startup is already ready', () => {
        render(
            <StatusDiagnosticsPanel
                status={{
                    system_ready: true,
                    message: 'Running...',
                    provisioning_status: 'IDLE',
                    last_backfill_status: 'COMPLETED',
                    last_backfill_mode: 'MANUAL',
                    last_backfill_universe_choice: 'EGX70',
                    last_backfill_completed_trading_days: 252,
                    last_backfill_target_trading_days: 252,
                    metrics: { total_signals: 314, last_signal_date: '2026-03-17' },
                }}
                lastRefresh={new Date('2026-03-18T12:00:00Z')}
            />
        );

        expect(screen.getByText(/Last manual backfill completed \(EGX70\): 252 \/ 252 trading days/i)).toBeInTheDocument();
        expect(screen.queryByText(/Historical provisioning still in progress/i)).not.toBeInTheDocument();
    });

    it('shows a stable placeholder timestamp before the first live refresh arrives', () => {
        render(
            <StatusDiagnosticsPanel
                status={{
                    system_ready: false,
                    message: 'Initializing...',
                    metrics: { total_signals: 0, last_signal_date: null },
                }}
                lastRefresh={null}
            />
        );

        expect(screen.getByText(/\[--:--:--\] System Status Poll/i)).toBeInTheDocument();
    });

    it('renders runtime universe counts and ticker buckets when present', () => {
        render(
            <StatusDiagnosticsPanel
                status={{
                    system_ready: true,
                    message: 'Running...',
                    metrics: { total_signals: 314, last_signal_date: '2026-03-17' },
                    runtime_universe: {
                        source_context: {
                            archive_intraday_stale: true,
                            realtime_overlay_active: true,
                            runtime_review_note: 'Realtime overlay is live; SOURCE_STALE review candidates indicate archive/source lag, not live-feed quarantine.',
                        },
                        summary: {
                            tracked_count: 270,
                            runtime_quarantined_count: 16,
                            review_candidate_count: 11,
                        },
                        runtime_quarantined: [
                            { ticker: 'ADIB_R3', reason: 'RIGHTS' },
                            { ticker: 'MEGM', reason: 'DORMANT' },
                        ],
                        review_candidates: [
                            { ticker: 'CPME', reason: 'SOURCE_STALE' },
                            { ticker: 'TRTO', reason: 'SOURCE_STALE' },
                        ],
                    },
                }}
                lastRefresh={new Date('2026-03-18T12:00:00Z')}
            />
        );

        expect(screen.getByText('Runtime Universe')).toBeInTheDocument();
        expect(screen.getByText('Archive stale / realtime overlay live')).toBeInTheDocument();
        expect(screen.getByText(/archive\/source lag, not live-feed quarantine/i)).toBeInTheDocument();
        expect(screen.getByText('Tracked')).toBeInTheDocument();
        expect(screen.getByText('270')).toBeInTheDocument();
        expect(screen.getByText('Runtime Quarantined')).toBeInTheDocument();
        expect(screen.getByText('Review Candidates')).toBeInTheDocument();
        expect(screen.getByText('ADIB_R3')).toBeInTheDocument();
        expect(screen.getByText('TRTO')).toBeInTheDocument();
    });
});
