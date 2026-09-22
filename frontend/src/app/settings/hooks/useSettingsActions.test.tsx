import { act, renderHook, waitFor } from '@testing-library/react';

import type { SettingsState } from './useSettingsRuntime';
import { useSettingsActions } from './useSettingsActions';

const DEFAULT_SETTINGS: SettingsState = {
    MOMENTUM: 2.5,
    TELEGRAM_TOKEN: 'token',
    CHAT_ID: '-100123',
    OLLAMA_API_KEY: '',
    OLLAMA_BASE_URL: 'http://127.0.0.1:11434',
    AI_REPORT_OLLAMA_MODEL: 'qwen3-coder:30b',
    PINE_IMPORT_TRANSLATION_PROVIDER: 'LOCAL',
    TELEGRAM_AUTO_BROADCAST_INTRADAY: true,
    TELEGRAM_AUTO_BROADCAST_DAILY: true,
    TELEGRAM_AUTO_BROADCAST_HORUS_EYE: true,
    TELEGRAM_AUTO_BROADCAST_AI_REPORT: true,
    TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT: false,
    TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT: false,
    TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL: 'type_2',
    TELEGRAM_REPORT_LANGUAGE: 'AR',
    WEBHOOK_URL: 'https://example.com/hook',
};

const DEFAULT_SIGNAL_DESK_POLICY = {
    operatingMode: 'MANUAL' as const,
    autopilotArmed: false,
    confidenceFloor: 0,
    minCandidates: 1,
    sourceModules: ['SCANNER'],
    signalTypes: ['INTRADAY'],
};

function buildFetchMock(overrides: Record<string, (init?: RequestInit) => Response | Promise<Response>> = {}) {
    return jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        for (const [pattern, handler] of Object.entries(overrides)) {
            if (url.includes(pattern)) return handler(init);
        }

        if (url.includes('/api/v1/settings') && init?.method === 'POST') {
            return { ok: true, json: async () => ({ status: 'success' }) } as Response;
        }
        if (url.includes('/api/v1/settings/exclusions') && init?.method === 'POST') {
            return { ok: true, json: async () => ({ status: 'success' }) } as Response;
        }
        if (url.includes('/api/v1/signals/desk/mode') && init?.method === 'POST') {
            return { ok: true, json: async () => ({ status: 'success' }) } as Response;
        }
        if (url.includes('/api/v1/ai/provider/test')) {
            return { ok: true, json: async () => ({ message: 'Provider OK' }) } as Response;
        }
        if (url.includes('/api/v1/telegram/config')) {
            return { ok: true, json: async () => ({ status: 'saved' }) } as Response;
        }
        if (url.includes('/api/v1/alerts/test')) {
            return { ok: true, json: async () => ({ status: 'sent' }) } as Response;
        }
        if (url.includes('/api/v1/notifications/webhook/test')) {
            return { ok: true, json: async () => ({ status: 'success' }) } as Response;
        }

        return { ok: true, json: async () => ({}) } as Response;
    }) as jest.Mock;
}

describe('useSettingsActions', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
        jest.useRealTimers();
    });

    it('saves settings and exclusions and updates original snapshots', async () => {
        jest.useFakeTimers();
        global.fetch = buildFetchMock();

        const setOriginal = jest.fn();
        const setOriginalExcluded = jest.fn();
        const setOriginalSignalDeskPolicy = jest.fn();
        const setMessage = jest.fn();

        const { result } = renderHook(() =>
            useSettingsActions({
                settings: DEFAULT_SETTINGS,
                excluded: ['COMI'],
                signalDeskPolicy: DEFAULT_SIGNAL_DESK_POLICY,
                apiBase: 'http://127.0.0.1:8000',
                setOriginal,
                setOriginalExcluded,
                setOriginalSignalDeskPolicy,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleSave();
        });

        expect(setOriginal).toHaveBeenCalledWith(DEFAULT_SETTINGS);
        expect(setOriginalExcluded).toHaveBeenCalledWith(['COMI']);
        expect(setOriginalSignalDeskPolicy).toHaveBeenCalledWith(DEFAULT_SIGNAL_DESK_POLICY);
        expect(setMessage).toHaveBeenCalledWith('Configuration Saved Successfully!');

        act(() => {
            jest.advanceTimersByTime(3000);
        });

        expect(setMessage).toHaveBeenLastCalledWith('');
    });

    it('omits blank redacted credential fields during shared settings save', async () => {
        const fetchMock = buildFetchMock();
        global.fetch = fetchMock;

        const setOriginal = jest.fn();
        const setOriginalExcluded = jest.fn();
        const setOriginalSignalDeskPolicy = jest.fn();
        const setMessage = jest.fn();

        const redactedSettings: SettingsState = {
            ...DEFAULT_SETTINGS,
            TELEGRAM_TOKEN: '',
            TELEGRAM_TOKEN_CONFIGURED: true,
            CHAT_ID: '',
            CHAT_ID_CONFIGURED: true,
            TELEGRAM_TEST_BOT_TOKEN: '',
            TELEGRAM_TEST_BOT_TOKEN_CONFIGURED: true,
            TELEGRAM_TEST_CHAT_ID: '',
            TELEGRAM_TEST_CHAT_ID_CONFIGURED: true,
            OLLAMA_API_KEY: '',
            OLLAMA_API_KEY_CONFIGURED: true,
        };

        const { result } = renderHook(() =>
            useSettingsActions({
                settings: redactedSettings,
                excluded: [],
                signalDeskPolicy: DEFAULT_SIGNAL_DESK_POLICY,
                apiBase: 'http://127.0.0.1:8000',
                setOriginal,
                setOriginalExcluded,
                setOriginalSignalDeskPolicy,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleSave();
        });

        const settingsCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/api/v1/settings'));
        const body = JSON.parse(String((settingsCall?.[1] as RequestInit)?.body ?? '{}'));
        expect(body.MOMENTUM).toBe(2.5);
        expect(body).not.toHaveProperty('TELEGRAM_TOKEN');
        expect(body).not.toHaveProperty('CHAT_ID');
        expect(body).not.toHaveProperty('TELEGRAM_TEST_BOT_TOKEN');
        expect(body).not.toHaveProperty('TELEGRAM_TEST_CHAT_ID');
        expect(body).not.toHaveProperty('OLLAMA_API_KEY');
    });

    it('reports Ollama save failures with structured details', async () => {
        global.fetch = buildFetchMock({
            '/api/v1/settings': () =>
                ({
                    ok: false,
                    status: 422,
                    statusText: 'Unprocessable Entity',
                    json: async () => ({ detail: 'Validation failed' }),
                }) as Response,
        });

        const setOriginal = jest.fn();
        const setOriginalExcluded = jest.fn();
        const setOriginalSignalDeskPolicy = jest.fn();
        const setMessage = jest.fn();

        const { result } = renderHook(() =>
            useSettingsActions({
                settings: DEFAULT_SETTINGS,
                excluded: [],
                signalDeskPolicy: DEFAULT_SIGNAL_DESK_POLICY,
                apiBase: 'http://127.0.0.1:8000',
                setOriginal,
                setOriginalExcluded,
                setOriginalSignalDeskPolicy,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleSaveOllamaSettings();
        });

        expect(result.current.ollamaResult).toEqual({ ok: false, message: 'Validation failed' });
        expect(setMessage).toHaveBeenCalledWith('Failed to save Ollama settings: Validation failed');
    });

    it('saves the Pine import translator provider with Ollama settings', async () => {
        const fetchMock = buildFetchMock();
        global.fetch = fetchMock;

        const setOriginal = jest.fn();
        const setOriginalExcluded = jest.fn();
        const setOriginalSignalDeskPolicy = jest.fn();
        const setMessage = jest.fn();

        const { result } = renderHook(() =>
            useSettingsActions({
                settings: { ...DEFAULT_SETTINGS, PINE_IMPORT_TRANSLATION_PROVIDER: 'OLLAMA' },
                excluded: [],
                signalDeskPolicy: DEFAULT_SIGNAL_DESK_POLICY,
                apiBase: 'http://127.0.0.1:8000',
                setOriginal,
                setOriginalExcluded,
                setOriginalSignalDeskPolicy,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleSaveOllamaSettings();
        });

        const settingsCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/api/v1/settings'));
        expect(settingsCall).toBeTruthy();
        expect(JSON.parse(String((settingsCall?.[1] as RequestInit)?.body ?? '{}'))).toMatchObject({
            OLLAMA_BASE_URL: 'http://127.0.0.1:11434',
            AI_REPORT_OLLAMA_MODEL: 'qwen3-coder:30b',
            PINE_IMPORT_TRANSLATION_PROVIDER: 'OLLAMA',
        });
    });

    it('tests Ollama connectivity and surfaces success messages', async () => {
        jest.useFakeTimers();
        global.fetch = buildFetchMock({
            '/api/v1/ai/provider/test': () =>
                ({ ok: true, json: async () => ({ message: 'Provider OK' }) }) as Response,
        });

        const setOriginal = jest.fn();
        const setOriginalExcluded = jest.fn();
        const setOriginalSignalDeskPolicy = jest.fn();
        const setMessage = jest.fn();

        const { result } = renderHook(() =>
            useSettingsActions({
                settings: DEFAULT_SETTINGS,
                excluded: [],
                signalDeskPolicy: DEFAULT_SIGNAL_DESK_POLICY,
                apiBase: 'http://127.0.0.1:8000',
                setOriginal,
                setOriginalExcluded,
                setOriginalSignalDeskPolicy,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleTestOllamaSettings();
        });

        expect(result.current.ollamaResult).toEqual({ ok: true, message: 'Provider OK' });
        expect(setMessage).toHaveBeenCalledWith('Provider OK');

        act(() => {
            jest.advanceTimersByTime(3000);
        });

        expect(setMessage).toHaveBeenLastCalledWith('');
    });

    it('saves telegram config, sends test alerts, and tests webhooks through the action seam', async () => {
        global.fetch = buildFetchMock();

        const setOriginal = jest.fn();
        const setOriginalExcluded = jest.fn();
        const setOriginalSignalDeskPolicy = jest.fn();
        const setMessage = jest.fn();

        const { result } = renderHook(() =>
            useSettingsActions({
                settings: DEFAULT_SETTINGS,
                excluded: [],
                signalDeskPolicy: {
                    operatingMode: 'AUTOPILOT' as const,
                    autopilotArmed: true,
                    confidenceFloor: 78,
                    minCandidates: 2,
                    sourceModules: ['SCANNER', 'ORACLE'],
                    signalTypes: ['INTRADAY', 'SWING', 'POSITION'],
                },
                apiBase: 'http://127.0.0.1:8000',
                setOriginal,
                setOriginalExcluded,
                setOriginalSignalDeskPolicy,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleSaveTelegramConfig();
            await result.current.handleSendTelegramTest();
            await result.current.handleTestWebhook();
        });

        const telegramConfigCall = (global.fetch as jest.Mock).mock.calls.find(([input]) => String(input).includes('/api/v1/telegram/config'));
        expect(JSON.parse(String((telegramConfigCall?.[1] as RequestInit)?.body ?? '{}'))).toMatchObject({
            main_channel_signal_level: 'type_2',
            report_language: 'AR',
        });
        expect(setMessage).toHaveBeenCalledWith('Telegram Config Saved');
        expect(setMessage).toHaveBeenCalledWith('Primary Telegram test sent to -100123.');
        expect(setMessage).toHaveBeenCalledWith('Webhook Test Success!');
    });

    it('sends the primary Telegram test to the visible channel target', async () => {
        const fetchMock = buildFetchMock({
            '/api/v1/alerts/test': (init) => {
                expect(JSON.parse(String(init?.body ?? '{}'))).toMatchObject({
                    token: 'token',
                    chat_id: '1822794531',
                });
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        target_chat_id: '1822794531',
                        message: 'Primary Telegram test sent to 1822794531.',
                    }),
                } as Response;
            },
        });
        global.fetch = fetchMock;

        const setOriginal = jest.fn();
        const setOriginalExcluded = jest.fn();
        const setOriginalSignalDeskPolicy = jest.fn();
        const setMessage = jest.fn();

        const { result } = renderHook(() =>
            useSettingsActions({
                settings: { ...DEFAULT_SETTINGS, CHAT_ID: '1822794531' },
                excluded: [],
                signalDeskPolicy: DEFAULT_SIGNAL_DESK_POLICY,
                apiBase: 'http://127.0.0.1:8000',
                setOriginal,
                setOriginalExcluded,
                setOriginalSignalDeskPolicy,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleSendTelegramTest();
        });

        expect(result.current.telegramResult).toEqual({
            ok: true,
            message: 'Primary Telegram test sent to 1822794531.',
        });
        expect(setMessage).toHaveBeenCalledWith('Primary Telegram test sent to 1822794531.');
    });

    it('still tests Ollama without requiring an API key', async () => {
        const fetchMock = buildFetchMock();
        global.fetch = fetchMock;
        const setOriginal = jest.fn();
        const setOriginalExcluded = jest.fn();
        const setOriginalSignalDeskPolicy = jest.fn();
        const setMessage = jest.fn();

        const { result } = renderHook(() =>
            useSettingsActions({
                settings: { ...DEFAULT_SETTINGS, OLLAMA_API_KEY: '' },
                excluded: [],
                signalDeskPolicy: DEFAULT_SIGNAL_DESK_POLICY,
                apiBase: 'http://127.0.0.1:8000',
                setOriginal,
                setOriginalExcluded,
                setOriginalSignalDeskPolicy,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleTestOllamaSettings();
        });

        expect(fetchMock).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/ai/provider/test'),
            expect.objectContaining({ method: 'POST' })
        );
        expect(result.current.ollamaResult).toEqual({ ok: true, message: 'Provider OK' });
    });

    it('restores a successful Ollama test result for the same saved configuration after remount', async () => {
        global.fetch = buildFetchMock({
            '/api/v1/ai/provider/test': () =>
                ({ ok: true, json: async () => ({ message: 'Provider OK' }) }) as Response,
        });

        const setOriginal = jest.fn();
        const setOriginalExcluded = jest.fn();
        const setOriginalSignalDeskPolicy = jest.fn();
        const setMessage = jest.fn();

        const { result, unmount } = renderHook(() =>
            useSettingsActions({
                settings: DEFAULT_SETTINGS,
                excluded: [],
                signalDeskPolicy: DEFAULT_SIGNAL_DESK_POLICY,
                apiBase: 'http://127.0.0.1:8000',
                setOriginal,
                setOriginalExcluded,
                setOriginalSignalDeskPolicy,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleTestOllamaSettings();
        });

        expect(result.current.ollamaResult).toEqual({ ok: true, message: 'Provider OK' });

        unmount();

        const remounted = renderHook(() =>
            useSettingsActions({
                settings: DEFAULT_SETTINGS,
                excluded: [],
                signalDeskPolicy: DEFAULT_SIGNAL_DESK_POLICY,
                apiBase: 'http://127.0.0.1:8000',
                setOriginal,
                setOriginalExcluded,
                setOriginalSignalDeskPolicy,
                setMessage,
            })
        );

        expect(remounted.result.current.ollamaResult).toEqual({ ok: true, message: 'Provider OK' });
    });

    it('persists the signal desk operating policy through the shared save action', async () => {
        const fetchMock = buildFetchMock();
        global.fetch = fetchMock;
        const setOriginal = jest.fn();
        const setOriginalExcluded = jest.fn();
        const setOriginalSignalDeskPolicy = jest.fn();
        const setMessage = jest.fn();
        const signalDeskPolicy = {
            operatingMode: 'AUTOPILOT' as const,
            autopilotArmed: true,
            confidenceFloor: 84,
            minCandidates: 3,
            sourceModules: ['SCANNER', 'ORACLE'],
            signalTypes: ['INTRADAY', 'SWING'],
        };

        const { result } = renderHook(() =>
            useSettingsActions({
                settings: DEFAULT_SETTINGS,
                excluded: ['COMI'],
                signalDeskPolicy,
                apiBase: 'http://127.0.0.1:8000',
                setOriginal,
                setOriginalExcluded,
                setOriginalSignalDeskPolicy,
                setMessage,
            })
        );

        await act(async () => {
            await result.current.handleSave();
        });

        const deskCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/api/v1/signals/desk/mode'));
        expect(deskCall).toBeTruthy();
        expect(JSON.parse(String((deskCall?.[1] as RequestInit)?.body ?? '{}'))).toEqual({
            operating_mode: 'AUTOPILOT',
            autopilot_armed: true,
            publish_policy: {
                confidence_floor: 84,
                min_candidates: 3,
                source_modules: ['SCANNER', 'ORACLE'],
                signal_types: ['INTRADAY', 'SWING'],
            },
        });
        expect(setOriginalSignalDeskPolicy).toHaveBeenCalledWith(signalDeskPolicy);
    });
});
