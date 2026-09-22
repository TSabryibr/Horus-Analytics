import { act, renderHook } from '@testing-library/react';

import { useScannerExecution } from './useScannerExecution';

const mockUsePolling = jest.fn();

jest.mock('@/hooks/usePolling', () => ({
    usePolling: (...args: unknown[]) => mockUsePolling(...args),
}));

describe('useScannerExecution', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockUsePolling.mockClear();
    });

    it('disables polling when scanner execution is inactive', () => {
        renderHook(() =>
            useScannerExecution({
                index: 'ALL',
                isIntraday: false,
                isPolling: false,
                setData: jest.fn(),
                setError: jest.fn(),
                setErrorTitle: jest.fn(),
                setIsPolling: jest.fn(),
                setLoading: jest.fn(),
                setProgress: jest.fn(),
            }),
        );

        expect(mockUsePolling).toHaveBeenCalledWith(
            expect.any(Function),
            expect.objectContaining({ enabled: false }),
        );
    });

    it('starts a scan and enables polling on success', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ started: true }),
        }) as Response) as jest.Mock;

        const setData = jest.fn();
        const setError = jest.fn();
        const setErrorTitle = jest.fn();
        const setIsPolling = jest.fn();
        const setLoading = jest.fn();
        const setProgress = jest.fn();

        const { result } = renderHook(() =>
            useScannerExecution({
                index: 'EGX70',
                isIntraday: true,
                isPolling: false,
                setData,
                setError,
                setErrorTitle,
                setIsPolling,
                setLoading,
                setProgress,
            }),
        );

        await act(async () => {
            await result.current.runScan();
        });

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/scanner/start?index=EGX70&intraday=true'),
            expect.objectContaining({ method: 'POST' }),
        );
        expect(setLoading).toHaveBeenCalledWith(true);
        expect(setError).toHaveBeenCalledWith('');
        expect(setErrorTitle).toHaveBeenCalledWith('Connection Error');
        expect(setProgress).toHaveBeenCalledWith('Starting...');
        expect(setData).toHaveBeenCalledWith(null);
        expect(setIsPolling).toHaveBeenCalledWith(true);
    });

    it('maps stale-mode failures to the correct title and message', async () => {
        global.fetch = jest.fn(async () => ({
            ok: false,
            json: async () => ({
                status: 'stale_mode',
                message: 'Read-only stale mode is active.',
                pipeline_state: 'SYNCING',
            }),
        }) as Response) as jest.Mock;

        const setError = jest.fn();
        const setErrorTitle = jest.fn();
        const setIsPolling = jest.fn();
        const setLoading = jest.fn();
        const setProgress = jest.fn();

        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

        const { result } = renderHook(() =>
            useScannerExecution({
                index: 'ALL',
                isIntraday: false,
                isPolling: false,
                setData: jest.fn(),
                setError,
                setErrorTitle,
                setIsPolling,
                setLoading,
                setProgress,
            }),
        );

        await act(async () => {
            await result.current.runScan();
        });

        expect(setErrorTitle).toHaveBeenCalledWith('Read-Only Stale Mode');
        expect(setError).toHaveBeenCalledWith('Read-only stale mode is active. (SYNCING)');
        expect(setLoading).toHaveBeenCalledWith(false);
        expect(setProgress).toHaveBeenCalledWith('');
        expect(setIsPolling).not.toHaveBeenCalledWith(true);

        consoleErrorSpy.mockRestore();
    });

    it('applies completed polling results through the provided setters', async () => {
        const completedPayload = { regime: 'BULLISH', breadth: 50, signals_count: 0, signals: [] };
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: 'COMPLETED', result: completedPayload }),
        }) as Response) as jest.Mock;

        const setData = jest.fn();
        const setError = jest.fn();
        const setIsPolling = jest.fn();
        const setLoading = jest.fn();
        const setProgress = jest.fn();

        renderHook(() =>
            useScannerExecution({
                index: 'ALL',
                isIntraday: false,
                isPolling: true,
                setData,
                setError,
                setErrorTitle: jest.fn(),
                setIsPolling,
                setLoading,
                setProgress,
            }),
        );

        const pollStatus = mockUsePolling.mock.calls[0][0] as () => Promise<void>;

        await act(async () => {
            await pollStatus();
        });

        expect(setData).toHaveBeenCalledWith(completedPayload);
        expect(setIsPolling).toHaveBeenCalledWith(false);
        expect(setLoading).toHaveBeenCalledWith(false);
        expect(setProgress).toHaveBeenCalledWith('');
        expect(setError).not.toHaveBeenCalledWith('Lost connection to API during scan.');
    });
});
