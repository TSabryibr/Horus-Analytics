import React from 'react';
import { render, screen } from '@testing-library/react';

import PortfolioReportSection from './PortfolioReportSection';

jest.mock('recharts', () => {
    const actual = jest.requireActual('recharts');
    return {
        ...actual,
        ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
            <div style={{ width: 800, height: 280 }}>{children}</div>
        ),
    };
});

describe('PortfolioReportSection', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders from provided report data without issuing its own fetches', () => {
        global.fetch = jest.fn() as jest.Mock;

        render(
            <PortfolioReportSection
                portfolioId={7}
                report={{
                    metrics: { total_pnl: 300, win_rate: 50, profit_factor: 1.2, total_trades: 3 },
                    curve: [{ date: 'Baseline', equity: 1000000 }],
                    trades: [{ ticker: 'COMI', entry_price: 50, exit_price: 53, exit_date: '2026-03-17', pnl: 300 }],
                }}
                loading={false}
            />
        );

        expect(screen.getByText(/Investment Committee Report/i)).toBeInTheDocument();
        expect(screen.getByText(/Total Trades/i)).toBeInTheDocument();
        expect(global.fetch).not.toHaveBeenCalled();
    });

    it('renders strategy attribution headline and signal quality cards', () => {
        render(
            <PortfolioReportSection
                portfolioId={21}
                report={{
                    metrics: { total_pnl: 1200, win_rate: 55, profit_factor: 1.5, total_trades: 5 },
                    curve: [{ date: 'Baseline', equity: 1000000 }],
                    trades: [{ ticker: 'COMI', entry_price: 50, exit_price: 53, exit_date: '2026-03-17', pnl: 300 }],
                }}
                performance={{
                    portfolio: { id: 21, name: 'Breakout Strategy', type: 'STRATEGY' },
                    scope: 'STRATEGY_ATTRIBUTION',
                    metrics: {
                        total_pnl: 1200,
                        win_rate: 55,
                        profit_factor: 1.5,
                        total_trades: 5,
                        avg_pnl_pct: 2.4,
                        max_drawdown: 4.2,
                        avg_holding_days: 3.2,
                    },
                    summary: { open_positions: 1, winners: 3, losers: 2, best_trade: 4.1, worst_trade: -1.9 },
                    signal_quality: {
                        generated_count: 10,
                        active_count: 10,
                        filled_count: 6,
                        pending_count: 1,
                        skipped_count: 2,
                        failed_count: 1,
                        no_fill_count: 3,
                        fill_rate: 60,
                        no_fill_rate: 30,
                        no_trade_rate: 20,
                        outcome_distribution: { CLOSED: 4, OPEN: 2, NO_TRADE: 2 },
                        execution_state_distribution: { CLOSED: 4, OPEN: 2, SKIPPED: 2, FAILED: 1, PENDING_OPEN: 1 },
                    },
                }}
                executionHistory={[]}
                loading={false}
            />
        );

        expect(screen.getByText(/Strategy Attribution Report/i)).toBeInTheDocument();
        expect(screen.getByText(/Signals/i)).toBeInTheDocument();
        expect(screen.getByText(/Fill Rate/i)).toBeInTheDocument();
    });
});
