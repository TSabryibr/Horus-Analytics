'use client';

import { useEffect, useMemo, useState } from 'react';
import { getBaseUrl, isIgnorableNetworkError } from '@/lib/api';

export interface SettingsState {
    LOOKBACK?: number;
    VOL_SPIKE?: number;
    MOMENTUM?: number;
    RSI_MIN?: number;
    RSI_MAX?: number;
    SL_PCT?: number;
    TP1_PCT?: number;
    MIN_TURNOVER?: number;
    TRICKSTER_RSI_MAX?: number;
    TRICKSTER_REL_VOL_MIN?: number;
    TRICKSTER_STRETCH_ATR?: number;
    RISK_PER_TRADE?: number;
    MIN_RISK_REWARD?: number;
    MIN_SIGNAL_SCORE?: number;
    MIN_SIGNAL_CONFIDENCE?: number;
    MAX_DAILY_TRADES?: number;
    MAX_PORTFOLIO_HEAT?: number;
    PENDING_ENTRY_MAX_GAP_PCT?: number;
    USE_ATR_EXITS?: boolean;
    ATR_TP_MULTIPLIER?: number;
    ATR_SL_MULTIPLIER?: number;
    TRAILING_STOP_ENABLED?: boolean;
    TRAILING_STOP_TYPE?: string;
    TRAILING_STOP_VALUE?: number;
    REGIME_FILTER_ENABLED?: boolean;
    REGIME_MODE?: string;
    SECTOR_LIMIT_ENABLED?: boolean;
    MAX_PER_SECTOR?: number;
    SLIPPAGE_PCT?: number;
    COMMISSION_PCT?: number;
    TELEGRAM_TOKEN?: string;
    TELEGRAM_TOKEN_CONFIGURED?: boolean;
    TELEGRAM_TOKEN_PREVIEW?: string | null;
    CHAT_ID?: string;
    CHAT_ID_CONFIGURED?: boolean;
    CHAT_ID_PREVIEW?: string | null;
    TELEGRAM_TEST_BOT_TOKEN?: string;
    TELEGRAM_TEST_BOT_TOKEN_CONFIGURED?: boolean;
    TELEGRAM_TEST_BOT_TOKEN_PREVIEW?: string | null;
    TELEGRAM_TEST_CHAT_ID?: string;
    TELEGRAM_TEST_CHAT_ID_CONFIGURED?: boolean;
    TELEGRAM_TEST_CHAT_ID_PREVIEW?: string | null;
    OLLAMA_API_KEY?: string;
    OLLAMA_API_KEY_CONFIGURED?: boolean;
    OLLAMA_API_KEY_PREVIEW?: string | null;
    OLLAMA_BASE_URL?: string;
    AI_REPORT_OLLAMA_MODEL?: string;
    PINE_IMPORT_TRANSLATION_PROVIDER?: string;
    TELEGRAM_AUTO_BROADCAST_INTRADAY?: boolean;
    TELEGRAM_AUTO_BROADCAST_DAILY?: boolean;
    TELEGRAM_AUTO_BROADCAST_HORUS_EYE?: boolean;
    TELEGRAM_AUTO_BROADCAST_AI_REPORT?: boolean;
    TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT?: boolean;
    TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT?: boolean;
    TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL?: string;
    TELEGRAM_REPORT_LANGUAGE?: string;
    MAX_POSITIONS?: number;
    ENABLE_INTRADAY_ALERTS?: boolean;
    AUTO_TRADE_ENABLED?: boolean;
    SIGNAL_AUTO_EXECUTION_ENABLED?: boolean;
    LIVE_ARM_GUARD_ENABLED?: boolean;
    HEAT_PROTECTION_ENABLED?: boolean;
    LOCAL_HISTORY_PROVIDER?: string;
    LOCAL_INTRADAY_PROVIDER?: string;
    LOCAL_TICKS_PROVIDER?: string;
    TICK_SYNC_ENABLED?: boolean;
    MUBASHER_ROOT_DIR?: string;
    MUBASHER_USER_ID?: string;
    MUBASHER_HISTORY_DB_PATH?: string;
    MUBASHER_HISTORY_DB_AVAILABLE?: boolean;
    MUBASHER_INTRADAY_DB_PATH?: string;
    MUBASHER_INTRADAY_DB_AVAILABLE?: boolean;
    MUBASHER_HISTORICAL_TRADE_FOLDER?: string;
    MUBASHER_HISTORICAL_TRADE_AVAILABLE?: boolean;
    MUBASHER_HISTORICAL_TRADE_DB_COUNT?: number;
    MUBASHER_HISTORICAL_TRADE_LATEST_DATE?: string | null;
    MUBASHER_STREAM_DISCOVERY_ERROR?: string | null;
    METASTOCK_DAT_HISTORY_FOLDER?: string;
    METASTOCK_DAT_HISTORY_AVAILABLE?: boolean;
    METASTOCK_DAT_INTRADAY_FOLDER?: string;
    METASTOCK_DAT_INTRADAY_AVAILABLE?: boolean;
    METASTOCK_INTRADAY_FOLDER?: string;
    METASTOCK_INTRADAY_AVAILABLE?: boolean;
    MARKET_START_HHMM_NORMAL?: string;
    MARKET_END_HHMM_NORMAL?: string;
    MARKET_START_HHMM_RAMADAN?: string;
    MARKET_END_HHMM_RAMADAN?: string;
    RAMADAN_MODE?: boolean;
    PRE_CLOSE_OFFSET_MINS?: number;
    DAILY_SIGNAL_OFFSET_MINS?: number;
    INTRADAY_INTERVAL_MINS?: number;
    HISTORICAL_BACKFILL_TRADING_DAYS?: number;
    HISTORICAL_BACKFILL_SIGNAL_LANES?: string;
    PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS?: number;
    PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES?: boolean;
    PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT?: number;
    PORTFOLIO_MGMT_REPORT_ACTION_ITEMS_LIMIT?: number;
    PORTFOLIO_MGMT_REPORT_RISK_RECOMMENDATIONS_LIMIT?: number;
    PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT?: number;
    PORTFOLIO_MGMT_PREPARE_TP_PROXIMITY_PCT?: number;
    PORTFOLIO_MGMT_TP2_PCT?: number;
    PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN?: number;
    WEBHOOK_URL?: string;
    WEBHOOK_ENABLED?: boolean;
    [key: string]: string | number | boolean | null | undefined;
}

export interface SignalDeskPolicyState {
    operatingMode: 'MANUAL' | 'AI_ASSIST' | 'AUTOPILOT';
    autopilotArmed: boolean;
    confidenceFloor: number;
    minCandidates: number;
    sourceModules: string[];
    signalTypes: string[];
}

export const DEFAULT_SETTINGS: SettingsState = {
    LOOKBACK: 30,
    VOL_SPIKE: 1.5,
    MOMENTUM: 2.5,
    RSI_MIN: 55,
    RSI_MAX: 85,
    SL_PCT: 1.5,
    TP1_PCT: 4.0,
    MIN_TURNOVER: 2000000,
    TRICKSTER_RSI_MAX: 30.0,
    TRICKSTER_REL_VOL_MIN: 1.2,
    TRICKSTER_STRETCH_ATR: 2.0,
    RISK_PER_TRADE: 2.0,
    MIN_RISK_REWARD: 1.0,
    MIN_SIGNAL_SCORE: 0.0,
    MIN_SIGNAL_CONFIDENCE: 0.0,
    MAX_DAILY_TRADES: 3,
    MAX_PORTFOLIO_HEAT: 6.0,
    PENDING_ENTRY_MAX_GAP_PCT: 1.5,
    TRAILING_STOP_ENABLED: false,
    TRAILING_STOP_TYPE: 'FIXED',
    TRAILING_STOP_VALUE: 2.0,
    REGIME_FILTER_ENABLED: false,
    REGIME_MODE: 'AUTO',
    SECTOR_LIMIT_ENABLED: false,
    MAX_PER_SECTOR: 2,
    USE_ATR_EXITS: false,
    SLIPPAGE_PCT: 0.1,
    COMMISSION_PCT: 0.05,
    TELEGRAM_TOKEN: '',
    TELEGRAM_TOKEN_CONFIGURED: false,
    TELEGRAM_TOKEN_PREVIEW: '',
    CHAT_ID: '',
    CHAT_ID_CONFIGURED: false,
    CHAT_ID_PREVIEW: '',
    TELEGRAM_TEST_BOT_TOKEN: '',
    TELEGRAM_TEST_BOT_TOKEN_CONFIGURED: false,
    TELEGRAM_TEST_BOT_TOKEN_PREVIEW: '',
    TELEGRAM_TEST_CHAT_ID: '',
    TELEGRAM_TEST_CHAT_ID_CONFIGURED: false,
    TELEGRAM_TEST_CHAT_ID_PREVIEW: '',
    OLLAMA_API_KEY: '',
    OLLAMA_API_KEY_CONFIGURED: false,
    OLLAMA_API_KEY_PREVIEW: '',
    OLLAMA_BASE_URL: 'http://127.0.0.1:11434',
    AI_REPORT_OLLAMA_MODEL: 'qwen3-coder:30b',
    PINE_IMPORT_TRANSLATION_PROVIDER: 'LOCAL',
    TELEGRAM_AUTO_BROADCAST_INTRADAY: true,
    TELEGRAM_AUTO_BROADCAST_DAILY: true,
    TELEGRAM_AUTO_BROADCAST_HORUS_EYE: true,
    TELEGRAM_AUTO_BROADCAST_AI_REPORT: true,
    TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT: false,
    TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT: false,
    TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL: 'none',
    TELEGRAM_REPORT_LANGUAGE: 'EN',
    AUTO_TRADE_ENABLED: false,
    SIGNAL_AUTO_EXECUTION_ENABLED: false,
    LIVE_ARM_GUARD_ENABLED: false,
    HEAT_PROTECTION_ENABLED: true,
    LOCAL_HISTORY_PROVIDER: 'MUBASHER_DB',
    LOCAL_INTRADAY_PROVIDER: 'MUBASHER_DB',
    LOCAL_TICKS_PROVIDER: 'MUBASHER_DB',
    TICK_SYNC_ENABLED: true,
    MUBASHER_ROOT_DIR: '',
    MUBASHER_USER_ID: '',
    MUBASHER_HISTORY_DB_PATH: '',
    MUBASHER_HISTORY_DB_AVAILABLE: false,
    MUBASHER_INTRADAY_DB_PATH: '',
    MUBASHER_INTRADAY_DB_AVAILABLE: false,
    MUBASHER_HISTORICAL_TRADE_FOLDER: '',
    MUBASHER_HISTORICAL_TRADE_AVAILABLE: false,
    MUBASHER_HISTORICAL_TRADE_DB_COUNT: 0,
    MUBASHER_HISTORICAL_TRADE_LATEST_DATE: '',
    MUBASHER_STREAM_DISCOVERY_ERROR: '',
    MARKET_START_HHMM_NORMAL: '1000',
    MARKET_END_HHMM_NORMAL: '1430',
    MARKET_START_HHMM_RAMADAN: '1000',
    MARKET_END_HHMM_RAMADAN: '1330',
    RAMADAN_MODE: false,
    PRE_CLOSE_OFFSET_MINS: 20,
    DAILY_SIGNAL_OFFSET_MINS: 30,
    INTRADAY_INTERVAL_MINS: 5,
    HISTORICAL_BACKFILL_TRADING_DAYS: 252,
    HISTORICAL_BACKFILL_SIGNAL_LANES: 'BOTH',
    PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS: 15,
    PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES: true,
    PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT: 15,
    PORTFOLIO_MGMT_REPORT_ACTION_ITEMS_LIMIT: 10,
    PORTFOLIO_MGMT_REPORT_RISK_RECOMMENDATIONS_LIMIT: 8,
    PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT: 3.0,
    PORTFOLIO_MGMT_PREPARE_TP_PROXIMITY_PCT: 1.0,
    PORTFOLIO_MGMT_TP2_PCT: 4.0,
    PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN: 3500,
    WEBHOOK_URL: '',
    WEBHOOK_ENABLED: false,
};

export const DEFAULT_SIGNAL_DESK_POLICY: SignalDeskPolicyState = {
    operatingMode: 'MANUAL',
    autopilotArmed: false,
    confidenceFloor: 0,
    minCandidates: 1,
    sourceModules: ['SCANNER', 'ORACLE', 'WHALES', 'TRAPS', 'ANALYTICS'],
    signalTypes: ['INTRADAY', 'SWING', 'POSITION'],
};

export const fetchJsonWithTimeout = async <T,>(url: string, init?: RequestInit, timeoutMs = 8000, externalSignal?: AbortSignal): Promise<T> => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs);

    const onExternalAbort = () => controller.abort();
    externalSignal?.addEventListener('abort', onExternalAbort);

    try {
        const res = await fetch(url, {
            ...init,
            signal: controller.signal,
        });
        if (!res.ok) {
            throw new Error(`${res.status} ${res.statusText}`);
        }
        return await res.json() as T;
    } finally {
        window.clearTimeout(timeout);
        externalSignal?.removeEventListener('abort', onExternalAbort);
    }
};

export function useSettingsRuntime() {
    const [settings, setSettings] = useState<SettingsState>(DEFAULT_SETTINGS);
    const [original, setOriginal] = useState<SettingsState>(DEFAULT_SETTINGS);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState('');
    const [excluded, setExcluded] = useState<string[]>([]);
    const [originalExcluded, setOriginalExcluded] = useState<string[]>([]);
    const [allTickers, setAllTickers] = useState<string[]>([]);
    const [apiBase, setApiBase] = useState(getBaseUrl());
    const [signalDeskPolicy, setSignalDeskPolicy] = useState<SignalDeskPolicyState>(DEFAULT_SIGNAL_DESK_POLICY);
    const [originalSignalDeskPolicy, setOriginalSignalDeskPolicy] = useState<SignalDeskPolicyState>(DEFAULT_SIGNAL_DESK_POLICY);

    useEffect(() => {
        const controller = new AbortController();
        const signal = controller.signal;

        const base = getBaseUrl();
        setApiBase(base);
        setLoading(true);

        const loadCore = async () => {
            const [settingsResult, exclusionsResult, signalDeskResult] = await Promise.allSettled([
                fetchJsonWithTimeout<Partial<SettingsState>>(`${base}/api/v1/settings`, undefined, 8000, signal),
                fetchJsonWithTimeout<string[]>(`${base}/api/v1/settings/exclusions`, undefined, 8000, signal),
                fetchJsonWithTimeout<{ desk?: {
                    operating_mode?: string;
                    autopilot_armed?: boolean;
                    publish_policy?: {
                        confidence_floor?: number;
                        min_candidates?: number;
                        source_modules?: string[];
                        signal_types?: string[];
                    };
                } }>(`${base}/api/v1/signals/desk`, undefined, 8000, signal),
            ]);

            if (signal.aborted) return;

            const settingsPayload = settingsResult.status === 'fulfilled' ? settingsResult.value : null;
            const exclusionsPayload = exclusionsResult.status === 'fulfilled' ? exclusionsResult.value : null;

            if (settingsPayload) {
                const mergedSettings = { ...DEFAULT_SETTINGS, ...settingsPayload };
                setSettings(mergedSettings);
                setOriginal(mergedSettings);
            } else {
                if (settingsResult.status === 'rejected') {
                    const reason = settingsResult.reason;
                    if (!isIgnorableNetworkError(reason)) {
                        console.error(reason);
                    }
                }
                setSettings(DEFAULT_SETTINGS);
                setOriginal(DEFAULT_SETTINGS);
                setMessage('Failed to load settings payload from backend.');
            }

            if (signalDeskResult.status === 'fulfilled' && signalDeskResult.value?.desk) {
                const desk = signalDeskResult.value.desk;
                const nextPolicy: SignalDeskPolicyState = {
                    operatingMode: desk.operating_mode === 'AUTOPILOT' || desk.operating_mode === 'AI_ASSIST' ? desk.operating_mode : 'MANUAL',
                    autopilotArmed: Boolean(desk.autopilot_armed),
                    confidenceFloor: Number(desk.publish_policy?.confidence_floor ?? DEFAULT_SIGNAL_DESK_POLICY.confidenceFloor),
                    minCandidates: Number(desk.publish_policy?.min_candidates ?? DEFAULT_SIGNAL_DESK_POLICY.minCandidates),
                    sourceModules: Array.isArray(desk.publish_policy?.source_modules)
                        ? desk.publish_policy.source_modules.map((item) => String(item).toUpperCase())
                        : DEFAULT_SIGNAL_DESK_POLICY.sourceModules,
                    signalTypes: Array.isArray(desk.publish_policy?.signal_types)
                        ? desk.publish_policy.signal_types.map((item) => String(item).toUpperCase())
                        : DEFAULT_SIGNAL_DESK_POLICY.signalTypes,
                };
                setSignalDeskPolicy(nextPolicy);
                setOriginalSignalDeskPolicy(nextPolicy);
            } else if (signalDeskResult.status === 'rejected') {
                const reason = signalDeskResult.reason;
                if (!isIgnorableNetworkError(reason)) {
                    console.error(reason);
                }
            }

            if (Array.isArray(exclusionsPayload)) {
                setExcluded(exclusionsPayload);
                setOriginalExcluded(exclusionsPayload);
            } else if (exclusionsResult.status === 'rejected') {
                const reason = exclusionsResult.reason;
                if (!isIgnorableNetworkError(reason)) console.error(reason);
                setExcluded([]);
            }

            if (!signal.aborted) {
                setLoading(false);
            }
        };

        const loadSecondary = async () => {
            const [tickersResult] = await Promise.allSettled([
                fetchJsonWithTimeout<string[]>(`${base}/api/v1/data/tickers`, undefined, 10000, signal),
            ]);

            if (signal.aborted) return;

            if (tickersResult.status === 'fulfilled') {
                setAllTickers(tickersResult.value || []);
            }
        };

        void loadCore();
        void loadSecondary();

        return () => {
            controller.abort();
        };
    }, []);

    const hasChanges = useMemo(
        () =>
            JSON.stringify(settings) !== JSON.stringify(original)
            || JSON.stringify(excluded) !== JSON.stringify(originalExcluded)
            || JSON.stringify(signalDeskPolicy) !== JSON.stringify(originalSignalDeskPolicy),
        [settings, original, excluded, originalExcluded, signalDeskPolicy, originalSignalDeskPolicy]
    );

    const handleChange = (key: string, value: any) => {
        setSettings((prev) => ({ ...prev, [key]: value }));
    };

    const handleSignalDeskPolicyChange = <K extends keyof SignalDeskPolicyState>(key: K, value: SignalDeskPolicyState[K]) => {
        setSignalDeskPolicy((prev) => ({ ...prev, [key]: value }));
    };

    return {
        settings,
        setSettings,
        original,
        setOriginal,
        loading,
        setLoading,
        message,
        setMessage,
        excluded,
        setExcluded,
        originalExcluded,
        setOriginalExcluded,
        signalDeskPolicy,
        setSignalDeskPolicy,
        originalSignalDeskPolicy,
        setOriginalSignalDeskPolicy,
        allTickers,
        apiBase,
        hasChanges,
        handleChange,
        handleSignalDeskPolicyChange,
    };
}
