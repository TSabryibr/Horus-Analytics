import { act, renderHook, waitFor } from '@testing-library/react';

import { useAnalyticsRuntime } from './useAnalyticsRuntime';

const analyticsRows = [
    {
        Ticker: 'COMI',
        Price: 102.25,
        Signal_Score: 4,
        Status: 'WATCHLIST',
        Trend: 'BULLISH',
        RSI: 48,
        Target_1: 106,
        Target_2: 108,
        Risk_Reward_Ratio: 1.8,
        Stop_Loss: 99,
        Avg_Turnover_M: 12,
        ATR: 2.4,
    },
    {
        Ticker: 'HRHO',
        Price: 38.75,
        Signal_Score: 9,
        Status: 'HIGH CONVICTION BUY',
        Trend: 'BULLISH',
        RSI: 61,
        Target_1: 40,
        Target_2: 42,
        Risk_Reward_Ratio: 2.9,
        Stop_Loss: 36.5,
        Avg_Turnover_M: 8,
        ATR: 1.6,
    },
];

describe('useAnalyticsRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('normalizes analytics payloads and exposes fetch metadata', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({
                status: 'COMPLETED',
                last_updated: '2026-03-18T12:00:00Z',
                rows: analyticsRows,
            }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useAnalyticsRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.data).toHaveLength(2);
            expect(result.current.status).toBe('COMPLETED');
            expect(result.current.lastUpdated).toBe('2026-03-18T12:00:00Z');
            expect(result.current.formattedLastUpdated).toContain('Mar');
        });
    });

    it('lets search override score and status filters', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({
                status: 'COMPLETED',
                data: analyticsRows,
            }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useAnalyticsRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.sortedData).toHaveLength(2);
        });

        act(() => {
            result.current.setMinScore(8);
        });

        expect(result.current.sortedData.map((item) => item.Ticker)).toEqual(['HRHO']);

        act(() => {
            result.current.setSearch('COMI');
        });

        expect(result.current.sortedData.map((item) => item.Ticker)).toEqual(['COMI']);
    });

    it('updates sort order and column visibility', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({
                status: 'COMPLETED',
                data: analyticsRows,
            }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useAnalyticsRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        act(() => {
            result.current.requestSort('Signal_Score');
        });

        expect(result.current.sortConfig).toEqual({ key: 'Signal_Score', direction: 'asc' });
        expect(result.current.sortedData.map((item) => item.Ticker)).toEqual(['COMI', 'HRHO']);

        act(() => {
            result.current.requestSort('Signal_Score');
            result.current.toggleColumn('Volume');
        });

        expect(result.current.sortConfig).toEqual({ key: 'Signal_Score', direction: 'desc' });
        expect(result.current.sortedData.map((item) => item.Ticker)).toEqual(['HRHO', 'COMI']);
        expect(result.current.columns.Volume).toBe(true);
    });

    it('suppresses expected offline fetch errors', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        global.fetch = jest.fn(async () => {
            throw new TypeError('Failed to fetch');
        }) as jest.Mock;

        const { result } = renderHook(() => useAnalyticsRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(consoleErrorSpy).not.toHaveBeenCalled();
        consoleErrorSpy.mockRestore();
    });
});
