import { act, renderHook, waitFor } from '@testing-library/react';

import { useTelegramConfig } from './useTelegramConfig';

describe('useTelegramConfig', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('hydrates the form from config and saves updates successfully', async () => {
        const addToLog = jest.fn();
        const setSending = jest.fn();
        const closeConfigModal = jest.fn();
        const refreshConfig = jest.fn(async () => ({
            configured: true,
            auto_intraday: false,
            auto_daily: true,
            auto_horus_eye: true,
            auto_ai_daily_report: false,
            auto_weekly_report: true,
            auto_monthly_report: false,
        }));

        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: 'success' }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() =>
            useTelegramConfig({
                apiBase: 'http://localhost:8000/api/v1',
                buildHeaders: (includeJson = false) => (includeJson ? { 'Content-Type': 'application/json' } : {}),
                addToLog,
                setSending,
                closeConfigModal,
                refreshConfig,
            })
        );

        act(() => {
            result.current.hydrateConfigForm({
                auto_intraday: false,
                auto_daily: true,
                auto_horus_eye: true,
                auto_ai_daily_report: false,
                auto_weekly_report: true,
                auto_monthly_report: false,
            });
        });

        expect(result.current.configForm.auto_intraday).toBe(false);
        expect(result.current.configForm.auto_weekly_report).toBe(true);

        await act(async () => {
            await result.current.handleUpdateConfig({
                preventDefault: jest.fn(),
            } as any);
        });

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/telegram/config'),
                expect.objectContaining({ method: 'POST' })
            );
            expect(closeConfigModal).toHaveBeenCalled();
            expect(refreshConfig).toHaveBeenCalled();
        });
    });
});
