import { act, renderHook, waitFor } from '@testing-library/react';

import { useWeeklyReportRuntime } from './useWeeklyReportRuntime';

const apiFetchMock = jest.fn();
const readJsonSafeMock = jest.fn();
const pickApiMessageMock = jest.fn((data: any, fallback: string) => data?.detail || fallback);

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
        review_source: 'PUBLISHED_LIFECYCLE',
        run_count: 5,
        signals_generated: 16,
        published_signals: 12,
        closed_outcomes: 8,
        open_outcomes: 4,
        no_trade_outcomes: 4,
        win_rate_pct: 62.5,
        avg_pnl_pct: 1.12,
        expectancy_pct: 0.41,
        fill_rate_pct: 66.67,
        followup_total: 6,
        followup_sent_rate_pct: 83.33,
        followup_failure_rate_pct: 16.67,
        followup_avg_retry_count: 0.5,
        followup_pending_count: 1,
        followup_suppressed_count: 1,
        tp1_hit_rate_pct: 50.0,
        full_win_rate_pct: 37.5,
        stop_loss_rate_pct: 25.0,
        expiry_rate_pct: 12.5,
        avg_time_to_open_hours: 2.5,
        avg_time_to_resolution_hours: 17,
        lane_breakdown: [{ key: 'SWING', published_count: 6, avg_realized_pnl_pct: 1.87 }],
        what_worked: ['Win rate held above 55% in closed outcomes.'],
        what_failed: [],
    },
    warnings: [],
    notes: [],
};

describe('useWeeklyReportRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        apiFetchMock.mockImplementation(async (endpoint: string) => ({ ok: true, endpoint }) as any);
        readJsonSafeMock.mockResolvedValue(baseReportPayload);
    });

    it('loads the weekly report on mount and exposes derived fallback arrays', async () => {
        const { result } = renderHook(() => useWeeklyReportRuntime());

        await waitFor(() => {
            expect(apiFetchMock).toHaveBeenCalledWith('/reports/analysis?period=weekly');
        });

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.period).toBe('weekly');
        expect(result.current.data?.period_start).toBe('2026-03-08');
        expect(result.current.keyShifts).toEqual(['Regime shifted from CAUTIOUS to BULLISH during the period.']);
        expect(result.current.worked).toEqual(['Win rate held above 55% in closed outcomes.']);
        expect(result.current.review.review_source).toBe('PUBLISHED_LIFECYCLE');
        expect(result.current.review.fill_rate_pct).toBe(66.67);
        expect(result.current.review.followup_sent_rate_pct).toBe(83.33);
        expect(result.current.failed).toEqual([]);
        expect(result.current.warnings).toEqual([]);
        expect(result.current.notes).toEqual([]);
    });

    it('switches period and supports forced refresh', async () => {
        const { result } = renderHook(() => useWeeklyReportRuntime());

        await waitFor(() => {
            expect(apiFetchMock).toHaveBeenCalledWith('/reports/analysis?period=weekly');
        });

        await act(async () => {
            result.current.setPeriod('monthly');
        });

        await waitFor(() => {
            expect(apiFetchMock).toHaveBeenCalledWith('/reports/analysis?period=monthly');
        });

        await act(async () => {
            await result.current.loadReport(true);
        });

        expect(apiFetchMock).toHaveBeenCalledWith('/reports/analysis?period=monthly&force_refresh=true');
    });

    it('reports API failures and clears data', async () => {
        apiFetchMock.mockResolvedValueOnce({ ok: false, endpoint: '/reports/analysis?period=weekly' });
        readJsonSafeMock.mockResolvedValueOnce({ detail: 'Report unavailable.' });

        const { result } = renderHook(() => useWeeklyReportRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.error).toBe('Report unavailable.');
        expect(result.current.data).toBeNull();
    });
});
