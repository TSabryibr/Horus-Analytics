import { act, renderHook, waitFor } from '@testing-library/react';

import { useRagnarokSimulation } from './useRagnarokSimulation';

describe('useRagnarokSimulation', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
    });

    it('submits ticker-normalized payloads and stores successful results', async () => {
        global.fetch = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
            expect(JSON.parse(String(init?.body))).toEqual({
                iterations: 500,
                days: 10,
                tickers: ['COMI', 'ETEL'],
                ruin_threshold_pct: 50,
            });
            return {
                ok: true,
                json: async () => ({
                    status: 'success',
                    data: {
                        expected_value: 1050000,
                        var_95: 820000,
                        loss_probability: 20.0,
                        ruin_probability: 15.5,
                        ruin_threshold_pct: 50,
                        ruin_floor: 500000,
                        starting_value: 1000000,
                        iterations: 500,
                        days: 10,
                        assets_count: 2,
                        assets_used: ['COMI', 'ETEL'],
                        plot_paths: [[1, 2, 3]],
                    },
                }),
            } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useRagnarokSimulation({ apiBase: 'http://127.0.0.1:8000' }));

        act(() => {
            result.current.setTickerInput('comi, etel ');
            result.current.setRagnarokIterations('500');
            result.current.setRagnarokDays('10');
        });

        await act(async () => {
            await result.current.runRagnarokSimulation();
        });

        await waitFor(() => {
            expect(result.current.ragnarokLoading).toBe(false);
            expect(result.current.ragnarokError).toBeNull();
            expect(result.current.ragnarokResult?.assets_used).toEqual(['COMI', 'ETEL']);
        });
    });

    it('stores the backend error message on failure responses', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({
                status: 'error',
                message: 'Ragnarok backend unavailable.',
            }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useRagnarokSimulation({ apiBase: 'http://127.0.0.1:8000' }));

        await act(async () => {
            await result.current.runRagnarokSimulation();
        });

        expect(result.current.ragnarokLoading).toBe(false);
        expect(result.current.ragnarokError).toBe('Ragnarok backend unavailable.');
    });
});
