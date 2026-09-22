"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import clsx from 'clsx';
import {
    AlertCircle,
    AlertTriangle,
    ChevronLeft,
    ChevronRight,
    ClipboardList,
    Info,
    RefreshCw,
    Search,
} from 'lucide-react';

import { useLanguage } from '@/context/LanguageContext';
import { apiFetch } from '@/lib/api';
import { CommandHeader } from '@/app/components/custom/CommandHeader';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';
import { IndustrialInput } from '@/app/components/custom/IndustrialInput';

interface AuditEvent {
    id: number;
    event_type: string;
    severity: string;
    message: string;
    actor_type: string;
    created_at: string;
}

const limit = 20;

function formatAuditTimestamp(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return {
            dateLabel: 'Unknown Date',
            timeLabel: '--:--',
            isoLabel: value || 'UNSTAMPED',
        };
    }

    return {
        dateLabel: new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: '2-digit',
        }).format(date),
        timeLabel: new Intl.DateTimeFormat('en-US', {
            hour: '2-digit',
            minute: '2-digit',
        }).format(date),
        isoLabel: date.toISOString(),
    };
}

function normalizeAuditToken(value: string, fallback: string) {
    return value?.trim() ? value.replaceAll('_', ' ') : fallback;
}

function getSeverityTone(severity: string) {
    switch (severity.toUpperCase()) {
        case 'ERROR':
        case 'CRITICAL':
            return {
                icon: <AlertCircle className="h-4 w-4 text-rose-300" />,
                badgeClassName: 'border-rose-400/25 bg-rose-500/10 text-rose-100',
                railClassName: 'bg-rose-400/70',
            };
        case 'WARN':
        case 'WARNING':
            return {
                icon: <AlertTriangle className="h-4 w-4 text-amber-300" />,
                badgeClassName: 'border-amber-300/25 bg-amber-500/10 text-amber-100',
                railClassName: 'bg-amber-300/70',
            };
        default:
            return {
                icon: <Info className="h-4 w-4 text-sky-300" />,
                badgeClassName: 'border-sky-300/20 bg-sky-500/10 text-sky-100',
                railClassName: 'bg-sky-300/60',
            };
    }
}

function AuditLogSkeletonCell({ widthClassName }: { widthClassName: string }) {
    return (
        <div className={['section-surface-muted industrial-corner h-4 rounded-sm border border-white/8', widthClassName].join(' ')} />
    );
}

import { formatTimeSince, getPollingStatus, isStale } from '@/utils/telemetry';

export default function AuditLogsPage() {
    const { t, isRtl } = useLanguage();
    const [events, setEvents] = useState<AuditEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(0);
    const [total, setTotal] = useState(0);
    const [query, setQuery] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    useEffect(() => {
        void fetchLogs();
    }, [page]);

    const fetchLogs = async () => {
        setLoading(true);
        setErrorMessage('');
        try {
            const offset = page * limit;
            const res = await apiFetch(`/system/audit-logs?limit=${limit}&offset=${offset}`);
            if (res.ok) {
                const data = await res.json();
                setEvents(Array.isArray(data.events) ? data.events : []);
                setTotal(Number(data.total || 0));
                setLastUpdated(new Date());
                return;
            }

            setEvents([]);
            setTotal(0);
            setErrorMessage(`Audit ledger request failed with status ${res.status}. Retry the query window.`);
        } catch (err) {
            console.error("Failed to fetch audit logs", err);
            setEvents([]);
            setTotal(0);
            setErrorMessage('Audit ledger is temporarily unreachable. Check the backend link and retry.');
        } finally {
            setLoading(false);
        }
    };

    const visibleEvents = useMemo(() => {
        const normalizedQuery = query.trim().toLowerCase();
        if (!normalizedQuery) {
            return events;
        }

        return events.filter((event) =>
            `${event.event_type} ${event.severity} ${event.message} ${event.actor_type}`.toLowerCase().includes(normalizedQuery)
        );
    }, [events, query]);

    const start = total === 0 ? 0 : page * limit + 1;
    const end = total === 0 ? 0 : Math.min((page + 1) * limit, total);

    return (
        <div className="page-shell page-shell-wide">
            <CommandHeader
                eyebrow="Compliance Ledger"
                title={t('audit.title')}
                description="Institutional-grade event history for operator actions, system warnings, and execution traceability."
                icon={<ClipboardList className="h-7 w-7" />}
                iconClassName="border-cyan-400/20 bg-cyan-500/10 text-cyan-100"
                statusItems={[
                    getPollingStatus(loading, Boolean(errorMessage)),
                    { label: 'Sync', value: formatTimeSince(lastUpdated), tone: isStale(lastUpdated) ? 'warning' : 'muted' },
                    { label: 'Page Window', value: `${start}-${end}`, tone: 'primary' },
                    { label: 'Ledger Size', value: `${total} Events`, tone: 'muted' },
                ]}
                actions={
                    <div className="flex w-full flex-col gap-3 lg:w-auto lg:items-end">
                        <IndustrialInput
                            value={query}
                            onChange={(event) => setQuery(event.target.value)}
                            placeholder="FILTER LEDGER"
                            aria-label="Filter audit log entries"
                            shellClassName="w-full lg:w-[18rem]"
                            leadingSlot={<Search className="h-4 w-4" />}
                        />
                        <IndustrialButton
                            type="button"
                            variant={loading ? 'secondary' : 'primary'}
                            onClick={() => void fetchLogs()}
                        >
                            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
                            Refresh Ledger
                        </IndustrialButton>
                    </div>
                }
            />

            {errorMessage ? (
                <div
                    className="section-surface industrial-corner flex flex-col gap-4 rounded-[1.35rem] border border-destructive/30 bg-destructive/10 px-4 py-4 sm:flex-row sm:items-center sm:justify-between"
                    role="alert"
                >
                    <div className="min-w-0">
                        <div className="meta-label text-rose-300">Ledger Fault</div>
                        <p className="mt-2 text-sm leading-6 text-rose-100">{errorMessage}</p>
                    </div>
                    <IndustrialButton type="button" variant="alert" onClick={() => void fetchLogs()}>
                        <RefreshCw size={12} />
                        Retry Query
                    </IndustrialButton>
                </div>
            ) : null}

            <IndustrialCard
                tone="secondary"
                title="Event Register"
                subtitle="Timestamped system memory with severity, actor class, and execution detail"
                className="rounded-[1.6rem] overflow-hidden"
                contentClassName="overflow-x-auto p-0"
            >
                <table className={`w-full min-w-[1040px] table-fixed text-sm ${isRtl ? 'text-right' : 'text-left'}`}>
                    <colgroup>
                        <col className="w-[14rem]" />
                        <col className="w-[13rem]" />
                        <col className="w-[11rem]" />
                        <col className="w-[10rem]" />
                        <col />
                    </colgroup>
                    <thead className="border-b border-white/8 bg-white/[0.02]">
                        <tr>
                            <th scope="col" className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.24em] text-slate-400">{t('audit.timestamp')}</th>
                            <th scope="col" className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.24em] text-slate-400">{t('audit.event_type')}</th>
                            <th scope="col" className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.24em] text-slate-400">{t('audit.severity')}</th>
                            <th scope="col" className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.24em] text-slate-400">Actor</th>
                            <th scope="col" className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.24em] text-slate-400">{t('audit.message')}</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        <AnimatePresence mode="popLayout">
                            {loading ? (
                                Array.from({ length: 5 }).map((_, i) => (
                                    <tr key={`skeleton-${i}`}>
                                        <td className="px-6 py-4"><AuditLogSkeletonCell widthClassName="w-32" /></td>
                                        <td className="px-6 py-4"><AuditLogSkeletonCell widthClassName="w-24" /></td>
                                        <td className="px-6 py-4"><AuditLogSkeletonCell widthClassName="w-16" /></td>
                                        <td className="px-6 py-4"><AuditLogSkeletonCell widthClassName="w-16" /></td>
                                        <td className="px-6 py-4"><AuditLogSkeletonCell widthClassName="w-64" /></td>
                                    </tr>
                                ))
                            ) : visibleEvents.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center">
                                        <div className="mx-auto max-w-lg space-y-3">
                                            <div className="meta-label">No Matching Entries</div>
                                            <p className="text-sm leading-6 text-slate-400">
                                                {query.trim()
                                                    ? 'No audit entries match the current filter window.'
                                                    : 'The audit ledger has not recorded any events in this page window yet.'}
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                visibleEvents.map((event) => {
                                    const timestamp = formatAuditTimestamp(event.created_at);
                                    const severityTone = getSeverityTone(event.severity);
                                    const actorLabel = normalizeAuditToken(event.actor_type, 'SYSTEM');
                                    const eventTypeLabel = normalizeAuditToken(event.event_type, 'UNCLASSIFIED');

                                    return (
                                        <motion.tr
                                            key={event.id}
                                            initial={{ opacity: 0, y: 5 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className="group align-top transition-colors hover:bg-white/[0.03]"
                                        >
                                            <td className="px-6 py-4">
                                                <div className="flex items-start gap-3">
                                                    <div className={clsx('mt-1 h-12 w-1 shrink-0 rounded-full', severityTone.railClassName)} />
                                                    <div className="min-w-0">
                                                        <time className="block font-mono text-[11px] font-black uppercase tracking-[0.18em] text-slate-300" dateTime={timestamp.isoLabel}>
                                                            {timestamp.dateLabel}
                                                        </time>
                                                        <span className="mt-1 block font-mono text-[10px] uppercase tracking-[0.22em] text-slate-600">
                                                            {timestamp.timeLabel}
                                                        </span>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="inline-flex max-w-full items-center rounded-[0.7rem] border border-white/10 bg-slate-950/45 px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-slate-300">
                                                    <span className="truncate">{eventTypeLabel}</span>
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={clsx('inline-flex items-center gap-2 rounded-[0.7rem] border px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em]', severityTone.badgeClassName)}>
                                                    {severityTone.icon}
                                                    {event.severity || 'INFO'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="inline-flex max-w-full rounded-[0.7rem] border border-white/8 bg-white/[0.03] px-3 py-2 text-[10px] font-black uppercase tracking-[0.18em] text-slate-500">
                                                    <span className="truncate">{actorLabel}</span>
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="space-y-2">
                                                    <p className="break-words text-sm leading-6 text-slate-200">
                                                        {event.message || 'No message recorded for this audit event.'}
                                                    </p>
                                                    <div className="flex flex-wrap items-center gap-2 text-[9px] font-mono uppercase tracking-[0.2em] text-slate-600">
                                                        <span>ID:{event.id}</span>
                                                        <span className="h-1 w-1 rounded-full bg-slate-700" />
                                                        <span>{eventTypeLabel}</span>
                                                    </div>
                                                </div>
                                            </td>
                                        </motion.tr>
                                    );
                                })
                            )}
                        </AnimatePresence>
                    </tbody>
                </table>

                <div className="flex flex-col gap-4 border-t border-white/8 bg-slate-950/35 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
                    <p className="text-[10px] font-mono uppercase tracking-[0.26em] text-slate-500">
                        Showing {start} - {end} of {total} events
                    </p>
                    <div className="flex items-center gap-2">
                        <IndustrialButton
                            type="button"
                            variant="ghost"
                            size="sm"
                            aria-label="Go to previous audit log page"
                            onClick={() => setPage((current) => Math.max(0, current - 1))}
                            disabled={page === 0}
                        >
                            <ChevronLeft className="h-4 w-4" />
                            Prev
                        </IndustrialButton>
                        <IndustrialButton
                            type="button"
                            variant="ghost"
                            size="sm"
                            aria-label="Go to next audit log page"
                            onClick={() => setPage((current) => current + 1)}
                            disabled={(page + 1) * limit >= total}
                        >
                            Next
                            <ChevronRight className="h-4 w-4" />
                        </IndustrialButton>
                    </div>
                </div>
            </IndustrialCard>
        </div>
    );
}
