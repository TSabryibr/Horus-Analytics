'use client';

import { RefreshCw } from 'lucide-react';

import { StrategyControlsPanel } from './components/StrategyControlsPanel';
import { PriceActionLabPanel } from './components/PriceActionLabPanel';
import { StrategyReasoningPanel } from './components/StrategyReasoningPanel';
import { StrategyShell } from './components/StrategyShell';
import { StrategyTerrainPanel } from './components/StrategyTerrainPanel';
import { usePriceActionLab } from './hooks/usePriceActionLab';
import { useStrategyActions } from './hooks/useStrategyActions';
import { useStrategyRuntime } from './hooks/useStrategyRuntime';

export default function StrategyPage() {
    const {
        proposal,
        isLoading,
        refreshStrategy,
        successMsg,
        setSuccessMsg,
        errorMsg,
        setErrorMsg,
        manualMode,
        manualParams,
        toggleManualMode,
        updateManualParam,
        buildApplyPayload,
        getRegimeColor,
    } = useStrategyRuntime();

    const { applying, applyStrategy, refresh } = useStrategyActions({
        manualMode,
        proposal,
        refreshStrategy,
        buildApplyPayload,
        setErrorMsg,
        setSuccessMsg,
    });

    const priceActionLab = usePriceActionLab();

    return (
        <StrategyShell
            errorMsg={errorMsg}
            isLoading={isLoading}
            manualMode={manualMode}
            onRefresh={refresh}
            onToggleManualMode={toggleManualMode}
            successMsg={successMsg}
            activeRegime={proposal?.regime}
            riskBudget="🛡️ 2.5% ATR"
        >
            {isLoading ? (
                <div className="flex-1 flex justify-center items-center">
                    <RefreshCw className="w-10 h-10 text-gray-600 animate-spin" />
                </div>
            ) : proposal && (
                <div className="space-y-8">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        <div className="space-y-6">
                            <StrategyTerrainPanel
                                getRegimeColor={getRegimeColor}
                                proposal={proposal}
                            />
                            <StrategyReasoningPanel reasoning={proposal.reasoning} />
                        </div>

                        <StrategyControlsPanel
                            applying={applying}
                            manualMode={manualMode}
                            manualParams={manualParams}
                            onApply={applyStrategy}
                            onManualParamChange={updateManualParam}
                            proposal={proposal}
                        />
                    </div>

                    <PriceActionLabPanel
                        actionError={priceActionLab.actionError}
                        actionSuccess={priceActionLab.actionSuccess}
                        backtestResult={priceActionLab.backtestResult}
                        busyAction={priceActionLab.busyAction}
                        capital={priceActionLab.capital}
                        catalogError={priceActionLab.catalogError}
                        catalogLoading={priceActionLab.catalogLoading}
                        dateFrom={priceActionLab.dateFrom}
                        dateTo={priceActionLab.dateTo}
                        familyFilter={priceActionLab.familyFilter}
                        filteredCatalog={priceActionLab.filteredCatalog}
                        market={priceActionLab.market}
                        profileName={priceActionLab.profileName}
                        promotedProfile={priceActionLab.promotedProfile}
                        selectedStrategy={priceActionLab.selectedStrategy}
                        selectedStrategyId={priceActionLab.selectedStrategyId}
                        signals={priceActionLab.signals}
                        ticker={priceActionLab.ticker}
                        onActivate={priceActionLab.activateProfile}
                        onBacktest={priceActionLab.backtestStrategy}
                        onEvaluate={priceActionLab.evaluateStrategy}
                        onPromote={priceActionLab.promoteStrategy}
                        onReloadCatalog={priceActionLab.reloadCatalog}
                        setCapital={priceActionLab.setCapital}
                        setDateFrom={priceActionLab.setDateFrom}
                        setDateTo={priceActionLab.setDateTo}
                        setFamilyFilter={priceActionLab.setFamilyFilter}
                        setMarket={priceActionLab.setMarket}
                        setProfileName={priceActionLab.setProfileName}
                        setSelectedStrategyId={priceActionLab.setSelectedStrategyId}
                        setTicker={priceActionLab.setTicker}
                    />
                </div>
            )}
        </StrategyShell>
    );
}
