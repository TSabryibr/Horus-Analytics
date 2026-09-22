import { useEffect, useMemo, useState } from 'react';

import type { SettingsState, SignalDeskPolicyState } from './useSettingsRuntime';

export type ActionResult = { ok: boolean; message: string };
export type OllamaResult = ActionResult;

const OLLAMA_RESULT_STORAGE_KEY = 'horus.settings.ollama-result.v1';
const REDACTED_CREDENTIAL_KEYS = [
    'TELEGRAM_TOKEN',
    'CHAT_ID',
    'TELEGRAM_TEST_BOT_TOKEN',
    'TELEGRAM_TEST_CHAT_ID',
    'OLLAMA_API_KEY',
] as const;

interface UseSettingsActionsArgs {
    settings: SettingsState;
    excluded: string[];
    signalDeskPolicy: SignalDeskPolicyState;
    apiBase: string;
    setOriginal: React.Dispatch<React.SetStateAction<SettingsState>>;
    setOriginalExcluded: React.Dispatch<React.SetStateAction<string[]>>;
    setOriginalSignalDeskPolicy: React.Dispatch<React.SetStateAction<SignalDeskPolicyState>>;
    setMessage: React.Dispatch<React.SetStateAction<string>>;
}

const buildHeaders = (includeJson: boolean = false): HeadersInit => {
    const headers: Record<string, string> = {};
    if (includeJson) {
        headers['Content-Type'] = 'application/json';
    }
    return headers;
};

const fetchResponseWithTimeout = async (url: string, init?: RequestInit, timeoutMs = 15000): Promise<Response> => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
        return await fetch(url, {
            ...init,
            signal: controller.signal,
        });
    } finally {
        window.clearTimeout(timeout);
    }
};

const getErrorDetail = async (res: Response): Promise<string> => {
    try {
        const payload = await res.json();
        if (payload?.detail) return String(payload.detail);
        if (payload?.message) return String(payload.message);
        return JSON.stringify(payload);
    } catch {
        return `${res.status} ${res.statusText}`;
    }
};

const buildOllamaSignature = (settings: SettingsState) =>
    JSON.stringify({
        apiKey: String(settings.OLLAMA_API_KEY || '').trim(),
        baseUrl: String(settings.OLLAMA_BASE_URL || '').trim() || 'http://127.0.0.1:11434',
        model: String(settings.AI_REPORT_OLLAMA_MODEL || '').trim() || 'qwen3-coder:30b',
    });

const stripRedactedCredentialFields = (settings: SettingsState): SettingsState => {
    const payload: SettingsState = { ...settings };
    for (const key of REDACTED_CREDENTIAL_KEYS) {
        const configuredKey = `${key}_CONFIGURED`;
        const previewKey = `${key}_PREVIEW`;
        const configured = Boolean(payload[configuredKey]);
        const value = String(payload[key] || '').trim();
        if (configured && !value) {
            delete payload[key];
        }
        delete payload[configuredKey];
        delete payload[previewKey];
    }
    return payload;
};

const configuredCredentialValue = (settings: SettingsState, key: typeof REDACTED_CREDENTIAL_KEYS[number]) => {
    const value = String(settings[key] || '').trim();
    return value || undefined;
};

const readPersistedOllamaResult = (signature: string): OllamaResult | null => {
    if (typeof window === 'undefined') return null;

    try {
        const raw = window.sessionStorage.getItem(OLLAMA_RESULT_STORAGE_KEY);
        if (!raw) return null;

        const payload = JSON.parse(raw) as { signature?: string; result?: OllamaResult | null };
        if (payload?.signature !== signature || !payload.result) return null;
        return payload.result;
    } catch {
        return null;
    }
};

const persistOllamaResult = (signature: string, result: OllamaResult | null) => {
    if (typeof window === 'undefined') return;

    try {
        if (!result) {
            window.sessionStorage.removeItem(OLLAMA_RESULT_STORAGE_KEY);
            return;
        }

        window.sessionStorage.setItem(
            OLLAMA_RESULT_STORAGE_KEY,
            JSON.stringify({ signature, result })
        );
    } catch {
        // Ignore session storage availability issues.
    }
};

export function useSettingsActions({
    settings,
    excluded,
    signalDeskPolicy,
    apiBase,
    setOriginal,
    setOriginalExcluded,
    setOriginalSignalDeskPolicy,
    setMessage,
}: UseSettingsActionsArgs) {
    const [saving, setSaving] = useState(false);
    const [ollamaSaving, setOllamaSaving] = useState(false);
    const [ollamaTesting, setOllamaTesting] = useState(false);
    const [ollamaResult, setOllamaResult] = useState<OllamaResult | null>(null);
    const [telegramResult, setTelegramResult] = useState<ActionResult | null>(null);
    const [testBotResult, setTestBotResult] = useState<ActionResult | null>(null);
    const [webhookResult, setWebhookResult] = useState<ActionResult | null>(null);
    const ollamaSignature = useMemo(() => buildOllamaSignature(settings), [settings]);

    useEffect(() => {
        const persisted = readPersistedOllamaResult(ollamaSignature);

        setOllamaResult((current) => {
            if (persisted) {
                if (current?.ok === persisted.ok && current?.message === persisted.message) return current;
                return persisted;
            }

            if (!current) return current;

            return null;
        });
    }, [ollamaSignature]);

    const handleSaveOllamaSettings = async () => {
        const keyValue = configuredCredentialValue(settings, 'OLLAMA_API_KEY');
        setOllamaSaving(true);
        setOllamaResult({ ok: true, message: 'Saving...' });
        try {
            const payload: SettingsState = {
                OLLAMA_BASE_URL: String(settings.OLLAMA_BASE_URL || '').trim() || 'http://127.0.0.1:11434',
                AI_REPORT_OLLAMA_MODEL: String(settings.AI_REPORT_OLLAMA_MODEL || '').trim() || 'qwen3-coder:30b',
                PINE_IMPORT_TRANSLATION_PROVIDER: String(settings.PINE_IMPORT_TRANSLATION_PROVIDER || 'LOCAL').trim().toUpperCase() || 'LOCAL',
            };
            if (keyValue !== undefined) {
                payload.OLLAMA_API_KEY = keyValue;
            }
            const res = await fetchResponseWithTimeout(`${apiBase}/api/v1/settings`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify(payload),
            }, 20000);
            if (!res.ok) {
                const details = await getErrorDetail(res);
                setOllamaResult({ ok: false, message: details });
                setMessage(`Failed to save Ollama settings: ${details}`);
                return;
            }

            setOriginal((prev) => ({ ...prev, ...payload }));
            const nextResult = { ok: true, message: 'Ollama settings saved.' };
            setOllamaResult(nextResult);
            persistOllamaResult(buildOllamaSignature(payload), nextResult);
            setMessage('Ollama settings saved.');
            window.setTimeout(() => setMessage(''), 2500);
        } catch (e) {
            const timedOut = e instanceof DOMException && e.name === 'AbortError';
            const detail = timedOut ? 'Request timed out while saving.' : 'Network error while saving.';
            const nextResult = { ok: false, message: detail };
            setOllamaResult(nextResult);
            persistOllamaResult(ollamaSignature, nextResult);
            setMessage(`${detail} Ollama settings were not updated.`);
        } finally {
            setOllamaSaving(false);
        }
    };

    const handleTestOllamaSettings = async () => {
        const keyValue = String(settings.OLLAMA_API_KEY || '').trim();

        setOllamaTesting(true);
        setOllamaResult({ ok: true, message: 'Testing...' });
        try {
            const res = await fetchResponseWithTimeout(`${apiBase}/api/v1/ai/provider/test`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({
                    provider: 'OLLAMA',
                    api_key: keyValue,
                    base_url: String(settings.OLLAMA_BASE_URL || '').trim(),
                    model: String(settings.AI_REPORT_OLLAMA_MODEL || '').trim(),
                }),
            }, 25000);
            if (!res.ok) {
                const details = await getErrorDetail(res);
                const nextResult = { ok: false, message: details };
                setOllamaResult(nextResult);
                persistOllamaResult(ollamaSignature, nextResult);
                setMessage(`OLLAMA test failed: ${details}`);
                return;
            }
            const data = await res.json();
            const successMsg = data?.message || 'OLLAMA test passed.';
            const nextResult = { ok: true, message: successMsg };
            setOllamaResult(nextResult);
            persistOllamaResult(ollamaSignature, nextResult);
            setMessage(successMsg);
            window.setTimeout(() => setMessage(''), 3000);
        } catch (e) {
            const timedOut = e instanceof DOMException && e.name === 'AbortError';
            const detail = timedOut ? 'Request timed out while testing provider.' : 'Network error while testing OLLAMA.';
            const nextResult = { ok: false, message: detail };
            setOllamaResult(nextResult);
            persistOllamaResult(ollamaSignature, nextResult);
            setMessage(detail);
        } finally {
            setOllamaTesting(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const [res, exclRes, deskRes] = await Promise.all([
                fetch(`${apiBase}/api/v1/settings`, {
                    method: 'POST',
                    headers: buildHeaders(true),
                    body: JSON.stringify(stripRedactedCredentialFields(settings)),
                }),
                fetch(`${apiBase}/api/v1/settings/exclusions`, {
                    method: 'POST',
                    headers: buildHeaders(true),
                    body: JSON.stringify(excluded),
                }),
                fetch(`${apiBase}/api/v1/signals/desk/mode`, {
                    method: 'POST',
                    headers: buildHeaders(true),
                    body: JSON.stringify({
                        operating_mode: signalDeskPolicy.operatingMode,
                        autopilot_armed: signalDeskPolicy.autopilotArmed,
                        publish_policy: {
                            confidence_floor: signalDeskPolicy.confidenceFloor,
                            min_candidates: signalDeskPolicy.minCandidates,
                            source_modules: signalDeskPolicy.sourceModules,
                            signal_types: signalDeskPolicy.signalTypes,
                        },
                    }),
                }),
            ]);

            if (res.ok && exclRes.ok && deskRes.ok) {
                setOriginal(settings);
                setOriginalExcluded(excluded);
                setOriginalSignalDeskPolicy(signalDeskPolicy);
                setMessage('Configuration Saved Successfully!');
                window.setTimeout(() => setMessage(''), 3000);
            } else {
                const details = !res.ok
                    ? await getErrorDetail(res)
                    : !exclRes.ok
                        ? await getErrorDetail(exclRes)
                        : await getErrorDetail(deskRes);
                setMessage(`Failed to save settings: ${details}`);
            }
        } catch {
            setMessage('Network Error.');
        } finally {
            setSaving(false);
        }
    };

    const handleSaveTelegramConfig = async () => {
        setSaving(true);
        setTelegramResult({ ok: true, message: 'Saving Telegram route...' });
        try {
            const res = await fetch(`${apiBase}/api/v1/telegram/config`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({
                    token: configuredCredentialValue(settings, 'TELEGRAM_TOKEN'),
                    chat_id: configuredCredentialValue(settings, 'CHAT_ID'),
                    auto_intraday: settings.TELEGRAM_AUTO_BROADCAST_INTRADAY,
                    auto_daily: settings.TELEGRAM_AUTO_BROADCAST_DAILY,
                    auto_horus_eye: settings.TELEGRAM_AUTO_BROADCAST_HORUS_EYE,
                    auto_ai_daily_report: settings.TELEGRAM_AUTO_BROADCAST_AI_REPORT,
                    auto_weekly_report: settings.TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT,
                    auto_monthly_report: settings.TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT,
                    main_channel_signal_level: settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL,
                    report_language: settings.TELEGRAM_REPORT_LANGUAGE,
                }),
            });
            if (!res.ok) {
                const detail = await getErrorDetail(res);
                setTelegramResult({ ok: false, message: detail });
                setMessage(`Failed to save Telegram config: ${detail}`);
                return;
            }
            setTelegramResult({ ok: true, message: 'Telegram route armed.' });
            setMessage('Telegram Config Saved');
        } catch {
            setTelegramResult({ ok: false, message: 'Network error while saving Telegram config.' });
            setMessage('Save Failed');
        } finally {
            setSaving(false);
        }
    };

    const handleSendTelegramTest = async () => {
        setSaving(true);
        setTelegramResult({ ok: true, message: 'Sending Telegram test...' });
        try {
            const res = await fetch(`${apiBase}/api/v1/alerts/test`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({
                    token: configuredCredentialValue(settings, 'TELEGRAM_TOKEN'),
                    chat_id: configuredCredentialValue(settings, 'CHAT_ID'),
                }),
            });
            if (!res.ok) {
                const detail = await getErrorDetail(res);
                setTelegramResult({ ok: false, message: detail });
                setMessage(`Telegram test failed: ${detail}`);
                return;
            }
            const data = await res.json();
            const target = String(data?.target_chat_id || settings.CHAT_ID || '').trim();
            const successMessage = data?.message || (target ? `Primary Telegram test sent to ${target}.` : 'Primary Telegram test sent.');
            setTelegramResult({ ok: true, message: successMessage });
            setMessage(successMessage);
        } catch {
            setTelegramResult({ ok: false, message: 'Network error while testing Telegram.' });
            setMessage('Test Failed');
        } finally {
            setSaving(false);
        }
    };

    const handleSaveTestTelegramConfig = async () => {
        setSaving(true);
        setTestBotResult({ ok: true, message: 'Saving Test Bot route...' });
        try {
            const res = await fetch(`${apiBase}/api/v1/telegram/test-bot/config`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({
                    token: configuredCredentialValue(settings, 'TELEGRAM_TEST_BOT_TOKEN'),
                    chat_id: configuredCredentialValue(settings, 'TELEGRAM_TEST_CHAT_ID'),
                }),
            });
            if (!res.ok) {
                const detail = await getErrorDetail(res);
                setTestBotResult({ ok: false, message: detail });
                setMessage(`Failed to save Test Bot config: ${detail}`);
                return;
            }
            setTestBotResult({ ok: true, message: 'Test Bot route armed.' });
            setMessage('Test Bot Config Saved');
        } catch {
            setTestBotResult({ ok: false, message: 'Network error while saving Test Bot config.' });
            setMessage('Save Failed');
        } finally {
            setSaving(false);
        }
    };

    const handleSendTestTelegramBotTest = async () => {
        setSaving(true);
        setTestBotResult({ ok: true, message: 'Sending Test Bot check...' });
        try {
            const res = await fetch(`${apiBase}/api/v1/telegram/test-bot/test`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({
                    token: configuredCredentialValue(settings, 'TELEGRAM_TEST_BOT_TOKEN'),
                    chat_id: configuredCredentialValue(settings, 'TELEGRAM_TEST_CHAT_ID'),
                }),
            });
            if (!res.ok) {
                const detail = await getErrorDetail(res);
                setTestBotResult({ ok: false, message: detail });
                setMessage(`Test Bot check failed: ${detail}`);
                return;
            }
            setTestBotResult({ ok: true, message: 'Test Bot route armed.' });
            setMessage('Test Bot Check Sent!');
        } catch {
            setTestBotResult({ ok: false, message: 'Network error while testing Test Bot.' });
            setMessage('Test Failed');
        } finally {
            setSaving(false);
        }
    };

    const handleTestWebhook = async () => {
        setSaving(true);
        setWebhookResult({ ok: true, message: 'Probing webhook route...' });
        try {
            const res = await fetch(`${apiBase}/api/v1/notifications/webhook/test`, {
                method: 'POST',
                headers: buildHeaders(true),
            });
            if (res.ok) {
                setWebhookResult({ ok: true, message: 'Webhook probe passed.' });
                setMessage('Webhook Test Success!');
            } else {
                const detail = await getErrorDetail(res);
                setWebhookResult({ ok: false, message: detail });
                setMessage('Webhook Test Failed');
            }
        } catch {
            setWebhookResult({ ok: false, message: 'Network error while probing webhook.' });
            setMessage('Network Error during test');
        } finally {
            setSaving(false);
        }
    };

    return {
        saving,
        ollamaSaving,
        ollamaTesting,
        ollamaResult,
        telegramResult,
        testBotResult,
        webhookResult,
        handleSave,
        handleSaveOllamaSettings,
        handleTestOllamaSettings,
        handleSaveTelegramConfig,
        handleSendTelegramTest,
        handleSaveTestTelegramConfig,
        handleSendTestTelegramBotTest,
        handleTestWebhook,
    };
}
