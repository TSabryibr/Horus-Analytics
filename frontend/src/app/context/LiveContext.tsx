'use client';

import React, { createContext, useContext, useState, useCallback, useRef, useEffect, ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { getApiBase, isIgnorableNetworkError } from '@/lib/api';
import { usePolling } from '@/hooks/usePolling';

const API_BASE = getApiBase();
const LIVE_TICKERS_CACHE_TTL_MS = 30_000;
const LIVE_STATUS_CACHE_TTL_MS = 5_000;

let liveTickersCache:
    | {
        data: string[];
        fetchedAt: number;
    }
    | null = null;

let liveStatusCache:
    | {
        data: LiveStatusResponse;
        fetchedAt: number;
    }
    | null = null;

export interface Candle {
    Date: string;
    Time?: string;
    Open: number;
    High: number;
    Low: number;
    Close: number;
    Volume: number;
    timeLabel: string;
    wickRange: [number, number];
    bodyRange: [number, number];
    isBullish: boolean;
}

export interface LiveStatusResponse {
    status: string;
    running: boolean;
    market_open?: boolean;
    message?: string;
    last_update?: string | null;
}

interface LiveContextType {
    ticker: string;
    setTicker: (t: string) => void;
    tickers: string[];
    liveStatus: LiveStatusResponse | null;
    liveRunning: boolean;
    marketOpen: boolean;
    candleData: Candle[];
    loading: boolean;
    refreshing: boolean;
    error: string | null;
    setError: (e: string | null) => void;
    lastUpdate: string;
    fetchLiveStatus: () => Promise<void>;
    fetchIntradayData: (mode?: 'initial' | 'background') => Promise<void>;
    handleLiveFeedAction: (action: 'start' | 'stop') => Promise<LiveStatusResponse | null>;
}

const LiveContext = createContext<LiveContextType | undefined>(undefined);

const toNumber = (value: unknown): number => {
    const normalized = typeof value === 'string' ? value.replace(/,/g, '') : value;
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : 0;
};

const toTimeLabel = (value: string): string => {
    if (!value) return '--:--';
    const parsedDate = new Date(value);
    if (!Number.isNaN(parsedDate.getTime())) {
        return parsedDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    }
    const match = value.match(/(\d{2}:\d{2})/);
    if (match?.[1]) return match[1];
    const parts = value.split(' ');
    return parts[1]?.slice(0, 5) ?? value.slice(-5);
};

const parseCandle = (row: Record<string, unknown>): Candle => {
    const date = String(row.Date ?? row.date ?? row.datetime ?? row.timestamp ?? row.time ?? row.Time ?? '');
    const open = toNumber(row.Open ?? row.open ?? row.o);
    const high = toNumber(row.High ?? row.high ?? row.h);
    const low = toNumber(row.Low ?? row.low ?? row.l);
    const close = toNumber(row.Close ?? row.close ?? row.c);
    const baseLow = Math.min(open, close);
    const baseHigh = Math.max(open, close);
    const dojiPad = baseHigh === baseLow ? Math.max((high - low) * 0.0025, 0.0001) : 0;

    return {
        Date: date,
        Time: row.Time ? String(row.Time) : undefined,
        Open: open,
        High: high,
        Low: low,
        Close: close,
        Volume: toNumber(row.Volume ?? row.volume ?? row.vol ?? row.v),
        timeLabel: toTimeLabel(date),
        wickRange: [low, high],
        bodyRange: [baseLow, baseHigh + dojiPad],
        isBullish: close >= open,
    };
};

export function __resetLiveContextCachesForTests() {
    liveTickersCache = null;
    liveStatusCache = null;
}

export function LiveProvider({ children, enabled: enabledProp }: { children: ReactNode; enabled?: boolean }) {
    const pathname = usePathname();
    const enabled = enabledProp ?? pathname === '/live';
    const [ticker, setTicker] = useState('COMI');
    const [tickers, setTickers] = useState<string[]>([]);
    const [liveStatus, setLiveStatus] = useState<LiveStatusResponse | null>(null);
    const [candleData, setCandleData] = useState<Candle[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdate, setLastUpdate] = useState('');

    const abortRef = useRef<AbortController | null>(null);
    const requestSeqRef = useRef(0);

    const safeFetch = useCallback(async <T,>(path: string, init?: RequestInit): Promise<T | null> => {
        if (!enabled) {
            return null;
        }
        try {
            const res = await fetch(`${API_BASE}${path}`, {
                cache: 'no-store',
                ...init,
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json() as T;
        } catch (err) {
            if (!isIgnorableNetworkError(err)) {
                console.warn(`Fetch failed for ${path}:`, err);
            }
            return null;
        }
    }, [enabled]);

    const fetchLiveStatus = useCallback(async () => {
        if (!enabled) {
            return;
        }
        const now = Date.now();
        if (liveStatusCache && now - liveStatusCache.fetchedAt < LIVE_STATUS_CACHE_TTL_MS) {
            setLiveStatus(liveStatusCache.data);
            return;
        }
        const status = await safeFetch<LiveStatusResponse>('/live/status');
        if (status) {
            liveStatusCache = {
                data: status,
                fetchedAt: now,
            };
            setLiveStatus(status);
        }
    }, [enabled, safeFetch]);

    const fetchIntradayData = useCallback(async (mode: 'initial' | 'background' = 'background') => {
        if (!enabled || !ticker) return;
        if (!ticker) return;
        if (mode === 'initial') setLoading(true);
        else setRefreshing(true);

        abortRef.current?.abort();
        const controller = new AbortController();
        abortRef.current = controller;
        const requestId = ++requestSeqRef.current;

        try {
            const res = await fetch(`${API_BASE}/data/intraday/${ticker}?limit=240`, {
                cache: 'no-store',
                signal: controller.signal,
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            const rows = Array.isArray(json) ? json : (json.data || []);
            
            const parsed = rows.map(parseCandle).filter((c: any) => Number.isFinite(c.Close));
            if (requestId !== requestSeqRef.current) return;
            
            setCandleData(parsed);
            setLastUpdate(new Date().toLocaleTimeString());
        } catch (e: any) {
            if (e.name !== 'AbortError') setError('Failed to load intraday stream');
        } finally {
            if (requestId === requestSeqRef.current) {
                setLoading(false);
                setRefreshing(false);
            }
        }
    }, [enabled, ticker]);

    const handleLiveFeedAction = useCallback(async (action: 'start' | 'stop') => {
        if (!enabled) {
            return null;
        }
        const response = await safeFetch<LiveStatusResponse>(`/live/${action}`, { method: 'POST' });
        if (response) {
            liveStatusCache = {
                data: response,
                fetchedAt: Date.now(),
            };
            setLiveStatus(response);
            if (response.status === 'market_closed') {
                return response;
            }

            await fetchLiveStatus();
            if (action === 'start') {
                void fetchIntradayData('background');
            }
        }
        return response;
    }, [enabled, fetchLiveStatus, fetchIntradayData, safeFetch]);

    // Initial Tickers
    useEffect(() => {
        if (!enabled) {
            return;
        }
        const loadTickers = async () => {
            const now = Date.now();
            if (liveTickersCache && now - liveTickersCache.fetchedAt < LIVE_TICKERS_CACHE_TTL_MS) {
                setTickers(liveTickersCache.data);
                if (!liveTickersCache.data.includes(ticker)) {
                    setTicker(liveTickersCache.data[0] || 'COMI');
                }
                return;
            }

            const data = await safeFetch<string[]>('/data/tickers');
            if (Array.isArray(data)) {
                liveTickersCache = {
                    data,
                    fetchedAt: now,
                };
                setTickers(data);
                if (!data.includes(ticker)) setTicker(data[0] || 'COMI');
            }
        };
        void loadTickers();
    }, [enabled, safeFetch]);

    useEffect(() => {
        if (enabled) {
            return;
        }

        abortRef.current?.abort();
        setLiveStatus(null);
        setCandleData([]);
        setLoading(false);
        setRefreshing(false);
        setError(null);
    }, [enabled]);

    useEffect(() => {
        if (!enabled || !ticker) {
            return;
        }

        void fetchIntradayData('initial');
    }, [enabled, ticker, fetchIntradayData]);

    // Persistent Polling (Disable pauseWhenHidden)
    usePolling(fetchLiveStatus, { enabled, intervalMs: 10_000, runImmediately: true, pauseWhenHidden: false });
    usePolling(() => {
        if (liveStatus?.running && liveStatus?.market_open !== false) {
            void fetchIntradayData('background');
        }
    }, { enabled: enabled && !!liveStatus?.running && liveStatus?.market_open !== false, intervalMs: 15_000, pauseWhenHidden: false });

    const value = {
        ticker, setTicker, tickers, liveStatus,
        liveRunning: !!liveStatus?.running,
        marketOpen: liveStatus?.market_open !== false,
        candleData, loading, refreshing, error, setError, lastUpdate,
        fetchLiveStatus, fetchIntradayData, handleLiveFeedAction,
    };

    return <LiveContext.Provider value={value}>{children}</LiveContext.Provider>;
}

export function useLiveContext() {
    const context = useContext(LiveContext);
    if (!context) throw new Error('useLiveContext must be used within a LiveProvider');
    return context;
}
