'use client';

import React from 'react';
import clsx from 'clsx';

import type { ActionResult } from '../hooks/useSettingsActions';
import type { SettingsState, SignalDeskPolicyState } from '../hooks/useSettingsRuntime';

interface SettingsDeliveryChannelsSectionProps {
    settings: SettingsState;
    signalDeskPolicy: SignalDeskPolicyState;
    saving: boolean;
    telegramResult: ActionResult | null;
    testBotResult: ActionResult | null;
    webhookResult: ActionResult | null;
    onChange: (key: string, value: string | boolean) => void;
    onSignalDeskPolicyChange: <K extends keyof SignalDeskPolicyState>(key: K, value: SignalDeskPolicyState[K]) => void;
    onSaveTelegramConfig: () => void | Promise<void>;
    onSendTelegramTest: () => void | Promise<void>;
    onSaveTestTelegramConfig: () => void | Promise<void>;
    onSendTestTelegramBotTest: () => void | Promise<void>;
    onTestWebhook: () => void | Promise<void>;
}

const FieldGroup = ({
    label,
    desc,
    id,
    children,
}: {
    label: string;
    desc: string;
    id?: string;
    children: React.ReactNode;
}) => (
    <div className="mb-6">
        <label htmlFor={id} className="block text-sm font-medium text-gray-300 mb-1">{label}</label>
        <p className="text-xs text-gray-500 mb-2">{desc}</p>
        {children}
    </div>
);

const ToggleRow = ({
    id,
    label,
    description,
    checked,
    onChange,
}: {
    id: string;
    label: string;
    description: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
}) => (
    <label htmlFor={id} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
        <div>
            <span className="block text-sm font-medium text-slate-100">{label}</span>
            <span className="text-xs text-slate-500">{description}</span>
        </div>
        <input
            id={id}
            aria-label={label}
            type="checkbox"
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            className="h-5 w-5 accent-cyan-400"
        />
    </label>
);

const ResultNote = ({ result }: { result: ActionResult | null }) => {
    if (!result) return null;

    return (
        <p aria-live="polite" className={clsx('text-xs', result.ok ? 'text-cyan-200' : 'text-orange-200')}>
            {result.message}
        </p>
    );
};

const CredentialNote = ({
    configured,
    preview,
}: {
    configured?: boolean;
    preview?: string | null;
}) => {
    if (!configured) return null;
    return (
        <p className="mt-2 font-mono text-[10px] font-black uppercase tracking-[0.18em] text-cyan-300">
            Configured: {preview || '[set]'}
        </p>
    );
};

export function SettingsDeliveryChannelsSection({
    settings,
    signalDeskPolicy,
    saving,
    telegramResult,
    testBotResult,
    webhookResult,
    onChange,
    onSignalDeskPolicyChange,
    onSaveTelegramConfig,
    onSendTelegramTest,
    onSaveTestTelegramConfig,
    onSendTestTelegramBotTest,
    onTestWebhook,
}: SettingsDeliveryChannelsSectionProps) {
    return (
        <div className="space-y-8">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(18rem,0.9fr)]">
                <div className="space-y-6">
                    <div className="space-y-1">
                        <p className="meta-label text-slate-500">Telegram Route</p>
                        <h3 className="text-xl font-semibold text-white">Primary operator dispatch</h3>
                        <p className="text-sm leading-6 text-slate-400">
                            Configure the local Telegram bot for the main premium signal channel and choose which report streams should auto-broadcast.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                        <FieldGroup id="telegram-token" label="Telegram Bot Token" desc="Issued by @BotFather">
                            <input
                                id="telegram-token"
                                type="password"
                                value={settings.TELEGRAM_TOKEN || ''}
                                onChange={(e) => onChange('TELEGRAM_TOKEN', e.target.value)}
                                className="control-input w-full font-mono text-sm focus:border-cyan-400"
                                placeholder="123456:ABC-DEF..."
                            />
                            <CredentialNote configured={Boolean(settings.TELEGRAM_TOKEN_CONFIGURED)} preview={settings.TELEGRAM_TOKEN_PREVIEW} />
                        </FieldGroup>

                        <FieldGroup id="telegram-chat-id" label="Premium Signal Channel ID" desc="Main Type 1 signal channel. Subscriber private reports use each subscriber record instead.">
                            <input
                                id="telegram-chat-id"
                                type="text"
                                value={settings.CHAT_ID || ''}
                                onChange={(e) => onChange('CHAT_ID', e.target.value)}
                                className="control-input w-full font-mono text-sm focus:border-cyan-400"
                                placeholder="-100..."
                            />
                            <CredentialNote configured={Boolean(settings.CHAT_ID_CONFIGURED)} preview={settings.CHAT_ID_PREVIEW} />
                        </FieldGroup>

                        <FieldGroup id="telegram-report-language" label="Telegram report language" desc="Default language for AI, weekly, and monthly report broadcasts. Subscriber private reports can override it per client.">
                            <select
                                id="telegram-report-language"
                                value={String(settings.TELEGRAM_REPORT_LANGUAGE || 'EN').toUpperCase()}
                                onChange={(e) => onChange('TELEGRAM_REPORT_LANGUAGE', e.target.value)}
                                className="control-input w-full text-sm focus:border-cyan-400"
                            >
                                <option value="EN">English</option>
                                <option value="AR">Arabic</option>
                            </select>
                        </FieldGroup>
                    </div>

                    <div className="flex flex-wrap gap-3">
                        <button
                            type="button"
                            onClick={() => {
                                void onSaveTelegramConfig();
                            }}
                            disabled={saving}
                            className="action-secondary rounded-xl px-4 py-2 text-xs font-black uppercase tracking-[0.22em]"
                        >
                            Save
                        </button>
                        <button
                            type="button"
                            onClick={() => {
                                void onSendTelegramTest();
                            }}
                            disabled={saving}
                            className="action-primary rounded-xl !bg-cyan-500 px-4 py-2 text-xs font-black uppercase tracking-[0.22em] !text-slate-950 hover:!bg-cyan-400"
                        >
                            Test Main Channel
                        </button>
                    </div>

                    <p className="text-xs leading-5 text-slate-500">
                        Subscriber private tests run from the Subscribers console on the subscriber row.
                    </p>
                    <ResultNote result={telegramResult} />
                </div>

                <div className="space-y-6">
                    <div className="space-y-1">
                        <p className="meta-label text-slate-500">Test Telegram Route</p>
                        <h3 className="text-xl font-semibold text-white">Replay & Dry Run isolation</h3>
                        <p className="text-sm leading-6 text-slate-400">
                            Configure a dedicated test bot for offline simulations. If left blank, simulation alerts will fall back to the primary route.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                        <FieldGroup id="telegram-test-token" label="Test Bot Token" desc="Dedicated test bot (Market Replay / Dry Run)">
                            <input
                                id="telegram-test-token"
                                type="password"
                                value={settings.TELEGRAM_TEST_BOT_TOKEN || ''}
                                onChange={(e) => onChange('TELEGRAM_TEST_BOT_TOKEN', e.target.value)}
                                className="control-input w-full font-mono text-sm focus:border-cyan-400"
                                placeholder="1234567890:ABC..."
                            />
                            <CredentialNote configured={Boolean(settings.TELEGRAM_TEST_BOT_TOKEN_CONFIGURED)} preview={settings.TELEGRAM_TEST_BOT_TOKEN_PREVIEW} />
                        </FieldGroup>

                        <FieldGroup id="telegram-test-chat-id" label="Test Channel / Chat ID" desc="Target ID for test alerts">
                            <input
                                id="telegram-test-chat-id"
                                type="text"
                                value={settings.TELEGRAM_TEST_CHAT_ID || ''}
                                onChange={(e) => onChange('TELEGRAM_TEST_CHAT_ID', e.target.value)}
                                className="control-input w-full font-mono text-sm focus:border-cyan-400"
                                placeholder="-100..."
                            />
                            <CredentialNote configured={Boolean(settings.TELEGRAM_TEST_CHAT_ID_CONFIGURED)} preview={settings.TELEGRAM_TEST_CHAT_ID_PREVIEW} />
                        </FieldGroup>
                    </div>

                    <div className="flex flex-wrap gap-3">
                        <button
                            type="button"
                            onClick={() => {
                                void onSaveTestTelegramConfig();
                            }}
                            disabled={saving}
                            className="action-secondary rounded-xl px-4 py-2 text-xs font-black uppercase tracking-[0.22em]"
                        >
                            Save Test Route
                        </button>
                        <button
                            type="button"
                            onClick={() => {
                                void onSendTestTelegramBotTest();
                            }}
                            disabled={saving}
                            className="action-primary rounded-xl !bg-orange-500/80 px-4 py-2 text-xs font-black uppercase tracking-[0.22em] !text-white hover:!bg-orange-400"
                        >
                            Probe Test Bot
                        </button>
                    </div>

                    <ResultNote result={testBotResult} />
                </div>

                <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                    <div className="space-y-1">
                        <p className="meta-label text-slate-500">Dispatch Matrix</p>
                        <h3 className="text-lg font-semibold text-white">Auto-broadcast policy</h3>
                    </div>

                    <div className="mt-5 space-y-3">
                        <FieldGroup id="telegram-main-channel-signal-level" label="Automated signal channel level" desc="Controls which subscriber service tiers are mirrored to the main channel.">
                            <select
                                id="telegram-main-channel-signal-level"
                                aria-label="Automated signal channel level"
                                value={String(settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL || 'none')}
                                onChange={(e) => onChange('TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL', e.target.value)}
                                className="control-input w-full text-sm focus:border-cyan-400"
                            >
                                <option value="none">None</option>
                                <option value="type_1">Type 1 only</option>
                                <option value="type_2">Type 1 + Type 2</option>
                                <option value="type_3">Type 1 + Type 2 + Type 3</option>
                            </select>
                        </FieldGroup>
                        <ToggleRow id="telegram-intraday" label="Intraday dispatch" description="Sync intraday alert automation" checked={Boolean(settings.TELEGRAM_AUTO_BROADCAST_INTRADAY)} onChange={(checked) => onChange('TELEGRAM_AUTO_BROADCAST_INTRADAY', checked)} />
                        <ToggleRow id="telegram-daily" label="Daily dispatch" description="Send end-of-session signal outputs" checked={Boolean(settings.TELEGRAM_AUTO_BROADCAST_DAILY)} onChange={(checked) => onChange('TELEGRAM_AUTO_BROADCAST_DAILY', checked)} />
                        <ToggleRow id="telegram-horus-eye" label="Horus Eye dispatch" description="Publish higher-order watch intelligence" checked={Boolean(settings.TELEGRAM_AUTO_BROADCAST_HORUS_EYE)} onChange={(checked) => onChange('TELEGRAM_AUTO_BROADCAST_HORUS_EYE', checked)} />
                        <ToggleRow id="telegram-ai-report" label="AI report dispatch" description="Allow Ollama reports to broadcast automatically" checked={Boolean(settings.TELEGRAM_AUTO_BROADCAST_AI_REPORT)} onChange={(checked) => onChange('TELEGRAM_AUTO_BROADCAST_AI_REPORT', checked)} />
                        <ToggleRow id="telegram-weekly" label="Weekly dispatch" description="Route weekly reporting packets" checked={Boolean(settings.TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT)} onChange={(checked) => onChange('TELEGRAM_AUTO_BROADCAST_WEEKLY_REPORT', checked)} />
                        <ToggleRow id="telegram-monthly" label="Monthly dispatch" description="Route monthly reporting packets" checked={Boolean(settings.TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT)} onChange={(checked) => onChange('TELEGRAM_AUTO_BROADCAST_MONTHLY_REPORT', checked)} />
                    </div>
                </div>
            </div>

            <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(18rem,0.9fr)]">
                    <div className="space-y-5">
                        <div className="space-y-1">
                            <p className="meta-label text-slate-500">Signal Desk Policy</p>
                            <h3 className="text-xl font-semibold text-white">Horus operating authority</h3>
                            <p className="text-sm leading-6 text-slate-400">
                                Control whether Horus stays manual, drafts with AI Assist, or publishes directly when Autopilot is armed and the desk policy passes.
                            </p>
                        </div>

                        <div className="grid gap-4 md:grid-cols-3">
                            {[
                                { id: 'MANUAL', label: 'Manual', detail: 'Admin selects and dispatches the batch.' },
                                { id: 'AI_ASSIST', label: 'AI Assist', detail: 'Horus drafts the batch, operator decides.' },
                                { id: 'AUTOPILOT', label: 'Autopilot', detail: 'Horus can publish directly under policy.' },
                            ].map((mode) => {
                                const active = signalDeskPolicy.operatingMode === mode.id;
                                return (
                                    <button
                                        key={mode.id}
                                        type="button"
                                        onClick={() => onSignalDeskPolicyChange('operatingMode', mode.id as SignalDeskPolicyState['operatingMode'])}
                                        className={clsx(
                                            'rounded-2xl border px-4 py-4 text-left transition',
                                            active ? 'border-cyan-400/60 bg-cyan-500/10' : 'border-white/10 bg-white/[0.03] hover:border-white/20'
                                        )}
                                    >
                                        <div className="text-sm font-semibold text-white">{mode.label}</div>
                                        <div className="mt-1 text-xs leading-5 text-slate-400">{mode.detail}</div>
                                    </button>
                                );
                            })}
                        </div>

                        <ToggleRow
                            id="desk-autopilot-armed"
                            label="Autopilot armed"
                            description="Allow Horus to execute the direct-publish path when Autopilot mode is active."
                            checked={Boolean(signalDeskPolicy.autopilotArmed)}
                            onChange={(checked) => onSignalDeskPolicyChange('autopilotArmed', checked)}
                        />
                    </div>

                    <div className="rounded-[1.5rem] border border-white/10 bg-slate-950/40 p-5">
                        <div className="space-y-1">
                            <p className="meta-label text-slate-500">Policy Gate</p>
                            <h3 className="text-lg font-semibold text-white">Release eligibility</h3>
                        </div>

                        <div className="mt-5 space-y-5">
                            <FieldGroup id="desk-confidence-floor" label="Confidence Floor" desc="Minimum confidence score for Autopilot-eligible candidates">
                                <input
                                    id="desk-confidence-floor"
                                    type="number"
                                    min={0}
                                    max={100}
                                    value={signalDeskPolicy.confidenceFloor}
                                    onChange={(e) => onSignalDeskPolicyChange('confidenceFloor', Number(e.target.value || 0))}
                                    className="control-input w-full font-mono text-sm focus:border-cyan-400"
                                />
                            </FieldGroup>

                            <FieldGroup id="desk-min-candidates" label="Minimum Candidates" desc="Block direct publish unless enough eligible signals survive the desk filters">
                                <input
                                    id="desk-min-candidates"
                                    type="number"
                                    min={1}
                                    max={20}
                                    value={signalDeskPolicy.minCandidates}
                                    onChange={(e) => onSignalDeskPolicyChange('minCandidates', Number(e.target.value || 1))}
                                    className="control-input w-full font-mono text-sm focus:border-cyan-400"
                                />
                            </FieldGroup>

                            <div className="space-y-3">
                                <p className="text-sm font-medium text-gray-300">Allowed source modules</p>
                                {['SCANNER', 'ORACLE', 'WHALES', 'TRAPS', 'ANALYTICS'].map((moduleName) => (
                                    <ToggleRow
                                        key={moduleName}
                                        id={`desk-source-${moduleName.toLowerCase()}`}
                                        label={moduleName}
                                        description="Permit this feeder to contribute Autopilot-eligible candidates"
                                        checked={signalDeskPolicy.sourceModules.includes(moduleName)}
                                        onChange={(checked) => {
                                            const next = checked
                                                ? Array.from(new Set([...signalDeskPolicy.sourceModules, moduleName]))
                                                : signalDeskPolicy.sourceModules.filter((item) => item !== moduleName);
                                            onSignalDeskPolicyChange('sourceModules', next);
                                        }}
                                    />
                                ))}
                            </div>

                            <div className="space-y-3">
                                <p className="text-sm font-medium text-gray-300">Allowed signal lanes</p>
                                {['INTRADAY', 'SWING', 'POSITION'].map((lane) => (
                                    <ToggleRow
                                        key={lane}
                                        id={`desk-lane-${lane.toLowerCase()}`}
                                        label={lane.charAt(0) + lane.slice(1).toLowerCase()}
                                        description="Allow this lane to enter the direct release batch"
                                        checked={signalDeskPolicy.signalTypes.includes(lane)}
                                        onChange={(checked) => {
                                            const next = checked
                                                ? Array.from(new Set([...signalDeskPolicy.signalTypes, lane]))
                                                : signalDeskPolicy.signalTypes.filter((item) => item !== lane);
                                            onSignalDeskPolicyChange('signalTypes', next);
                                        }}
                                    />
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
                    <div className="space-y-1">
                        <p className="meta-label text-slate-500">Secondary Delivery</p>
                        <h3 className="text-xl font-semibold text-white">Generic webhook route</h3>
                        <p className="text-sm leading-6 text-slate-400">
                            Mirror local events into an external HTTP receiver when the downstream integration is live.
                        </p>
                    </div>

                    <label htmlFor="webhook-enabled" className="flex items-center gap-3 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2">
                        <span className="text-[10px] font-black uppercase tracking-[0.22em] text-slate-300">Webhook enabled</span>
                        <input
                            id="webhook-enabled"
                            aria-label="Webhook enabled"
                            type="checkbox"
                            checked={Boolean(settings.WEBHOOK_ENABLED)}
                            onChange={(e) => onChange('WEBHOOK_ENABLED', e.target.checked)}
                            className="h-5 w-5 accent-cyan-400"
                        />
                    </label>
                </div>

                <div className="mt-6 flex flex-col gap-3 xl:flex-row">
                    <input
                        type="url"
                        value={settings.WEBHOOK_URL || ''}
                        onChange={(e) => onChange('WEBHOOK_URL', e.target.value)}
                        className="control-input flex-1 font-mono text-sm focus:border-cyan-400"
                        placeholder="https://your-api.com/webhooks/horus"
                    />
                    <button
                        type="button"
                        onClick={() => {
                            void onTestWebhook();
                        }}
                        disabled={!settings.WEBHOOK_URL || saving}
                        className="action-primary rounded-xl !bg-slate-200 px-4 py-3 text-xs font-black uppercase tracking-[0.22em] !text-slate-950 hover:!bg-white disabled:opacity-50"
                    >
                        Test Webhook
                    </button>
                </div>

                <div className="mt-3">
                    <ResultNote result={webhookResult} />
                </div>
            </div>
        </div>
    );
}
