'use client';

import { useEffect, useRef, useState } from 'react';
import { RefreshCw } from 'lucide-react';

import { Position, PortfolioIntakeResult } from '@/types';
import { apiFetch, readJsonSafe } from '@/lib/api';
import { PortfolioAnalysisModal } from './components/PortfolioAnalysisModal';
import { PortfolioCloseDialog } from './components/PortfolioCloseDialog';
import { PortfolioGenesisModal } from './components/PortfolioGenesisModal';
import { PortfolioManagementModal } from './components/PortfolioManagementModal';
import { PortfolioPositionModal } from './components/PortfolioPositionModal';
import { PortfolioReplicateDialog } from './components/PortfolioReplicateDialog';
import { PortfolioRebalanceModal } from './components/PortfolioRebalanceModal';
import { PortfolioShell } from './components/PortfolioShell';

import { usePortfolioData, useTrapsData } from '../context/GlobalDataContext';
import { usePortfolioRuntime } from './hooks/usePortfolioRuntime';
import { usePortfolioActions } from './hooks/usePortfolioActions';
import { usePortfolioManagement } from './hooks/usePortfolioManagement';
import { useSystemPerformance } from './hooks/useSystemPerformance';
import { usePortfolioWebSocket } from './hooks/usePortfolioWebSocket';

import { usePortfolioDialogs } from './hooks/usePortfolioDialogs';
import { usePortfolioForms } from './hooks/usePortfolioForms';
import { truncatePrice } from './lib/forms';

export default function PortfolioPage() {
    const portfolioContext = usePortfolioData();
    const { traps } = useTrapsData();
    const activePortfolioId = portfolioContext?.activePortfolioId ?? null;
    const portfolioList = portfolioContext?.portfolios || [];
    const activePortfolio = portfolioList.find((p) => p.id === activePortfolioId);
    const isSystemPortfolio = Boolean(activePortfolio?.type === 'SYSTEM' || activePortfolio?.type === 'STRATEGY');
    const reportingSectionRef = useRef<HTMLDivElement | null>(null);
    const importFileInputRef = useRef<HTMLInputElement | null>(null);
    const [sectionParam, setSectionParam] = useState<string | null>(null);
    const [isRebalanceModalOpen, setIsRebalanceModalOpen] = useState(false);

    const [replicateModalState, setReplicateModalState] = useState<{
        sourcePortfolioId: number;
        sourcePortfolioName?: string;
        sourcePositions: Position[];
    } | null>(null);
    const [replicateSubmitting, setReplicateSubmitting] = useState(false);

    // 1. Core Data Runtime & FX/Fee state
    const {
        hoard,
        health,
        analysis,
        report,
        currencyMode,
        setCurrencyMode,
        feeMode,
        setFeeMode,
        usdRate,
        displayNetWorth,
        displayFloatingPnl,
        displaySettledPnl,
        floatingFees,
        settledFees,
        loading,
        uiMessage,
        showUiMessage,
        clearUiMessage,
        refreshData: fetchData,
    } = usePortfolioRuntime({ activePortfolioId });

    // 2. Real-Time Telemetry via WebSocket
    const { livePrices, wsConnected } = usePortfolioWebSocket();

    const {
        performance: systemPerformance,
        comparison: systemComparison,
        executionHistory,
        loading: systemLoading,
        refreshSystemData,
    } = useSystemPerformance({ activePortfolioId });

    const handleRefreshAll = async () => {
        await Promise.all([fetchData(), refreshSystemData()]);
    };

    // 3. Action Submissions & Batch Controls
    const {
        actionLoading,
        closeActionLoading,
        importLoading,
        handleGenesis: submitGenesis,
        handleAddPosition: submitAddPosition,
        handleUpdatePosition: submitUpdatePosition,
        handleClosePosition: submitClosePosition,
        handleExport,
        handleExportExcel,
        handleDownloadTemplate,
        triggerImportPicker,
        handleImportCsv,
        handleBatchAction,
        handleApplyRebalance,
    } = usePortfolioActions({
        activePortfolioId,
        refreshData: handleRefreshAll,
        showUiMessage,
        clearUiMessage,
        importFileInputRef,
    });

    // 4. Management Actions
    const {
        managedHoldings,
        managementLoading,
        managementMessage,
        managementReport,
        managementSendResult,
        reportControls,
        actionItemsPreviewLimit,
        setReportControls,
        setManagementMessage,
        fetchManagementReport,
        addManagedHoldingRow,
        removeManagedHoldingRow,
        clearManagedHoldings,
        updateManagedHoldingRow,
        handleManagementIntake,
        handleUploadIntakeFile,
        handleSendManagementReport,
    } = usePortfolioManagement({ activePortfolioId, refreshData: handleRefreshAll });

    // 5. Extracted Dialogs & Forms Subsystems
    const dialogs = usePortfolioDialogs({ hoard, showUiMessage, submitClosePosition });
    const forms = usePortfolioForms({ submitAddPosition, submitUpdatePosition });

    const handleGenesis = async (e: React.FormEvent) => {
        e.preventDefault();
        await submitGenesis(dialogs.genesisData, {
            closeModal: () => dialogs.setIsGenesisModalOpen(false),
        });
    };

    const handleReplicatePortfolio = async (sourcePortfolioId: number): Promise<void> => {
        if (!activePortfolioId) {
            showUiMessage('error', 'Select an active target portfolio first');
            return;
        }
        try {
            const res = await apiFetch(`/api/v1/positions?portfolio_id=${sourcePortfolioId}`);
            if (!res.ok) throw new Error('Failed to fetch system fleet positions');
            const data = await readJsonSafe<any>(res);
            const sourcePositions: Position[] = Array.isArray(data) ? data : (data?.positions || []);
            if (sourcePositions.length === 0) {
                showUiMessage('error', 'Selected System Fleet has no open positions to replicate');
                return;
            }
            const fleetName = systemComparison?.portfolios?.find(p => p.portfolio.id === sourcePortfolioId)?.portfolio?.name;
            setReplicateModalState({
                sourcePortfolioId,
                sourcePortfolioName: fleetName,
                sourcePositions,
            });
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Fleet replication failed';
            showUiMessage('error', msg);
        }
    };

    const confirmReplication = async () => {
        if (!replicateModalState || !activePortfolioId || replicateSubmitting) return;
        setReplicateSubmitting(true);
        try {
            const { sourcePortfolioId, sourcePositions } = replicateModalState;
            const holdingsPayload = sourcePositions.map((p) => ({
                ticker: p.ticker,
                shares: p.shares,
                entry_price: p.entry_price || p.current_price,
                stop_loss: p.stop_loss ? String(p.stop_loss) : null,
                target_price: p.target_price ? String(p.target_price) : null,
                currency: p.currency || 'EGP',
                sector: p.sector || null,
                notes: p.notes || `Replicated from System Fleet #${sourcePortfolioId}`,
            }));

            const intakeRes = await apiFetch('/api/v1/portfolio/management/intake', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    portfolio_id: activePortfolioId,
                    holdings: holdingsPayload,
                    refresh_prices: true,
                }),
            });

            const resJson = await readJsonSafe<PortfolioIntakeResult>(intakeRes);
            const isSuccess = intakeRes.ok && resJson.status === 'completed' && (!resJson.errors || resJson.errors.length === 0);
            const isPartial = resJson.status === 'partial' || (resJson.errors && resJson.errors.length > 0);

            if (isSuccess && (resJson.created > 0 || resJson.updated > 0)) {
                await handleRefreshAll();
                showUiMessage(
                    'success',
                    `Successfully replicated ${sourcePositions.length} position(s) from ${replicateModalState.sourcePortfolioName || `System Fleet #${sourcePortfolioId}`}: ${resJson.created} created, ${resJson.updated} updated.`
                );
                setReplicateModalState(null);
            } else if (isPartial) {
                if (resJson.created > 0 || resJson.updated > 0) {
                    await handleRefreshAll();
                }
                const errorDetail = resJson.errors && resJson.errors.length > 0 ? ` (${resJson.errors.join('; ')})` : '';
                showUiMessage(
                    'error',
                    `Fleet replication finished with warnings: ${resJson.created || 0} created, ${resJson.updated || 0} updated, ${resJson.errors?.length || 0} failed${errorDetail}`
                );
                setReplicateModalState(null);
            } else {
                const errorMsg = (resJson.errors && resJson.errors.length > 0) ? resJson.errors.join('; ') : 'No positions modified or backend error';
                showUiMessage('error', `Fleet replication failed: ${errorMsg}`);
                setReplicateModalState(null);
            }
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Fleet replication failed';
            showUiMessage('error', msg);
            setReplicateModalState(null);
        } finally {
            setReplicateSubmitting(false);
        }
    };

    const cancelReplication = () => {
        setReplicateModalState(null);
    };

    // Routing Effects
    useEffect(() => {
        const readSectionParam = () => {
            const params = new URLSearchParams(window.location.search);
            setSectionParam(params.get('section'));
        };
        readSectionParam();
        window.addEventListener('popstate', readSectionParam);
        return () => window.removeEventListener('popstate', readSectionParam);
    }, []);

    useEffect(() => {
        if (sectionParam !== 'reporting') return;
        const timer = window.setTimeout(() => {
            reportingSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 120);
        return () => window.clearTimeout(timer);
    }, [sectionParam, hoard?.status, activePortfolioId]);

    if ((loading || systemLoading) && !hoard) {
        return (
            <div className="flex-1 flex justify-center items-center h-full">
                <RefreshCw className="w-10 h-10 text-cyan-500 animate-spin" />
            </div>
        );
    }

    return (
        <>
            <PortfolioShell
                hoard={hoard}
                health={health}
                analysis={analysis}
                report={report}
                systemPerformance={systemPerformance}
                systemComparison={systemComparison}
                executionHistory={executionHistory}
                loading={loading || systemLoading}
                uiMessage={uiMessage}
                importLoading={importLoading}
                activePortfolioId={activePortfolioId}
                isSystemPortfolio={isSystemPortfolio}
                importFileInputRef={importFileInputRef}
                reportingSectionRef={reportingSectionRef}
                currencyMode={currencyMode}
                setCurrencyMode={setCurrencyMode}
                feeMode={feeMode}
                setFeeMode={setFeeMode}
                usdRate={usdRate}
                displayNetWorth={displayNetWorth}
                displayFloatingPnl={displayFloatingPnl}
                displaySettledPnl={displaySettledPnl}
                floatingFees={floatingFees}
                settledFees={settledFees}
                livePrices={livePrices}
                wsConnected={wsConnected}
                onImportCsv={handleImportCsv}
                onRefresh={handleRefreshAll}
                onExport={handleExport}
                onExportExcel={handleExportExcel}
                onDownloadTemplate={handleDownloadTemplate}
                onTriggerImportPicker={triggerImportPicker}
                onOpenGenesis={() => dialogs.setIsGenesisModalOpen(true)}
                onUpdateBalances={() => {
                    if (!hoard) return;
                    dialogs.setGenesisData({
                        egp_balance: String(hoard.cash_egp),
                        usd_balance: String(hoard.cash_usd),
                        holdings: []
                    });
                    dialogs.setIsGenesisModalOpen(true);
                }}
                onOpenAddPosition={() => forms.setIsAddModalOpen(true)}
                onOpenManagement={async () => {
                    dialogs.setIsManagementModalOpen(true);
                    setManagementMessage('');
                    if (!managementReport) await fetchManagementReport(reportControls.refresh_prices);
                }}
                onOpenAnalysis={() => dialogs.setIsAnalysisModalOpen(true)}
                onOpenRebalance={() => setIsRebalanceModalOpen(true)}
                onBatchMoveBreakeven={(tickers) => handleBatchAction('MOVE_STOPS_BREAKEVEN', tickers)}
                onBatchScaleOut50={(tickers) => handleBatchAction('SCALE_OUT_50', tickers)}
                onBatchFlatten={(tickers) => handleBatchAction('FLATTEN', tickers)}
                onEditPosition={(p: Position) => {
                    forms.setSelectedPosition(p);
                    forms.setFormData({ ...forms.formData, sl: p.stop_loss ? String(p.stop_loss) : '', tp: p.target_price ? String(p.target_price) : '' });
                    forms.setIsUpdateModalOpen(true);
                }}
                onClosePosition={dialogs.requestClosePosition}
                onReplicatePortfolio={handleReplicatePortfolio}
                traps={traps}
                genesisModal={!hoard && dialogs.isGenesisModalOpen ? (
                    <PortfolioGenesisModal
                        actionLoading={actionLoading}
                        genesisData={dialogs.genesisData}
                        onClose={() => dialogs.setIsGenesisModalOpen(false)}
                        onSubmit={handleGenesis}
                        onFieldChange={dialogs.handleGenesisFieldChange}
                        onAddHolding={dialogs.addGenesisHoldingRow}
                        onRemoveHolding={dialogs.removeGenesisHoldingRow}
                        onUpdateHolding={dialogs.updateGenesisHoldingRow}
                    />
                ) : null}
            />

            {forms.isAddModalOpen && (
                <PortfolioPositionModal
                    mode="add"
                    actionLoading={actionLoading}
                    formData={forms.formData}
                    onClose={() => forms.setIsAddModalOpen(false)}
                    onSubmit={forms.handleAddPosition}
                    onFieldChange={forms.handleFormFieldChange}
                />
            )}

            {forms.isUpdateModalOpen && forms.selectedPosition && (
                <PortfolioPositionModal
                    mode="update"
                    actionLoading={actionLoading}
                    position={forms.selectedPosition}
                    formData={forms.formData}
                    onClose={() => forms.setIsUpdateModalOpen(false)}
                    onSubmit={forms.handleUpdatePosition}
                    onFieldChange={forms.handleFormFieldChange}
                />
            )}

            {dialogs.closeConfirmOpen && dialogs.pendingClosePosition && (
                <div
                    className="fixed inset-0 z-[130] flex items-center justify-center bg-black/60 p-4"
                    onClick={(e) => {
                        if (e.target === e.currentTarget && !closeActionLoading) dialogs.resetCloseDialog();
                    }}
                >
                    <PortfolioCloseDialog
                        position={dialogs.pendingClosePosition}
                        sharesValue={dialogs.pendingCloseShares}
                        priceValue={dialogs.pendingClosePrice}
                        maxShares={dialogs.getMaxSellableShares(dialogs.pendingClosePosition)}
                        loading={closeActionLoading}
                        onCancel={dialogs.resetCloseDialog}
                        onConfirm={dialogs.confirmClosePosition}
                        onPriceChange={dialogs.setPendingClosePrice}
                        onSharesChange={dialogs.setPendingCloseShares}
                        onPercentClick={dialogs.setQuickCloseShares}
                    />
                </div>
            )}

            {dialogs.isAnalysisModalOpen && analysis && (
                <PortfolioAnalysisModal
                    analysis={analysis}
                    activePortfolioId={activePortfolioId}
                    onClose={() => dialogs.setIsAnalysisModalOpen(false)}
                />
            )}

            {isRebalanceModalOpen && (
                <PortfolioRebalanceModal
                    isOpen={isRebalanceModalOpen}
                    onClose={() => setIsRebalanceModalOpen(false)}
                    activePortfolioId={activePortfolioId}
                    onApplyRebalance={handleApplyRebalance}
                    actionLoading={actionLoading}
                />
            )}

            <PortfolioManagementModal
                open={dialogs.isManagementModalOpen}
                managementLoading={managementLoading}
                managementMessage={managementMessage}
                managementReport={managementReport}
                managementSendResult={managementSendResult}
                managedHoldings={managedHoldings}
                reportControls={reportControls}
                actionItemsPreviewLimit={actionItemsPreviewLimit}
                onClose={() => dialogs.setIsManagementModalOpen(false)}
                onAddHolding={addManagedHoldingRow}
                onRemoveHolding={removeManagedHoldingRow}
                onUpdateHolding={updateManagedHoldingRow}
                onClearRows={clearManagedHoldings}
                onRunIntake={handleManagementIntake}
                onUploadFile={(file, options) =>
                    handleUploadIntakeFile(file, {
                        ...options,
                        onCreated: async (newId) => {
                            if (portfolioContext?.refreshPortfolios) {
                                await portfolioContext.refreshPortfolios();
                            }
                            if (portfolioContext?.setActivePortfolioId) {
                                portfolioContext.setActivePortfolioId(newId);
                            }
                        },
                    })
                }
                onDownloadTemplate={handleDownloadTemplate}
                onOpenRebalance={() => setIsRebalanceModalOpen(true)}
                onGenerateReport={() => fetchManagementReport(reportControls.refresh_prices)}
                onSendReport={handleSendManagementReport}
                onSetReportControls={setReportControls}
                truncatePrice={truncatePrice}
            />

            {hoard && dialogs.isGenesisModalOpen && (
                <PortfolioGenesisModal
                    actionLoading={actionLoading}
                    genesisData={dialogs.genesisData}
                    onClose={() => dialogs.setIsGenesisModalOpen(false)}
                    onSubmit={handleGenesis}
                    onFieldChange={dialogs.handleGenesisFieldChange}
                    onAddHolding={dialogs.addGenesisHoldingRow}
                    onRemoveHolding={dialogs.removeGenesisHoldingRow}
                    onUpdateHolding={dialogs.updateGenesisHoldingRow}
                />
            )}

            {replicateModalState && activePortfolioId && (
                <PortfolioReplicateDialog
                    open={Boolean(replicateModalState)}
                    loading={replicateSubmitting}
                    sourcePortfolioId={replicateModalState.sourcePortfolioId}
                    sourcePortfolioName={replicateModalState.sourcePortfolioName}
                    targetPortfolioId={activePortfolioId}
                    sourcePositions={replicateModalState.sourcePositions}
                    onClose={cancelReplication}
                    onConfirm={confirmReplication}
                />
            )}
        </>
    );
}
