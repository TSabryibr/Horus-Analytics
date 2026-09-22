'use client';

import { memo } from 'react';
import { Database, Inbox, BarChart3, Activity, FileX } from 'lucide-react';
import clsx from 'clsx';

interface EmptyStateProps {
    title?: string;
    message?: string;
    icon?: 'database' | 'inbox' | 'chart' | 'activity' | 'file';
    compact?: boolean;
    className?: string;
}

const icons = {
    database: Database,
    inbox: Inbox,
    chart: BarChart3,
    activity: Activity,
    file: FileX,
};

const EmptyState = memo(function EmptyState({
    title = "No Data Available",
    message = "Initialize the pipeline or record positions to populate this view.",
    icon = 'database',
    compact = false,
    className,
}: EmptyStateProps) {
    const Icon = icons[icon];

    if (compact) {
        return (
            <div className={clsx("flex items-center justify-center gap-3 py-6 text-slate-500", className)}>
                <Icon className="h-4 w-4 text-primary/70" />
                <span className="text-sm font-medium uppercase tracking-[0.16em]">{title}</span>
            </div>
        );
    }

    return (
        <div className={clsx("flex flex-col items-center justify-center py-16 px-6 text-center", className)}>
            <div className="section-surface-muted industrial-corner mb-6 flex size-20 items-center justify-center rounded-[1.4rem] border border-primary/15 bg-primary/5">
                <Icon className="h-10 w-10 text-primary/80" />
            </div>
            <div className="meta-label">Awaiting Data</div>
            <h3 className="mt-3 text-lg font-black uppercase tracking-[0.14em] text-slate-100">{title}</h3>
            <p className="mt-3 max-w-md text-sm leading-6 text-slate-400">{message}</p>
        </div>
    );
});

export default EmptyState;
