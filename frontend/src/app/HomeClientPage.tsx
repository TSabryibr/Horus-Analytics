'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';

import { IndustrialButton } from './components/custom/IndustrialButton';
import { IndustrialCard } from './components/custom/IndustrialCard';
import { IndustrialInput } from './components/custom/IndustrialInput';
import { HomeArchivesModal } from './components/HomeArchivesModal';
import { HomeShell } from './components/HomeShell';
import { HomeSignalsPanel } from './components/HomeSignalsPanel';
import { useHomeActions } from './hooks/useHomeActions';
import { useHomeRuntime } from './hooks/useHomeRuntime';

const HomeEquityChart = dynamic(() => import('./components/charts/HomeEquityChart'), {
    ssr: false,
    loading: () => <div className="h-full w-full bg-white/5 rounded-none animate-pulse" />,
});

type FocusMode = 'FULL' | 'CHART' | 'FEED';

export default function HomeClientPage() {
    const router = useRouter();
    const {
        archivesByDate,
        curve,
        dataSource,
        error,
        hasCurve,
        health,
        metrics,
        setShowArchives,
        showArchives,
        isSourceLoading,
        signalDesk,
    } = useHomeRuntime();
    const { initializeLoading, initializeRun, setDeskMode } = useHomeActions();
    const [focusMode, setFocusMode] = useState<FocusMode>('FULL');
    const [deepScanSymbol, setDeepScanSymbol] = useState('');
    const [isAutopilotModalOpen, setIsAutopilotModalOpen] = useState(false);

    const totalCandidates = signalDesk.intradayCount + signalDesk.swingCount + signalDesk.positionCount;
    const publishReadinessLabel = totalCandidates > 0
        ? `${totalCandidates} candidates ready`
        : 'Pipeline idle';

    const normalizedDeepScanSymbol = deepScanSymbol.trim().toUpperCase();

    const handleExecuteDeepScan = () => {
        if (!normalizedDeepScanSymbol) {
            return;
        }
        router.push(`/oracle?ticker=${encodeURIComponent(normalizedDeepScanSymbol)}`);
    };

    const handleOverride = () => {
        router.push(normalizedDeepScanSymbol ? `/oracle?ticker=${encodeURIComponent(normalizedDeepScanSymbol)}` : '/oracle');
    };

    const handleModeChange = async (operatingMode: 'MANUAL' | 'AI_ASSIST' | 'AUTOPILOT') => {
        if (operatingMode === 'AUTOPILOT' && signalDesk.operatingMode !== 'AUTOPILOT') {
            setIsAutopilotModalOpen(true);
            return;
        }
        await setDeskMode(operatingMode, false);
    };

    const confirmArmAutopilot = async () => {
        setIsAutopilotModalOpen(false);
        await setDeskMode('AUTOPILOT', true);
    };

    return (
        <HomeShell
            dataSource={dataSource}
            error={error || signalDesk.error}
            deskMode={signalDesk.operatingMode}
            autopilotArmed={signalDesk.autopilotArmed}
            failedDeliveryCount={signalDesk.failedDeliveryCount}
            laneSummary={{
                intraday: signalDesk.intradayCount,
                swing: signalDesk.swingCount,
                position: signalDesk.positionCount,
            }}
            publishReadinessLabel={publishReadinessLabel}
            initializeLoading={initializeLoading}
            marketStatus={(
                <div className="flex items-center gap-3">
                    <span className="meta-label text-slate-500">Desk Mode</span>
                    <div className="flex items-center gap-2">
                        {(['MANUAL', 'AI_ASSIST', 'AUTOPILOT'] as const).map((mode) => (
                            <button
                                key={mode}
                                type="button"
                                onClick={() => {
                                    void handleModeChange(mode);
                                }}
                                className={cn(
                                    'rounded-[0.8rem] border px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.18em] transition',
                                    signalDesk.operatingMode === mode
                                        ? 'border-primary/40 bg-primary/10 text-primary'
                                        : 'border-white/10 bg-white/[0.03] text-slate-400 hover:border-primary/25 hover:text-white'
                                )}
                            >
                                {mode === 'AI_ASSIST' ? 'AI Assist' : mode}
                            </button>
                        ))}
                    </div>
                </div>
            )}
            metrics={metrics}
            health={health}
            isSourceLoading={isSourceLoading || signalDesk.loading}
            focusMode={focusMode}
            onSetFocusMode={setFocusMode}
            onInitializeRun={initializeRun}
        >
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
                <div className={cn('space-y-5', focusMode === 'FEED' ? 'xl:col-span-5' : 'xl:col-span-8')}>
                    <IndustrialCard
                        title="Performance Analytics"
                        subtitle="Equity Curve · Backtest Performance"
                        className="h-[clamp(20rem,38vw,26rem)]"
                    >
                        <div className="h-full w-full relative">
                            {hasCurve ? (
                                <HomeEquityChart curve={curve} />
                            ) : (
                                <div className="h-full w-full flex flex-col items-center justify-center border border-dashed border-white/5 bg-white/[0.02]">
                                    <span className="material-symbols-outlined text-4xl text-slate-700 mb-2">monitoring</span>
                                    <p className="meta-label">Awaiting pipeline initialization…</p>
                                    <IndustrialButton
                                        variant="primary"
                                        size="sm"
                                        className="mt-4"
                                        onClick={initializeRun}
                                        disabled={isSourceLoading}
                                    >
                                        Initialize Pipeline
                                    </IndustrialButton>
                                </div>
                            )}
                        </div>
                    </IndustrialCard>

                    {focusMode !== 'CHART' ? (
                        <HomeSignalsPanel
                            hasSignals={totalCandidates > 0}
                            isSourceLoading={isSourceLoading || signalDesk.loading}
                            onOpenArchives={() => setShowArchives(true)}
                            onOpenTelegram={() => router.push('/telegram')}
                            operatingMode={signalDesk.operatingMode}
                            autopilotArmed={signalDesk.autopilotArmed}
                            failedDeliveryCount={signalDesk.failedDeliveryCount}
                            lifecycle={signalDesk.lifecycleSummary}
                            followUps={signalDesk.followUps}
                            lanes={{
                                intraday: signalDesk.desk?.lanes?.intraday ?? { count: 0, candidates: [] },
                                swing: signalDesk.desk?.lanes?.swing ?? { count: 0, candidates: [] },
                                position: signalDesk.desk?.lanes?.position ?? { count: 0, candidates: [] },
                            }}
                        />
                    ) : null}
                </div>

                <div className={cn('space-y-5', focusMode === 'FEED' ? 'xl:col-span-7' : 'xl:col-span-4')}>
                    <IndustrialCard title="Signal Pipeline" subtitle="Candidate distribution by release horizon">
                        <div className="space-y-4">
                            {[
                                {
                                    label: 'Intraday',
                                    count: signalDesk.intradayCount,
                                    note: 'Session-cycle candidates from scanner and intraday signals.',
                                },
                                {
                                    label: 'Swing',
                                    count: signalDesk.swingCount,
                                    note: 'Multi-session candidates for swing-horizon campaigns.',
                                },
                                {
                                    label: 'Position',
                                    count: signalDesk.positionCount,
                                    note: 'Long-horizon conviction candidates for premium dispatch.',
                                },
                            ].map((lane) => (
                                <div key={lane.label} className="rounded-[1rem] border border-white/8 bg-white/[0.03] p-4">
                                    <div className="flex items-center justify-between gap-3">
                                        <div>
                                            <p className="text-[10px] font-black uppercase tracking-[0.26em] text-slate-500">{lane.label}</p>
                                            <p className="mt-1 text-xs text-slate-400">{lane.note}</p>
                                        </div>
                                        <div className="text-2xl font-black text-white">{lane.count}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </IndustrialCard>

                    <IndustrialCard title="Quick Access" subtitle="Operator control points">
                        <div className="space-y-3">
                            <IndustrialInput
                                placeholder="Enter ticker for deep analysis…"
                                value={deepScanSymbol}
                                onChange={(event) => setDeepScanSymbol(event.target.value)}
                                className="uppercase"
                                aria-label="Deep Scan Symbol"
                            />
                            <div className="grid grid-cols-2 gap-2">
                                <IndustrialButton
                                    variant="primary"
                                    size="sm"
                                    className="w-full"
                                    onClick={handleExecuteDeepScan}
                                    disabled={!normalizedDeepScanSymbol}
                                >
                                    Analyze
                                </IndustrialButton>
                                <IndustrialButton
                                    variant="ghost"
                                    size="sm"
                                    className="w-full"
                                    onClick={handleOverride}
                                >
                                    Override
                                </IndustrialButton>
                            </div>
                            <div className="grid grid-cols-2 gap-2 pt-2">
                                <IndustrialButton variant="ghost" size="sm" className="w-full" onClick={() => router.push('/scanner')}>
                                    Scanner
                                </IndustrialButton>
                                <IndustrialButton variant="ghost" size="sm" className="w-full" onClick={() => router.push('/telegram')}>
                                    Dispatch Rail
                                </IndustrialButton>
                            </div>
                        </div>
                    </IndustrialCard>
                </div>
            </div>

            <HomeArchivesModal
                archivesByDate={archivesByDate}
                isOpen={showArchives}
                onClose={() => setShowArchives(false)}
            />

            {isAutopilotModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
                    <div className="w-full max-w-md rounded-2xl border border-rose-500/30 bg-slate-900 p-6 shadow-2xl">
                        <div className="mb-3 flex items-center gap-3">
                            <span className="rounded-full bg-rose-500/20 p-2 text-rose-400 font-bold">
                                ⚠️
                            </span>
                            <h3 className="text-lg font-black uppercase tracking-wider text-white">
                                Arm Autopilot Mode?
                            </h3>
                        </div>
                        <p className="text-sm leading-relaxed text-slate-300">
                            Arming Autopilot mode enables automated signal processing and candidate dispatch across active lanes.
                            Ensure your strategy parameters, stop-loss rules, and risk limits are verified in Settings before proceeding.
                        </p>
                        <div className="mt-6 flex justify-end gap-3">
                            <button
                                type="button"
                                onClick={() => setIsAutopilotModalOpen(false)}
                                className="rounded-lg border border-white/10 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-white/5"
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                onClick={confirmArmAutopilot}
                                className="rounded-lg bg-rose-500 px-4 py-2 text-xs font-bold text-white hover:bg-rose-600"
                            >
                                Confirm & Arm Autopilot
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </HomeShell>
    );
}
