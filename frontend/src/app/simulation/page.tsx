'use client';

import dynamic from 'next/dynamic';
import { useEffect, useMemo, useState } from 'react';
import { getBaseUrl } from '@/lib/api';

const CrashSimulationPanel = dynamic(
    () => import('./components/CrashSimulationPanel').then(mod => mod.CrashSimulationPanel),
    { ssr: false, loading: () => <div className="flex h-[400px] items-center justify-center bg-slate-950/50 rounded-xl border border-white/5 text-slate-500">Loading Crash Simulation...</div> }
);

const RagnarokSimulationPanel = dynamic(
    () => import('./components/RagnarokSimulationPanel').then(mod => mod.RagnarokSimulationPanel),
    { ssr: false, loading: () => <div className="flex h-[400px] items-center justify-center bg-slate-950/50 rounded-xl border border-white/5 text-slate-500">Loading Ragnarok Engine...</div> }
);

const StrategyMonteCarloPanel = dynamic(
    () => import('./components/StrategyMonteCarloPanel').then(mod => mod.StrategyMonteCarloPanel),
    { ssr: false, loading: () => <div className="flex h-[400px] items-center justify-center bg-slate-950/50 rounded-xl border border-white/5 text-slate-500">Loading Monte Carlo...</div> }
);
const StrategyBacktestPanel = dynamic(
    () => import('./components/StrategyBacktestPanel').then(mod => mod.StrategyBacktestPanel),
    { ssr: false, loading: () => <div className="flex h-[400px] items-center justify-center bg-slate-950/50 rounded-xl border border-white/5 text-slate-500">Loading Backtest...</div> }
);

import { ReplayPanel } from './components/ReplayPanel';
import { DryRunPanel } from './components/DryRunPanel';
import { SimulationShell, type SimulationTab } from './components/SimulationShell';
import { useCrashSimulation } from './hooks/useCrashSimulation';
import { useRagnarokSimulation } from './hooks/useRagnarokSimulation';
import { useStrategyMonteCarlo } from './hooks/useStrategyMonteCarlo';
import { useReplay } from './hooks/useReplay';
import { useDryRun } from './hooks/useDryRun';
import { useSimulationBacktest } from './hooks/useSimulationBacktest';
import { normalizeSimulationProfiles, type SimulationProfileSummary } from './lib/profileSelection';
import { formatSimulationChartData } from './lib/simulationTransforms';

export default function SimulationPage() {
    const [tab, setTab] = useState<SimulationTab>('DRYRUN');
    const [simulationProfiles, setSimulationProfiles] = useState<SimulationProfileSummary[]>([]);
    const [simulationProfileId, setSimulationProfileId] = useState('');
    const [simulationProfilesLoading, setSimulationProfilesLoading] = useState(false);
    const [simulationProfilesError, setSimulationProfilesError] = useState<string | null>(null);
    const [activeProfileId, setActiveProfileId] = useState<number | null>(null);

    const apiBase = getBaseUrl();
    const selectedSimulationProfileId = simulationProfileId ? parseInt(simulationProfileId, 10) : null;
    const {
        stressLoading,
        stressResult,
        indexChoice,
        setIndexChoice,
        startDate,
        setStartDate,
        initialCapital,
        setInitialCapital,
        runCrashSimulation,
    } = useCrashSimulation({ apiBase });
    const {
        ragnarokLoading,
        ragnarokResult,
        ragnarokError,
        ragnarokIterations,
        setRagnarokIterations,
        ragnarokDays,
        setRagnarokDays,
        ragnarokStartingValue,
        setRagnarokStartingValue,
        ragnarokRuinThresholdPct,
        setRagnarokRuinThresholdPct,
        tickerInput,
        setTickerInput,
        runRagnarokSimulation,
    } = useRagnarokSimulation({ apiBase });
    const {
        mcLoading,
        mcResult,
        mcError,
        mcCapital,
        setMcCapital,
        mcSims,
        setMcSims,
        mcRuinThreshold,
        setMcRuinThreshold,
        runStrategyMonteCarlo,
    } = useStrategyMonteCarlo({ apiBase });
    const {
        backtestLoading,
        backtestError,
        backtestResult,
        strategyCatalog,
        strategyId,
        setStrategyId,
        backtestMarket,
        setBacktestMarket,
        backtestStartDate,
        setBacktestStartDate,
        backtestEndDate,
        setBacktestEndDate,
        backtestCapital,
        setBacktestCapital,
        backtestCommission,
        setBacktestCommission,
        backtestSlippage,
        setBacktestSlippage,
        loadStrategyCatalog,
        runBacktest,
    } = useSimulationBacktest({ apiBase });
    const {
        replayDate,
        setReplayDate,
        replayMode,
        setReplayMode,
        replayStartDate,
        setReplayStartDate,
        replayEndDate,
        setReplayEndDate,
        replaySpeed,
        setReplaySpeed,
        replayNotify,
        setReplayNotify,
        replayReport,
        setReplayReport,
        replayResetPortfolio,
        setReplayResetPortfolio,
        replayCloseOpenPositionsEnd,
        setReplayCloseOpenPositionsEnd,
        replayTreatMissingDaysAsHolidays,
        setReplayTreatMissingDaysAsHolidays,
        replayLiveChannelRouting,
        setReplayLiveChannelRouting,
        replayLoading,
        replayStatus,
        replayError,
        startReplay,
        stopReplay,
        downloadExcelReport,
        fetchStatus: fetchReplayStatus,
    } = useReplay({ apiBase, selectedProfileId: selectedSimulationProfileId });
    const {
        dryrunDate,
        setDryrunDate,
        dryrunNotify,
        setDryrunNotify,
        dryrunReport,
        setDryrunReport,
        dryrunAiReport,
        setDryrunAiReport,
        dryrunLoading,
        dryrunStatus,
        dryrunError,
        startDryRun,
    } = useDryRun({ apiBase, selectedProfileId: selectedSimulationProfileId });

    const ragnarokChartData = useMemo(() => (ragnarokResult ? formatSimulationChartData(ragnarokResult.plot_paths) : []), [ragnarokResult]);
    const mcChartData = useMemo(() => (mcResult ? formatSimulationChartData(mcResult.plot_paths) : []), [mcResult]);
    const selectedSimulationProfile = useMemo(
        () => simulationProfiles.find((profile) => profile.id === selectedSimulationProfileId) ?? null,
        [simulationProfiles, selectedSimulationProfileId]
    );
    const activeSimulationProfile = useMemo(
        () => simulationProfiles.find((profile) => profile.id === activeProfileId) ?? null,
        [simulationProfiles, activeProfileId]
    );
    const selectedProfileLabel = selectedSimulationProfile
        ? `${selectedSimulationProfile.profile_name} (${selectedSimulationProfile.source_type})`
        : 'Horus Core';

    useEffect(() => {
        let active = true;
        const loadProfiles = async () => {
            setSimulationProfilesLoading(true);
            setSimulationProfilesError(null);
            try {
                const res = await fetch(`${apiBase}/api/v1/strategy/pine/scanner-profiles`);
                const json = await res.json();
                if (!active) return;
                if (!res.ok || json.status !== 'success') {
                    throw new Error(json.detail || json.message || 'Failed to load strategy profiles');
                }
                setSimulationProfiles(normalizeSimulationProfiles(json.profiles));
                const normalizedActiveProfileId = Number(json.active_profile_id);
                setActiveProfileId(Number.isFinite(normalizedActiveProfileId) ? normalizedActiveProfileId : null);
            } catch (error) {
                if (!active) return;
                const message = error instanceof Error ? error.message : 'Failed to load strategy profiles';
                setSimulationProfilesError(message);
            } finally {
                if (active) {
                    setSimulationProfilesLoading(false);
                }
            }
        };

        void loadProfiles();
        return () => {
            active = false;
        };
    }, [apiBase]);

    useEffect(() => {
        void loadStrategyCatalog();
        // load once per API base
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [apiBase]);

    useEffect(() => {
        if (tab === 'REPLAY') {
            void fetchReplayStatus();
        }
    }, [tab, fetchReplayStatus]);

    return (
        <SimulationShell
            tab={tab}
            onSelectTab={setTab}
            profileControls={
                <div className="grid gap-4 rounded-[1.2rem] border border-white/10 bg-slate-950/70 p-4 lg:grid-cols-[minmax(0,1fr)_360px]">
                    <div className="space-y-2">
                        <div className="meta-label text-cyan-200/70">Shared Strategy Profile Context</div>
                        <p className="text-sm leading-6 text-slate-300">
                            One selector now drives scanner-backed simulator execution flows. Replay and Dry Run both honor this choice; leaving it on Horus Core keeps the default engine behavior.
                        </p>
                        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                            <span>
                                Active live profile: <span className="font-semibold text-slate-200">{activeSimulationProfile?.profile_name || 'None'}</span>
                            </span>
                            {simulationProfilesError ? (
                                <span className="text-rose-300">{simulationProfilesError}</span>
                            ) : null}
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="block text-[10px] font-black uppercase tracking-[0.18em] text-slate-500">
                            Strategy Profile
                        </label>
                        <select
                            value={simulationProfileId}
                            onChange={(event) => setSimulationProfileId(event.target.value)}
                            disabled={simulationProfilesLoading}
                            className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400/40 focus:ring-2 focus:ring-cyan-500/20 disabled:opacity-50"
                        >
                            <option value="">Horus Core (No profile override)</option>
                            {simulationProfiles.map((profile) => (
                                <option key={profile.id} value={profile.id}>
                                    {profile.profile_name} - {profile.source_type} - {profile.profile_state || 'DRAFT'}
                                </option>
                            ))}
                        </select>
                        <p className="text-xs text-slate-500">
                            Current selection: <span className="font-semibold text-slate-300">{selectedProfileLabel}</span>
                        </p>
                    </div>
                </div>
            }
        >
            {tab === 'CRASH' && (
                <CrashSimulationPanel
                    stressLoading={stressLoading}
                    stressResult={stressResult}
                    indexChoice={indexChoice}
                    setIndexChoice={setIndexChoice}
                    startDate={startDate}
                    setStartDate={setStartDate}
                    initialCapital={initialCapital}
                    setInitialCapital={setInitialCapital}
                    onSimulate={runCrashSimulation}
                />
            )}

            {tab === 'RAGNAROK' && (
                <RagnarokSimulationPanel
                    ragnarokLoading={ragnarokLoading}
                    ragnarokResult={ragnarokResult}
                    ragnarokError={ragnarokError}
                    ragnarokIterations={ragnarokIterations}
                    setRagnarokIterations={setRagnarokIterations}
                    ragnarokDays={ragnarokDays}
                    setRagnarokDays={setRagnarokDays}
                    ragnarokStartingValue={ragnarokStartingValue}
                    setRagnarokStartingValue={setRagnarokStartingValue}
                    ragnarokRuinThresholdPct={ragnarokRuinThresholdPct}
                    setRagnarokRuinThresholdPct={setRagnarokRuinThresholdPct}
                    tickerInput={tickerInput}
                    setTickerInput={setTickerInput}
                    ragnarokChartData={ragnarokChartData}
                    onSimulate={runRagnarokSimulation}
                />
            )}

            {tab === 'STRATEGY' && (
                <StrategyMonteCarloPanel
                    mcLoading={mcLoading}
                    mcResult={mcResult}
                    mcError={mcError}
                    mcCapital={mcCapital}
                    setMcCapital={setMcCapital}
                    mcSims={mcSims}
                    setMcSims={setMcSims}
                    mcRuinThreshold={mcRuinThreshold}
                    setMcRuinThreshold={setMcRuinThreshold}
                    mcChartData={mcChartData}
                    onSimulate={runStrategyMonteCarlo}
                />
            )}

            {tab === 'BACKTEST' && (
                <StrategyBacktestPanel
                    loading={backtestLoading}
                    error={backtestError}
                    result={backtestResult}
                    strategyCatalog={strategyCatalog}
                    strategyId={strategyId}
                    setStrategyId={setStrategyId}
                    market={backtestMarket}
                    setMarket={setBacktestMarket}
                    startDate={backtestStartDate}
                    setStartDate={setBacktestStartDate}
                    endDate={backtestEndDate}
                    setEndDate={setBacktestEndDate}
                    capital={backtestCapital}
                    setCapital={setBacktestCapital}
                    commission={backtestCommission}
                    setCommission={setBacktestCommission}
                    slippage={backtestSlippage}
                    setSlippage={setBacktestSlippage}
                    onRun={runBacktest}
                />
            )}

            {tab === 'REPLAY' && (
                <ReplayPanel
                    replayDate={replayDate}
                    setReplayDate={setReplayDate}
                    replayMode={replayMode}
                    setReplayMode={setReplayMode}
                    replayStartDate={replayStartDate}
                    setReplayStartDate={setReplayStartDate}
                    replayEndDate={replayEndDate}
                    setReplayEndDate={setReplayEndDate}
                    replaySpeed={replaySpeed}
                    setReplaySpeed={setReplaySpeed}
                    replayNotify={replayNotify}
                    setReplayNotify={setReplayNotify}
                    replayReport={replayReport}
                    setReplayReport={setReplayReport}
                    replayResetPortfolio={replayResetPortfolio}
                    setReplayResetPortfolio={setReplayResetPortfolio}
                    replayCloseOpenPositionsEnd={replayCloseOpenPositionsEnd}
                    setReplayCloseOpenPositionsEnd={setReplayCloseOpenPositionsEnd}
                    replayTreatMissingDaysAsHolidays={replayTreatMissingDaysAsHolidays}
                    setReplayTreatMissingDaysAsHolidays={setReplayTreatMissingDaysAsHolidays}
                    replayLiveChannelRouting={replayLiveChannelRouting}
                    setReplayLiveChannelRouting={setReplayLiveChannelRouting}
                    replayLoading={replayLoading}
                    replayStatus={replayStatus}
                    replayError={replayError}
                    selectedProfileLabel={selectedProfileLabel}
                    onStart={startReplay}
                    onStop={stopReplay}
                    onDownloadExcel={downloadExcelReport}
                />
            )}

            {tab === 'DRYRUN' && (
                <DryRunPanel
                    dryrunDate={dryrunDate}
                    setDryrunDate={setDryrunDate}
                    dryrunNotify={dryrunNotify}
                    setDryrunNotify={setDryrunNotify}
                    dryrunReport={dryrunReport}
                    setDryrunReport={setDryrunReport}
                    dryrunAiReport={dryrunAiReport}
                    setDryrunAiReport={setDryrunAiReport}
                    dryrunLoading={dryrunLoading}
                    dryrunStatus={dryrunStatus}
                    dryrunError={dryrunError}
                    selectedProfileLabel={selectedProfileLabel}
                    onStart={startDryRun}
                />
            )}
        </SimulationShell>
    );
}
