'use client';

import { LucideIcon, Clock, Cpu, Database, Send } from 'lucide-react';
import clsx from 'clsx';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';

interface StatusOverviewPanelProps {
    status: any;
}

export function StatusOverviewPanel({ status }: StatusOverviewPanelProps) {
    const provisioningStatus = String(status?.provisioning_status || '').toUpperCase();
    const provisioningCompleted = Number(status?.provisioning_completed_trading_days || 0);
    const provisioningTarget = Number(status?.provisioning_target_trading_days || 0);
    const provisioningError = String(status?.provisioning_error || status?.message || '').trim();
    const lastBackfillStatus = String(status?.last_backfill_status || '').toUpperCase();
    const lastBackfillMode = String(status?.last_backfill_mode || '').toUpperCase();
    const lastBackfillCompleted = Number(status?.last_backfill_completed_trading_days || 0);
    const lastBackfillTarget = Number(status?.last_backfill_target_trading_days || 0);
    const lastBackfillUniverseChoice = String(status?.last_backfill_universe_choice || 'EGX30').toUpperCase();
    const hasHistoricalBackfillSnapshot = status?.system_ready
        && ['COMPLETED', 'COMPLETED_WITH_WARNINGS'].includes(lastBackfillStatus)
        && lastBackfillTarget > 0;
    const lastBackfillModeLabel = lastBackfillMode === 'MANUAL'
        ? 'manual'
        : lastBackfillMode === 'AUTOMATIC'
            ? 'automatic'
            : 'historical';

    const readinessValue = status?.system_ready
        ? 'OPERATIONAL'
        : provisioningStatus === 'RUNNING'
            ? 'PROVISIONING'
            : provisioningStatus === 'ERROR'
                ? 'FAILED'
                : 'BOOTING';
    const readinessDesc = status?.system_ready && hasHistoricalBackfillSnapshot
        ? `Last ${lastBackfillModeLabel} backfill (${lastBackfillUniverseChoice}): ${lastBackfillCompleted} / ${lastBackfillTarget} trading days`
        : provisioningStatus === 'RUNNING' && provisioningTarget > 0
            ? `${provisioningCompleted} / ${provisioningTarget} trading days provisioned`
            : provisioningStatus === 'ERROR' && provisioningError
                ? provisioningError
                : 'Core FastAPI process & middleware';
    const readinessStatus = status?.system_ready
        ? 'success'
        : provisioningStatus === 'ERROR'
            ? 'danger'
            : 'warning';

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatusCard
                title="Engine Readiness"
                value={readinessValue}
                icon={Cpu}
                status={readinessStatus}
                desc={readinessDesc}
            />
            <StatusCard
                title="Database Link"
                value={status?.db_connected ? 'CONNECTED' : 'OFFLINE'}
                icon={Database}
                status={status?.db_connected ? 'success' : 'danger'}
                desc="Horus.db SQLite (WAL Mode)"
            />
            <StatusCard
                title="Telegram Sentinel"
                value={status?.alerts?.telegram?.configured ? 'ACTIVE' : 'DISABLED'}
                icon={Send}
                status={status?.alerts?.telegram?.configured ? 'success' : 'warning'}
                desc="Global signal broadcast link"
            />
            <StatusCard
                title="Scheduler Status"
                value={status?.scheduler?.running ? 'RUNNING' : 'STOPPED'}
                icon={Clock}
                status={status?.scheduler?.running ? 'success' : 'danger'}
                desc="Market scans & trade monitoring"
            />
        </div>
    );
}

function StatusCard({
    title,
    value,
    icon: Icon,
    status,
    desc,
}: {
    title: string;
    value: string;
    icon: LucideIcon;
    status: 'success' | 'warning' | 'danger';
    desc: string;
}) {
    const isSuccess = status === 'success';
    const isWarning = status === 'warning';
    const isDanger = status === 'danger';

    return (
        <IndustrialCard
            tone="secondary"
            className="h-full rounded-[1.5rem] transition hover:border-primary/15"
            contentClassName="p-6"
        >
            <div className="mb-4 flex items-start justify-between">
                <div className={clsx(
                    'p-2.5 rounded-2xl',
                    isSuccess && 'bg-emerald-500/10 text-emerald-500',
                    isWarning && 'bg-amber-500/10 text-amber-500',
                    isDanger && 'bg-rose-500/10 text-rose-500'
                )}>
                    <Icon className="w-6 h-6" />
                </div>
                <div className={clsx(
                    'w-2 h-2 rounded-full',
                    isSuccess ? 'bg-emerald-500  ' : isWarning ? 'bg-amber-500' : 'bg-rose-500'
                )} />
            </div>
            <div>
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{title}</p>
                <p className={clsx(
                    'text-xl font-black uppercase tracking-tight',
                    isSuccess && 'text-white',
                    isWarning && 'text-amber-500',
                    isDanger && 'text-rose-500'
                )}>
                    {value}
                </p>
                <p className="text-[10px] text-slate-500 font-medium mt-2">{desc}</p>
            </div>
        </IndustrialCard>
    );
}
