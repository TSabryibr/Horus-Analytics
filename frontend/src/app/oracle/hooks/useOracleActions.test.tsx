import { act, renderHook, waitFor } from '@testing-library/react';

import { useOracleActions } from './useOracleActions';

jest.mock('@/lib/api', () => ({
    apiFetch: jest.fn(),
    readJsonSafe: jest.fn(),
}));

const { apiFetch, readJsonSafe } = jest.requireMock('@/lib/api') as {
    apiFetch: jest.Mock;
    readJsonSafe: jest.Mock;
};

describe('useOracleActions', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('dispatches refresh actions through the seam', () => {
        const refreshOracle = jest.fn();
        const refreshOracleNoCache = jest.fn();
        const refreshOracleWithProvider = jest.fn();

        const { result } = renderHook(() =>
            useOracleActions({
                aiReport: { status: 'success' },
                refreshOracle,
                refreshOracleNoCache,
                refreshOracleWithProvider,
            })
        );

        act(() => {
            result.current.handleRefresh();
            result.current.handleRefreshNoCache();
            result.current.handleRefreshWithProvider('OLLAMA');
        });

        expect(refreshOracle).toHaveBeenCalledTimes(1);
        expect(refreshOracleNoCache).toHaveBeenCalledTimes(1);
        expect(refreshOracleWithProvider).toHaveBeenCalledWith('OLLAMA');
    });

    it('maps successful broadcasts to the current success message', async () => {
        apiFetch.mockResolvedValue({ ok: true });
        readJsonSafe.mockResolvedValue({ status: 'sent' });

        const { result } = renderHook(() =>
            useOracleActions({
                aiReport: { status: 'success' },
                refreshOracle: jest.fn(),
                refreshOracleNoCache: jest.fn(),
                refreshOracleWithProvider: jest.fn(),
            })
        );

        await act(async () => {
            await result.current.handleBroadcastAiReport();
        });

        await waitFor(() => {
            expect(apiFetch).toHaveBeenCalledWith(
                '/api/v1/ai/daily-report/broadcast',
                expect.objectContaining({ method: 'POST' })
            );
            expect(result.current.broadcastFeedback).toBe('AI daily report broadcast sent to Telegram.');
            expect(result.current.broadcastingReport).toBe(false);
        });
    });

    it('maps broadcast failures and network errors through the seam', async () => {
        apiFetch.mockResolvedValueOnce({ ok: false });
        readJsonSafe.mockResolvedValueOnce({ detail: 'Broadcast failed hard' });

        const { result } = renderHook(() =>
            useOracleActions({
                aiReport: { status: 'success' },
                refreshOracle: jest.fn(),
                refreshOracleNoCache: jest.fn(),
                refreshOracleWithProvider: jest.fn(),
            })
        );

        await act(async () => {
            await result.current.handleBroadcastAiReport();
        });

        expect(result.current.broadcastFeedback).toBe('Broadcast failed hard');

        apiFetch.mockRejectedValueOnce(new TypeError('Network error'));

        await act(async () => {
            await result.current.handleBroadcastAiReport();
        });

        expect(result.current.broadcastFeedback).toBe('Network error while broadcasting AI report.');
    });
});
