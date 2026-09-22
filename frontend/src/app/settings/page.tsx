'use client';

import { useMemo, useState } from 'react';

import { SettingsAiProvidersSection } from './components/SettingsAiProvidersSection';
import { SettingsDangerZoneSection } from './components/SettingsDangerZoneSection';
import { SettingsDataSourcesSection } from './components/SettingsDataSourcesSection';
import { SettingsDeliveryChannelsSection } from './components/SettingsDeliveryChannelsSection';
import { SettingsExclusionsSection } from './components/SettingsExclusionsSection';
import { SettingsExecutionDock } from './components/SettingsExecutionDock';
import { SettingsHolidayCalendarSection } from './components/SettingsHolidayCalendarSection';
import { SettingsMarketHoursSection } from './components/SettingsMarketHoursSection';
import { SettingsOperationsSection } from './components/SettingsOperationsSection';
import { SettingsOperatorModule } from './components/SettingsOperatorModule';
import { SettingsPortfolioManagerSection } from './components/SettingsPortfolioManagerSection';
import { SettingsRiskControlsSection } from './components/SettingsRiskControlsSection';
import { SettingsSectionRail, type SettingsRailSection } from './components/SettingsSectionRail';
import { SettingsShell } from './components/SettingsShell';
import { SettingsSignalLogicSection } from './components/SettingsSignalLogicSection';
import { SettingsStatusMatrix } from './components/SettingsStatusMatrix';
import { useSettingsActions } from './hooks/useSettingsActions';
import { useSettingsExclusions } from './hooks/useSettingsExclusions';
import { useSettingsOperations } from './hooks/useSettingsOperations';
import { useSettingsRuntime } from './hooks/useSettingsRuntime';
import type { SettingsDeckCard } from './lib/settingsCommandDeck';
import { buildSettingsCommandDeckState } from './lib/settingsCommandDeck';

const sections: SettingsRailSection[] = [
    { id: 'operations-runtime', label: 'Operations & Runtime', detail: 'Backfill command surface and scheduler posture.' },
    { id: 'strategy-risk', label: 'Strategy & Risk', detail: 'Signal thresholds, ATR policy, and execution risk.' },
    { id: 'portfolio-manager-controls', label: 'Portfolio Manager', detail: 'Report defaults, thresholds, and action limits.' },
    { id: 'delivery-ai', label: 'Delivery & AI', detail: 'Telegram, webhook, and Ollama routing.' },
    { id: 'data-source-policy', label: 'Data Source Policy', detail: 'Local provider selection and mount readiness.' },
    { id: 'exclusions-market-hours', label: 'Exclusions & Market Hours', detail: 'Universe suppression and session timing.' },
    { id: 'danger-zone', label: 'Danger Zone', detail: 'Hard reset corridor for destructive recovery.' },
];

export default function SettingsPage() {
    const [backfillUniverseChoice, setBackfillUniverseChoice] = useState<'EGX30' | 'EGX70' | 'EGX100' | 'FULL'>('EGX30');
    const {
        settings,
        original,
        setOriginal,
        loading,
        message,
        setMessage,
        excluded,
        setExcluded,
        originalExcluded,
        setOriginalExcluded,
        signalDeskPolicy,
        originalSignalDeskPolicy,
        setOriginalSignalDeskPolicy,
        allTickers,
        apiBase,
        hasChanges,
        handleChange,
        handleSignalDeskPolicyChange,
    } = useSettingsRuntime();
    const {
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
    } = useSettingsActions({
        settings,
        excluded,
        signalDeskPolicy,
        apiBase,
        setOriginal,
        setOriginalExcluded,
        setOriginalSignalDeskPolicy,
        setMessage,
    });
    const {
        newExclusion,
        setNewExclusion,
        addExclusion,
        removeExclusion,
        autocompleteOptions,
    } = useSettingsExclusions({
        excluded,
        setExcluded,
        allTickers,
    });
    const {
        operationLoading,
        backfill,
        handleHardReset,
        handleBackfill,
    } = useSettingsOperations({
        apiBase,
        backfillTradingDays: Number(settings.HISTORICAL_BACKFILL_TRADING_DAYS ?? 252),
        backfillUniverseChoice,
        setMessage,
    });

    const deckState = useMemo(
        () => buildSettingsCommandDeckState({
            settings,
            hasChanges,
            saving,
            message,
            ollamaResult,
            telegramResult,
            webhookResult,
            backfill,
        }),
        [settings, hasChanges, saving, message, ollamaResult, telegramResult, webhookResult, backfill]
    );

    const cardMap = useMemo(
        () => Object.fromEntries(deckState.cards.map((card) => [card.id, card])),
        [deckState.cards]
    ) as Record<string, SettingsDeckCard>;

    return (
        <SettingsShell
            loading={loading}
            message={message}
            saving={saving}
            hasChanges={hasChanges}
            onSave={handleSave}
            settings={settings}
            originalSettings={original}
            excluded={excluded}
            originalExcluded={originalExcluded}
            signalDeskPolicy={signalDeskPolicy}
            originalSignalDeskPolicy={originalSignalDeskPolicy}
        >
            <div className="space-y-8">
                <SettingsExecutionDock settings={settings} executionCard={cardMap.execution} schedulerCard={cardMap.scheduler} />
                <SettingsStatusMatrix cards={deckState.cards} />

                <div className="grid gap-8 xl:grid-cols-[18rem_minmax(0,1fr)]">
                    <SettingsSectionRail sections={sections} attentionItems={deckState.attentionItems} />

                    <div className="space-y-14">
                        <SettingsOperatorModule
                            id="operations-runtime"
                            label="Command Surface"
                            title="Operations & Runtime"
                            description="Manual backfill, scheduler posture, and immediate runtime guidance stay at the top so the operator sees readiness before editing lower-priority configuration."
                            aside={
                                <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] px-4 py-3">
                                    <p className="meta-label text-slate-500">Scheduler pulse</p>
                                    <p className="mt-2 font-mono text-lg text-white">{cardMap.scheduler?.tag}</p>
                                    <p className="mt-1 max-w-xs text-xs leading-5 text-slate-500">{cardMap.scheduler?.detail}</p>
                                </div>
                            }
                        >
                            <div className="grid gap-6 2xl:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)]">
                                <SettingsOperationsSection
                                    saving={saving}
                                    operationLoading={operationLoading}
                                    backfillTradingDays={Number(settings.HISTORICAL_BACKFILL_TRADING_DAYS ?? 252)}
                                    backfillUniverseChoice={backfillUniverseChoice}
                                    backfill={backfill}
                                    includeDangerZone={false}
                                    onBackfillTradingDaysChange={(value) => handleChange('HISTORICAL_BACKFILL_TRADING_DAYS', value)}
                                    onBackfillUniverseChoiceChange={setBackfillUniverseChoice}
                                    onBackfill={handleBackfill}
                                    onHardReset={handleHardReset}
                                />

                                <div className="section-surface rounded-[1.5rem] p-6">
                                    <div className="space-y-1">
                                        <p className="meta-label text-slate-500">Runtime Guide</p>
                                        <h3 className="text-xl font-semibold text-white">Cold operator readout</h3>
                                    </div>

                                    <div className="mt-5 space-y-4">
                                        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                                            <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-500">Backfill posture</p>
                                            <p className="mt-2 text-sm text-slate-200">{cardMap.backfill?.detail}</p>
                                            {cardMap.backfill?.meta ? <p className="mt-2 font-mono text-xs text-slate-500">{cardMap.backfill.meta}</p> : null}
                                        </div>
                                        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                                            <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-500">Session profile</p>
                                            <p className="mt-2 text-sm text-slate-200">{cardMap.scheduler?.detail}</p>
                                            {cardMap.scheduler?.meta ? <p className="mt-2 text-xs text-slate-500">{cardMap.scheduler.meta}</p> : null}
                                        </div>
                                        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                                            <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-500">Save discipline</p>
                                            <p className="mt-2 text-sm text-slate-200">{cardMap.save?.detail}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </SettingsOperatorModule>

                        <SettingsOperatorModule
                            id="strategy-risk"
                            label="Execution Model"
                            title="Strategy & Risk"
                            description="Signal logic and risk boundaries stay adjacent so threshold changes can be reviewed together with exposure controls and ATR behavior."
                        >
                            <div className="grid gap-6 xl:grid-cols-2">
                                <SettingsSignalLogicSection settings={settings} onChange={(key, value) => handleChange(key, value)} />
                                <SettingsRiskControlsSection settings={settings} onChange={handleChange} />
                            </div>
                        </SettingsOperatorModule>

                        <SettingsOperatorModule
                            id="portfolio-manager-controls"
                            label="Treasury Service"
                            title="Portfolio Manager Controls"
                            description="Manage Portfolio Manager report defaults, trigger thresholds, and Telegram formatting limits from one settings block."
                        >
                            <SettingsPortfolioManagerSection settings={settings} onChange={handleChange} />
                        </SettingsOperatorModule>

                        <SettingsOperatorModule
                            id="delivery-ai"
                            label="Distribution Mesh"
                            title="Delivery & AI"
                            description="Telegram, webhooks, and local Ollama routing are grouped into one runtime-adjacent block so field edits and action probes stay close to the systems they affect."
                        >
                            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)]">
                                <div className="section-surface rounded-[1.5rem] p-6">
                                    <SettingsDeliveryChannelsSection
                                        settings={settings}
                                        signalDeskPolicy={signalDeskPolicy}
                                        saving={saving}
                                        telegramResult={telegramResult}
                                        testBotResult={testBotResult}
                                        webhookResult={webhookResult}
                                        onChange={handleChange}
                                        onSignalDeskPolicyChange={handleSignalDeskPolicyChange}
                                        onSaveTelegramConfig={handleSaveTelegramConfig}
                                        onSendTelegramTest={handleSendTelegramTest}
                                        onSaveTestTelegramConfig={handleSaveTestTelegramConfig}
                                        onSendTestTelegramBotTest={handleSendTestTelegramBotTest}
                                        onTestWebhook={handleTestWebhook}
                                    />
                                </div>

                                <div className="section-surface rounded-[1.5rem] p-6">
                                    <div className="space-y-1">
                                        <p className="meta-label text-slate-500">Local AI</p>
                                        <h3 className="text-xl font-semibold text-white">Ollama report engine</h3>
                                        <p className="text-sm leading-6 text-slate-400">
                                            Keep the AI report stack strictly local and validate the selected model before relying on automated narrative generation.
                                        </p>
                                    </div>

                                    <SettingsAiProvidersSection
                                        settings={settings}
                                        ollamaSaving={ollamaSaving}
                                        ollamaTesting={ollamaTesting}
                                        ollamaResult={ollamaResult}
                                        onChange={(key, value) => handleChange(key, value)}
                                        onSaveOllamaSettings={handleSaveOllamaSettings}
                                        onTestOllamaSettings={handleTestOllamaSettings}
                                    />
                                </div>
                            </div>
                        </SettingsOperatorModule>

                        <SettingsOperatorModule
                            id="data-source-policy"
                            label="Input Layer"
                            title="Data Source Policy"
                            description="Local provider policy remains explicit, with mount readiness exposed alongside source selection so input assumptions are visible before scans run."
                        >
                            <SettingsDataSourcesSection settings={settings} onChange={(key, value) => handleChange(key, value)} />
                        </SettingsOperatorModule>

                        <SettingsOperatorModule
                            id="exclusions-market-hours"
                            label="Universe & Clock"
                            title="Exclusions & Market Hours"
                            description="Lower-priority filters and session timing stay together near the bottom of the workspace, but they remain fully editable and easier to audit."
                        >
                            <div className="space-y-6">
                                <SettingsExclusionsSection
                                    excluded={excluded}
                                    newExclusion={newExclusion}
                                    autocompleteOptions={autocompleteOptions}
                                    onInputChange={setNewExclusion}
                                    onAddExclusion={addExclusion}
                                    onRemoveExclusion={removeExclusion}
                                />
                                <SettingsHolidayCalendarSection apiBase={apiBase} onMessage={setMessage} />
                                <SettingsMarketHoursSection settings={settings} onChange={handleChange} />
                            </div>
                        </SettingsOperatorModule>

                        <SettingsOperatorModule
                            id="danger-zone"
                            label="Last Resort"
                            title="Danger Zone"
                            description="Destructive recovery actions are isolated from normal runtime controls so irreversible operations never blend into routine settings work."
                        >
                            <SettingsDangerZoneSection saving={saving} operationLoading={operationLoading} onHardReset={handleHardReset} />
                        </SettingsOperatorModule>
                    </div>
                </div>
            </div>
        </SettingsShell>
    );
}
