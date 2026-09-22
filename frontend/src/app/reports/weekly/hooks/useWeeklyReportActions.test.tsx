import { act, renderHook, waitFor } from '@testing-library/react';

import { useWeeklyReportActions } from './useWeeklyReportActions';

const apiFetchMock = jest.fn();
const readJsonSafeMock = jest.fn();
const pickApiMessageMock = jest.fn((data: any, fallback: string) => data?.detail || fallback);

jest.mock('@/lib/api', () => ({
    apiFetch: (...args: any[]) => apiFetchMock(...args),
    readJsonSafe: (...args: any[]) => readJsonSafeMock(...args),
    pickApiMessage: (...args: any[]) => pickApiMessageMock(...args),
}));

describe('useWeeklyReportActions', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('broadcasts successfully and refreshes the active period', async () => {
        apiFetchMock.mockResolvedValue({ ok: true, endpoint: '/reports/analysis/broadcast' } as any);
        readJsonSafeMock.mockResolvedValue({ status: 'sent' });

        const setFeedback = jest.fn();
        const loadReport = jest.fn().mockResolvedValue(undefined);

        const { result } = renderHook(() =>
            useWeeklyReportActions({
                period: 'weekly',
                loadReport,
                setFeedback,
            }),
        );

        await act(async () => {
            await result.current.broadcastReport();
        });

        await waitFor(() => {
            expect(result.current.broadcasting).toBe(false);
        });

        expect(apiFetchMock).toHaveBeenCalledWith(
            '/reports/analysis/broadcast',
            expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({ period: 'weekly', force_refresh: true }),
            }),
        );
        expect(setFeedback).toHaveBeenCalledWith('');
        expect(setFeedback).toHaveBeenCalledWith('Weekly report broadcast sent to Telegram.');
        expect(loadReport).toHaveBeenCalledWith(true, 'weekly');
    });

    it('reports broadcast failures through feedback', async () => {
        apiFetchMock.mockResolvedValue({ ok: false, endpoint: '/reports/analysis/broadcast' } as any);
        readJsonSafeMock.mockResolvedValue({ detail: 'Broadcast unavailable.' });

        const setFeedback = jest.fn();
        const loadReport = jest.fn();

        const { result } = renderHook(() =>
            useWeeklyReportActions({
                period: 'monthly',
                loadReport,
                setFeedback,
            }),
        );

        await act(async () => {
            await result.current.broadcastReport();
        });

        expect(setFeedback).toHaveBeenCalledWith('Broadcast unavailable.');
        expect(loadReport).not.toHaveBeenCalled();
        expect(result.current.broadcasting).toBe(false);
    });
});
