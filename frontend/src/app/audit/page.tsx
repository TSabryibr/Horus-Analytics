'use client';

import dynamic from 'next/dynamic';
import { AuditFollowUpsPanel } from './components/AuditFollowUpsPanel';
import { AuditLifecyclePanel } from './components/AuditLifecyclePanel';
import { AuditLedgerPanel } from './components/AuditLedgerPanel';
import { AuditShell } from './components/AuditShell';
import { AuditSummaryPanel } from './components/AuditSummaryPanel';
import { PanelErrorBoundary } from './components/PanelErrorBoundary';

const AuditChartsPanel = dynamic(
    () => import('./components/AuditChartsPanel').then(mod => mod.AuditChartsPanel),
    { ssr: false, loading: () => <div className="col-span-12 xl:col-span-8 flex h-[400px] items-center justify-center bg-slate-950/50 rounded-xl border border-white/5 text-slate-500">Loading Audit Analytics...</div> }
);
import { useAuditStream } from './hooks/useAuditStream';
import { useAuditRuntime } from './hooks/useAuditRuntime';

export default function AuditPage() {
    const {
        audit,
        setAudit,
        loading,
        lifecycleRows,
        lifecycleSummary,
        followUpRows,
        followUpSummary,
        filter,
        setFilter,
        days,
        setDays,
        expandedRow,
        setExpandedRow,
        apiBase,
        fetchData,
        overrideLifecycle,
        actOnFollowUp,
        handleExport,
        comparisonData,
        colors,
        lastUpdated,
    } = useAuditRuntime();

    const { wsConnected } = useAuditStream({ apiBase, setAudit });

    return (
        <AuditShell
            days={days}
            setDays={setDays}
            fetchData={fetchData}
            handleExport={handleExport}
            loading={loading}
            wsConnected={wsConnected}
            lastUpdated={lastUpdated}
        >
            <div className="grid grid-cols-12 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                <PanelErrorBoundary panelName="Audit Charts">
                    <AuditChartsPanel
                        comparisonData={comparisonData}
                        strategies={audit?.strategies || []}
                        colors={colors}
                    />
                </PanelErrorBoundary>
                <PanelErrorBoundary panelName="Audit Summary">
                    <AuditSummaryPanel
                        strategies={audit?.strategies || []}
                        colors={colors}
                    />
                </PanelErrorBoundary>
                <PanelErrorBoundary panelName="Audit Ledger">
                    <AuditLedgerPanel
                        strategies={audit?.strategies || []}
                        logs={audit?.logs || []}
                        filter={filter}
                        setFilter={setFilter}
                        expandedRow={expandedRow}
                        setExpandedRow={setExpandedRow}
                    />
                </PanelErrorBoundary>
                <PanelErrorBoundary panelName="Lifecycle Review">
                    <AuditLifecyclePanel
                        rows={lifecycleRows}
                        summary={lifecycleSummary}
                        loading={loading}
                        onOverride={overrideLifecycle}
                    />
                </PanelErrorBoundary>
                <PanelErrorBoundary panelName="Follow-Up Delivery">
                    <AuditFollowUpsPanel
                        rows={followUpRows}
                        summary={followUpSummary}
                        loading={loading}
                        onAction={actOnFollowUp}
                    />
                </PanelErrorBoundary>
            </div>
        </AuditShell>
    );
}
