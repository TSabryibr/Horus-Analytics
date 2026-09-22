import { act, renderHook, waitFor } from '@testing-library/react';

import { useCrashSimulation } from './useCrashSimulation';

describe('useCrashSimulation', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
    });

    it('submits the crash payload and stores successful results', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/stress-test') && init?.method === 'POST') {
                expect(JSON.parse(String(init.body))).toEqual({
                    index: 'EGX70',
                    ref_date: '2020-03-15',
                    initial_capital: 2500000,
                    lookback_days: 365,
                    simulation_days: 5,
                });
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        data: {
                            crash_date: '2020-03-15',
                            market_impact: -12.8,
                            worst_affected: [],
                            least_affected: [],
                        },
                    }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useCrashSimulation({ apiBase: 'http://127.0.0.1:8000' }));

        act(() => {
            result.current.setIndexChoice('EGX70');
            result.current.setStartDate('2020-03-15');
            result.current.setInitialCapital('2500000');
        });

        await act(async () => {
            await result.current.runCrashSimulation();
        });

        await waitFor(() => {
            expect(result.current.stressLoading).toBe(false);
            expect(result.current.stressResult?.crash_date).toBe('2020-03-15');
            expect(result.current.stressResult?.market_impact).toBe(-12.8);
        });
    });

    it('falls back to the default capital when the input is invalid', async () => {
        global.fetch = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
            expect(JSON.parse(String(init?.body)).initial_capital).toBe(1000000);
            return {
                ok: true,
                json: async () => ({
                    status: 'success',
                    data: {
                        crash_date: '2020-03-15',
                        market_impact: -12.8,
                        worst_affected: [],
                        least_affected: [],
                    },
                }),
            } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useCrashSimulation({ apiBase: 'http://127.0.0.1:8000' }));

        act(() => {
            result.current.setInitialCapital('not-a-number');
        });

        await act(async () => {
            await result.current.runCrashSimulation();
        });

        expect(result.current.stressLoading).toBe(false);
    });
});
