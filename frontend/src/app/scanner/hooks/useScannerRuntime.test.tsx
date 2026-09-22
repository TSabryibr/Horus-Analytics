import { act, renderHook, waitFor } from '@testing-library/react';

import { useScannerRuntime } from './useScannerRuntime';

const completedScannerPayload = {
    regime: 'BULLISH',
    breadth: 62.5,
    signals_count: 1,
    signals: [
        {
            Ticker: 'COMI',
            Signal_Type: 'BUY',
            Signal_Setup: 'BREAKOUT',
            Conviction: 'HIGH',
            Entry_Price: 104.5,
            Stop_Loss: 99.9,
            Target_Price: 110.0,
            Target_Price_2: 114.0,
            Score: 4.2,
            Volume_x: 2.3,
        },
    ],
};

describe('useScannerRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.spyOn(console, 'error').mockImplementation(() => { });
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    it('hydrates completed scanner status into local route state', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: 'COMPLETED', result: completedScannerPayload }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useScannerRuntime());

        await waitFor(() => {
            expect(result.current.data).toEqual(completedScannerPayload);
            expect(result.current.hasData).toBe(true);
            expect(result.current.errorTitle).toBe('Connection Error');
            expect(result.current.loading).toBe(false);
        });
    });

    it('restores running status and exposes filter state setters', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/scanner/status')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'RUNNING' }),
                } as Response;
            }
            return {
                ok: true,
                json: async () => ({
                    status: 'success',
                    active_profile_id: 7,
                    profiles: [
                        {
                            profile_id: 7,
                            profile_name: 'EGX Breakout Pine',
                            source_type: 'PINE',
                            market: 'EGX30',
                            timeframe: '1D',
                            profile_state: 'ACTIVE',
                        },
                    ],
                }),
            } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useScannerRuntime());

        await waitFor(() => {
            expect(result.current.isPolling).toBe(true);
            expect(result.current.scannerProfiles).toHaveLength(1);
            expect(result.current.selectedProfileId).toBe('7');
        });

        act(() => {
            result.current.setIndex('EGX70');
            result.current.setIsIntraday(true);
        });

        expect(result.current.index).toBe('EGX70');
        expect(result.current.isIntraday).toBe(true);
        expect(result.current.hasData).toBe(false);
    });

    it('fails safely when initial scanner status cannot be loaded', async () => {
        global.fetch = jest.fn(async () => {
            throw new TypeError('Network error');
        }) as jest.Mock;

        const { result } = renderHook(() => useScannerRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.data).toBeNull();
        expect(result.current.hasData).toBe(false);
        expect(result.current.isPolling).toBe(false);
    });

    it('suppresses expected offline bootstrap noise', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        global.fetch = jest.fn(async () => {
            throw new TypeError('Failed to fetch');
        }) as jest.Mock;

        renderHook(() => useScannerRuntime());

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalled();
        });

        expect(consoleErrorSpy).not.toHaveBeenCalled();
        consoleErrorSpy.mockRestore();
    });
});
