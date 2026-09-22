import { Dispatch, SetStateAction, useEffect, useRef, useState } from 'react';
import { AuditLog } from '@/types/domain';
import { mergeAuditLog } from '../lib/auditTransforms';
import type { AuditResponse } from './useAuditRuntime';
import { getWsBase } from '@/lib/api';

interface UseAuditStreamOptions {
    apiBase: string;
    setAudit: Dispatch<SetStateAction<AuditResponse | null>>;
}

const MAX_RECONNECT_DELAY = 30_000;
const INITIAL_RECONNECT_DELAY = 1_000;
const HEARTBEAT_INTERVAL = 30_000;

export function useAuditStream({ apiBase, setAudit }: UseAuditStreamOptions) {
    const [wsConnected, setWsConnected] = useState(false);
    const reconnectDelay = useRef(INITIAL_RECONNECT_DELAY);
    const heartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);
    const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const socketRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        let mounted = true;

        function clearHeartbeat() {
            if (heartbeatTimer.current) {
                clearInterval(heartbeatTimer.current);
                heartbeatTimer.current = null;
            }
        }

        function startHeartbeat() {
            clearHeartbeat();
            heartbeatTimer.current = setInterval(() => {
                const s = socketRef.current;
                if (s && s.readyState === WebSocket.OPEN) {
                    s.send(JSON.stringify({ type: 'ping' }));
                }
            }, HEARTBEAT_INTERVAL);
        }

        function connect() {
            if (!mounted) return;

            const wsUrl = getWsBase() + '/ws';
            const socket = new WebSocket(wsUrl);
            socketRef.current = socket;

            socket.onopen = () => {
                if (!mounted) return;
                setWsConnected(true);
                reconnectDelay.current = INITIAL_RECONNECT_DELAY;
                startHeartbeat();
            };

            socket.onmessage = (event) => {
                try {
                    const payload = JSON.parse(event.data);
                    if (payload.type !== 'audit') {
                        return;
                    }

                    const newLog = payload.data as AuditLog;
                    setAudit((prev) => {
                        if (!prev) {
                            return prev;
                        }

                        const nextLogs = mergeAuditLog(prev.logs, newLog);
                        if (nextLogs === prev.logs) {
                            return prev;
                        }

                        return {
                            ...prev,
                            logs: nextLogs,
                        };
                    });
                } catch (error) {
                    console.error('WS parse error:', error);
                }
            };

            socket.onerror = () => {
                console.error('WebSocket error — will attempt reconnect');
            };

            socket.onclose = () => {
                if (!mounted) return;
                clearHeartbeat();
                setWsConnected(false);
                socketRef.current = null;

                reconnectTimer.current = setTimeout(() => {
                    reconnectDelay.current = Math.min(reconnectDelay.current * 2, MAX_RECONNECT_DELAY);
                    connect();
                }, reconnectDelay.current);
            };
        }

        connect();

        return () => {
            mounted = false;
            clearHeartbeat();
            if (reconnectTimer.current) {
                clearTimeout(reconnectTimer.current);
            }
            const s = socketRef.current;
            if (s) {
                s.onclose = null;
                s.close();
                socketRef.current = null;
            }
        };
    }, [apiBase, setAudit]);

    return { wsConnected };
}
