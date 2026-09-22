import { act, renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useLiveControls } from './useLiveControls';
import { __resetLiveContextCachesForTests, LiveProvider } from '../../context/LiveContext';

jest.mock('next/navigation', () => ({
    usePathname: () => '/live',
}));

describe('useLiveControls', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
        __resetLiveContextCachesForTests();
    });

    it('loads live status on demand', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/live/status')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'success', running: true, market_open: true, last_update: '2026-03-18T10:30:00Z' }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() =>
            useLiveControls({
                onSetError: jest.fn(),
                onEnableAutoRefresh: jest.fn(),
                onStartSuccess: jest.fn(),
            }), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        }
        );

        await act(async () => {
            await result.current.fetchLiveStatus();
        });

        expect(result.current.liveStatus?.running).toBe(true);
        expect(result.current.liveRunning).toBe(true);
        expect(result.current.marketOpen).toBe(true);
        expect(result.current.liveLastUpdate).not.toBe('N/A');
    });

    it('surfaces market-closed start responses as route errors', async () => {
        const onSetError = jest.fn();

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/live/start') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'market_closed',
                        running: false,
                        market_open: false,
                        message: 'Market is closed. Live feed start is blocked outside EGX hours.',
                    }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() =>
            useLiveControls({
                onSetError,
                onEnableAutoRefresh: jest.fn(),
                onStartSuccess: jest.fn(),
            }), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        }
        );

        await act(async () => {
            await result.current.handleLiveFeedAction('start');
        });

        expect(onSetError).toHaveBeenCalledWith('Market is closed. Live feed start is blocked outside EGX hours.');
        expect(result.current.marketOpen).toBe(false);
        expect(result.current.liveRunning).toBe(false);
    });

    it('refreshes status and triggers start-side effects after a successful start', async () => {
        const onSetError = jest.fn();
        const onEnableAutoRefresh = jest.fn();
        const onStartSuccess = jest.fn();

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/live/start') && init?.method === 'POST') {
                return { ok: true, json: async () => ({ status: 'success', running: true, market_open: true }) } as Response;
            }
            if (url.includes('/api/v1/live/status')) {
                return { ok: true, json: async () => ({ status: 'success', running: true, market_open: true }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() =>
            useLiveControls({
                onSetError,
                onEnableAutoRefresh,
                onStartSuccess,
            }), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        }
        );

        await act(async () => {
            await result.current.handleLiveFeedAction('start');
        });

        await waitFor(() => {
            expect(result.current.liveRunning).toBe(true);
        });

        expect(onSetError).toHaveBeenCalledWith(null);
        expect(onEnableAutoRefresh).toHaveBeenCalled();
        expect(onStartSuccess).toHaveBeenCalled();
    });

    it('reuses a fresh live status cache across provider remounts', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/live/status')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'success', running: true, market_open: true, last_update: '2026-03-18T10:30:00Z' }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const firstRender = renderHook(() =>
            useLiveControls({
                onSetError: jest.fn(),
                onEnableAutoRefresh: jest.fn(),
                onStartSuccess: jest.fn(),
            }), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        });

        await act(async () => {
            await firstRender.result.current.fetchLiveStatus();
        });
        firstRender.unmount();

        const secondRender = renderHook(() =>
            useLiveControls({
                onSetError: jest.fn(),
                onEnableAutoRefresh: jest.fn(),
                onStartSuccess: jest.fn(),
            }), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        });

        await act(async () => {
            await secondRender.result.current.fetchLiveStatus();
        });

        const statusRequests = (global.fetch as jest.Mock).mock.calls
            .map(([input]) => String(input))
            .filter((url) => url.includes('/api/v1/live/status'));

        expect(statusRequests).toHaveLength(1);
    });
});
