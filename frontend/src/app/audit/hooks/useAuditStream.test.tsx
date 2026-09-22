import { renderHook } from '@testing-library/react';

import type { AuditResponse } from './useAuditRuntime';
import { useAuditStream } from './useAuditStream';

class MockWebSocket {
    static instances: MockWebSocket[] = [];

    url: string;
    onmessage: ((event: MessageEvent) => void) | null = null;
    close = jest.fn();

    constructor(url: string) {
        this.url = url;
        MockWebSocket.instances.push(this);
    }
}

const baseAudit: AuditResponse = {
    status: 'success',
    strategies: [],
    logs: [
        {
            id: 'existing',
            timestamp: '2026-03-18T10:00:00Z',
            date: '2026-03-18',
            ticker: 'COMI',
            strategy: 'Falcon',
            action: 'BUY',
            pnl_history: { '1D': 1.2 },
        },
    ],
};

describe('useAuditStream', () => {
    beforeEach(() => {
        MockWebSocket.instances = [];
        (globalThis as typeof globalThis & { WebSocket: typeof MockWebSocket }).WebSocket = MockWebSocket;
        jest.clearAllMocks();
    });

    it('subscribes to the audit socket and inserts new logs at the front', () => {
        const setAudit = jest.fn();

        renderHook(() => useAuditStream({
            apiBase: 'http://127.0.0.1:8000',
            setAudit,
        }));

        expect(MockWebSocket.instances[0]?.url).toBe('ws://localhost/ws');

        MockWebSocket.instances[0]?.onmessage?.({
            data: JSON.stringify({
                type: 'audit',
                data: {
                    id: 'fresh',
                    timestamp: '2026-03-18T11:00:00Z',
                    date: '2026-03-18',
                    ticker: 'HRHO',
                    strategy: 'Wolf',
                    action: 'SELL',
                    pnl_history: { '1D': -0.4 },
                },
            }),
        } as MessageEvent);

        const updater = setAudit.mock.calls[0]?.[0] as (prev: AuditResponse | null) => AuditResponse | null;
        const nextState = updater(baseAudit);
        expect(nextState?.logs[0]?.id).toBe('fresh');
        expect(nextState?.logs).toHaveLength(2);
    });

    it('ignores duplicate logs and closes the socket on unmount', () => {
        const setAudit = jest.fn();

        const { unmount } = renderHook(() => useAuditStream({
            apiBase: 'http://127.0.0.1:8000',
            setAudit,
        }));

        MockWebSocket.instances[0]?.onmessage?.({
            data: JSON.stringify({
                type: 'audit',
                data: {
                    id: 'existing',
                    timestamp: '2026-03-18T10:00:00Z',
                    date: '2026-03-18',
                    ticker: 'COMI',
                    strategy: 'Falcon',
                    action: 'BUY',
                    pnl_history: { '1D': 1.2 },
                },
            }),
        } as MessageEvent);

        const updater = setAudit.mock.calls[0]?.[0] as (prev: AuditResponse | null) => AuditResponse | null;
        expect(updater(baseAudit)).toBe(baseAudit);

        unmount();

        expect(MockWebSocket.instances[0]?.close).toHaveBeenCalledTimes(1);
    });
});
