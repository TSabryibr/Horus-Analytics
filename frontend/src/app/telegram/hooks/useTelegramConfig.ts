'use client';

import { useState } from 'react';

type ConfigForm = {
    auto_intraday: boolean;
    auto_daily: boolean;
    auto_horus_eye: boolean;
    auto_ai_daily_report: boolean;
    auto_weekly_report: boolean;
    auto_monthly_report: boolean;
};

type UseTelegramConfigOptions = {
    apiBase: string;
    buildHeaders: (includeJson?: boolean) => HeadersInit;
    addToLog: (message: string) => void;
    setSending: (sending: boolean) => void;
    closeConfigModal: () => void;
    refreshConfig: () => Promise<any>;
};

const DEFAULT_CONFIG_FORM: ConfigForm = {
    auto_intraday: true,
    auto_daily: true,
    auto_horus_eye: true,
    auto_ai_daily_report: true,
    auto_weekly_report: false,
    auto_monthly_report: false,
};

export function useTelegramConfig({
    apiBase,
    buildHeaders,
    addToLog,
    setSending,
    closeConfigModal,
    refreshConfig,
}: UseTelegramConfigOptions) {
    const [configForm, setConfigForm] = useState<ConfigForm>(DEFAULT_CONFIG_FORM);

    const hydrateConfigForm = (config: Partial<ConfigForm> | null | undefined) => {
        setConfigForm({
            auto_intraday: config?.auto_intraday || false,
            auto_daily: config?.auto_daily ?? true,
            auto_horus_eye: config?.auto_horus_eye ?? true,
            auto_ai_daily_report: config?.auto_ai_daily_report ?? false,
            auto_weekly_report: config?.auto_weekly_report ?? false,
            auto_monthly_report: config?.auto_monthly_report ?? false,
        });
    };

    const handleUpdateConfig = async (event: React.FormEvent) => {
        event.preventDefault();
        setSending(true);
        addToLog('Updating Telegram configuration...');
        try {
            const res = await fetch(`${apiBase}/telegram/config`, {
                method: 'POST',
                headers: buildHeaders(true),
                body: JSON.stringify(configForm),
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                addToLog('✅ Configuration Updated.');
                closeConfigModal();
                try {
                    await refreshConfig();
                } catch {
                    addToLog('❌ Failed to refresh configuration.');
                }
            } else {
                addToLog('❌ Failed to update config.');
            }
        } catch {
            addToLog('❌ Network Error.');
        } finally {
            setSending(false);
        }
    };

    return {
        configForm,
        setConfigForm,
        hydrateConfigForm,
        handleUpdateConfig,
    };
}
