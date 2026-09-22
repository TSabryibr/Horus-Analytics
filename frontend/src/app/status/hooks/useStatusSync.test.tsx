import { act, renderHook, waitFor } from '@testing-library/react';

import { useStatusSync } from './useStatusSync';

describe('useStatusSync', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('sets syncing state and message when the sync status is RUNNING', async () => {
        global.fetch = jest.fn(async () => ({ ok: true, json: async () => ({ status: 'RUNNING' }) } as Response)) as jest.Mock;

        const { result } = renderHook(() => useStatusSync({
            apiBase: 'http://127.0.0.1:8000',
            fetchStatus: jest.fn(),
        }));

        await act(async () => {
            await result.current.fetchDataSyncStatus();
        });

        expect(result.current.syncingData).toBe(true);
        expect(result.current.syncStatusMessage).toBe('Data sync in progress...');
    });

    it('transitions RUNNING to COMPLETED and refreshes status', async () => {
        const fetchStatus = jest.fn();
        const syncStates = ['RUNNING', 'COMPLETED'];
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: syncStates.shift() ?? 'IDLE' }),
        } as Response)) as jest.Mock;

        const { result } = renderHook(() => useStatusSync({
            apiBase: 'http://127.0.0.1:8000',
            fetchStatus,
        }));

        await act(async () => {
            await result.current.fetchDataSyncStatus();
            await result.current.fetchDataSyncStatus();
        });

        expect(result.current.syncStatusMessage).toBe('Data sync completed.');
        expect(fetchStatus).toHaveBeenCalledTimes(1);
    });

    it('starts sync and handles already-running responses', async () => {
        const fetchMock = jest.fn()
            .mockResolvedValueOnce({ ok: true, json: async () => ({ started: true }) } as Response)
            .mockResolvedValueOnce({ ok: true, json: async () => ({ started: false, message: 'Data sync already running.' }) } as Response);
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useStatusSync({
            apiBase: 'http://127.0.0.1:8000',
            fetchStatus: jest.fn(),
        }));

        await act(async () => {
            await result.current.triggerDataSync();
        });

        await waitFor(() => {
            expect(result.current.syncingData).toBe(true);
            expect(result.current.syncStatusMessage).toBe('Data sync started.');
        });

        act(() => {
            result.current.setSyncingData(false);
        });

        await act(async () => {
            await result.current.triggerDataSync();
        });

        expect(result.current.syncStatusMessage).toBe('Data sync already running.');
        expect(result.current.syncingData).toBe(true);
    });
});
