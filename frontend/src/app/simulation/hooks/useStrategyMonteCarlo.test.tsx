import { act, renderHook, waitFor } from '@testing-library/react';

import { useStrategyMonteCarlo } from './useStrategyMonteCarlo';

describe('useStrategyMonteCarlo', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
    });

    it('submits the Monte Carlo payload and stores successful results', async () => {
        global.fetch = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
            expect(JSON.parse(String(init?.body))).toEqual({
                initial_capital: 250000,
                simulations: 5000,
                ruin_threshold_pct: 50,
            });
            return {
                ok: true,
                json: async () => ({
                    status: 'success',
                    data: {
                        simulations: 5000,
                        median_equity: 110000,
                        worst_case_equity: 70000,
                        best_case_equity: 180000,
                        avg_max_drawdown: 12,
                        median_max_drawdown: 10,
                        worst_max_drawdown: 24,
                        loss_probability: 9.0,
                        ruin_probability: 4.5,
                        ruin_threshold_pct: 50,
                        ruin_floor: 125000,
                        drawdown_probability_20: 15,
                        drawdown_probability_50: 1.2,
                        plot_paths: [[1, 2, 3]],
                    },
                }),
            } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useStrategyMonteCarlo({ apiBase: 'http://127.0.0.1:8000' }));

        act(() => {
            result.current.setMcCapital('250000');
            result.current.setMcSims('5000');
        });

        await act(async () => {
            await result.current.runStrategyMonteCarlo();
        });

        await waitFor(() => {
            expect(result.current.mcLoading).toBe(false);
            expect(result.current.mcError).toBeNull();
            expect(result.current.mcResult?.simulations).toBe(5000);
        });
    });

    it('stores warning messages from the backend', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({
                status: 'warning',
                message: 'Insufficient data for some paths.',
            }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useStrategyMonteCarlo({ apiBase: 'http://127.0.0.1:8000' }));

        await act(async () => {
            await result.current.runStrategyMonteCarlo();
        });

        expect(result.current.mcLoading).toBe(false);
        expect(result.current.mcError).toBe('Insufficient data for some paths.');
    });
});
