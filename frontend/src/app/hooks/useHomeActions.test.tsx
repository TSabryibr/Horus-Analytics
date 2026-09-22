import { act, renderHook } from '@testing-library/react';

import { useHomeActions } from './useHomeActions';
import { getBaseUrl } from '@/lib/api';

const mockSetOperatingMode = jest.fn();

jest.mock('../context/GlobalDataContext', () => ({
    useSignalDeskData: () => ({
        setOperatingMode: mockSetOperatingMode,
    }),
}));

describe('useHomeActions', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.spyOn(console, 'error').mockImplementation(() => { });
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    it('posts the initialize-run payload and clears loading after success', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: 'queued' }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useHomeActions());

        await act(async () => {
            await result.current.initializeRun();
        });

        expect(global.fetch).toHaveBeenCalledWith(
            `${getBaseUrl()}/api/v1/control/scan`,
            expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'DAILY', notify: true }),
            }),
        );
        expect(result.current.initializeLoading).toBe(false);
    });

    it('clears loading and logs when the initialize-run request fails', async () => {
        global.fetch = jest.fn(async () => {
            throw new Error('network down');
        }) as jest.Mock;

        const { result } = renderHook(() => useHomeActions());

        await act(async () => {
            await result.current.initializeRun();
        });

        expect(console.error).toHaveBeenCalled();
        expect(result.current.initializeLoading).toBe(false);
    });

    it('forwards desk mode changes through the shared signal desk context', async () => {
        mockSetOperatingMode.mockResolvedValue(true);

        const { result } = renderHook(() => useHomeActions());

        await act(async () => {
            await result.current.setDeskMode('AUTOPILOT', true);
        });

        expect(mockSetOperatingMode).toHaveBeenCalledWith('AUTOPILOT', true);
    });
});
