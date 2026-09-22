import { act, renderHook, waitFor } from '@testing-library/react';

import { useSovereignAlerts } from './useSovereignAlerts';

class MockWebSocket {
    static instances: MockWebSocket[] = [];

    url: string;
    onopen: (() => void) | null = null;
    onmessage: ((event: { data: string }) => void) | null = null;
    onerror: (() => void) | null = null;
    onclose: (() => void) | null = null;
    close = jest.fn();

    constructor(url: string) {
        this.url = url;
        MockWebSocket.instances.push(this);
    }

    simulateOpen() {
        this.onopen?.();
    }

    simulateClose() {
        this.onclose?.();
    }
}

describe('useSovereignAlerts', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        MockWebSocket.instances = [];
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    it('subscribes to the websocket and buffers only sovereign alerts', async () => {
        const { result } = renderHook(() =>
            useSovereignAlerts({
                apiBase: 'http://127.0.0.1:8000',
                WebSocketImpl: MockWebSocket as unknown as typeof WebSocket,
            })
        );

        expect(MockWebSocket.instances).toHaveLength(1);
        expect(MockWebSocket.instances[0]?.url).toBe('ws://127.0.0.1:8000/ws');

        act(() => {
            MockWebSocket.instances[0]?.simulateOpen();
        });

        await waitFor(() => {
            expect(result.current.wsConnected).toBe(true);
        });

        act(() => {
            MockWebSocket.instances[0]?.onmessage?.({
                data: JSON.stringify({ type: 'other', data: { Type: 'IGNORED', Message: 'skip' } }),
            });
            MockWebSocket.instances[0]?.onmessage?.({
                data: JSON.stringify({ type: 'sovereign', data: { Type: 'DEBT_STRESS', Message: 'Yield spike' } }),
            });
        });

        await waitFor(() => {
            expect(result.current.sovereignAlerts).toEqual([
                { Type: 'DEBT_STRESS', Message: 'Yield spike' },
            ]);
        });
    });

    it('caps the alert buffer at five items and supports dismiss', async () => {
        const { result } = renderHook(() =>
            useSovereignAlerts({
                apiBase: 'http://127.0.0.1:8000',
                WebSocketImpl: MockWebSocket as unknown as typeof WebSocket,
            })
        );

        act(() => {
            for (let index = 0; index < 6; index += 1) {
                MockWebSocket.instances[0]?.onmessage?.({
                    data: JSON.stringify({
                        type: 'sovereign',
                        data: { Type: `ALERT_${index}`, Message: `Message ${index}` },
                    }),
                });
            }
        });

        await waitFor(() => {
            expect(result.current.sovereignAlerts).toHaveLength(5);
            expect(result.current.sovereignAlerts[0]?.Type).toBe('ALERT_5');
            expect(result.current.sovereignAlerts[4]?.Type).toBe('ALERT_1');
        });

        act(() => {
            result.current.dismissSovereignAlert(1);
        });

        expect(result.current.sovereignAlerts).toHaveLength(4);
        expect(result.current.sovereignAlerts.map((item) => item.Type)).toEqual([
            'ALERT_5',
            'ALERT_3',
            'ALERT_2',
            'ALERT_1',
        ]);
    });

    it('closes the socket on cleanup', () => {
        const { unmount } = renderHook(() =>
            useSovereignAlerts({
                apiBase: 'http://127.0.0.1:8000',
                WebSocketImpl: MockWebSocket as unknown as typeof WebSocket,
            })
        );

        unmount();

        expect(MockWebSocket.instances[0]?.close).toHaveBeenCalled();
    });

    it('reconnects with exponential backoff after disconnect', async () => {
        const { result } = renderHook(() =>
            useSovereignAlerts({
                apiBase: 'http://127.0.0.1:8000',
                WebSocketImpl: MockWebSocket as unknown as typeof WebSocket,
            })
        );

        act(() => {
            MockWebSocket.instances[0]?.simulateOpen();
        });

        await waitFor(() => {
            expect(result.current.wsConnected).toBe(true);
        });

        act(() => {
            MockWebSocket.instances[0]?.simulateClose();
        });

        await waitFor(() => {
            expect(result.current.wsConnected).toBe(false);
        });

        expect(MockWebSocket.instances).toHaveLength(1);

        act(() => {
            jest.advanceTimersByTime(1000);
        });

        await waitFor(() => {
            expect(MockWebSocket.instances).toHaveLength(2);
        });

        expect(MockWebSocket.instances[1]?.url).toBe('ws://127.0.0.1:8000/ws');
    });

    it('resets backoff on successful connection', async () => {
        const { result } = renderHook(() =>
            useSovereignAlerts({
                apiBase: 'http://127.0.0.1:8000',
                WebSocketImpl: MockWebSocket as unknown as typeof WebSocket,
            })
        );

        act(() => {
            MockWebSocket.instances[0]?.simulateOpen();
        });

        await waitFor(() => {
            expect(result.current.wsConnected).toBe(true);
        });

        act(() => {
            MockWebSocket.instances[0]?.simulateClose();
        });

        act(() => {
            jest.advanceTimersByTime(1000);
        });

        await waitFor(() => {
            expect(MockWebSocket.instances).toHaveLength(2);
        });

        act(() => {
            MockWebSocket.instances[1]?.simulateOpen();
        });

        await waitFor(() => {
            expect(result.current.wsConnected).toBe(true);
        });

        act(() => {
            MockWebSocket.instances[1]?.simulateClose();
        });

        act(() => {
            jest.advanceTimersByTime(1000);
        });

        await waitFor(() => {
            expect(MockWebSocket.instances).toHaveLength(3);
        });
    });

    it('exposes wsConnected state', async () => {
        const { result } = renderHook(() =>
            useSovereignAlerts({
                apiBase: 'http://127.0.0.1:8000',
                WebSocketImpl: MockWebSocket as unknown as typeof WebSocket,
            })
        );

        expect(result.current.wsConnected).toBe(false);

        act(() => {
            MockWebSocket.instances[0]?.simulateOpen();
        });

        await waitFor(() => {
            expect(result.current.wsConnected).toBe(true);
        });
    });
});
