import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { AuditLog, Strategy, LifecycleSummary, FollowUpSummary } from '@/types/domain';
import { getBaseUrl, isIgnorableNetworkError } from '@/lib/api';

import { buildAuditCsvRows, buildComparisonData } from '../lib/auditTransforms';

export interface AuditResponse {
    status: string;
    strategies: Strategy[];
    logs: AuditLog[];
}

export interface AuditLifecycleRecord {
    id: number;
    ticker: string;
    state: string;
    lane: string;
    source_module?: string | null;
    published_at?: string | null;
    expires_at?: string | null;
    close_reason?: string | null;
}

export interface AuditFollowUpRecord {
    id: number;
    ticker: string;
    trigger_state: string;
    queue_state: string;
    message_type: string;
    lane: string;
    source_module?: string | null;
    service_tier?: string;
    destination_type?: string;
    destination_name?: string | null;
    destination_chat_id?: string | null;
    retry_count?: number;
    created_at?: string | null;
    sent_at?: string | null;
    suppression_reason?: string | null;
    last_error?: string | null;
}

export function useAuditRuntime() {
    const [audit, setAudit] = useState<AuditResponse | null>(null);
    const [lifecycleRows, setLifecycleRows] = useState<AuditLifecycleRecord[]>([]);
    const [lifecycleSummary, setLifecycleSummary] = useState<LifecycleSummary | null>(null);
    const [followUpRows, setFollowUpRows] = useState<AuditFollowUpRecord[]>([]);
    const [followUpSummary, setFollowUpSummary] = useState<FollowUpSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('ALL');
    const [days, setDays] = useState<number | 'ALL'>('ALL');
    const [expandedRow, setExpandedRow] = useState<number | null>(null);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    const apiBase = getBaseUrl();
    const requestIdRef = useRef(0);
    const daysRef = useRef(days);
    daysRef.current = days;
    const abortRef = useRef<AbortController | null>(null);

    const fetchData = useCallback(async () => {
        abortRef.current?.abort();
        const currentRequestId = ++requestIdRef.current;
        const controller = new AbortController();
        abortRef.current = controller;
        setLoading(true);
        try {
            const currentDays = daysRef.current;
            const url = currentDays === 'ALL' ? `${apiBase}/api/v1/audit` : `${apiBase}/api/v1/audit?days=${currentDays}`;
            const [auditRes, lifecycleRes, followUpRes] = await Promise.all([
                fetch(url, { signal: controller.signal }),
                fetch(`${apiBase}/api/v1/signals/lifecycle?limit=18`, { signal: controller.signal }),
                fetch(`${apiBase}/api/v1/signals/followups?limit=18`, { signal: controller.signal }),
            ]);

            if (currentRequestId !== requestIdRef.current) return;

            const json = await auditRes.json();
            const lifecycleJson = await lifecycleRes.json();
            const followUpJson = await followUpRes.json();
            if (json.status === 'success') setAudit(json);
            setLifecycleRows(Array.isArray(lifecycleJson?.lifecycles) ? lifecycleJson.lifecycles : []);
            setLifecycleSummary(lifecycleJson?.summary ?? null);
            setFollowUpRows(Array.isArray(followUpJson?.followups) ? followUpJson.followups : []);
            setFollowUpSummary(followUpJson?.summary ?? null);
            setLastUpdated(new Date());
        } catch (e) {
            if (currentRequestId !== requestIdRef.current) return;
            if (!isIgnorableNetworkError(e)) {
                console.error(e);
            }
        } finally {
            if (currentRequestId === requestIdRef.current) {
                setLoading(false);
            }
        }
    }, [apiBase]);

    const overrideLifecycle = useCallback(async (lifecycleId: number, payload: Record<string, unknown>) => {
        try {
            const response = await fetch(`${apiBase}/api/v1/signals/lifecycle/${lifecycleId}/override`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!response.ok) {
                return false;
            }
            await fetchData();
            return true;
        } catch (e) {
            if (!isIgnorableNetworkError(e)) {
                console.error(e);
            }
            return false;
        }
    }, [apiBase, fetchData]);

    const actOnFollowUp = useCallback(async (
        followUpId: number,
        action: 'SEND_NOW' | 'RETRY' | 'SUPPRESS' | 'RESEND',
        reason?: string,
    ) => {
        try {
            const response = await fetch(`${apiBase}/api/v1/signals/followups/${followUpId}/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action, reason }),
            });
            if (!response.ok) {
                return false;
            }
            await fetchData();
            return true;
        } catch (e) {
            if (!isIgnorableNetworkError(e)) {
                console.error(e);
            }
            return false;
        }
    }, [apiBase, fetchData]);

    useEffect(() => {
        fetchData();
    }, [fetchData, days]);

    const handleExport = useCallback(() => {
        if (!audit?.logs) return;
        const csvContent = buildAuditCsvRows(audit.logs).map((entry) => entry.join(',')).join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `horus_audit_report_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }, [audit]);

    const comparisonData = useMemo(() => buildComparisonData(audit?.strategies || []), [audit?.strategies]);
    const colors = useMemo(() => ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'], []);

    return {
        audit,
        setAudit,
        lifecycleRows,
        lifecycleSummary,
        followUpRows,
        followUpSummary,
        loading,
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
    };
}
