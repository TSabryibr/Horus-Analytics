'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { getWsBase } from '@/lib/api';

export interface SovereignAlert {
    Type: string;
    Message: string;
}

interface UseSovereignAlertsOptions {
    apiBase?: string;
    WebSocketImpl?: typeof WebSocket;
}

export function useSovereignAlerts(options: UseSovereignAlertsOptions = {}) {
    const [sovereignAlerts, setSovereignAlerts] = useState<SovereignAlert[]>([]);
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
            const SocketImpl = options.WebSocketImpl || WebSocket;
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
                    if (payload.type === 'sovereign') {
                        setSovereignAlerts((prev) => [payload.data, ...prev].slice(0, 5));
                    }
                } catch (err) {
                    console.error('Live WS parse error:', err);
                }
            };

            socket.onerror = () => {
                console.warn('Live WS error — will attempt reconnect');
            };

            socket.onclose = () => {
                if (!mountedRef.current) return;
                setWsConnected(false);
                const delay = Math.min(backoffRef.current, 30000);
                backoffRef.current = backoffRef.current * 2;
                reconnectTimerRef.current = setTimeout(connect, delay);
            };
        };

        connect();

        return () => {
            mountedRef.current = false;
            clearReconnectTimer();
            if (reconnectTimerRef.current) {
                clearTimeout(reconnectTimerRef.current);
                reconnectTimerRef.current = null;
            }
            socketRef.current?.close();
            socketRef.current = null;
        };
    }, [options.WebSocketImpl, options.apiBase, clearReconnectTimer]);

    const dismissSovereignAlert = (index: number) => {
        setSovereignAlerts((prev) => prev.filter((_, currentIndex) => currentIndex !== index));
    };

    return {
        sovereignAlerts,
        dismissSovereignAlert,
        wsConnected,
    };
}
