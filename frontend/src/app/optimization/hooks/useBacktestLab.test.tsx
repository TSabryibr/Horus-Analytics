import { act, renderHook, waitFor } from '@testing-library/react';

import { useBacktestLab } from './useBacktestLab';

describe('useBacktestLab', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
    });

    it('reports validation errors before running the simulator', async () => {
        const showMessage = jest.fn();
        const { result } = renderHook(() => useBacktestLab({ optIndex: 'ALL', showMessage }));

        act(() => {
            result.current.setSimParams((prev: any) => ({ ...prev, RSI_MIN: 90, RSI_MAX: 80 }));
        });

        await act(async () => {
            await result.current.runSimulation();
        });

        expect(showMessage).toHaveBeenCalledWith({
            type: 'error',
            text: 'RSI Entry must be lower than RSI Overbought.',
        });
    });

    it('runs the simulator and stores successful results', async () => {
        const showMessage = jest.fn();
        global.fetch = jest.fn(async () => ({
            ok: true,
            text: async () =>
                JSON.stringify({
                    metrics: { total_return: 12.34, final_value: 224680, trade_count: 18 },
                    equity_curve: [{ date: '2025-01-01', equity: 200000 }],
                }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useBacktestLab({ optIndex: 'EGX30', showMessage }));

        await act(async () => {
            await result.current.runSimulation();
        });

        await waitFor(() => {
            expect(result.current.simLoading).toBe(false);
            expect(result.current.simResult?.metrics?.total_return).toBe(12.34);
        });

        expect(showMessage).toHaveBeenCalledWith(null);
    });

    it('runs the simulator with an explicit optimizer candidate override', async () => {
        const showMessage = jest.fn();
        const candidateParams = {
            RSI_MIN: 45,
            RSI_MAX: 80,
            VOL_SPIKE: 2.0,
            MOMENTUM: 3.0,
            SL_PCT: 2.0,
            TP1_PCT: 6.0,
            MAX_POSITIONS: 5,
            TRAILING_STOP_ENABLED: true,
            TRAILING_STOP_TYPE: 'PERCENT',
            TRAILING_STOP_VALUE: 2.5,
        };
        global.fetch = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
            const body = JSON.parse(String(init?.body));
            expect(body.params).toEqual(candidateParams);
            return {
                ok: true,
                text: async () =>
                    JSON.stringify({
                        metrics: { total_return: 9.1, final_value: 109100, trade_count: 11 },
                        equity_curve: [{ date: '2025-01-01', equity: 100000 }],
                    }),
            } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useBacktestLab({ optIndex: 'EGX30', showMessage }));

        await act(async () => {
            await (result.current.runSimulation as any)(candidateParams);
        });

        await waitFor(() => {
            expect(result.current.simResult?.metrics?.total_return).toBe(9.1);
        });
    });

    it('shows a guidance message when simulator run completes with zero trades', async () => {
        const showMessage = jest.fn();
        global.fetch = jest.fn(async () => ({
            ok: true,
            text: async () =>
                JSON.stringify({
                    metrics: { total_return: 0, final_value: 200000, trade_count: 0 },
                    equity_curve: [],
                }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useBacktestLab({ optIndex: 'EGX30', showMessage }));

        await act(async () => {
            await result.current.runSimulation();
        });

        await waitFor(() => {
            expect(result.current.simLoading).toBe(false);
            expect(result.current.simResult?.metrics?.trade_count).toBe(0);
        });

        expect(showMessage).toHaveBeenCalledWith({
            type: 'success',
            text: 'Backtest completed with 0 trades. Try a wider date window or less strict filters.',
        });
    });

    it('opens the apply confirmation and commits settings on confirm', async () => {
        const showMessage = jest.fn();
        global.fetch = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
            const body = JSON.parse(String(init?.body));
            expect(body).toEqual({
                params: expect.objectContaining({ RSI_MIN: 55 }),
            });
            return {
                ok: true,
                text: async () => JSON.stringify({ status: 'success' }),
            } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useBacktestLab({ optIndex: 'ALL', showMessage }));

        act(() => {
            result.current.promptApplySettings({ RSI_MIN: 55 });
        });

        expect(result.current.applyConfirmOpen).toBe(true);

        await act(async () => {
            await result.current.confirmApplySettings();
        });

        expect(result.current.applyConfirmOpen).toBe(false);
        expect(showMessage).toHaveBeenCalledWith({
            type: 'success',
            text: 'Settings applied successfully.',
        });
    });

    it('loads Pine profiles only after switching the Backtester source to Pine Profile', async () => {
        const showMessage = jest.fn();
        const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    text: async () =>
                        JSON.stringify({
                            status: 'success',
                            profiles: [
                                {
                                    profile_id: 7,
                                    profile_name: 'Draft Pine Breakout',
                                    profile_state: 'DRAFT',
                                    market: 'EGX70',
                                    timeframe: '1W',
                                },
                            ],
                        }),
                } as Response;
            }
            return {
                ok: true,
                text: async () => JSON.stringify({}),
            } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useBacktestLab({ optIndex: 'ALL', showMessage, enabled: true }));

        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/strategy/pine/scanner-profiles'))).toHaveLength(0);

        act(() => {
            result.current.setBacktestSource('PINE_PROFILE');
        });

        await waitFor(() => {
            expect(result.current.profileRegistry).toHaveLength(1);
        });

        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/strategy/pine/scanner-profiles'))).toHaveLength(1);

        act(() => {
            result.current.setSelectedPineProfileId(7);
        });

        expect(result.current.selectedPineProfile?.profile_name).toBe('Draft Pine Breakout');
        expect(result.current.pineRunConfig.market).toBe('EGX70');
        expect(result.current.pineRunConfig.timeframe).toBe('1W');
    });

    it('routes Pine profile runs through the detail endpoint and Pine backtest API', async () => {
        const showMessage = jest.fn();
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    text: async () =>
                        JSON.stringify({
                            status: 'success',
                            profiles: [
                                {
                                    profile_id: 7,
                                    profile_name: 'Draft Pine Breakout',
                                    profile_state: 'DRAFT',
                                    market: 'EGX70',
                                    timeframe: '1W',
                                },
                            ],
                        }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/scanner-profile/7')) {
                return {
                    ok: true,
                    text: async () =>
                        JSON.stringify({
                            status: 'success',
                            profile: {
                                profile_id: 7,
                                profile_name: 'Draft Pine Breakout',
                                profile_state: 'DRAFT',
                                market: 'EGX70',
                                timeframe: '1W',
                            },
                            script_source: '//@version=5\nstrategy("Draft Pine Breakout")',
                        }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/backtest') && init?.method === 'POST') {
                const body = JSON.parse(String(init?.body));
                expect(body).toEqual({
                    script_source: '//@version=5\nstrategy("Draft Pine Breakout")',
                    market: 'EGX70',
                    timeframe: '1W',
                    date_from: expect.any(String),
                    date_to: expect.any(String),
                    capital: 100000,
                    commission_pct: 0.05,
                    slippage_pct: 0.1,
                });
                return {
                    ok: true,
                    text: async () =>
                        JSON.stringify({
                            status: 'success',
                            metrics: { total_return: 6.2, final_value: 106200, trade_count: 5 },
                            equity_curve: [{ date: '2026-01-01', equity: 100000 }],
                        }),
                } as Response;
            }
            return {
                ok: true,
                text: async () => JSON.stringify({}),
            } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useBacktestLab({ optIndex: 'ALL', showMessage, enabled: true }));

        act(() => {
            result.current.setBacktestSource('PINE_PROFILE');
        });

        await waitFor(() => {
            expect(result.current.profileRegistry).toHaveLength(1);
        });

        act(() => {
            result.current.setSelectedPineProfileId(7);
        });

        await act(async () => {
            await result.current.runBacktest();
        });

        await waitFor(() => {
            expect(result.current.simResult?.metrics?.total_return).toBe(6.2);
            expect(result.current.simResult?.source_metadata?.backtest_source).toBe('PINE_PROFILE');
            expect(result.current.simResult?.source_metadata?.profile_name).toBe('Draft Pine Breakout');
            expect(result.current.simResult?.source_metadata?.profile_state).toBe('DRAFT');
        });

        expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/strategy/pine/scanner-profile/7'))).toBe(true);
        expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/strategy/pine/backtest'))).toBe(true);
        expect(showMessage).toHaveBeenCalledWith(null);
    });

    it('routes saved imported Pine profiles through the import backtest API', async () => {
        const showMessage = jest.fn();
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    text: async () =>
                        JSON.stringify({
                            status: 'success',
                            profiles: [
                                {
                                    profile_id: 9,
                                    profile_name: 'Imported Pine Breakout',
                                    profile_state: 'READY',
                                    source_type: 'PINE_LOGIC_IMPORT',
                                    market: 'EGX30',
                                    timeframe: '1D',
                                },
                            ],
                        }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/scanner-profile/9')) {
                return {
                    ok: true,
                    text: async () =>
                        JSON.stringify({
                            status: 'success',
                            profile: {
                                profile_id: 9,
                                profile_name: 'Imported Pine Breakout',
                                profile_state: 'READY',
                                source_type: 'PINE_LOGIC_IMPORT',
                                market: 'EGX30',
                                timeframe: '1D',
                            },
                            script_source: '//@version=5\nindicator("Imported Pine Breakout")',
                            import_rule_spec: {
                                source: {
                                    import_mode: 'LOGIC_IMPORT',
                                },
                                execution_plan: {
                                    execution_mode: 'LONG_ONLY',
                                },
                            },
                        }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/import-backtest') && init?.method === 'POST') {
                const body = JSON.parse(String(init?.body));
                expect(body).toEqual({
                    rule_spec: {
                        source: {
                            import_mode: 'LOGIC_IMPORT',
                        },
                        execution_plan: {
                            execution_mode: 'LONG_ONLY',
                        },
                    },
                    operator_approved: true,
                    market: 'EGX30',
                    timeframe: '1D',
                    date_from: expect.any(String),
                    date_to: expect.any(String),
                    capital: 100000,
                    commission_pct: 0.05,
                    slippage_pct: 0.1,
                });
                return {
                    ok: true,
                    text: async () =>
                        JSON.stringify({
                            status: 'success',
                            import_mode: 'LOGIC_IMPORT',
                            backtest_source: 'IMPORTED_RULE_SPEC',
                            metrics: { total_return: 4.8, final_value: 104800, trade_count: 4 },
                            equity_curve: [{ date: '2026-01-01', equity: 100000 }],
                        }),
                } as Response;
            }
            return {
                ok: true,
                text: async () => JSON.stringify({}),
            } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useBacktestLab({ optIndex: 'ALL', showMessage, enabled: true }));

        act(() => {
            result.current.setBacktestSource('PINE_PROFILE');
        });

        await waitFor(() => {
            expect(result.current.profileRegistry).toHaveLength(1);
        });

        act(() => {
            result.current.setSelectedPineProfileId(9);
        });

        await act(async () => {
            await result.current.runBacktest();
        });

        await waitFor(() => {
            expect(result.current.simResult?.metrics?.total_return).toBe(4.8);
            expect(result.current.simResult?.source_metadata?.profile_name).toBe('Imported Pine Breakout');
            expect(result.current.simResult?.source_metadata?.profile_source_type).toBe('PINE_LOGIC_IMPORT');
        });

        expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/strategy/pine/import-backtest'))).toBe(true);
        expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/strategy/pine/backtest'))).toBe(false);
    });
});
