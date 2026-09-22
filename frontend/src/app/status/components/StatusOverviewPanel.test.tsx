import { render, screen } from '@testing-library/react';

import { StatusOverviewPanel } from './StatusOverviewPanel';

const status = {
    system_ready: true,
    db_connected: true,
    alerts: { telegram: { configured: true } },
    scheduler: { running: true },
};

describe('StatusOverviewPanel', () => {
    it('renders the four observability KPI cards', () => {
        render(<StatusOverviewPanel status={status} />);

        expect(screen.getByText('Engine Readiness')).toBeInTheDocument();
        expect(screen.getByText('Database Link')).toBeInTheDocument();
        expect(screen.getByText('Telegram Sentinel')).toBeInTheDocument();
        expect(screen.getByText('Scheduler Status')).toBeInTheDocument();
        expect(screen.getAllByText(/OPERATIONAL|CONNECTED|ACTIVE|RUNNING/)).toHaveLength(4);
    });

    it('surfaces provisioning progress instead of generic booting state', () => {
        render(
            <StatusOverviewPanel
                status={{
                    system_ready: false,
                    provisioning_status: 'RUNNING',
                    provisioning_completed_trading_days: 61,
                    provisioning_target_trading_days: 252,
                    db_connected: true,
                    alerts: { telegram: { configured: true } },
                    scheduler: { running: true },
                }}
            />
        );

        expect(screen.getByText('PROVISIONING')).toBeInTheDocument();
        expect(screen.getByText(/61 \/ 252 trading days/i)).toBeInTheDocument();
        expect(screen.queryByText('BOOTING')).not.toBeInTheDocument();
    });

    it('surfaces provisioning failures instead of generic booting state', () => {
        render(
            <StatusOverviewPanel
                status={{
                    system_ready: false,
                    provisioning_status: 'ERROR',
                    provisioning_error: 'Insufficient historical data coverage',
                    db_connected: true,
                    alerts: { telegram: { configured: true } },
                    scheduler: { running: true },
                }}
            />
        );

        expect(screen.getByText('FAILED')).toBeInTheDocument();
        expect(screen.getByText(/Insufficient historical data coverage/i)).toBeInTheDocument();
        expect(screen.queryByText('BOOTING')).not.toBeInTheDocument();
    });

    it('surfaces last manual backfill as historical context instead of startup work', () => {
        render(
            <StatusOverviewPanel
                status={{
                    system_ready: true,
                    provisioning_status: 'IDLE',
                    last_backfill_status: 'COMPLETED',
                    last_backfill_mode: 'MANUAL',
                    last_backfill_universe_choice: 'FULL',
                    last_backfill_completed_trading_days: 252,
                    last_backfill_target_trading_days: 252,
                    db_connected: true,
                    alerts: { telegram: { configured: true } },
                    scheduler: { running: true },
                }}
            />
        );

        expect(screen.getByText(/Last manual backfill \(FULL\): 252 \/ 252 trading days/i)).toBeInTheDocument();
        expect(screen.queryByText('PROVISIONING')).not.toBeInTheDocument();
    });
});
