import { useState } from 'react';

export interface BackfillStatus {
    status: 'IDLE' | 'RUNNING' | 'COMPLETED' | 'COMPLETED_WITH_WARNINGS' | 'ERROR';
    current_day: string | null;
    progress: number;
    total_days: number;
    signals_found: number;
    swing_signals_found?: number;
    intraday_signals_found?: number;
    universe_choice?: 'EGX30' | 'EGX70' | 'EGX100' | 'FULL' | null;
    signal_lanes?: 'SWING' | 'INTRADAY' | 'BOTH' | null;
    mode?: 'MANUAL' | 'AUTOMATIC' | null;
    target_kind?: 'TRADING_DAYS' | null;
    error: string | null;
}

interface UseSettingsOperationsArgs {
    apiBase: string;
    backfillTradingDays?: number;
    backfillUniverseChoice?: 'EGX30' | 'EGX70' | 'EGX100' | 'FULL';
    setMessage: React.Dispatch<React.SetStateAction<string>>;
}

const buildHeaders = (includeJson: boolean = false): HeadersInit => {
    const headers: Record<string, string> = {};
    if (includeJson) {
        headers['Content-Type'] = 'application/json';
    }
    return headers;
};

async function getErrorDetail(res: Response): Promise<string> {
    try {
        const payload = await res.json();
        if (payload?.detail) return String(payload.detail);
        if (payload?.message) return String(payload.message);
        return JSON.stringify(payload);
    } catch {
        return `${res.status} ${res.statusText}`;
    }
}

export function useSettingsOperations({
    apiBase,
    backfillTradingDays,
    backfillUniverseChoice = 'EGX30',
    setMessage,
}: UseSettingsOperationsArgs) {
    const [operationLoading, setOperationLoading] = useState(false);
    const [backfill, setBackfill] = useState<BackfillStatus>({
        status: 'IDLE',
        current_day: null,
        progress: 0,
        total_days: 0,
        signals_found: 0,
        universe_choice: backfillUniverseChoice,
        error: null,
    });

    const normalizedBackfillTradingDays = Number.isFinite(backfillTradingDays)
        ? Math.max(1, Math.min(Number(backfillTradingDays), 365))
        : 252;
    const normalizedBackfillUniverseChoice = String(backfillUniverseChoice || 'EGX30').toUpperCase() as NonNullable<BackfillStatus['universe_choice']>;

    const handleHardReset = async () => {
        if (!window.confirm('DANGER: Are you absolutely sure? This will permanently delete all downloaded market data, calculated signals, trade history, and portfolios.')) return;
        if (!window.confirm('FINAL WARNING: This action cannot be undone. Do you wish to destroy all data and reset the system from scratch?')) return;

        setOperationLoading(true);
        try {
            const tokenRes = await fetch(`${apiBase}/api/v1/system/hard-reset/token`);
            if (!tokenRes.ok) throw new Error('Could not acquire reset token.');
            const { token } = await tokenRes.json();

            const res = await fetch(`${apiBase}/api/v1/system/hard-reset`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({ token }),
            });

            if (res.ok) {
                setMessage('HARD RESET SUCCESSFUL. Please shut down and restart the Python backend server now.');
            } else {
                const details = await getErrorDetail(res);
                setMessage(`Hard Reset Failed: ${details}`);
            }
        } catch (e: any) {
            setMessage(`Reset Error: ${e?.message || 'Network Error'}`);
        } finally {
            setOperationLoading(false);
        }
    };

    const handleBackfill = async () => {
        if (backfill.status === 'RUNNING') return;
        if (!window.confirm(`This will rerun historical backfill for up to ${normalizedBackfillTradingDays} trading days using the ${normalizedBackfillUniverseChoice} universe to rebuild SWING and INTRADAY signal history.\n\nContinue?`)) return;

        try {
            await fetch(`${apiBase}/api/v1/system/backfill?days=${normalizedBackfillTradingDays}&universe=${normalizedBackfillUniverseChoice}`, {
                method: 'POST',
                headers: buildHeaders(),
            });
            setBackfill((prev) => ({
                ...prev,
                status: 'RUNNING',
                progress: 0,
                total_days: normalizedBackfillTradingDays,
                signals_found: 0,
                universe_choice: normalizedBackfillUniverseChoice,
                signal_lanes: 'BOTH',
                mode: 'MANUAL',
                target_kind: 'TRADING_DAYS',
                error: null,
            }));

            const poll = window.setInterval(async () => {
                try {
                    const res = await fetch(`${apiBase}/api/v1/system/backfill/status`);
                    if (res.ok) {
                        const data: BackfillStatus = await res.json();
                        setBackfill(data);
                        if (data.status !== 'RUNNING') {
                            window.clearInterval(poll);
                            const statusUniverse = String(data.universe_choice || normalizedBackfillUniverseChoice).toUpperCase();
                            if (data.status === 'COMPLETED') {
                                const swing = Number(data.swing_signals_found || 0);
                                const intraday = Number(data.intraday_signals_found || 0);
                                setMessage(`Historical backfill complete for ${statusUniverse}: ${data.signals_found} signals across ${data.total_days} trading days (Swing: ${swing}, Intraday: ${intraday}).`);
                            }
                            if (data.status === 'COMPLETED_WITH_WARNINGS') {
                                setMessage(
                                    `Historical backfill complete with limited coverage for ${statusUniverse}: ${data.signals_found} signals across ${data.total_days} trading days. ${data.error || 'Historical coverage is shorter than target.'}`
                                );
                            }
                            if (data.status === 'ERROR') setMessage(`Backfill error: ${data.error}`);
                        }
                    }
                } catch {
                    // ignore polling errors
                }
            }, 2000);
        } catch {
            setMessage('Failed to start backfill.');
        }
    };

    return {
        operationLoading,
        backfill,
        handleHardReset,
        handleBackfill,
    };
}
