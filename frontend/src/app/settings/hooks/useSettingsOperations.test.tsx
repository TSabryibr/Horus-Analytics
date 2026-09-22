import { act, renderHook, waitFor } from '@testing-library/react';

import { useSettingsOperations } from './useSettingsOperations';

describe('useSettingsOperations', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
        jest.useRealTimers();
    });

    it('starts backfill, polls status, and reports completion', async () => {
        jest.useFakeTimers();
        jest.spyOn(window, 'confirm').mockReturnValue(true);
        const setMessage = jest.fn();
        let statusCalls = 0;

        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/backfill?days=126&universe=FULL')) {
                return { ok: true, json: async () => ({}) } as Response;
            }
            if (url.includes('/api/v1/system/backfill/status')) {
                statusCalls += 1;
                return {
                    ok: true,
                    json: async () =>
                        statusCalls === 1
                            ? { status: 'RUNNING', current_day: '2026-03-01', progress: 0, total_days: 2, signals_found: 3, universe_choice: 'FULL', error: null }
                            : { status: 'COMPLETED', current_day: '2026-03-02', progress: 1, total_days: 2, signals_found: 7, universe_choice: 'FULL', error: null },
                } as Response;
            }
            throw new Error(`Unhandled fetch ${url}`);
        }) as jest.Mock;

        const { result } = renderHook(() =>
            useSettingsOperations({
                apiBase: 'http://127.0.0.1:8000',
                backfillTradingDays: 126,
                backfillUniverseChoice: 'FULL',
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleBackfill();
        });

        expect(window.confirm).toHaveBeenCalledWith(
            'This will rerun historical backfill for up to 126 trading days using the FULL universe to rebuild SWING and INTRADAY signal history.\n\nContinue?'
        );
        expect(result.current.backfill.status).toBe('RUNNING');

        await act(async () => {
            jest.advanceTimersByTime(4000);
        });

        await waitFor(() => {
            expect(result.current.backfill.status).toBe('COMPLETED');
            expect(setMessage).toHaveBeenCalledWith('Historical backfill complete for FULL: 7 signals across 2 trading days (Swing: 0, Intraday: 0).');
        });
    });

    it('reports provisioning warnings when history coverage is short', async () => {
        jest.useFakeTimers();
        jest.spyOn(window, 'confirm').mockReturnValue(true);
        const setMessage = jest.fn();
        let statusCalls = 0;

        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/backfill?days=252&universe=EGX30')) {
                return { ok: true, json: async () => ({}) } as Response;
            }
            if (url.includes('/api/v1/system/backfill/status')) {
                statusCalls += 1;
                return {
                    ok: true,
                    json: async () =>
                        statusCalls === 1
                            ? { status: 'RUNNING', current_day: '2026-03-01', progress: 0, total_days: 252, signals_found: 3, universe_choice: 'EGX30', error: null }
                            : { status: 'COMPLETED_WITH_WARNINGS', current_day: '2026-03-02', progress: 199, total_days: 200, signals_found: 7, universe_choice: 'EGX30', error: 'Short historical coverage' },
                } as Response;
            }
            throw new Error(`Unhandled fetch ${url}`);
        }) as jest.Mock;

        const { result } = renderHook(() =>
            useSettingsOperations({
                apiBase: 'http://127.0.0.1:8000',
                backfillTradingDays: 252,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleBackfill();
        });

        await act(async () => {
            jest.advanceTimersByTime(4000);
        });

        await waitFor(() => {
            expect(result.current.backfill.status).toBe('COMPLETED_WITH_WARNINGS');
            expect(setMessage).toHaveBeenCalledWith(
                'Historical backfill complete with limited coverage for EGX30: 7 signals across 200 trading days. Short historical coverage'
            );
        });
    });

    it('runs hard reset after double confirmation and reports success', async () => {
        jest.spyOn(window, 'confirm').mockReturnValue(true);
        const setMessage = jest.fn();

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/system/hard-reset/token')) {
                return { ok: true, json: async () => ({ token: 'abc' }) } as Response;
            }
            if (url.includes('/api/v1/system/hard-reset') && init?.method === 'POST') {
                return { ok: true, json: async () => ({ status: 'ok' }) } as Response;
            }
            throw new Error(`Unhandled fetch ${url}`);
        }) as jest.Mock;

        const { result } = renderHook(() =>
            useSettingsOperations({
                apiBase: 'http://127.0.0.1:8000',
                backfillTradingDays: 252,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleHardReset();
        });

        expect(window.confirm).toHaveBeenCalledTimes(2);
        expect(setMessage).toHaveBeenCalledWith('HARD RESET SUCCESSFUL. Please shut down and restart the Python backend server now.');
    });

    it('does nothing when confirmations are rejected', async () => {
        jest.spyOn(window, 'confirm').mockReturnValue(false);
        const setMessage = jest.fn();
        global.fetch = jest.fn() as jest.Mock;

        const { result } = renderHook(() =>
            useSettingsOperations({
                apiBase: 'http://127.0.0.1:8000',
                backfillTradingDays: 252,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleHardReset();
        });

        expect(global.fetch).not.toHaveBeenCalled();
        expect(setMessage).not.toHaveBeenCalled();
    });
});
