import type { ActionResult, OllamaResult } from '../hooks/useSettingsActions';
import type { BackfillStatus } from '../hooks/useSettingsOperations';
import type { SettingsState } from '../hooks/useSettingsRuntime';

export type SettingsDeckTone = 'ready' | 'warning' | 'danger' | 'neutral' | 'active';

export interface SettingsDeckCard {
    id: string;
    title: string;
    tone: SettingsDeckTone;
    tag: string;
    detail: string;
    meta?: string;
}

export interface SettingsAttentionItem {
    id: string;
    targetId: string;
    label: string;
    detail: string;
    tone: 'ready' | 'warning' | 'danger' | 'neutral';
}

interface BuildArgs {
    settings: SettingsState;
    hasChanges: boolean;
    saving: boolean;
    message: string;
    ollamaResult: OllamaResult | null;
    telegramResult: ActionResult | null;
    webhookResult: ActionResult | null;
    backfill: BackfillStatus;
}

const positive = (value: unknown) => typeof value === 'number' && Number.isFinite(value) && value > 0;

const hhmm = (value?: string) => {
    const digits = String(value || '').replace(/\D/g, '').slice(0, 4);
    return digits.length === 4 ? `${digits.slice(0, 2)}:${digits.slice(2)}` : '--:--';
};

const saveCard = ({ hasChanges, saving, message }: Pick<BuildArgs, 'hasChanges' | 'saving' | 'message'>): SettingsDeckCard => {
    if (saving) return { id: 'save', title: 'Save State', tone: 'active', tag: 'SYNCING', detail: 'Committing strategy and policy changes now.' };
    if (hasChanges) return { id: 'save', title: 'Save State', tone: 'warning', tag: 'PENDING', detail: 'Operator changes are staged locally and not committed yet.' };
    if (/failed|error/i.test(message)) return { id: 'save', title: 'Save State', tone: 'danger', tag: 'FAILED', detail: message };
    return { id: 'save', title: 'Save State', tone: 'ready', tag: 'SYNCED', detail: message || 'Runtime configuration matches the latest saved snapshot.' };
};

const executionGateCard = (settings: SettingsState): SettingsDeckCard => {
    if (!settings.AUTO_TRADE_ENABLED) {
        return {
            id: 'execution',
            title: 'Execution Gate',
            tone: 'danger',
            tag: 'AUTO_OFF',
            detail: 'Auto trading is disabled. Live entries are blocked until the operator enables Auto Trading.',
            meta: 'Executor offline',
        };
    }
    if (!settings.SIGNAL_AUTO_EXECUTION_ENABLED) {
        return {
            id: 'execution',
            title: 'Execution Gate',
            tone: 'danger',
            tag: 'SIGNAL_EXEC_OFF',
            detail: 'Signal auto-execution is disabled. The monitor will scan and publish, but it will not open live entries.',
            meta: 'Scheduler skip active',
        };
    }
    if (settings.LIVE_ARM_GUARD_ENABLED) {
        return {
            id: 'execution',
            title: 'Execution Gate',
            tone: 'warning',
            tag: 'MANUAL_ARM',
            detail: 'Live entries require a daily manual arm before the executor can open positions.',
            meta: 'Daily latch active',
        };
    }
    return {
        id: 'execution',
        title: 'Execution Gate',
        tone: 'ready',
        tag: 'AUTO_ENTRY',
        detail: 'Auto trading is enabled and the manual arm guard is bypassed. Valid signals can route through risk gates.',
        meta: 'Manual guard off',
    };
};

const ollamaCard = (settings: SettingsState, result: OllamaResult | null): SettingsDeckCard => {
    if (result) return { id: 'ollama', title: 'Ollama', tone: result.ok ? 'ready' : 'danger', tag: result.ok ? 'READY' : 'ERROR', detail: result.message };
    if (!String(settings.OLLAMA_BASE_URL || '').trim() || !String(settings.AI_REPORT_OLLAMA_MODEL || '').trim()) {
        return { id: 'ollama', title: 'Ollama', tone: 'danger', tag: 'INCOMPLETE', detail: 'Local AI routing is missing an endpoint or model identifier.' };
    }
    return { id: 'ollama', title: 'Ollama', tone: 'warning', tag: 'UNTESTED', detail: 'Endpoint and model are configured. Run a handshake test to verify reachability.', meta: String(settings.AI_REPORT_OLLAMA_MODEL || '') };
};

const telegramCard = (settings: SettingsState, result: ActionResult | null): SettingsDeckCard => {
    if (result) return { id: 'telegram', title: 'Telegram', tone: result.ok ? 'ready' : 'danger', tag: result.ok ? 'READY' : 'ERROR', detail: result.message };
    const tokenReady = Boolean(String(settings.TELEGRAM_TOKEN || '').trim());
    const chatReady = Boolean(String(settings.CHAT_ID || '').trim());
    if (!tokenReady || !chatReady) return { id: 'telegram', title: 'Telegram', tone: 'danger', tag: 'INCOMPLETE', detail: 'Bot token and chat target are both required before dispatch can be armed.' };
    const enabledRoutes = [
        settings.TELEGRAM_AUTO_BROADCAST_INTRADAY,
        settings.TELEGRAM_AUTO_BROADCAST_DAILY,
        settings.TELEGRAM_AUTO_BROADCAST_HORUS_EYE,
        settings.TELEGRAM_AUTO_BROADCAST_AI_REPORT,
        settings.TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT,
        settings.TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT,
    ].filter(Boolean).length;
    return {
        id: 'telegram',
        title: 'Telegram',
        tone: 'ready',
        tag: 'ARMED',
        detail: enabledRoutes ? `${enabledRoutes} automated Telegram route${enabledRoutes === 1 ? '' : 's'} armed.` : 'Telegram credentials are present, but all automated routes are disabled.',
        meta: String(settings.CHAT_ID || ''),
    };
};

const webhookCard = (settings: SettingsState, result: ActionResult | null): SettingsDeckCard => {
    if (!settings.WEBHOOK_ENABLED) return { id: 'webhook', title: 'Webhook', tone: 'neutral', tag: 'DISABLED', detail: 'Generic webhook delivery is offline until the route is enabled.' };
    if (result) return { id: 'webhook', title: 'Webhook', tone: result.ok ? 'ready' : 'danger', tag: result.ok ? 'READY' : 'ERROR', detail: result.message };
    if (!String(settings.WEBHOOK_URL || '').trim()) return { id: 'webhook', title: 'Webhook', tone: 'danger', tag: 'MISSING_URL', detail: 'Webhook delivery is enabled, but no endpoint URL has been configured.' };
    return { id: 'webhook', title: 'Webhook', tone: 'warning', tag: 'UNTESTED', detail: 'Webhook route is armed. Run a probe to verify the downstream receiver.', meta: String(settings.WEBHOOK_URL || '') };
};

const mountCard = (settings: SettingsState): SettingsDeckCard => {
    const ready = [
        Boolean(settings.METASTOCK_DAT_HISTORY_AVAILABLE),
        Boolean(settings.METASTOCK_DAT_INTRADAY_AVAILABLE),
        Boolean(settings.METASTOCK_INTRADAY_AVAILABLE),
    ].filter(Boolean).length;
    const missingRequired = (settings.LOCAL_HISTORY_PROVIDER === 'METASTOCK_DAT' && !settings.METASTOCK_DAT_HISTORY_AVAILABLE)
        || (settings.LOCAL_INTRADAY_PROVIDER === 'METASTOCK_DAT' && !settings.METASTOCK_DAT_INTRADAY_AVAILABLE)
        || (settings.LOCAL_INTRADAY_PROVIDER === 'CSV' && !settings.METASTOCK_INTRADAY_AVAILABLE);
    if (missingRequired) return { id: 'mounts', title: 'Data Mounts', tone: 'danger', tag: 'MISSING', detail: 'Selected local providers depend on mounts that are not currently available.', meta: `${ready}/3 detected` };
    if (ready === 0) return { id: 'mounts', title: 'Data Mounts', tone: 'neutral', tag: 'NO_MOUNTS', detail: 'No MetaStock mounts were detected. Remote or database providers must cover the selected routes.' };
    return { id: 'mounts', title: 'Data Mounts', tone: 'ready', tag: 'MOUNTED', detail: 'Required local history and intraday mounts are available for the selected provider policy.', meta: `${ready}/3 detected` };
};

const schedulerCard = (settings: SettingsState): SettingsDeckCard => {
    const sessionValid = [
        settings.MARKET_START_HHMM_NORMAL,
        settings.MARKET_END_HHMM_NORMAL,
        settings.MARKET_START_HHMM_RAMADAN,
        settings.MARKET_END_HHMM_RAMADAN,
    ].every((value) => String(value || '').replace(/\D/g, '').length === 4);
    if (!sessionValid || !positive(settings.PRE_CLOSE_OFFSET_MINS) || !positive(settings.DAILY_SIGNAL_OFFSET_MINS) || !positive(settings.INTRADAY_INTERVAL_MINS)) {
        return { id: 'scheduler', title: 'Scheduler', tone: 'danger', tag: 'BLOCKED', detail: 'Market session or cadence values are incomplete, so schedule windows cannot be trusted.' };
    }
    return {
        id: 'scheduler',
        title: 'Scheduler',
        tone: 'ready',
        tag: settings.RAMADAN_MODE ? 'RAMADAN' : 'ARMED',
        detail: `${hhmm(settings.MARKET_START_HHMM_NORMAL)}-${hhmm(settings.MARKET_END_HHMM_NORMAL)} normal session, ${settings.INTRADAY_INTERVAL_MINS}m intraday cadence.`,
        meta: settings.RAMADAN_MODE ? `${hhmm(settings.MARKET_START_HHMM_RAMADAN)}-${hhmm(settings.MARKET_END_HHMM_RAMADAN)} Ramadan profile live` : 'Normal profile live',
    };
};

const backfillCard = (backfill: BackfillStatus): SettingsDeckCard => {
    if (backfill.status === 'RUNNING') return { id: 'backfill', title: 'Backfill', tone: 'active', tag: 'RUNNING', detail: `Rebuilding historical context on ${backfill.current_day || 'pending session'} (${backfill.progress + 1} of ${backfill.total_days}).`, meta: `${backfill.signals_found} signals staged` };
    if (backfill.status === 'COMPLETED') return { id: 'backfill', title: 'Backfill', tone: 'ready', tag: 'READY', detail: `Historical context refreshed across ${backfill.total_days} trading days.`, meta: `${backfill.signals_found} signals` };
    if (backfill.status === 'COMPLETED_WITH_WARNINGS') return { id: 'backfill', title: 'Backfill', tone: 'warning', tag: 'PARTIAL', detail: backfill.error || 'Historical coverage completed with warnings.', meta: `${backfill.total_days} trading days` };
    if (backfill.status === 'ERROR') return { id: 'backfill', title: 'Backfill', tone: 'danger', tag: 'ERROR', detail: backfill.error || 'Historical backfill failed.' };
    return { id: 'backfill', title: 'Backfill', tone: 'neutral', tag: 'MANUAL', detail: 'Historical context rebuild is available on demand and does not auto-run at startup.' };
};

export function buildSettingsCommandDeckState({ settings, hasChanges, saving, message, ollamaResult, telegramResult, webhookResult, backfill }: BuildArgs) {
    const cards = [
        saveCard({ hasChanges, saving, message }),
        executionGateCard(settings),
        ollamaCard(settings, ollamaResult),
        telegramCard(settings, telegramResult),
        webhookCard(settings, webhookResult),
        mountCard(settings),
        schedulerCard(settings),
        backfillCard(backfill),
    ];

    const attentionItems: SettingsAttentionItem[] = [];
    if (hasChanges) attentionItems.push({ id: 'save-pending', targetId: 'header', label: 'Pending changes are not committed.', detail: 'Save the current command deck state to keep strategy, runtime, and exclusion policy aligned.', tone: 'warning' });
    if (!settings.AUTO_TRADE_ENABLED) {
        attentionItems.push({ id: 'execution-auto-off', targetId: 'strategy-risk', label: 'Auto trading is disabled.', detail: 'The executor will not open live positions until Auto Trading is enabled and saved.', tone: 'danger' });
    } else if (!settings.SIGNAL_AUTO_EXECUTION_ENABLED) {
        attentionItems.push({ id: 'execution-signal-auto-off', targetId: 'strategy-risk', label: 'Signal auto-execution is disabled.', detail: 'Scheduled signal scans can continue, but the execution monitor will skip entries until this gate is enabled and saved.', tone: 'danger' });
    } else if (settings.LIVE_ARM_GUARD_ENABLED) {
        attentionItems.push({ id: 'execution-manual-arm', targetId: 'strategy-risk', label: 'Live entries require a daily manual arm.', detail: 'Disable the daily manual arm guard for automatic live entries, or arm the executor manually each session.', tone: 'warning' });
    }
    if (!String(settings.TELEGRAM_TOKEN || '').trim() || !String(settings.CHAT_ID || '').trim()) attentionItems.push({ id: 'telegram-incomplete', targetId: 'delivery-ai', label: 'Telegram delivery is missing a token or chat target.', detail: 'Local broadcast actions cannot route to Telegram until both fields are complete.', tone: 'danger' });
    if (!String(settings.OLLAMA_BASE_URL || '').trim() || !String(settings.AI_REPORT_OLLAMA_MODEL || '').trim()) {
        attentionItems.push({ id: 'ollama-incomplete', targetId: 'delivery-ai', label: 'Ollama routing is incomplete.', detail: 'Set both the local endpoint and model before attempting AI report generation.', tone: 'danger' });
    } else if (!ollamaResult?.ok) {
        attentionItems.push({ id: 'ollama-untested', targetId: 'delivery-ai', label: 'Ollama has not been verified from this console session.', detail: 'Run the local handshake to confirm the currently selected model is reachable.', tone: ollamaResult ? 'danger' : 'warning' });
    }
    if (settings.WEBHOOK_ENABLED && !String(settings.WEBHOOK_URL || '').trim()) attentionItems.push({ id: 'webhook-missing', targetId: 'delivery-ai', label: 'Webhook delivery is enabled without a URL.', detail: 'Either disable the route or configure the receiver endpoint before testing it.', tone: 'danger' });
    if ((settings.LOCAL_HISTORY_PROVIDER === 'METASTOCK_DAT' && !settings.METASTOCK_DAT_HISTORY_AVAILABLE) || (settings.LOCAL_INTRADAY_PROVIDER === 'METASTOCK_DAT' && !settings.METASTOCK_DAT_INTRADAY_AVAILABLE) || (settings.LOCAL_INTRADAY_PROVIDER === 'CSV' && !settings.METASTOCK_INTRADAY_AVAILABLE)) {
        attentionItems.push({ id: 'mounts-missing', targetId: 'data-source-policy', label: 'Selected local providers depend on mounts that are not available.', detail: 'Review the local provider policy or restore the required MetaStock folders before relying on local inputs.', tone: 'danger' });
    }
    if (!positive(settings.PRE_CLOSE_OFFSET_MINS) || !positive(settings.DAILY_SIGNAL_OFFSET_MINS) || !positive(settings.INTRADAY_INTERVAL_MINS)) attentionItems.push({ id: 'scheduler-invalid', targetId: 'exclusions-market-hours', label: 'Scheduler cadence needs review.', detail: 'Pre-close, daily, and intraday offsets must all remain positive to keep dispatch timing deterministic.', tone: 'warning' });
    if (backfill.status === 'RUNNING') attentionItems.push({ id: 'backfill-running', targetId: 'operations-runtime', label: 'Historical backfill is active.', detail: 'Runtime context is being rebuilt now. Let it complete before reading deeper report readiness.', tone: 'warning' });
    if (backfill.status === 'ERROR') attentionItems.push({ id: 'backfill-error', targetId: 'operations-runtime', label: 'Historical backfill ended with an error.', detail: backfill.error || 'Review the backfill console block and retry after correcting the failure condition.', tone: 'danger' });

    return { cards, attentionItems };
}
