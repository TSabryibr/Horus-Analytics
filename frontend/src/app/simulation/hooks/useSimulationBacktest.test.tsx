import { act, renderHook, waitFor } from '@testing-library/react';

import { useSimulationBacktest } from './useSimulationBacktest';

describe('useSimulationBacktest', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
    });

    it('falls back to strategy backtest endpoint when simulation endpoint is not allowed', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/simulation/backtest')) {
                return {
                    ok: false,
                    status: 405,
                    statusText: 'Method Not Allowed',
                    json: async () => ({ detail: 'Method Not Allowed' }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/price-action/backtest')) {
                expect(init?.method).toBe('POST');
                return {
                    ok: true,
                    status: 200,
                    json: async () => ({
                        status: 'success',
                        metrics: {
                            total_return: 1.5,
                            max_drawdown: 2.1,
                            profit_factor: 1.3,
                            expectancy: 100.0,
                            win_rate: 60.0,
                            trade_count: 1,
                        },
                        equity_curve: [100000, 101500],
                        trades: [{ ticker: 'AAA', pnl: 1500 }],
                    }),
                } as Response;
            }
            return { ok: true, status: 200, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useSimulationBacktest({ apiBase: 'http://127.0.0.1:8100' }));

        act(() => {
            result.current.setBacktestStartDate('2026-05-12');
            result.current.setBacktestEndDate('2026-05-13');
        });

        await act(async () => {
            await result.current.runBacktest();
        });

        await waitFor(() => {
            expect(result.current.backtestLoading).toBe(false);
            expect(result.current.backtestError).toBeNull();
            expect(result.current.backtestResult?.total_return).toBe(1.5);
            expect(result.current.backtestResult?.trade_count).toBe(1);
        });
    });
});
