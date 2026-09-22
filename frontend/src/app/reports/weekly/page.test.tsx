import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import WeeklyReportPage from './page';

const apiFetchMock = jest.fn();
const readJsonSafeMock = jest.fn();
const pickApiMessageMock = jest.fn((data: any) => data?.detail || 'error');

jest.mock('@/lib/api', () => ({
    apiFetch: (...args: any[]) => apiFetchMock(...args),
    readJsonSafe: (...args: any[]) => readJsonSafeMock(...args),
    pickApiMessage: (...args: any[]) => pickApiMessageMock(...args),
}));

const baseReportPayload = {
    status: 'success',
    period_type: 'WEEKLY',
    period_start: '2026-03-08',
    period_end: '2026-03-12',
    generated_at: '2026-03-12T15:00:00',
    market_summary: {
        regime_start: 'CAUTIOUS',
        regime_end: 'BULLISH',
        period_return_pct: 2.1,
        breadth_change_pct: 3.4,
        volatility_context: 'EGX30: moderate volatility',
        key_shifts: ['Regime shifted from CAUTIOUS to BULLISH during the period.'],
    },
    signal_review: {
        run_count: 5,
        signals_generated: 16,
        closed_outcomes: 8,
        open_outcomes: 4,
        no_trade_outcomes: 4,
        win_rate_pct: 62.5,
        avg_pnl_pct: 1.12,
        expectancy_pct: 0.41,
        what_worked: ['Win rate held above 55% in closed outcomes.'],
        what_failed: [],
    },
    warnings: [],
    notes: [],
};

describe('WeeklyReportPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        apiFetchMock.mockImplementation(async (endpoint: string, options?: RequestInit) => {
            return {
                ok: true,
                endpoint,
                options,
            } as any;
        });
        readJsonSafeMock.mockImplementation(async (response: any) => {
            if (String(response.endpoint).includes('/reports/analysis/broadcast')) {
                return { status: 'sent' };
            }
            return baseReportPayload;
        });
    });

    it('loads weekly analysis report on mount', async () => {
        render(<WeeklyReportPage />);

        await waitFor(() => {
            expect(apiFetchMock).toHaveBeenCalledWith('/reports/analysis?period=weekly');
        });

        expect(screen.getByText(/Market Analysis Report/i)).toBeInTheDocument();
        await waitFor(() => {
            expect(screen.getByText(/^Regime Shift$/i)).toBeInTheDocument();
            expect(screen.getByText('2.10%')).toBeInTheDocument();
        });
    });

    it('switches to monthly period and fetches monthly report', async () => {
        render(<WeeklyReportPage />);

        await waitFor(() => {
            expect(apiFetchMock).toHaveBeenCalledWith('/reports/analysis?period=weekly');
        });

        fireEvent.click(screen.getByRole('button', { name: /Monthly/i }));

        await waitFor(() => {
            expect(apiFetchMock).toHaveBeenCalledWith('/reports/analysis?period=monthly');
        });
    });

    it('broadcasts current period report to Telegram', async () => {
        render(<WeeklyReportPage />);

        await waitFor(() => {
            expect(apiFetchMock).toHaveBeenCalledWith('/reports/analysis?period=weekly');
        });

        fireEvent.click(screen.getByRole('button', { name: /Broadcast/i }));

        await waitFor(() => {
            expect(apiFetchMock).toHaveBeenCalledWith(
                '/reports/analysis/broadcast',
                expect.objectContaining({
                    method: 'POST',
                })
            );
        });

        await waitFor(() => {
            expect(apiFetchMock).toHaveBeenCalledWith('/reports/analysis?period=weekly&force_refresh=true');
        });
    });
});
