import { render, screen, fireEvent } from '@testing-library/react';
import { StatusSlaPanel, DeliverySlaMetrics } from './StatusSlaPanel';

describe('StatusSlaPanel', () => {
    it('renders empty standby state when no delivery records exist', () => {
        render(<StatusSlaPanel deliverySla={null} />);

        expect(screen.getByText('Telegram Delivery SLA & Latency')).toBeInTheDocument();
        expect(screen.getByText('STANDBY / NO DISPATCHES')).toBeInTheDocument();
        expect(screen.getByText(/No dispatch events recorded in this window yet/i)).toBeInTheDocument();
    });

    it('renders compliant delivery metrics and latency histogram distribution', () => {
        const mockSla: DeliverySlaMetrics = {
            window_days: 7,
            target_latency_ms: 5000,
            total_deliveries: 45,
            sent_count: 44,
            failed_count: 1,
            skipped_count: 2,
            dry_run_count: 0,
            success_rate_pct: 97.8,
            sla_compliant: true,
            latency_stats: {
                count: 44,
                avg_ms: 320.5,
                p50_ms: 180.0,
                p90_ms: 450.0,
                p95_ms: 850.0,
                p99_ms: 1200.0,
                min_ms: 95.0,
                max_ms: 2800.0,
                breached_count: 0,
                breach_rate_pct: 0.0,
                histogram: [
                    { bucket: '<250ms', min_ms: 0, max_ms: 250, count: 25, pct: 56.8 },
                    { bucket: '250-500ms', min_ms: 250, max_ms: 500, count: 12, pct: 27.3 },
                    { bucket: '500-1000ms', min_ms: 500, max_ms: 1000, count: 5, pct: 11.4 },
                    { bucket: '1-2.5s', min_ms: 1000, max_ms: 2500, count: 2, pct: 4.5 },
                    { bucket: '2.5-5s', min_ms: 2500, max_ms: 5000, count: 0, pct: 0.0 },
                    { bucket: '>5s', min_ms: 5000, max_ms: null, count: 0, pct: 0.0 },
                ],
            },
        };

        const onRefreshMock = jest.fn();

        render(<StatusSlaPanel deliverySla={mockSla} onRefresh={onRefreshMock} />);

        expect(screen.getByText('SLA COMPLIANT')).toBeInTheDocument();
        expect(screen.getByText('97.8%')).toBeInTheDocument();
        expect(screen.getByText('850 ms')).toBeInTheDocument();
        expect(screen.getByText(/P50: 180 ms/)).toBeInTheDocument();
        expect(screen.getByText('Total Measured: 44')).toBeInTheDocument();

        // Check histogram buckets
        expect(screen.getByText('<250ms')).toBeInTheDocument();
        expect(screen.getAllByText(/25/).length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText(/56.8%/)).toBeInTheDocument();
        expect(screen.getByText('250-500ms')).toBeInTheDocument();
        expect(screen.getByText('>5s')).toBeInTheDocument();

        // Refresh button click
        const refreshBtn = screen.getByTitle('Refresh Delivery SLA Metrics');
        fireEvent.click(refreshBtn);
        expect(onRefreshMock).toHaveBeenCalledTimes(1);
    });

    it('renders SLA AT RISK badge when sla_compliant is false', () => {
        const mockSla: DeliverySlaMetrics = {
            window_days: 7,
            target_latency_ms: 5000,
            total_deliveries: 10,
            sent_count: 7,
            failed_count: 3,
            success_rate_pct: 70.0,
            sla_compliant: false,
            latency_stats: {
                count: 7,
                avg_ms: 4200.0,
                p50_ms: 3800.0,
                p90_ms: 6100.0,
                p95_ms: 7200.0,
                p99_ms: 8000.0,
                min_ms: 200.0,
                max_ms: 8000.0,
                breached_count: 2,
                breach_rate_pct: 28.57,
                histogram: [
                    { bucket: '<250ms', min_ms: 0, max_ms: 250, count: 1, pct: 14.3 },
                    { bucket: '250-500ms', min_ms: 250, max_ms: 500, count: 0, pct: 0.0 },
                    { bucket: '500-1000ms', min_ms: 500, max_ms: 1000, count: 0, pct: 0.0 },
                    { bucket: '1-2.5s', min_ms: 1000, max_ms: 2500, count: 1, pct: 14.3 },
                    { bucket: '2.5-5s', min_ms: 2500, max_ms: 5000, count: 3, pct: 42.9 },
                    { bucket: '>5s', min_ms: 5000, max_ms: null, count: 2, pct: 28.6 },
                ],
            },
        };

        render(<StatusSlaPanel deliverySla={mockSla} />);

        expect(screen.getByText('SLA AT RISK')).toBeInTheDocument();
        expect(screen.getByText('70.0%')).toBeInTheDocument();
        expect(screen.getByText('Rate: 28.57%')).toBeInTheDocument();
    });
});
