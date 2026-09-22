'use client';

import { useCallback, useEffect, useState } from 'react';

import dynamic from 'next/dynamic';

import ConfirmDialog from '../components/ConfirmDialog';
import StrategyAuditDrawer from '../components/StrategyAuditDrawer';
import { apiFetch, readJsonSafe } from '@/lib/api';
import { BacktestLabPanel } from './components/BacktestLabPanel';
import { OptimizationResultsPanel } from './components/OptimizationResultsPanel';
import { OptimizationShell, type OptimizationMode } from './components/OptimizationShell';
import { OptimizerControlPanel } from './components/OptimizerControlPanel';
import { PineLabPanel } from './components/PineLabPanel';
import { useBacktestLab } from './hooks/useBacktestLab';
import { useOptimizationAudit } from './hooks/useOptimizationAudit';
import { useOptimizerControl } from './hooks/useOptimizerControl';
import { usePineBacktest } from './hooks/usePineBacktest';
import { usePineImportBacktest } from './hooks/usePineImportBacktest';
import { usePineLogicImport } from './hooks/usePineLogicImport';
import { usePinePreflight } from './hooks/usePinePreflight';
import { usePineProfilePromotion } from './hooks/usePineProfilePromotion';

const OptimizationEquityChart = dynamic(() => import('../components/charts/OptimizationEquityChart'), {
    ssr: false,
    loading: () => <div className="section-surface-muted industrial-corner h-full w-full rounded-2xl border border-white/8" />,
});

export default function OptimizationPage() {
    const [mode, setMode] = useState<OptimizationMode>('SIMULATOR');
    const [focusedProfileId, setFocusedProfileId] = useState<string | null>(null);
    const [uiMessage, setUiMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);
    const [importTranslationProvider, setImportTranslationProvider] = useState<string>('LOCAL');

    useEffect(() => {
        if (typeof window === 'undefined') {
            return;
        }

        const params = new URLSearchParams(window.location.search);
        const requestedMode = params.get('mode');
        const requestedProfileId = params.get('profileId');

        if (requestedMode === 'SIMULATOR' || requestedMode === 'OPTIMIZER' || requestedMode === 'PINE_LAB') {
            setMode(requestedMode);
        }
        setFocusedProfileId(requestedProfileId);
    }, []);

    useEffect(() => {
        let active = true;

        const loadImportTranslatorProvider = async () => {
            try {
                const res = await apiFetch('/api/v1/settings');
                const data = await readJsonSafe<any>(res);
                if (!res.ok || !active) {
                    return;
                }
                const provider = String(data?.PINE_IMPORT_TRANSLATION_PROVIDER || 'LOCAL').trim().toUpperCase();
                setImportTranslationProvider(provider === 'OLLAMA' ? 'OLLAMA' : 'LOCAL');
            } catch {
                if (active) {
                    setImportTranslationProvider('LOCAL');
                }
            }
        };

        void loadImportTranslatorProvider();

        return () => {
            active = false;
        };
    }, []);

    const setRouteMessage = useCallback((message: { type: 'error' | 'success'; text: string } | null) => {
        setUiMessage(message);
    }, []);

    const optimizer = useOptimizerControl({ mode, showMessage: setRouteMessage });
    const backtestLab = useBacktestLab({
        optIndex: optimizer.optIndex,
        showMessage: setRouteMessage,
        enabled: mode === 'SIMULATOR',
    });
    const audit = useOptimizationAudit({ showMessage: setRouteMessage });
    const pineBacktest = usePineBacktest({ showMessage: setRouteMessage });
    const pinePreflight = usePinePreflight({
        buildPayload: pineBacktest.buildPayload,
        showMessage: setRouteMessage,
    });
    const pineLogicImport = usePineLogicImport({
        pineForm: pineBacktest.pineForm,
        showMessage: setRouteMessage,
        enabled: mode === 'PINE_LAB',
    });
    const pineImportBacktest = usePineImportBacktest({
        pineForm: pineBacktest.pineForm,
        importPreviewResult: pineLogicImport.importPreviewResult,
        showMessage: setRouteMessage,
        enabled: mode === 'PINE_LAB',
    });
    const pinePromotion = usePineProfilePromotion({
        pineForm: pineBacktest.pineForm,
        preflightResult: pinePreflight.preflightResult,
        backtestResult: pineBacktest.backtestResult,
        importPreviewResult: pineLogicImport.importPreviewResult,
        importBacktestResult: pineImportBacktest.importBacktestResult,
        operatorApproved: pineImportBacktest.operatorApproved,
        showMessage: setRouteMessage,
        enabled: mode === 'PINE_LAB',
    });

    return (
        <OptimizationShell mode={mode} onSelectMode={setMode} uiMessage={uiMessage}>
            {mode === 'SIMULATOR' && (
                <div className="grid grid-cols-1 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500 lg:grid-cols-4">
                    <BacktestLabPanel
                        optIndex={optimizer.optIndex}
                        simParams={backtestLab.simParams}
                        simLoading={backtestLab.simLoading}
                        backtestSource={backtestLab.backtestSource}
                        pineProfiles={backtestLab.profileRegistry}
                        pineProfilesLoading={backtestLab.profileRegistryLoading}
                        selectedPineProfileId={backtestLab.selectedPineProfileId}
                        pineRunConfig={backtestLab.pineRunConfig}
                        onSelectIndex={optimizer.setOptIndex}
                        onChangeParam={backtestLab.setSimParams}
                        onRunSimulation={backtestLab.runBacktest}
                        onChangeBacktestSource={backtestLab.setBacktestSource}
                        onSelectPineProfile={backtestLab.setSelectedPineProfileId}
                        onChangePineRunConfig={backtestLab.setPineRunConfig}
                    />
                    <OptimizationResultsPanel
                        simResult={backtestLab.simResult}
                        simParams={backtestLab.simParams}
                        auditLoading={audit.auditLoading}
                        onRunAiAudit={audit.runAiAudit}
                        onPromptApply={backtestLab.promptApplySettings}
                        chartContent={
                            backtestLab.simResult ? <OptimizationEquityChart data={backtestLab.simResult.equity_curve} /> : null
                        }
                    />
                </div>
            )}

            {mode === 'OPTIMIZER' && (
                <OptimizerControlPanel
                    optIndex={optimizer.optIndex}
                    setOptIndex={optimizer.setOptIndex}
                    optLoading={optimizer.optLoading}
                    optimizerStatus={optimizer.optimizerStatus}
                    optimizerIsActive={optimizer.optimizerIsActive}
                    optimizerHasResults={optimizer.optimizerHasResults}
                    optStatus={optimizer.optStatus}
                    onRunOptimizer={optimizer.runOptimizer}
                    onTestMatrix={(params) => {
                        const nextParams = { ...backtestLab.simParams, ...params };
                        if (Object.prototype.hasOwnProperty.call(params, 'TRAILING_STOP_ENABLED')) {
                            (nextParams as any).TRAILING_STOP_ENABLED = Boolean((params as any).TRAILING_STOP_ENABLED);
                        }
                        backtestLab.setSimParams(nextParams);
                        backtestLab.setBacktestSource('HORUS');
                        setMode('SIMULATOR');
                        void backtestLab.runSimulation(nextParams);
                    }}
                />
            )}

            {mode === 'PINE_LAB' && (
                <PineLabPanel
                    pineForm={pineBacktest.pineForm}
                    onChangeForm={pineBacktest.setPineForm}
                    preflightResult={pinePreflight.preflightResult}
                    preflightLoading={pinePreflight.preflightLoading}
                    onRunPreflight={pinePreflight.runPreflight}
                    importPreviewResult={pineLogicImport.importPreviewResult}
                    importPreviewLoading={pineLogicImport.importPreviewLoading}
                    onRunImportPreview={pineLogicImport.runImportPreview}
                    signalOverrides={pineLogicImport.signalOverrides}
                    onChangeSignalOverride={pineLogicImport.setSignalOverride}
                    operatorApproved={pineImportBacktest.operatorApproved}
                    onSetOperatorApproved={pineImportBacktest.setOperatorApproved}
                    importBacktestResult={pineImportBacktest.importBacktestResult}
                    importBacktestLoading={pineImportBacktest.importBacktestLoading}
                    onRunImportBacktest={pineImportBacktest.runImportBacktest}
                    backtestResult={pineBacktest.backtestResult}
                    backtestLoading={pineBacktest.backtestLoading}
                    onRunBacktest={pineBacktest.runBacktest}
                    promotionLoading={pinePromotion.promotionLoading}
                    importProfileLoading={pinePromotion.importProfileLoading}
                    activationLoading={pinePromotion.activationLoading}
                    createdProfile={pinePromotion.createdProfile}
                    profileRegistry={pinePromotion.profileRegistry}
                    profileRegistryLoading={pinePromotion.profileRegistryLoading}
                    focusedProfileId={focusedProfileId}
                    onCreateProfile={pinePromotion.createProfile}
                    onSaveImportedProfile={pinePromotion.saveImportedProfile}
                    onActivateProfile={pinePromotion.activateProfile}
                    importTranslationProvider={importTranslationProvider}
                    chartContent={
                        pineBacktest.backtestResult
                            ? <OptimizationEquityChart data={pineBacktest.backtestResult.equity_curve} />
                            : null
                    }
                />
            )}

            <ConfirmDialog
                isOpen={backtestLab.applyConfirmOpen}
                title="Overwrite system settings?"
                description="This will push the simulator parameters to the live strategy configuration."
                confirmLabel="Apply Settings"
                cancelLabel="Keep Current"
                tone="warning"
                onClose={backtestLab.closeApplyConfirm}
                onConfirm={backtestLab.confirmApplySettings}
            />

            <StrategyAuditDrawer
                isOpen={audit.isAuditOpen}
                onClose={() => audit.setIsAuditOpen(false)}
                auditResult={audit.auditResult}
                onCommit={audit.commitAuditResult}
                committing={audit.committingAudit}
            />
        </OptimizationShell>
    );
}
