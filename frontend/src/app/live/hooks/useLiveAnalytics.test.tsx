import { renderHook, waitFor } from '@testing-library/react';
import { act } from '@testing-library/react';

import { useLiveAnalytics } from './useLiveAnalytics';

const analyticsPayload = [
    {
        Ticker: 'COMI',
        Status: 'HIGH CONVICTION',
        Signal_Score: 9,
        Price: 104.25,
        Risk_Reward_Ratio: 2.8,
        Resistance_20D: 110.5,
        Key_Resistance_1: 112.4,
    },
];

describe('useLiveAnalytics', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
        jest.useRealTimers();
    });

    it('loads analytics candidates on mount when the endpoint returns rows', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/analytics')) {
                return { ok: true, json: async () => analyticsPayload } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useLiveAnalytics());

        await waitFor(() => {
            expect(result.current.analyticsLoading).toBe(false);
            expect(result.current.analyticsData).toEqual(analyticsPayload);
        });
    });

    it('refreshes and polls analytics status when the initial dataset is empty', async () => {
        let analyticsReads = 0;

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/analytics/status')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'COMPLETED', scan_id: 'scan-1' }),
                } as Response;
            }
            if (url.includes('/api/v1/analytics/refresh') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({ scan_id: 'scan-1', status: 'RUNNING' }),
                } as Response;
            }
            if (url.includes('/api/v1/analytics')) {
                analyticsReads += 1;
                return {
                    ok: true,
                    json: async () => (analyticsReads === 1 ? [] : analyticsPayload),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useLiveAnalytics({ pollDelayMs: 0 }));

        await waitFor(() => {
            expect(result.current.analyticsLoading).toBe(false);
            expect(result.current.analyticsData).toEqual(analyticsPayload);
        });
    });

    it('stops polling analytics when the hook unmounts mid-refresh', async () => {
        jest.useFakeTimers();

        let statusCalls = 0;

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/analytics/status')) {
                statusCalls += 1;
                return {
                    ok: true,
                    json: async () => ({ status: 'RUNNING', scan_id: 'scan-1' }),
                } as Response;
            }
            if (url.includes('/api/v1/analytics/refresh') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({ scan_id: 'scan-1', status: 'RUNNING' }),
                } as Response;
            }
            if (url.includes('/api/v1/analytics')) {
                return {
                    ok: true,
                    json: async () => [],
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { unmount } = renderHook(() => useLiveAnalytics({ pollDelayMs: 1000 }));

        await act(async () => {
            await Promise.resolve();
            await Promise.resolve();
        });

        unmount();

        await act(async () => {
            jest.advanceTimersByTime(1000);
            await Promise.resolve();
        });

        expect(statusCalls).toBe(0);
    });

    it('suppresses expected offline fetch warnings', async () => {
        const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
        global.fetch = jest.fn(async () => {
            throw new TypeError('Failed to fetch');
        }) as jest.Mock;

        const { result } = renderHook(() => useLiveAnalytics({ pollDelayMs: 0 }));

        await waitFor(() => {
            expect(result.current.analyticsLoading).toBe(false);
        });

        expect(consoleWarnSpy).not.toHaveBeenCalled();
        consoleWarnSpy.mockRestore();
    });
});
