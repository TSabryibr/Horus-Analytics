import { act, renderHook, waitFor } from '@testing-library/react';

import { useTelegramRuntime } from './useTelegramRuntime';

describe('useTelegramRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        (Element.prototype as any).scrollIntoView = jest.fn();
    });

    it('loads config on mount and manages log and modal state', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({
                configured: true,
                auto_intraday: true,
            }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useTelegramRuntime());

        await waitFor(() => {
            expect(result.current.config?.configured).toBe(true);
        });

        act(() => {
            result.current.addToLog('Runtime ready');
            result.current.openConfigModal();
        });

        expect(result.current.log[0]).toContain('Runtime ready');
        expect(result.current.isConfigModalOpen).toBe(true);

        act(() => {
            result.current.clearLog();
            result.current.closeConfigModal();
        });

        expect(result.current.log).toEqual([]);
        expect(result.current.isConfigModalOpen).toBe(false);
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/telegram/config'),
            expect.objectContaining({
                headers: {},
            })
        );
    });

    it('suppresses expected offline bootstrap errors', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        global.fetch = jest.fn(async () => {
            throw new TypeError('Failed to fetch');
        }) as jest.Mock;

        renderHook(() => useTelegramRuntime());

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalled();
        });

        expect(consoleErrorSpy).not.toHaveBeenCalled();
        consoleErrorSpy.mockRestore();
    });
});
