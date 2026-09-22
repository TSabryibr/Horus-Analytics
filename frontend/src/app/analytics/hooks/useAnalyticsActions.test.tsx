import { act, renderHook } from '@testing-library/react';

import { useAnalyticsActions } from './useAnalyticsActions';

const analyticsRow = {
    Ticker: 'HRHO',
    Price: 38.75,
    Signal_Score: 9,
    Status: 'HIGH CONVICTION BUY',
    Trend: 'BULLISH' as const,
    RSI: 61,
    Target_1: 40,
    Target_2: 42,
    Risk_Reward_Ratio: 2.9,
    Stop_Loss: 36.5,
    Avg_Turnover_M: 8,
    ATR: 1.6,
};

describe('useAnalyticsActions', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        jest.spyOn(console, 'error').mockImplementation(() => { });
        jest.spyOn(window, 'alert').mockImplementation(() => { });
    });

    afterEach(() => {
        jest.useRealTimers();
        jest.restoreAllMocks();
    });

    it('runs a fresh scan, polls to completion, and refreshes analytics data', async () => {
        const fetchData = jest.fn(async () => { });
        const setStatus = jest.fn();
        const setLastUpdated = jest.fn();

        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/analytics/refresh')) {
                return {
                    ok: true,
                    text: async () => JSON.stringify({ status: 'RUNNING', scan_id: 'scan-1' }),
                } as Response;
            }
            if (url.includes('/api/v1/analytics/status')) {
                const callCount = (global.fetch as jest.Mock).mock.calls.filter(([value]) =>
                    String(value).includes('/api/v1/analytics/status')
                ).length;
                if (callCount === 1) {
                    return {
                        ok: true,
                        text: async () => JSON.stringify({ status: 'RUNNING', scan_id: 'scan-1' }),
                    } as Response;
                }
                return {
                    ok: true,
                    text: async () => JSON.stringify({
                        status: 'COMPLETED',
                        scan_id: 'scan-1',
                        last_updated: '2026-03-18T14:00:00Z',
                    }),
                } as Response;
            }
            return { ok: true, text: async () => '{}' } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() =>
            useAnalyticsActions({
                fetchData,
                setStatus,
                setLastUpdated,
                pollDelayMs: 1,
                pollTimeoutMs: 10,
            })
        );

        await act(async () => {
            const pending = result.current.runScan();
            await jest.advanceTimersByTimeAsync(5);
            await pending;
        });

        expect(setStatus).toHaveBeenCalledWith('RUNNING');
        expect(setStatus).toHaveBeenCalledWith('COMPLETED');
        expect(setLastUpdated).toHaveBeenCalledWith('2026-03-18T14:00:00Z');
        expect(fetchData).toHaveBeenCalledTimes(1);
    });

    it('maps broadcast success and failure through alert messaging', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: 'sent' }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() =>
            useAnalyticsActions({
                fetchData: jest.fn(),
                setStatus: jest.fn(),
                setLastUpdated: jest.fn(),
            })
        );

        await act(async () => {
            await result.current.handleBroadcast(analyticsRow);
        });

        expect(window.alert).toHaveBeenCalledWith('✅ Successfully broadcasted HRHO to Telegram.');

        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: false,
            json: async () => ({ detail: 'Telegram unavailable' }),
        } as Response);

        await act(async () => {
            await result.current.handleBroadcast(analyticsRow);
        });

        expect(window.alert).toHaveBeenCalledWith('❌ Failed to broadcast: Telegram unavailable');
    });
});
