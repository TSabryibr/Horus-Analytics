export const SYSTEM_BOOT_SESSION_KEY = 'horus_booted_session';
export const OPEN_SYSTEM_BOOT_EVENT = 'horus:open-boot-console';

export type BootCheckState = 'ready' | 'warning' | 'pending' | 'offline';
export type BootConsoleState = 'BOOTING' | 'READY' | 'DEGRADED' | 'OFFLINE';
export type BootEntryMode = 'ready' | 'degraded' | 'blocked';
export type BootMode = 'startup' | 'manual-inspection';

export interface FullSystemStatusPayload {
    system_ready?: boolean;
    message?: string;
    pipeline_state?: string | null;
    provisioning_status?: string | null;
    stale_mode?: boolean;
    freshness?: {
        market_open?: boolean | null;
        last_successful_sync?: string | null;
        overall_ok?: boolean | null;
        checked_at?: string | null;
        history_ok?: boolean | null;
        intraday_ok?: boolean | null;
        history_fresh_ratio?: number | null;
        intraday_live_ratio?: number | null;
        history?: {
            ok?: boolean | null;
            status?: string | null;
            last_updated?: string | null;
            file_count?: number | null;
            kpis?: {
                symbol_count?: number | null;
                fresh_ratio?: number | null;
            } | null;
        } | null;
        intraday?: {
            ok?: boolean | null;
            status?: string | null;
            latest_age_mins?: number | null;
            age_mins?: number | null;
            kpis?: {
                live_ratio?: number | null;
            } | null;
        } | null;
    } | null;
    sync_worker?: {
        status?: string | null;
        last_run?: string | null;
    } | null;
    db_connected?: boolean;
    data_status?: {
        status?: string | null;
        history?: {
            ok?: boolean | null;
            status?: string | null;
            last_updated?: string | null;
            file_count?: number | null;
            kpis?: {
                symbol_count?: number | null;
            } | null;
        } | null;
        intraday?: {
            ok?: boolean | null;
            status?: string | null;
            age_mins?: number | null;
        } | null;
        source?: {
            intraday_provider?: string | null;
        } | null;
    } | null;
    scheduler?: {
        running?: boolean;
        jobs?: Array<{ id?: string | null }>;
    } | null;
    telegram?: {
        configured?: boolean;
        enabled?: boolean;
        chat_id?: string | null;
    } | null;
    signal_desk?: {
        configured?: boolean;
        operating_mode?: string | null;
        autopilot_armed?: boolean;
        autopilot_status?: string | null;
        last_autopilot_run_id?: number | null;
        last_autopilot_published_at?: string | null;
        last_autopilot_error?: string | null;
        updated_at?: string | null;
    } | null;
    metrics?: {
        total_signals?: number | null;
        last_signal_date?: string | null;
    } | null;
    timestamp?: string | null;
}

export interface BootCheck {
    key: string;
    label: string;
    shortLabel: string;
    state: BootCheckState;
    detail: string;
    critical?: boolean;
}

export interface BootSummaryMetric {
    label: string;
    value: string;
    tone: 'neutral' | 'support' | 'warning';
}

export interface BootConsoleModel {
    consoleState: BootConsoleState;
    entryMode: BootEntryMode;
    progress: number;
    headline: string;
    summary: string;
    primaryIssue: string | null;
    checks: BootCheck[];
    metrics: BootSummaryMetric[];
    timestampLabel: string;
    marketLabel: string;
}

const READY_WEIGHT = 1;
const WARNING_WEIGHT = 0.82;
const PENDING_WEIGHT = 0.3;
const OFFLINE_WEIGHT = 0.08;

function normalize(value?: string | null) {
    return String(value || '').trim().toUpperCase();
}

function toneValueFromState(state: BootCheckState): BootSummaryMetric['tone'] {
    if (state === 'ready') {
        return 'support';
    }

    if (state === 'warning') {
        return 'warning';
    }

    return 'neutral';
}

function resolveMarketDataCheck(payload: FullSystemStatusPayload): BootCheck {
    const historyStatus = normalize(payload.data_status?.history?.status || payload.freshness?.history?.status);
    const intradayStatus = normalize(payload.data_status?.intraday?.status || payload.freshness?.intraday?.status);
    const pipelineState = normalize(payload.pipeline_state);
    const marketOpen = payload.freshness?.market_open === true;
    const overallOk = payload.freshness?.overall_ok === true;
    const historyOk = payload.freshness?.history_ok === true
        || payload.freshness?.history?.ok === true
        || payload.data_status?.history?.ok === true
        || ['FRESH', 'READY', 'SYNCED'].includes(historyStatus);
    const intradayOk = payload.freshness?.intraday_ok === true
        || payload.freshness?.intraday?.ok === true
        || payload.data_status?.intraday?.ok === true
        || ['FRESH', 'LIVE', 'READY'].includes(intradayStatus);
    const intradayAgeMins = payload.freshness?.intraday?.latest_age_mins ?? payload.data_status?.intraday?.age_mins;
    const staleMode = payload.stale_mode === true;
    const hasDetailedDataStatus = Boolean(
        payload.data_status?.history || payload.data_status?.intraday || payload.freshness?.history || payload.freshness?.intraday
    );

    // 1. Off-hours / closed-market readiness: if session is closed and history is present, system is fully ready
    if (!marketOpen && (historyOk || pipelineState === 'FRESH' || overallOk)) {
        return {
            key: 'market',
            label: 'Market Data Readiness',
            shortLabel: 'Market',
            state: 'ready',
            detail: 'Session closed, history aligned',
            critical: true,
        };
    }

    // 2. In-session live readiness
    if (historyOk && (!marketOpen || intradayOk)) {
        return {
            key: 'market',
            label: 'Market Data Readiness',
            shortLabel: 'Market',
            state: 'ready',
            detail: marketOpen
                ? `Intraday ${typeof intradayAgeMins === 'number' ? `${intradayAgeMins}m drift` : 'live'}`
                : 'Session closed, history aligned',
            critical: true,
        };
    }

    if (!hasDetailedDataStatus) {
        if (pipelineState === 'FRESH' || overallOk) {
            return {
                key: 'market',
                label: 'Market Data Readiness',
                shortLabel: 'Market',
                state: 'ready',
                detail: marketOpen ? 'Pipeline freshness confirmed' : 'Session closed, pipeline aligned',
                critical: true,
            };
        }

        if (pipelineState === 'STALE' || pipelineState === 'DEGRADED' || staleMode) {
            const lastSync = payload.freshness?.last_successful_sync;
            const syncStamp = lastSync ? formatTimestamp(lastSync) : null;
            return {
                key: 'market',
                label: 'Market Data Readiness',
                shortLabel: 'Market',
                state: 'warning',
                detail: syncStamp
                    ? `Stale data (Last sync: ${syncStamp})`
                    : marketOpen ? 'Booting with degraded market freshness' : 'Historical data awaiting refresh',
                critical: true,
            };
        }

        if (pipelineState === 'SYNCING' || pipelineState === 'STARTING') {
            return {
                key: 'market',
                label: 'Market Data Readiness',
                shortLabel: 'Market',
                state: 'pending',
                detail: 'Awaiting pipeline freshness snapshot',
                critical: true,
            };
        }
    }

    if (marketOpen && (historyOk || staleMode)) {
        return {
            key: 'market',
            label: 'Market Data Readiness',
            shortLabel: 'Market',
            state: 'warning',
            detail: 'Intraday feed delayed',
            critical: true,
        };
    }

    if (normalize(payload.data_status?.status) === 'ERROR') {
        return {
            key: 'market',
            label: 'Market Data Readiness',
            shortLabel: 'Market',
            state: 'offline',
            detail: 'Data diagnostics unavailable',
            critical: true,
        };
    }

    return {
        key: 'market',
        label: 'Market Data Readiness',
        shortLabel: 'Market',
        state: 'pending',
        detail: 'Awaiting feed diagnostics',
        critical: true,
    };
}

function resolveScannerCheck(payload: FullSystemStatusPayload): BootCheck {
    const provisioningStatus = normalize(payload.provisioning_status);
    const pipelineState = normalize(payload.pipeline_state);
    const dataStatus = normalize(payload.data_status?.status);

    if (provisioningStatus === 'ERROR') {
        return {
            key: 'scanner',
            label: 'Scanner Core',
            shortLabel: 'Scanner',
            state: 'warning',
            detail: 'Provisioning fault detected',
            critical: true,
        };
    }

    if (pipelineState === 'FRESH' || payload.system_ready === true) {
        return {
            key: 'scanner',
            label: 'Scanner Core',
            shortLabel: 'Scanner',
            state: 'ready',
            detail: 'Execution stack synchronized',
            critical: true,
        };
    }

    if (pipelineState === 'SYNCING' || pipelineState === 'STARTING') {
        return {
            key: 'scanner',
            label: 'Scanner Core',
            shortLabel: 'Scanner',
            state: 'pending',
            detail: pipelineState === 'SYNCING' ? 'Sync worker refreshing market state' : 'Aligning pipeline state',
            critical: true,
        };
    }

    if (pipelineState === 'STALE' || pipelineState === 'DEGRADED') {
        return {
            key: 'scanner',
            label: 'Scanner Core',
            shortLabel: 'Scanner',
            state: 'warning',
            detail: 'Signal pipeline degraded',
            critical: true,
        };
    }

    if (pipelineState && pipelineState !== 'UNKNOWN' && dataStatus !== 'ERROR') {
        return {
            key: 'scanner',
            label: 'Scanner Core',
            shortLabel: 'Scanner',
            state: 'ready',
            detail: 'Execution stack aligned',
            critical: true,
        };
    }

    if (dataStatus === 'ERROR') {
        return {
            key: 'scanner',
            label: 'Scanner Core',
            shortLabel: 'Scanner',
            state: 'warning',
            detail: 'Signal pipeline degraded',
            critical: true,
        };
    }

    return {
        key: 'scanner',
        label: 'Scanner Core',
        shortLabel: 'Scanner',
        state: 'pending',
        detail: 'Aligning pipeline state',
        critical: true,
    };
}

function resolveTelegramCheck(payload: FullSystemStatusPayload): BootCheck {
    const enabled = payload.telegram?.enabled === true;
    const configured = payload.telegram?.configured === true;

    if (!enabled) {
        return {
            key: 'telegram',
            label: 'Telegram Relay',
            shortLabel: 'Telegram',
            state: 'ready',
            detail: 'Standby',
        };
    }

    if (configured) {
        return {
            key: 'telegram',
            label: 'Telegram Relay',
            shortLabel: 'Telegram',
            state: 'ready',
            detail: 'Relay armed',
        };
    }

    return {
        key: 'telegram',
        label: 'Telegram Relay',
        shortLabel: 'Telegram',
        state: 'warning',
        detail: 'Enabled without credentials',
    };
}

function resolveWeight(state: BootCheckState) {
    if (state === 'ready') {
        return READY_WEIGHT;
    }

    if (state === 'warning') {
        return WARNING_WEIGHT;
    }

    if (state === 'offline') {
        return OFFLINE_WEIGHT;
    }

    return PENDING_WEIGHT;
}

function formatTimestamp(timestamp?: string | null) {
    if (!timestamp) {
        return 'Awaiting first health sample';
    }

    const parsed = new Date(timestamp);
    if (Number.isNaN(parsed.getTime())) {
        return 'Awaiting first health sample';
    }

    return parsed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function resolveMarketLabel(payload: FullSystemStatusPayload) {
    if (payload.freshness?.market_open === true) {
        return 'MARKET OPEN';
    }

    if (payload.freshness?.market_open === false) {
        return 'MARKET CLOSED';
    }

    return 'MARKET UNKNOWN';
}

export function resolveBootConsoleModel(
    payload: FullSystemStatusPayload | null,
    errorMessage: string | null = null,
): BootConsoleModel {
    if (!payload) {
        return {
            consoleState: errorMessage ? 'OFFLINE' : 'BOOTING',
            entryMode: errorMessage ? 'blocked' : 'degraded',
            progress: errorMessage ? 4 : 12,
            headline: errorMessage ? 'Console Offline' : 'Boot Sequence Running',
            summary: errorMessage || 'Requesting operational health snapshot.',
            primaryIssue: errorMessage || null,
            checks: [
                { key: 'api', label: 'API Handshake', shortLabel: 'API', state: errorMessage ? 'offline' : 'pending', detail: errorMessage ? 'No response from backend' : 'Opening telemetry link', critical: true },
                { key: 'database', label: 'Database Link', shortLabel: 'Database', state: 'pending', detail: 'Awaiting handshake', critical: true },
                { key: 'market', label: 'Market Data Readiness', shortLabel: 'Market', state: 'pending', detail: 'Awaiting feed diagnostics', critical: true },
                { key: 'scanner', label: 'Scanner Core', shortLabel: 'Scanner', state: 'pending', detail: 'Awaiting pipeline status', critical: true },
                { key: 'scheduler', label: 'Scheduler Pulse', shortLabel: 'Scheduler', state: 'pending', detail: 'Awaiting job heartbeat', critical: true },
                { key: 'telegram', label: 'Telegram Relay', shortLabel: 'Telegram', state: 'pending', detail: 'Awaiting relay state' },
            ],
            metrics: [
                { label: 'Market', value: 'Unknown', tone: 'neutral' },
                { label: 'Pipeline', value: 'Unknown', tone: 'neutral' },
                { label: 'Jobs', value: '--', tone: 'neutral' },
                { label: 'Signals', value: '--', tone: 'neutral' },
            ],
            timestampLabel: 'Awaiting first health sample',
            marketLabel: 'MARKET UNKNOWN',
        };
    }

    const apiCheck: BootCheck = {
        key: 'api',
        label: 'API Handshake',
        shortLabel: 'API',
        state: 'ready',
        detail: 'Telemetry channel established',
        critical: true,
    };
    const databaseCheck: BootCheck = {
        key: 'database',
        label: 'Database Link',
        shortLabel: 'Database',
        state: payload.db_connected ? 'ready' : 'warning',
        detail: payload.db_connected ? 'Primary store linked' : 'Primary store degraded',
        critical: true,
    };
    const marketCheck = resolveMarketDataCheck(payload);
    const scannerCheck = resolveScannerCheck(payload);
    const schedulerRunning = payload.scheduler?.running === true;
    const schedulerCheck: BootCheck = {
        key: 'scheduler',
        label: 'Scheduler Pulse',
        shortLabel: 'Scheduler',
        state: schedulerRunning ? 'ready' : 'warning',
        detail: schedulerRunning ? `${payload.scheduler?.jobs?.length || 0} jobs armed` : 'Job runner paused',
        critical: true,
    };
    const telegramCheck = resolveTelegramCheck(payload);

    const checks = [apiCheck, databaseCheck, marketCheck, scannerCheck, schedulerCheck, telegramCheck];
    const hasPending = checks.some((check) => check.state === 'pending');
    const hasWarnings = checks.some((check) => check.state === 'warning' || check.state === 'offline');
    const criticalOffline = checks.some((check) => check.critical && check.state === 'offline');

    const consoleState: BootConsoleState = criticalOffline
        ? 'OFFLINE'
        : hasPending
            ? 'BOOTING'
            : hasWarnings
                ? 'DEGRADED'
                : 'READY';

    const entryMode: BootEntryMode = consoleState === 'OFFLINE'
        ? 'blocked'
        : consoleState === 'READY'
            ? 'ready'
            : 'degraded';

    const progress = Math.round(
        (checks.reduce((sum, check) => sum + resolveWeight(check.state), 0) / checks.length) * 100
    );

    const warnings = checks.filter((check) => check.state === 'warning' || check.state === 'offline');
    const primaryIssue = warnings[0]?.detail || null;
    const pipelineValue = normalize(payload.pipeline_state) || 'UNKNOWN';
    const historySymbols = payload.data_status?.history?.kpis?.symbol_count
        ?? payload.freshness?.history?.kpis?.symbol_count
        ?? payload.data_status?.history?.file_count
        ?? payload.freshness?.history?.file_count
        ?? 0;

    const marketOpen = payload.freshness?.market_open === true;
    const historyOk = payload.freshness?.history_ok === true
        || payload.freshness?.history?.ok === true
        || payload.data_status?.history?.ok === true;

    const historyValue = historySymbols > 0
        ? `${historySymbols} symbols`
        : (!marketOpen && (historyOk || marketCheck.state === 'ready'))
            ? 'Aligned (T-1)'
            : 'Not ready';

    const metrics: BootSummaryMetric[] = [
        { label: 'Market', value: resolveMarketLabel(payload).replace('MARKET ', ''), tone: 'neutral' },
        { label: 'Pipeline', value: pipelineValue, tone: consoleState === 'READY' ? 'support' : consoleState === 'DEGRADED' ? 'warning' : 'neutral' },
        { label: 'Jobs', value: String(payload.scheduler?.jobs?.length ?? (payload.scheduler?.running ? 1 : 0)), tone: toneValueFromState(schedulerCheck.state) },
        { label: 'Signals', value: String(payload.metrics?.total_signals ?? '--'), tone: 'neutral' },
        { label: 'History', value: historyValue, tone: toneValueFromState(marketCheck.state) },
        { label: 'Relay', value: telegramCheck.detail, tone: toneValueFromState(telegramCheck.state) },
    ];

    const headline = consoleState === 'READY'
        ? (marketOpen ? 'Trading Operations Ready' : 'Off-Hours Desk Ready')
        : consoleState === 'DEGRADED'
            ? 'Degraded Entry Available'
            : consoleState === 'OFFLINE'
                ? 'System Link Interrupted'
                : 'Boot Sequence Running';

    const summary = consoleState === 'READY'
        ? (payload.message || 'Trading operations stack aligned.')
        : consoleState === 'DEGRADED'
            ? warnings.slice(0, 3).map((check) => `${check.shortLabel}: ${check.detail}`).join(' • ')
            : consoleState === 'OFFLINE'
                ? (errorMessage || 'Boot console cannot reach the health surface.')
                : (payload.message || 'Running subsystem readiness checks.');

    return {
        consoleState,
        entryMode,
        progress,
        headline,
        summary,
        primaryIssue,
        checks,
        metrics,
        timestampLabel: formatTimestamp(payload.timestamp),
        marketLabel: resolveMarketLabel(payload),
    };
}
