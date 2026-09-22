'use client';

import { useEffect, useRef, useState } from 'react';

import { getApiBase, isIgnorableNetworkError } from '@/lib/api';

const API_BASE = getApiBase();

export function useTelegramRuntime() {
    const [config, setConfig] = useState<any>(null);
    const [sending, setSending] = useState(false);
    const [log, setLog] = useState<string[]>([]);
    const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
    const logEndRef = useRef<HTMLDivElement>(null);

    const buildHeaders = (includeJson: boolean = false): HeadersInit => {
        const headers: Record<string, string> = {};
        if (includeJson) {
            headers['Content-Type'] = 'application/json';
        }
        return headers;
    };

    const refreshConfig = async () => {
        const res = await fetch(`${API_BASE}/telegram/config`, {
            headers: buildHeaders(),
        });
        if (!res.ok) {
            throw new Error(`${res.status} ${res.statusText}`);
        }
        const data = await res.json();
        setConfig(data);
        return data;
    };

    useEffect(() => {
        refreshConfig().catch((error) => {
            if (isIgnorableNetworkError(error)) {
                return;
            }
            console.error(error);
        });
    }, []);

    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [log]);

    const addToLog = (msg: string) => {
        setLog((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev]);
    };

    const clearLog = () => {
        setLog([]);
    };

    const openConfigModal = () => {
        setIsConfigModalOpen(true);
    };

    const closeConfigModal = () => {
        setIsConfigModalOpen(false);
    };

    return {
        config,
        setConfig,
        sending,
        setSending,
        log,
        setLog,
        addToLog,
        clearLog,
        isConfigModalOpen,
        setIsConfigModalOpen,
        openConfigModal,
        closeConfigModal,
        buildHeaders,
        refreshConfig,
        logEndRef,
    };
}
