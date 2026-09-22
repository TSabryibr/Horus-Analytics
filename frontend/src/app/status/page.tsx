'use client';

import { useEffect, useRef } from 'react';
import {
    Database,
    Network,
    ShieldCheck,
    Clock,
    RefreshCcw,
    AlertTriangle,
    CheckCircle2,
    Send,
    BarChart3,
    Calendar,
    Server,
    Cpu
} from 'lucide-react';
import clsx from 'clsx';
import { usePolling } from '@/hooks/usePolling';
import { resolveRuntimeSurfaceState } from '../lib/runtimeStatus';
import { StatusBackupCard } from './components/StatusBackupCard';
import { StatusDiagnosticsPanel } from './components/StatusDiagnosticsPanel';
import { StatusFreshnessPanel } from './components/StatusFreshnessPanel';
import { StatusLifecyclePanel } from './components/StatusLifecyclePanel';
import { StatusOverviewPanel } from './components/StatusOverviewPanel';
import { StatusSchedulerPanel } from './components/StatusSchedulerPanel';
import { StatusShell } from './components/StatusShell';
import { StatusSlaPanel } from './components/StatusSlaPanel';
import { useStatusSync } from './hooks/useStatusSync';
import { useStatusRuntime } from './hooks/useStatusRuntime';

export default function StatusPage() {
    const hasBootstrappedSyncRef = useRef(false);
    const {
        status,
        loading,
        lastRefresh,
        apiBase,
        fetchStatus,
        runtimeState,
        sourceEngine,
        driftValue,
        historySymbolCount,
        historyAgeHours,
    } = useStatusRuntime();
    const {
        syncingData,
        syncStatusMessage,
        fetchDataSyncStatus,
        bootstrapDataSyncStatus,
        triggerDataSync,
    } = useStatusSync({
        apiBase,
        fetchStatus,
    });

    useEffect(() => {
        if (hasBootstrappedSyncRef.current) {
            return;
        }
        hasBootstrappedSyncRef.current = true;
        void bootstrapDataSyncStatus();
    }, [bootstrapDataSyncStatus]);

    usePolling(fetchStatus, { intervalMs: 30_000, runImmediately: false, pauseWhenHidden: true });
    usePolling(fetchDataSyncStatus, {
        intervalMs: 5_000,
        enabled: syncingData,
        runImmediately: false,
        pauseWhenHidden: true,
    });

    const displayRuntimeState = syncingData
        ? resolveRuntimeSurfaceState({
            isSyncing: true,
            backendKnown: Boolean(status?.data_status),
            provisioningStatus: status?.provisioning_status,
            pipelineState: status?.pipeline_state,
            marketOpen: status?.freshness?.market_open,
            historyStatus: status?.data_status?.history?.status,
            intradayStatus: status?.data_status?.intraday?.status,
            historyOk: status?.data_status?.history?.ok,
            intradayOk: status?.data_status?.intraday?.ok,
        })
        : runtimeState;

    return (
        <StatusShell
            loading={loading && !status}
            lastRefresh={lastRefresh}
            runtimeState={displayRuntimeState}
            fetchStatus={fetchStatus}
        >

            <StatusOverviewPanel status={status} />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-8">
                    <StatusFreshnessPanel
                        status={status}
                        syncingData={syncingData}
                        syncStatusMessage={syncStatusMessage}
                        triggerDataSync={triggerDataSync}
                        historySymbolCount={historySymbolCount}
                        historyAgeHours={historyAgeHours}
                        sourceEngine={sourceEngine}
                        driftValue={driftValue}
                    />
                    <StatusLifecyclePanel
                        signalDesk={status?.signal_desk}
                        lifecycle={status?.signal_lifecycle}
                        followups={status?.signal_followups}
                    />
                    <StatusSlaPanel
                        deliverySla={status?.delivery_sla}
                        onRefresh={fetchStatus}
                    />
                    <StatusBackupCard
                        backupStatus={status?.database_backup}
                        onSnapshotTaken={fetchStatus}
                    />
                    <StatusSchedulerPanel jobs={status?.scheduler?.jobs || []} />
                </div>

                <StatusDiagnosticsPanel
                    status={status}
                    lastRefresh={lastRefresh}
                />
            </div >
        </StatusShell>
    );
}
