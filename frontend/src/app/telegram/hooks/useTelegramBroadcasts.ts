'use client';

import { useState } from 'react';

type SignalForm = {
    ticker: string;
    entry: string;
    sl: string;
    tp1: string;
    tp2: string;
    caption: string;
};

type UseTelegramBroadcastsOptions = {
    apiBase: string;
    buildHeaders: (includeJson?: boolean) => HeadersInit;
    addToLog: (message: string) => void;
    setSending: (sending: boolean) => void;
    activeRunId?: number | null;
    failedDeliveryCount?: number;
};

const EMPTY_SIGNAL_FORM: SignalForm = {
    ticker: '',
    entry: '',
    sl: '',
    tp1: '',
    tp2: '',
    caption: '',
};

export function useTelegramBroadcasts({
    apiBase,
    buildHeaders,
    addToLog,
    setSending,
    activeRunId,
    failedDeliveryCount,
}: UseTelegramBroadcastsOptions) {
    const [message, setMessage] = useState('');
    const [image, setImage] = useState<string | null>(null);
    const [signalForm, setSignalForm] = useState<SignalForm>(EMPTY_SIGNAL_FORM);

    const handleBroadcast = async () => {
        if (!message && !image) {
            return;
        }
        setSending(true);
        addToLog('Sending general broadcast...');

        try {
            const res = await fetch(`${apiBase}/telegram/broadcast`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({ message, image_base64: image }),
            });

            const data = await res.json();
            if (res.ok && data.status === 'sent') {
                addToLog('✅ Broadcast Sent Successfully.');
                setMessage('');
                setImage(null);
            } else {
                addToLog(`❌ Error: ${data.detail || 'Unknown error'}`);
            }
        } catch {
            addToLog('❌ Network Error.');
        } finally {
            setSending(false);
        }
    };

    const handleSignalBroadcast = async () => {
        if (!signalForm.ticker || !signalForm.entry || !signalForm.sl || !signalForm.tp1) {
            addToLog('⚠️ Missing required signal fields.');
            return;
        }
        setSending(true);
        addToLog(`Generating Horus Signal Card for ${signalForm.ticker.toUpperCase()}...`);

        try {
            const res = await fetch(`${apiBase}/telegram/signal-card`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({
                    ticker: signalForm.ticker,
                    entry: parseFloat(signalForm.entry),
                    sl: parseFloat(signalForm.sl),
                    tp1: parseFloat(signalForm.tp1),
                    tp2: signalForm.tp2 ? parseFloat(signalForm.tp2) : null,
                    caption: signalForm.caption || null,
                }),
            });

            const data = await res.json();
            if (res.ok && data.status === 'sent') {
                addToLog(`✅ Premium Signal Card for ${signalForm.ticker.toUpperCase()} Sent!`);
                setSignalForm(EMPTY_SIGNAL_FORM);
            } else {
                addToLog(`❌ Card Generation Error: ${data.detail || 'Unknown internal error'}`);
            }
        } catch (error: any) {
            addToLog(`❌ Network Error: ${error?.message || 'Request failed.'}`);
        } finally {
            setSending(false);
        }
    };

    const handleAiDailyReportBroadcast = async () => {
        setSending(true);
        addToLog('Generating AI Daily report and dispatching to Telegram...');
        try {
            const res = await fetch(`${apiBase}/ai/daily-report/broadcast`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({ force_refresh: true, use_llm: true }),
            });
            const data = await res.json();
            if (res.ok && data?.status === 'sent') {
                addToLog(`✅ AI Daily Report broadcast sent (${data?.source_module || 'LOCAL'}).`);
            } else {
                addToLog(`❌ AI Daily Report broadcast failed: ${data?.detail || data?.message || 'Unknown error'}`);
            }
        } catch (error: any) {
            addToLog(`❌ Network Error: ${error?.message || 'Failed to broadcast AI report.'}`);
        } finally {
            setSending(false);
        }
    };

    const handleAnalysisReportBroadcast = async (period: 'weekly' | 'monthly') => {
        const label = period === 'weekly' ? 'Weekly' : 'Monthly';
        setSending(true);
        addToLog(`Generating ${label} analysis report and dispatching to Telegram...`);
        try {
            const res = await fetch(`${apiBase}/reports/analysis/broadcast`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({ period, force_refresh: true }),
            });
            const data = await res.json();
            if (res.ok && data?.status === 'sent') {
                addToLog(`✅ ${label} analysis report broadcast sent.`);
            } else {
                addToLog(`❌ ${label} analysis report failed: ${data?.detail || data?.message || 'Unknown error'}`);
            }
        } catch (error: any) {
            addToLog(`❌ ${label} analysis report error: ${error?.message || 'Network failure.'}`);
        } finally {
            setSending(false);
        }
    };

    const triggerScan = async (type: 'DAILY' | 'INTRADAY') => {
        const label = type === 'INTRADAY' ? 'Intraday' : 'Daily Close';
        setSending(true);
        addToLog(`📡 Broadcasting ${label} signals...`);
        try {
            const res = await fetch(`${apiBase}/control/scan`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({ type, notify: true }),
            });
            const data = await res.json();
            if (res.ok && data.started) {
                addToLog(`✅ ${label} broadcast triggered. Signals will be sent to Telegram.`);
            } else if (res.ok) {
                addToLog(`⚠️ ${label} broadcast skipped: ${data.message || 'No new signals found.'}`);
            } else {
                addToLog(`❌ ${label} broadcast failed: ${data.detail || data.message || `HTTP ${res.status}`}`);
            }
        } catch (error: any) {
            addToLog(`❌ ${label} broadcast error: ${error?.message || 'Network failure.'}`);
        } finally {
            setSending(false);
        }
    };

    const handleDeskRelease = async () => {
        if (!activeRunId) {
            addToLog('No completed desk run is available for dispatch.');
            return;
        }

        setSending(true);
        addToLog(`Dispatching latest desk run #${activeRunId} to Telegram...`);
        try {
            const res = await fetch(`${apiBase}/signals/publish`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({ run_id: activeRunId, channel: 'TELEGRAM' }),
            });
            const data = await res.json();
            if (res.ok && data?.status === 'completed') {
                addToLog(`Release rail dispatched run #${activeRunId}.`);
            } else {
                addToLog(`Desk release failed: ${data?.detail || data?.message || `HTTP ${res.status}`}`);
            }
        } catch (error: any) {
            addToLog(`Desk release error: ${error?.message || 'Network failure.'}`);
        } finally {
            setSending(false);
        }
    };

    const handleRetryFailedDeliveries = async () => {
        if (!activeRunId) {
            addToLog('No completed desk run is available for retry.');
            return;
        }
        if (!failedDeliveryCount) {
            addToLog('No failed Telegram deliveries need a retry right now.');
            return;
        }

        setSending(true);
        addToLog(`Retrying ${failedDeliveryCount} failed Telegram deliver${failedDeliveryCount === 1 ? 'y' : 'ies'} for run #${activeRunId}...`);
        try {
            const res = await fetch(`${apiBase}/signals/publish/retry`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify({ run_id: activeRunId, channel: 'TELEGRAM' }),
            });
            const data = await res.json();
            if (res.ok && (data?.status === 'completed' || data?.status === 'noop')) {
                addToLog(data?.status === 'noop' ? 'Retry request was accepted but nothing needed replay.' : `Retry flow completed for run #${activeRunId}.`);
            } else {
                addToLog(`Retry failed: ${data?.detail || data?.message || `HTTP ${res.status}`}`);
            }
        } catch (error: any) {
            addToLog(`Retry error: ${error?.message || 'Network failure.'}`);
        } finally {
            setSending(false);
        }
    };

    return {
        message,
        setMessage,
        image,
        setImage,
        signalForm,
        setSignalForm,
        handleBroadcast,
        handleSignalBroadcast,
        handleAiDailyReportBroadcast,
        handleAnalysisReportBroadcast,
        triggerScan,
        handleDeskRelease,
        handleRetryFailedDeliveries,
    };
}
