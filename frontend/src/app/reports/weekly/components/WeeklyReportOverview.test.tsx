import { render, screen } from '@testing-library/react';

import { WeeklyReportOverview } from './WeeklyReportOverview';

describe('WeeklyReportOverview', () => {
    it('renders window, regime shift, and signal quality cards', () => {
        render(
            <WeeklyReportOverview
                data={{
                    generated_at: '2026-03-12T15:00:00',
                    period_end: '2026-03-12',
                    period_start: '2026-03-08',
                    status: 'success',
                }}
                market={{
                    breadth_change_pct: 3.4,
                    period_return_pct: 2.1,
                    regime_end: 'BULLISH',
                    regime_start: 'CAUTIOUS',
                }}
                review={{
                    avg_pnl_pct: 1.12,
                    run_count: 5,
                    signals_generated: 16,
                    win_rate_pct: 62.5,
                }}
            />,
        );

        expect(screen.getByText('Window')).toBeInTheDocument();
        expect(screen.getByText('2026-03-08 to 2026-03-12')).toBeInTheDocument();
        expect(screen.getByText('Regime Shift')).toBeInTheDocument();
        expect(screen.getByText('CAUTIOUS to BULLISH')).toBeInTheDocument();
        expect(screen.getByText('2.10%')).toBeInTheDocument();
        expect(screen.getByText('Signal Quality')).toBeInTheDocument();
        expect(screen.getByText('Win Rate: 62.50%')).toBeInTheDocument();
    });
});
