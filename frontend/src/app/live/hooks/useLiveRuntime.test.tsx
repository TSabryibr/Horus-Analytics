import { act, renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useLiveRuntime } from './useLiveRuntime';
import { __resetLiveContextCachesForTests, LiveProvider } from '../../context/LiveContext';

jest.mock('next/navigation', () => ({
    usePathname: () => '/live',
}));

const intradayPayload = [
    {
        Date: '2026-02-17T09:30:00Z',
        Open: 101,
        High: 103,
        Low: 100,
        Close: 102,
        Volume: 15000,
    },
    {
        Date: '2026-02-17T09:31:00Z',
        Open: 102,
        High: 104,
        Low: 101,
        Close: 103,
        Volume: 18000,
    },
];

describe('useLiveRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        __resetLiveContextCachesForTests();
    });

    it('automatically loads intraday candles for the active ticker on mount', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/data/tickers')) {
                return { ok: true, json: async () => ['COMI', 'HRHO'] } as Response;
            }
            if (url.includes('/api/v1/data/intraday/COMI?limit=240')) {
                return { ok: true, json: async () => intradayPayload } as Response;
            }
            return { ok: true, json: async () => ({ status: 'success', running: false, market_open: true }) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useLiveRuntime(), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        });

        await waitFor(() => {
            expect(result.current.ticker).toBe('COMI');
            expect(result.current.data).toHaveLength(2);
            expect(result.current.loading).toBe(false);
        });
    });

    it('loads tickers and intraday candles for the selected ticker', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/data/tickers')) {
                return { ok: true, json: async () => ['COMI', 'HRHO'] } as Response;
            }
            if (url.includes('/api/v1/data/intraday/COMI?limit=240')) {
                return { ok: true, json: async () => intradayPayload } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useLiveRuntime(), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        });

        await waitFor(() => {
            expect(result.current.ticker).toBe('COMI');
            expect(result.current.tickers).toEqual(['COMI', 'HRHO']);
        });

        await act(async () => {
            await result.current.fetchData('initial');
        });

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.data).toHaveLength(2);
            expect(result.current.error).toBeNull();
            expect(result.current.lastUpdate).not.toBe('');
        });
    });

    it('automatically reloads intraday candles when the active ticker changes', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/data/tickers')) {
                return { ok: true, json: async () => ['COMI', 'HRHO'] } as Response;
            }
            if (url.includes('/api/v1/data/intraday/COMI?limit=240')) {
                return { ok: true, json: async () => intradayPayload } as Response;
            }
            if (url.includes('/api/v1/data/intraday/HRHO?limit=240')) {
                return {
                    ok: true,
                    json: async () => [
                        {
                            Date: '2026-02-17T09:32:00Z',
                            Open: 90,
                            High: 92,
                            Low: 89,
                            Close: 91,
                            Volume: 12000,
                        },
                    ],
                } as Response;
            }
            return { ok: true, json: async () => ({ status: 'success', running: false, market_open: true }) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useLiveRuntime(), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        });

        await waitFor(() => {
            expect(result.current.ticker).toBe('COMI');
            expect(result.current.data).toHaveLength(2);
        });

        act(() => {
            result.current.setTicker('HRHO');
        });

        await waitFor(() => {
            expect(result.current.ticker).toBe('HRHO');
            expect(result.current.data).toHaveLength(1);
            expect(result.current.data[0]?.Close).toBe(91);
        });
    });

    it('falls back to the first available ticker when the default one is absent', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/data/tickers')) {
                return { ok: true, json: async () => ['HRHO', 'ETEL'] } as Response;
            }
            if (url.includes('/api/v1/data/intraday/COMI?limit=240')) {
                return { ok: true, json: async () => intradayPayload } as Response;
            }
            if (url.includes('/api/v1/data/intraday/HRHO?limit=240')) {
                return { ok: true, json: async () => intradayPayload } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useLiveRuntime(), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        });

        await waitFor(() => {
            expect(result.current.ticker).toBe('HRHO');
            expect(result.current.tickers).toEqual(['HRHO', 'ETEL']);
        });

        await act(async () => {
            await result.current.fetchData('initial');
        });

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.data).toHaveLength(2);
        });
    });

    it('keeps the latest ticker payload when responses resolve out of order', async () => {
        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        let resolveComi: ((value: Response) => void) | null = null;
        let resolveHrho: ((value: Response) => void) | null = null;

        global.fetch = jest.fn((input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/data/tickers')) {
                return Promise.resolve({ ok: true, json: async () => ['COMI', 'HRHO'] } as Response);
            }
            if (url.includes('/api/v1/data/intraday/COMI?limit=240')) {
                return new Promise<Response>((resolve, reject) => {
                    resolveComi = resolve;
                    if (init?.signal instanceof AbortSignal) {
                        init.signal.addEventListener('abort', () => {
                            reject(new DOMException('Aborted', 'AbortError'));
                        });
                    }
                });
            }
            if (url.includes('/api/v1/data/intraday/HRHO?limit=240')) {
                return new Promise<Response>((resolve) => {
                    resolveHrho = resolve;
                });
            }
            return Promise.resolve({ ok: true, json: async () => ({}) } as Response);
        }) as jest.Mock;

        const { result } = renderHook(() => useLiveRuntime(), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        });

        await waitFor(() => {
            expect(result.current.tickers).toEqual(['COMI', 'HRHO']);
        });

        act(() => {
            void result.current.fetchData('initial');
        });

        await waitFor(() => {
            expect(resolveComi).not.toBeNull();
        });

        act(() => {
            result.current.setTicker('HRHO');
        });

        act(() => {
            void result.current.fetchData('initial');
        });

        await waitFor(() => {
            expect(resolveHrho).not.toBeNull();
        });

        act(() => {
            resolveHrho?.({
                ok: true,
                json: async () => [
                    {
                        Date: '2026-02-17T09:32:00Z',
                        Open: 90,
                        High: 92,
                        Low: 89,
                        Close: 91,
                        Volume: 12000,
                    },
                ],
            } as Response);
        });

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.data).toHaveLength(1);
            expect(result.current.data[0]?.Close).toBe(91);
        });

        act(() => {
            resolveComi?.({
                ok: true,
                json: async () => intradayPayload,
            } as Response);
        });

        await waitFor(() => {
            expect(result.current.data).toHaveLength(1);
            expect(result.current.data[0]?.Close).toBe(91);
        });

        errorSpy.mockRestore();
    });

    it('does not refetch the ticker universe when the selected ticker changes', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/data/tickers')) {
                return { ok: true, json: async () => ['COMI', 'HRHO'] } as Response;
            }
            if (url.includes('/api/v1/data/intraday/COMI?limit=240')) {
                return { ok: true, json: async () => intradayPayload } as Response;
            }
            if (url.includes('/api/v1/data/intraday/HRHO?limit=240')) {
                return { ok: true, json: async () => intradayPayload } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useLiveRuntime(), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        });

        await waitFor(() => {
            expect(result.current.tickers).toEqual(['COMI', 'HRHO']);
        });

        act(() => {
            result.current.setTicker('HRHO');
        });

        await waitFor(() => {
            expect(result.current.ticker).toBe('HRHO');
        });

        const tickerRequests = (global.fetch as jest.Mock).mock.calls
            .map(([input]) => String(input))
            .filter((url) => url.includes('/api/v1/data/tickers'));

        expect(tickerRequests).toHaveLength(1);
    });

    it('reuses a fresh ticker universe across provider remounts', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/data/tickers')) {
                return { ok: true, json: async () => ['COMI', 'HRHO'] } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const firstRender = renderHook(() => useLiveRuntime(), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        });

        await waitFor(() => {
            expect(firstRender.result.current.tickers).toEqual(['COMI', 'HRHO']);
        });
        firstRender.unmount();

        const secondRender = renderHook(() => useLiveRuntime(), {
            wrapper: ({ children }) => <LiveProvider>{children}</LiveProvider>
        });

        await waitFor(() => {
            expect(secondRender.result.current.tickers).toEqual(['COMI', 'HRHO']);
        });

        const tickerRequests = (global.fetch as jest.Mock).mock.calls
            .map(([input]) => String(input))
            .filter((url) => url.includes('/api/v1/data/tickers'));

        expect(tickerRequests).toHaveLength(1);
    });
});
