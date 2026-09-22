import { renderHook, act } from '@testing-library/react';
import { usePortfolioWebSocket } from './usePortfolioWebSocket';

describe('usePortfolioWebSocket', () => {
    class MockWebSocket {
        static instances: MockWebSocket[] = [];
        onopen: (() => void) | null = null;
        onmessage: ((event: { data: string }) => void) | null = null;
        onerror: (() => void) | null = null;
        onclose: (() => void) | null = null;
        url: string;

        constructor(url: string) {
            this.url = url;
            MockWebSocket.instances.push(this);
            setTimeout(() => this.onopen?.(), 0);
        }

        close() {
            this.onclose?.();
        }
    }

    beforeEach(() => {
        MockWebSocket.instances = [];
    });

    it('connects and receives price ticks', async () => {
        const { result } = renderHook(() =>
            usePortfolioWebSocket({
                apiBase: 'http://localhost:8000',
                WebSocketImpl: MockWebSocket as any,
            })
        );

        await act(async () => {
            await new Promise((r) => setTimeout(r, 10));
        });

        expect(result.current.wsConnected).toBe(true);

        // Simulate incoming tick
        act(() => {
            const socket = MockWebSocket.instances[0];
            socket.onmessage?.({
                data: JSON.stringify({ ticker: 'COMI', price: 86.5 }),
            });
        });

        expect(result.current.livePrices['COMI']).toBeDefined();
        expect(result.current.livePrices['COMI'].price).toBe(86.5);
    });
});
