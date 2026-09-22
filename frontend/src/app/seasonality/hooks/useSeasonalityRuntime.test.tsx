import { renderHook, act, waitFor } from '@testing-library/react';
import { useSeasonalityRuntime } from './useSeasonalityRuntime';

const marketPayload = {
    status: 'success',
    top_historical_performers: [
        { ticker: 'COMI', avg_return: 3.2, win_rate: 64, best_month: 'APR' },
    ],
};

const tickerPayload = (ticker: string) => ({
    status: 'success',
    ticker,
    verdict: {
        best_month: 'APR',
        worst_month: 'SEP',
        summary: `${ticker} summary`,
    },
    months: [
        { label: 'Jan', average_return: 1.2, win_rate: 58, count: 10 },
    ],
});

function mockSeasonalityFetch() {
    return jest.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('/api/v1/seasonality/market')) {
            return { ok: true, json: async () => marketPayload } as Response;
        }
        if (url.includes('/api/v1/seasonality?ticker=')) {
            const match = url.match(/ticker=([A-Z]+)/);
            const ticker = match ? match[1] : 'COMI';
            return { ok: true, json: async () => tickerPayload(ticker) } as Response;
        }
        return { ok: true, json: async () => ({ status: 'error' }) } as Response;
    });
}

describe('useSeasonalityRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('loads market and ticker stats on mount', async () => {
        global.fetch = mockSeasonalityFetch() as jest.Mock;

        const { result } = renderHook(() => useSeasonalityRuntime('COMI'));

        expect(result.current.loadingMarket).toBe(true);

        await waitFor(() => {
            expect(result.current.loadingMarket).toBe(false);
            expect(result.current.marketStats?.status).toBe('success');
            expect(result.current.tickerStats?.ticker).toBe('COMI');
        });
    });

    it('updates ticker stats on handleSearch', async () => {
        const fetchMock = mockSeasonalityFetch();
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useSeasonalityRuntime('COMI'));

        await waitFor(() => !result.current.loadingMarket);

        act(() => {
            result.current.setSearchTicker('HRHO');
        });

        act(() => {
            result.current.handleSearch();
        });

        await waitFor(() => {
            expect(result.current.tickerStats?.ticker).toBe('HRHO');
            expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('ticker=HRHO'));
        });
    });

    it('reloads everything on handleRefresh', async () => {
        const fetchMock = mockSeasonalityFetch();
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useSeasonalityRuntime('COMI'));

        await waitFor(() => !result.current.loadingMarket);
        fetchMock.mockClear();

        act(() => {
            result.current.handleRefresh();
        });

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/market'));
            expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('ticker=COMI'));
        });
    });

    it('handles fetch errors gracefully', async () => {
        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        global.fetch = jest.fn(() => Promise.reject('API Error')) as jest.Mock;

        const { result } = renderHook(() => useSeasonalityRuntime('COMI'));

        await waitFor(() => {
            expect(result.current.loadingMarket).toBe(false);
            expect(result.current.marketStats).toBeNull();
            expect(result.current.tickerStats).toBeNull();
        });

        errorSpy.mockRestore();
    });

    it('suppresses expected offline fetch errors', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        global.fetch = jest.fn(() => Promise.reject(new TypeError('Failed to fetch'))) as jest.Mock;

        const { result } = renderHook(() => useSeasonalityRuntime('COMI'));

        await waitFor(() => {
            expect(result.current.loadingMarket).toBe(false);
            expect(result.current.tickerStats).toBeNull();
        });

        expect(consoleErrorSpy).not.toHaveBeenCalled();
        consoleErrorSpy.mockRestore();
    });
});
