'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { getWsBase } from '@/lib/api';

export interface PriceTick {
    ticker: string;
    price: number;
    change?: number;
    direction: 'up' | 'down' | 'neutral';
    timestamp: number;
}

interface UsePortfolioWebSocketOptions {
    apiBase?: string;
    WebSocketImpl?: typeof WebSocket;
    activeTickers?: string[];
}

export function usePortfolioWebSocket(options: UsePortfolioWebSocketOptions = {}) {
    const [livePrices, setLivePrices] = useState<Record<string, PriceTick>>({});
    const [wsConnected, setWsConnected] = useState(false);

    const socketRef = useRef<WebSocket | null>(null);
    const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const backoffRef = useRef(1000);
    const mountedRef = useRef(true);

    const clearReconnectTimer = useCallback(() => {
        if (reconnectTimerRef.current) {
            clearTimeout(reconnectTimerRef.current);
            reconnectTimerRef.current = null;
        }
    }, []);

    useEffect(() => {
        mountedRef.current = true;

        const connect = () => {
            if (!mountedRef.current) return;

            const wsUrl = options.apiBase
                ? options.apiBase.replace(/^http/, 'ws') + '/ws'
                : getWsBase() + '/ws';

            try {
                const SocketImpl = options.WebSocketImpl || (typeof WebSocket !== 'undefined' ? WebSocket : null);
                if (!SocketImpl) return;

                const socket = new SocketImpl(wsUrl);
                socketRef.current = socket;

                socket.onopen = () => {
                    if (!mountedRef.current) return;
                    backoffRef.current = 1000;
                    setWsConnected(true);
                };

                socket.onmessage = (event: MessageEvent | { data: string }) => {
                    try {
                        const payload = JSON.parse(String(event.data));
                        const ticker = payload.ticker || payload.symbol || (payload.data && (payload.data.ticker || payload.data.symbol));
                        const price = payload.price || (payload.data && payload.data.price);

                        if (ticker && typeof price === 'number' && price > 0) {
                            const sym = String(ticker).toUpperCase();
                            setLivePrices((prev) => {
                                const oldPrice = prev[sym]?.price || price;
                                const direction: 'up' | 'down' | 'neutral' =
                                    price > oldPrice ? 'up' : price < oldPrice ? 'down' : 'neutral';
                                return {
                                    ...prev,
                                    [sym]: {
                                        ticker: sym,
                                        price,
                                        change: price - oldPrice,
                                        direction,
                                        timestamp: Date.now(),
                                    },
                                };
                            });
                        }
                    } catch (err) {
                        // Ignore non-json or unformatted messages
                    }
                };

                socket.onerror = () => {
                    // Reconnect on next tick
                };

                socket.onclose = () => {
                    if (!mountedRef.current) return;
                    setWsConnected(false);
                    const delay = Math.min(backoffRef.current, 30000);
                    backoffRef.current = backoffRef.current * 2;
                    reconnectTimerRef.current = setTimeout(connect, delay);
                };
            } catch (err) {
                console.warn('Portfolio WS connection error:', err);
            }
        };

        connect();

        return () => {
            mountedRef.current = false;
            clearReconnectTimer();
            if (socketRef.current) {
                try {
                    socketRef.current.close();
                } catch {
                    // Ignore close on unmounted
                }
                socketRef.current = null;
            }
        };
    }, [options.apiBase, options.WebSocketImpl, clearReconnectTimer]);

    return {
        livePrices,
        wsConnected,
    };
}
