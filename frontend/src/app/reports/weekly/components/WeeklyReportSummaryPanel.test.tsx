import { render, screen } from '@testing-library/react';

import { WeeklyReportSummaryPanel } from './WeeklyReportSummaryPanel';

describe('WeeklyReportSummaryPanel', () => {
    it('renders market summary and signal review sections', () => {
        render(
            <WeeklyReportSummaryPanel
                failed={[]}
                keyShifts={['Regime shifted from CAUTIOUS to BULLISH during the period.']}
                market={{ volatility_context: 'EGX30: moderate volatility' }}
                recommendations={['Concentrate capital in SWING lane — highest expectancy.']}
                review={{
                    avg_pnl_pct: 1.12,
                    avg_time_to_open_hours: 2.5,
                    avg_time_to_resolution_hours: 17,
                    closed_outcomes: 8,
                    expectancy_pct: 0.41,
                    expiry_rate_pct: 12.5,
                    fill_rate_pct: 66.67,
                    followup_total: 6,
                    followup_sent_rate_pct: 83.33,
                    followup_failure_rate_pct: 16.67,
                    followup_avg_retry_count: 0.5,
                    followup_pending_count: 1,
                    followup_suppressed_count: 1,
                    full_win_rate_pct: 37.5,
                    lane_breakdown: [
                        { key: 'SWING', published_count: 6, avg_realized_pnl_pct: 1.87, tp1_hit_rate_pct: 50, full_win_rate_pct: 37.5, stop_loss_rate_pct: 25 },
                        { key: 'SCALP', published_count: 4, avg_realized_pnl_pct: 0.82, tp1_hit_rate_pct: 40, full_win_rate_pct: 25, stop_loss_rate_pct: 30 },
                    ],
                    no_trade_outcomes: 4,
                    open_outcomes: 4,
                    published_signals: 12,
                    review_source: 'PUBLISHED_LIFECYCLE',
                    stop_loss_rate_pct: 25,
                    tp1_hit_rate_pct: 50,
                    win_rate_pct: 62.5,
                }}
                worked={['Win rate held above 55% in closed outcomes.']}
            />,
        );

        expect(screen.getByText('Market Summary')).toBeInTheDocument();
        expect(screen.getByText('EGX30: moderate volatility')).toBeInTheDocument();
        expect(screen.getByText('- Regime shifted from CAUTIOUS to BULLISH during the period.')).toBeInTheDocument();
        expect(screen.getByText('Signal Review')).toBeInTheDocument();
        expect(screen.getByText('Closed/Open/NoTrade: 8/4/4')).toBeInTheDocument();
        expect(screen.getByText('Published Lifecycle')).toBeInTheDocument();
        expect(screen.getByText('Published/Fill: 12/66.67%')).toBeInTheDocument();
        expect(screen.getByText('TP1/Full Win/Stop: 50.00%/37.50%/25.00%')).toBeInTheDocument();
        expect(screen.getByText('Avg time open/resolution: 2.50h/17.00h')).toBeInTheDocument();
        expect(screen.getByText('Win rate: 62.50%')).toBeInTheDocument();
        expect(screen.getByText('Avg PnL: 1.1200%')).toBeInTheDocument();
        expect(screen.getByText('Expectancy: 0.4100%')).toBeInTheDocument();
        // Lane breakdown table
        expect(screen.getByText('SWING')).toBeInTheDocument();
        expect(screen.getByText('SCALP')).toBeInTheDocument();
        expect(screen.getByText('Lane Breakdown')).toBeInTheDocument();
        // Delivery Performance
        expect(screen.getByText('Delivery Performance')).toBeInTheDocument();
        expect(screen.getByText('Follow-ups: 6')).toBeInTheDocument();
        expect(screen.getByText('Sent/Failed: 83.33%/16.67%')).toBeInTheDocument();
        expect(screen.getByText('Pending/Suppressed: 1/1')).toBeInTheDocument();
        expect(screen.getByText('Avg retry count: 0.50')).toBeInTheDocument();
        // Recommendations
        expect(screen.getByText('Recommendations')).toBeInTheDocument();
        expect(screen.getByText('- Concentrate capital in SWING lane — highest expectancy.')).toBeInTheDocument();
        // Worked/Failed
        expect(screen.getByText('- Win rate held above 55% in closed outcomes.')).toBeInTheDocument();
        expect(screen.getByText('- No major failure pattern flagged.')).toBeInTheDocument();
    });

    it('renders empty-state fallbacks when summary arrays are empty', () => {
        render(
            <WeeklyReportSummaryPanel
                failed={[]}
                keyShifts={[]}
                market={{}}
                recommendations={[]}
                review={{}}
                worked={[]}
            />,
        );

        expect(screen.getByText('No volatility context available.')).toBeInTheDocument();
        expect(screen.getByText('No key shifts detected.')).toBeInTheDocument();
        expect(screen.getByText('- No strong positive pattern yet.')).toBeInTheDocument();
    });
});
