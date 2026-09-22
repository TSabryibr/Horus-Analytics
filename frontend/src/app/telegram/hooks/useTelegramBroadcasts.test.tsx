import { act, renderHook, waitFor } from '@testing-library/react';

import { useTelegramBroadcasts } from './useTelegramBroadcasts';

describe('useTelegramBroadcasts', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('sends a general broadcast and clears the composer on success', async () => {
        const addToLog = jest.fn();
        const setSending = jest.fn();

        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: 'sent' }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() =>
            useTelegramBroadcasts({
                apiBase: 'http://localhost:8000/api/v1',
                buildHeaders: (includeJson = false) => (includeJson ? { 'Content-Type': 'application/json' } : {}),
                addToLog,
                setSending,
                activeRunId: null,
                failedDeliveryCount: 0,
            })
        );

        act(() => {
            result.current.setMessage('Desk update');
            result.current.setImage('data:image/png;base64,abc');
        });

        await act(async () => {
            await result.current.handleBroadcast();
        });

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/telegram/broadcast'),
                expect.objectContaining({ method: 'POST' })
            );
            expect(result.current.message).toBe('');
            expect(result.current.image).toBeNull();
        });
    });

    it('blocks signal broadcast when required fields are missing', async () => {
        const addToLog = jest.fn();
        const setSending = jest.fn();

        const { result } = renderHook(() =>
            useTelegramBroadcasts({
                apiBase: 'http://localhost:8000/api/v1',
                buildHeaders: (includeJson = false) => (includeJson ? { 'Content-Type': 'application/json' } : {}),
                addToLog,
                setSending,
                activeRunId: null,
                failedDeliveryCount: 0,
            })
        );

        await act(async () => {
            await result.current.handleSignalBroadcast();
        });

        expect(addToLog).toHaveBeenCalledWith('⚠️ Missing required signal fields.');
        expect(global.fetch).not.toHaveBeenCalled();
    });

    it('dispatches AI daily report, analysis reports, and scans through their endpoints', async () => {
        const addToLog = jest.fn();
        const setSending = jest.fn();

        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: 'sent', started: true }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() =>
            useTelegramBroadcasts({
                apiBase: 'http://localhost:8000/api/v1',
                buildHeaders: (includeJson = false) => (includeJson ? { 'Content-Type': 'application/json' } : {}),
                addToLog,
                setSending,
                activeRunId: 42,
                failedDeliveryCount: 0,
            })
        );

        await act(async () => {
            await result.current.handleAiDailyReportBroadcast();
            await result.current.handleAnalysisReportBroadcast('weekly');
            await result.current.triggerScan('INTRADAY');
        });

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/ai/daily-report/broadcast'),
            expect.objectContaining({ method: 'POST' })
        );
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/reports/analysis/broadcast'),
            expect.objectContaining({ method: 'POST' })
        );
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/control/scan'),
            expect.objectContaining({ method: 'POST' })
        );
    });

    it('dispatches the latest desk run through the signals publish endpoint', async () => {
        const addToLog = jest.fn();
        const setSending = jest.fn();

        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: 'completed' }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() =>
            useTelegramBroadcasts({
                apiBase: 'http://localhost:8000/api/v1',
                buildHeaders: (includeJson = false) => (includeJson ? { 'Content-Type': 'application/json' } : {}),
                addToLog,
                setSending,
                activeRunId: 77,
                failedDeliveryCount: 0,
            })
        );

        await act(async () => {
            await result.current.handleDeskRelease();
        });

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/signals/publish'),
            expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({ run_id: 77, channel: 'TELEGRAM' }),
            }),
        );
    });

    it('retries failed deliveries through the retry endpoint when desk failures exist', async () => {
        const addToLog = jest.fn();
        const setSending = jest.fn();

        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: 'completed' }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() =>
            useTelegramBroadcasts({
                apiBase: 'http://localhost:8000/api/v1',
                buildHeaders: (includeJson = false) => (includeJson ? { 'Content-Type': 'application/json' } : {}),
                addToLog,
                setSending,
                activeRunId: 77,
                failedDeliveryCount: 2,
            })
        );

        await act(async () => {
            await result.current.handleRetryFailedDeliveries();
        });

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/signals/publish/retry'),
            expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({ run_id: 77, channel: 'TELEGRAM' }),
            }),
        );
    });
});
