import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { usePortfolioRuntime } from './usePortfolioRuntime';

function HookHarness({ activePortfolioId }: { activePortfolioId: number | null }) {
    const runtime = usePortfolioRuntime({ activePortfolioId });

    return (
        <div>
            <span data-testid="loading">{runtime.loading ? 'yes' : 'no'}</span>
            <span data-testid="hoard-status">{runtime.hoard?.status || 'none'}</span>
            <span data-testid="health-status">{runtime.health?.status || 'none'}</span>
            <span data-testid="analysis-status">{runtime.analysis?.status || 'none'}</span>
            <span data-testid="report-trades">{runtime.report?.metrics.total_trades ?? 'none'}</span>
            <button type="button" onClick={() => runtime.showUiMessage('success', 'manual')}>
                show-message
            </button>
            <span data-testid="ui-message">{runtime.uiMessage?.text || 'none'}</span>
        </div>
    );
}

describe('usePortfolioRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('loads active hoard, health, and analysis for the active portfolio', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/boot-status')) {
                return { ok: true, json: async () => ({ system_ready: true, pipeline_state: 'FRESH' }) } as Response;
            }
            if (url.includes('/api/v1/portfolio?portfolio_id=7')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'active',
                        net_worth_egp: 1500000,
                        net_worth_usd: 10000,
                        cash_egp: 250000,
                        cash_usd: 1200,
                        positions: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/analytics/health')) {
                return { ok: true, json: async () => ({ status: 'success', score: 80 }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/analysis?portfolio_id=7')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'success', recommendations: [], sector_breakdown: {}, heat: 1, health_score: 90 }),
                } as Response;
            }
            if (url.includes('/api/v1/portfolio/report?portfolio_id=7')) {
                return {
                    ok: true,
                    json: async () => ({
                        metrics: { total_pnl: 300, win_rate: 50, profit_factor: 1.2, total_trades: 3 },
                        curve: [{ date: 'Baseline', equity: 1000000 }],
                        trades: [{ ticker: 'COMI', entry_price: 50, exit_price: 53, exit_date: '2026-03-17', pnl: 300 }],
                    }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<HookHarness activePortfolioId={7} />);

        await waitFor(() => {
            expect(screen.getByTestId('loading')).toHaveTextContent('no');
            expect(screen.getByTestId('hoard-status')).toHaveTextContent('active');
            expect(screen.getByTestId('health-status')).toHaveTextContent('success');
            expect(screen.getByTestId('analysis-status')).toHaveTextContent('success');
            expect(screen.getByTestId('report-trades')).toHaveTextContent('3');
        });

        const urls = (global.fetch as jest.Mock).mock.calls.map(([input]) => String(input));
        expect(urls.some((url) => url.includes('/api/v1/system/boot-status'))).toBe(true);
        expect(urls.some((url) => url.includes('/api/v1/portfolio/report?portfolio_id=7'))).toBe(true);
        expect(urls.some((url) => url.includes('/api/v1/portfolio/metrics'))).toBe(false);
        expect(urls.some((url) => url.includes('/api/v1/portfolio/curve'))).toBe(false);
        expect(urls.some((url) => url.includes('/api/v1/portfolio/trades'))).toBe(false);
    });

    it('stays empty when no active portfolio is selected', async () => {
        global.fetch = jest.fn() as jest.Mock;

        render(<HookHarness activePortfolioId={null} />);

        await waitFor(() => {
            expect(screen.getByTestId('loading')).toHaveTextContent('no');
            expect(screen.getByTestId('hoard-status')).toHaveTextContent('none');
            expect(screen.getByTestId('health-status')).toHaveTextContent('none');
            expect(screen.getByTestId('analysis-status')).toHaveTextContent('none');
            expect(screen.getByTestId('report-trades')).toHaveTextContent('none');
        });

        expect(global.fetch).not.toHaveBeenCalled();
    });
});
