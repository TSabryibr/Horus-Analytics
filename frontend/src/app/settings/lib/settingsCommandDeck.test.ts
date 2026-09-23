import type { BackfillStatus } from '../hooks/useSettingsOperations';
import type { OllamaResult } from '../hooks/useSettingsActions';
import type { SettingsState } from '../hooks/useSettingsRuntime';
import { buildSettingsCommandDeckState } from './settingsCommandDeck';

const BASE_SETTINGS: SettingsState = {
    TELEGRAM_TOKEN: '',
    CHAT_ID: '',
    OLLAMA_BASE_URL: 'http://127.0.0.1:11434',
    AI_REPORT_OLLAMA_MODEL: 'qwen3-coder:30b',
    OLLAMA_API_KEY: '',
    WEBHOOK_ENABLED: false,
    WEBHOOK_URL: '',
    LOCAL_HISTORY_PROVIDER: 'METASTOCK_DAT',
    LOCAL_INTRADAY_PROVIDER: 'METASTOCK_DAT',
    METASTOCK_DAT_HISTORY_AVAILABLE: true,
    METASTOCK_DAT_INTRADAY_AVAILABLE: true,
    METASTOCK_INTRADAY_AVAILABLE: false,
    METASTOCK_DAT_HISTORY_FOLDER: 'D:/meta/history',
    METASTOCK_DAT_INTRADAY_FOLDER: 'D:/meta/intraday',
    MARKET_START_HHMM_NORMAL: '1000',
    MARKET_END_HHMM_NORMAL: '1430',
    MARKET_START_HHMM_RAMADAN: '1000',
    MARKET_END_HHMM_RAMADAN: '1330',
    RAMADAN_MODE: false,
    PRE_CLOSE_OFFSET_MINS: 20,
    DAILY_SIGNAL_OFFSET_MINS: 30,
    INTRADAY_INTERVAL_MINS: 5,
    AUTO_TRADE_ENABLED: true,
    SIGNAL_AUTO_EXECUTION_ENABLED: true,
    LIVE_ARM_GUARD_ENABLED: false,
};

const IDLE_BACKFILL: BackfillStatus = {
    status: 'IDLE',
    current_day: null,
    progress: 0,
    total_days: 0,
    signals_found: 0,
    error: null,
};

describe('buildSettingsCommandDeckState', () => {
    it('derives pending save state, incomplete delivery states, and attention items', () => {
        const state = buildSettingsCommandDeckState({
            settings: {
                ...BASE_SETTINGS,
                TELEGRAM_TOKEN: '',
                CHAT_ID: '',
                LOCAL_INTRADAY_PROVIDER: 'CSV',
                METASTOCK_INTRADAY_AVAILABLE: false,
                METASTOCK_INTRADAY_FOLDER: '',
                WEBHOOK_ENABLED: true,
                WEBHOOK_URL: '',
            },
            hasChanges: true,
            saving: false,
            message: '',
            ollamaResult: null,
            telegramResult: null,
            webhookResult: null,
            backfill: IDLE_BACKFILL,
        });

        expect(state.cards.map((card) => card.title)).toEqual([
            'Save State',
            'Execution Gate',
            'Ollama',
            'Telegram',
            'Webhook',
            'Data Mounts',
            'Scheduler',
            'Backfill',
        ]);
        expect(state.cards.find((card) => card.title === 'Save State')).toMatchObject({
            tone: 'warning',
            tag: 'PENDING',
        });
        expect(state.cards.find((card) => card.title === 'Execution Gate')).toMatchObject({
            tone: 'ready',
            tag: 'AUTO_ENTRY',
        });
        expect(state.cards.find((card) => card.title === 'Telegram')).toMatchObject({
            tone: 'danger',
            tag: 'INCOMPLETE',
        });
        expect(state.cards.find((card) => card.title === 'Webhook')).toMatchObject({
            tone: 'danger',
            tag: 'MISSING_URL',
        });
        expect(state.cards.find((card) => card.title === 'Data Mounts')).toMatchObject({
            tone: 'danger',
            tag: 'MISSING',
        });
        expect(state.attentionItems).toEqual(
            expect.arrayContaining([
                expect.objectContaining({ targetId: 'header', label: 'Pending changes are not committed.' }),
                expect.objectContaining({ targetId: 'delivery-ai', label: 'Telegram delivery is missing a token or chat target.' }),
                expect.objectContaining({ targetId: 'delivery-ai', label: 'Webhook delivery is enabled without a URL.' }),
                expect.objectContaining({ targetId: 'data-source-policy', label: 'Selected local providers depend on mounts that are not available.' }),
            ])
        );
    });

    it('derives active backfill progress and successful provider verification', () => {
        const ollamaResult: OllamaResult = { ok: true, message: 'Ollama handshake passed.' };

        const state = buildSettingsCommandDeckState({
            settings: {
                ...BASE_SETTINGS,
                TELEGRAM_TOKEN: 'token',
                CHAT_ID: '-100123',
                WEBHOOK_ENABLED: false,
            },
            hasChanges: false,
            saving: false,
            message: 'Configuration Saved Successfully!',
            ollamaResult,
            telegramResult: { ok: true, message: 'Telegram route armed.' },
            webhookResult: null,
            backfill: {
                status: 'RUNNING',
                current_day: '2026-04-01',
                progress: 4,
                total_days: 20,
                signals_found: 9,
                error: null,
            },
        });

        expect(state.cards.find((card) => card.title === 'Save State')).toMatchObject({
            tone: 'ready',
            tag: 'SYNCED',
        });
        expect(state.cards.find((card) => card.title === 'Ollama')).toMatchObject({
            tone: 'ready',
            tag: 'READY',
            detail: 'Ollama handshake passed.',
        });
        expect(state.cards.find((card) => card.title === 'Backfill')).toMatchObject({
            tone: 'active',
            tag: 'RUNNING',
        });
        expect(state.cards.find((card) => card.title === 'Backfill')?.detail).toContain('5 of 20');
        expect(state.attentionItems).toEqual(
            expect.arrayContaining([
                expect.objectContaining({ targetId: 'operations-runtime', label: 'Historical backfill is active.' }),
            ])
        );
    });

    it('marks the execution gate as a manual hold when daily arming is required', () => {
        const state = buildSettingsCommandDeckState({
            settings: {
                ...BASE_SETTINGS,
                AUTO_TRADE_ENABLED: true,
                LIVE_ARM_GUARD_ENABLED: true,
            },
            hasChanges: false,
            saving: false,
            message: '',
            ollamaResult: null,
            telegramResult: null,
            webhookResult: null,
            backfill: IDLE_BACKFILL,
        });

        expect(state.cards.find((card) => card.title === 'Execution Gate')).toMatchObject({
            tone: 'warning',
            tag: 'MANUAL_ARM',
            detail: expect.stringContaining('daily manual arm'),
        });
        expect(state.attentionItems).toEqual(
            expect.arrayContaining([
                expect.objectContaining({ targetId: 'strategy-risk', label: 'Live entries require a daily manual arm.' }),
            ])
        );
    });

    it('marks the execution gate blocked when signal auto execution is disabled', () => {
        const state = buildSettingsCommandDeckState({
            settings: {
                ...BASE_SETTINGS,
                AUTO_TRADE_ENABLED: true,
                SIGNAL_AUTO_EXECUTION_ENABLED: false,
                LIVE_ARM_GUARD_ENABLED: false,
            },
            hasChanges: false,
            saving: false,
            message: '',
            ollamaResult: null,
            telegramResult: null,
            webhookResult: null,
            backfill: IDLE_BACKFILL,
        });

        expect(state.cards.find((card) => card.title === 'Execution Gate')).toMatchObject({
            tone: 'danger',
            tag: 'SIGNAL_EXEC_OFF',
            detail: expect.stringContaining('Signal auto-execution is disabled'),
        });
        expect(state.attentionItems).toEqual(
            expect.arrayContaining([
                expect.objectContaining({ targetId: 'strategy-risk', label: 'Signal auto-execution is disabled.' }),
            ])
        );
    });
});
