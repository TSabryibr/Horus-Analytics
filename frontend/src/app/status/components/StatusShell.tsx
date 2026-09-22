'use client';

import { ReactNode } from 'react';
import { Activity, RefreshCcw } from 'lucide-react';

import type { RuntimeSurfaceState } from '@/app/lib/runtimeStatus';
import { CommandHeader } from '@/app/components/custom/CommandHeader';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';

interface StatusShellProps {
    loading: boolean;
    lastRefresh: Date | null;
    runtimeState: RuntimeSurfaceState;
    fetchStatus: () => void | Promise<void>;
    children: ReactNode;
}

export function StatusShell({
    loading,
    lastRefresh,
    runtimeState,
    fetchStatus,
    children,
}: StatusShellProps) {
    const runtimeTone =
        runtimeState.code === 'FRESH'
            ? 'success'
            : runtimeState.code === 'DETECTING' || runtimeState.code === 'SYNCING' || runtimeState.code === 'PROVISIONING'
                ? 'primary'
                : runtimeState.code === 'PROVISIONING_ERROR'
                    ? 'danger'
                    : 'warning';

    return (
        <div className="page-shell page-shell-wide custom-scrollbar gap-8 overflow-x-hidden bg-slate-950">
            <CommandHeader
                eyebrow="System Observability"
                title="Observability Terminal"
                description="Real-time system health, data ingestion latency, and core engine diagnostics."
                icon={<Activity className="h-8 w-8" />}
                statusItems={[
                    { label: 'Runtime State', value: runtimeState.label, tone: runtimeTone },
                    { label: 'Last Engine Ping', value: lastRefresh ? lastRefresh.toLocaleTimeString() : '--:--:--', tone: 'muted' },
                ]}
                actions={
                    <IndustrialButton type="button" variant={loading ? 'secondary' : 'primary'} onClick={fetchStatus}>
                        <RefreshCcw size={12} className={loading ? 'animate-spin' : ''} />
                        Force Re-Validation
                    </IndustrialButton>
                }
            />

            {loading ? (
                <div className="section-surface-muted flex items-center gap-3 rounded-[1.25rem] border border-primary/20 bg-primary/5 px-4 py-3 text-sm text-slate-300">
                    <RefreshCcw className="h-4 w-4 animate-spin text-primary" />
                    <span>Sampling live status feed...</span>
                </div>
            ) : null}

            {children}
        </div>
    );
}
