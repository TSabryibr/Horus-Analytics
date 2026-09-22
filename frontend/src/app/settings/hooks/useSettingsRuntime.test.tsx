import { act, renderHook, waitFor } from '@testing-library/react';

import { useSettingsRuntime } from './useSettingsRuntime';

const BACKEND_SETTINGS = {
    LOOKBACK: 40,
    VOL_SPIKE: 2.0,
    MOMENTUM: 2.5,
    RSI_MIN: 55,
    RSI_MAX: 85,
    SL_PCT: 1.5,
    TP1_PCT: 4.0,
    MIN_TURNOVER: 2000000,
    TRICKSTER_RSI_MAX: 30.0,
    TRICKSTER_REL_VOL_MIN: 1.2,
    TRICKSTER_STRETCH_ATR: 2.0,
    USE_ATR_EXITS: false,
    MIN_RISK_REWARD: 1.0,
    MIN_SIGNAL_SCORE: 5.0,
    MIN_SIGNAL_CONFIDENCE: 70.0,
    MAX_DAILY_TRADES: 3,
    MAX_PORTFOLIO_HEAT: 6.0,
    PENDING_ENTRY_MAX_GAP_PCT: 1.5,
    AUTO_TRADE_ENABLED: false,
    TRAILING_STOP_ENABLED: false,
    TRAILING_STOP_TYPE: 'FIXED',
    TRAILING_STOP_VALUE: 2.0,
    REGIME_FILTER_ENABLED: false,
    REGIME_MODE: 'AUTO',
    SECTOR_LIMIT_ENABLED: false,
    MAX_PER_SECTOR: 2,
    LOCAL_HISTORY_PROVIDER: 'MUBASHER_DB',
    LOCAL_INTRADAY_PROVIDER: 'METASTOCK_DAT',
    SLIPPAGE_PCT: 0.5,
    COMMISSION_PCT: 0.05,
    TELEGRAM_TOKEN: '',
    CHAT_ID: '',
    PRE_CLOSE_OFFSET_MINS: 20,
    DAILY_SIGNAL_OFFSET_MINS: 30,
    INTRADAY_INTERVAL_MINS: 5,
    HISTORICAL_BACKFILL_TRADING_DAYS: 126,
};

const EXCLUSIONS = ['COMI', 'HRHO'];
const TICKERS = ['COMI', 'HRHO', 'ETEL', 'SWDY', 'AMOC'];

function buildFetchMock(overrides: Record<string, (init?: RequestInit) => Response | Promise<Response>> = {}) {
    return jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        for (const [pattern, handler] of Object.entries(overrides)) {
            if (url.includes(pattern)) return handler(init);
        }

        if (url.includes('/api/v1/settings/exclusions') && (!init?.method || init.method === 'GET')) {
            return { ok: true, json: async () => EXCLUSIONS } as Response;
        }
        if (url.includes('/api/v1/signals/desk') && (!init?.method || init.method === 'GET')) {
            return {
                ok: true,
                json: async () => ({
                    desk: {
                        operating_mode: 'AI_ASSIST',
                        autopilot_armed: true,
                        publish_policy: {
                            confidence_floor: 76,
                            min_candidates: 2,
                            source_modules: ['SCANNER', 'ORACLE'],
                            signal_types: ['INTRADAY', 'SWING'],
                        },
                    },
                }),
            } as Response;
        }
        if (url.includes('/api/v1/settings') && (!init?.method || init.method === 'GET')) {
            return { ok: true, json: async () => ({ ...BACKEND_SETTINGS }) } as Response;
        }
        if (url.includes('/api/v1/data/tickers')) {
            return { ok: true, json: async () => TICKERS } as Response;
        }

        return { ok: true, json: async () => ({}) } as Response;
    }) as jest.Mock;
}

describe('useSettingsRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
    });

    it('loads settings, exclusions, and tickers and tracks dirty state', async () => {
        global.fetch = buildFetchMock();

        const { result } = renderHook(() => useSettingsRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.settings.LOOKBACK).toBe(40);
            expect(result.current.settings.HISTORICAL_BACKFILL_TRADING_DAYS).toBe(126);
            expect(result.current.settings.MIN_SIGNAL_SCORE).toBe(5);
            expect(result.current.settings.MIN_SIGNAL_CONFIDENCE).toBe(70);
            expect(result.current.settings.MAX_PORTFOLIO_HEAT).toBe(6);
            expect(result.current.excluded).toEqual(EXCLUSIONS);
            expect(result.current.allTickers).toEqual(TICKERS);
            expect(result.current.apiBase).toBe(window.location.origin);
            expect(result.current.signalDeskPolicy.operatingMode).toBe('AI_ASSIST');
            expect(result.current.signalDeskPolicy.autopilotArmed).toBe(true);
            expect(result.current.signalDeskPolicy.confidenceFloor).toBe(76);
            expect(result.current.hasChanges).toBe(false);
        });

        act(() => {
            result.current.handleChange('MOMENTUM', 3.1);
        });

        expect(result.current.settings.MOMENTUM).toBe(3.1);
        expect(result.current.hasChanges).toBe(true);
    });

    it('tracks desk policy changes as dirty state', async () => {
        global.fetch = buildFetchMock();

        const { result } = renderHook(() => useSettingsRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        act(() => {
            result.current.handleSignalDeskPolicyChange('operatingMode', 'AUTOPILOT');
        });

        expect(result.current.signalDeskPolicy.operatingMode).toBe('AUTOPILOT');
        expect(result.current.hasChanges).toBe(true);
    });

    it('keeps loaded settings when exclusions fail', async () => {
        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        global.fetch = buildFetchMock({
            '/api/v1/settings/exclusions': () => {
                throw new TypeError('Network error');
            },
        });

        const { result } = renderHook(() => useSettingsRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.settings.LOOKBACK).toBe(40);
            expect(result.current.excluded).toEqual([]);
            expect(result.current.hasChanges).toBe(false);
        });

        errorSpy.mockRestore();
    });

    it('falls back to defaults and reports a message when settings load fails', async () => {
        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        global.fetch = jest.fn(() => Promise.reject(new TypeError('Failed to fetch'))) as jest.Mock;

        const { result } = renderHook(() => useSettingsRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.message).toBe('Failed to load settings payload from backend.');
            expect(result.current.settings.LOCAL_HISTORY_PROVIDER).toBe('MUBASHER_DB');
            expect(result.current.settings.LOCAL_INTRADAY_PROVIDER).toBe('MUBASHER_DB');
            expect(result.current.settings.LOCAL_TICKS_PROVIDER).toBe('MUBASHER_DB');
            expect(result.current.settings.TICK_SYNC_ENABLED).toBe(true);
            expect(result.current.excluded).toEqual([]);
            expect(result.current.allTickers).toEqual([]);
            expect(result.current.hasChanges).toBe(false);
        });

        errorSpy.mockRestore();
    });

    it('falls back quietly when settings bootstrap receives a 404 in frontend-only mode', async () => {
        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        global.fetch = jest.fn(() => Promise.resolve({
            ok: false,
            status: 404,
            statusText: 'Not Found',
        } as Response)) as jest.Mock;

        const { result } = renderHook(() => useSettingsRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.message).toBe('Failed to load settings payload from backend.');
        });

        expect(errorSpy).not.toHaveBeenCalled();
        errorSpy.mockRestore();
    });
});
