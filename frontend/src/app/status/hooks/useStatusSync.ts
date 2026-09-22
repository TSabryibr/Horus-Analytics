import { useCallback, useRef, useState } from 'react';
import { createBootstrapRequest } from '../lib/bootstrapRequest';

interface UseStatusSyncOptions {
    apiBase: string;
    fetchStatus: () => void | Promise<void>;
}

type SyncStatusPayload = {
    status?: string;
    last_error?: string;
    [key: string]: unknown;
};

const bootstrapSyncStatusRequest = createBootstrapRequest<SyncStatusPayload>();

export function resetStatusSyncBootstrapCache() {
    bootstrapSyncStatusRequest.reset();
}

async function requestSyncStatus(apiBase: string): Promise<SyncStatusPayload> {
    const res = await fetch(`${apiBase}/api/v1/data/sync/status`, { cache: 'no-store' });
    if (!res.ok) {
        throw new Error('Failed to fetch data sync status');
    }

    return await res.json();
}

export function useStatusSync({ apiBase, fetchStatus }: UseStatusSyncOptions) {
    const [syncingData, setSyncingData] = useState(false);
    const [syncStatusMessage, setSyncStatusMessage] = useState<string | null>(null);
    const lastSyncStateRef = useRef<string>('IDLE');

    const applySyncStatus = useCallback(async (data: SyncStatusPayload) => {
        const nextState = String(data?.status || 'IDLE').toUpperCase();
        const prevState = lastSyncStateRef.current;
        lastSyncStateRef.current = nextState;

        setSyncingData(nextState === 'RUNNING');
        if (nextState === 'RUNNING') {
            setSyncStatusMessage('Data sync in progress...');
        } else if (nextState === 'ERROR') {
            setSyncStatusMessage(`Sync failed: ${data?.last_error || 'Unknown error'}`);
        } else if (prevState === 'RUNNING' && nextState === 'COMPLETED') {
            setSyncStatusMessage('Data sync completed.');
            await fetchStatus();
        }
    }, [fetchStatus]);

    const fetchDataSyncStatus = useCallback(async () => {
        try {
            const data = await requestSyncStatus(apiBase);
            await applySyncStatus(data);
        } catch {
            // Ignore transient polling failures for sync status.
        }
    }, [apiBase, applySyncStatus]);

    const bootstrapDataSyncStatus = useCallback(async () => {
        try {
            const data = await bootstrapSyncStatusRequest(apiBase, () => requestSyncStatus(apiBase));
            await applySyncStatus(data);
        } catch {
            // Ignore transient bootstrap failures for sync status.
        }
    }, [apiBase, applySyncStatus]);

    const triggerDataSync = useCallback(async () => {
        if (syncingData) return;

        setSyncStatusMessage('Starting data sync...');
        try {
            const res = await fetch(`${apiBase}/api/v1/data/sync/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            const data = await res.json();
            if (data?.started) {
                setSyncingData(true);
                setSyncStatusMessage('Data sync started.');
                lastSyncStateRef.current = 'RUNNING';
                return;
            }

            setSyncStatusMessage(data?.message || 'Data sync already running.');
            if (String(data?.message || '').toLowerCase().includes('running')) {
                setSyncingData(true);
                lastSyncStateRef.current = 'RUNNING';
            }
        } catch {
            setSyncStatusMessage('Failed to start data sync.');
        }
    }, [apiBase, syncingData]);

    return {
        syncingData,
        setSyncingData,
        syncStatusMessage,
        setSyncStatusMessage,
        fetchDataSyncStatus,
        bootstrapDataSyncStatus,
        triggerDataSync,
    };
}
