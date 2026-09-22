'use client';

import { useState } from 'react';

import { apiFetch } from '@/lib/api';

type UiMessage = {
    type: 'error' | 'success';
    text: string;
} | null;

type UseOptimizationAuditOptions = {
    showMessage: (message: UiMessage) => void;
};

export function useOptimizationAudit({ showMessage }: UseOptimizationAuditOptions) {
    const [isAuditOpen, setIsAuditOpen] = useState(false);
    const [auditLoading, setAuditLoading] = useState(false);
    const [auditResult, setAuditResult] = useState<any>(null);
    const [committingAudit, setCommittingAudit] = useState(false);

    const runAiAudit = async () => {
        setAuditLoading(true);
        try {
            const res = await apiFetch('/api/v1/ai/audit', { method: 'POST' });
            const data = await res.json();
            if (!res.ok) {
                showMessage({ type: 'error', text: data.detail || 'AI Audit failed.' });
                return;
            }
            setAuditResult(data);
            setIsAuditOpen(true);
        } catch (error) {
            showMessage({ type: 'error', text: 'Network error while running AI Audit.' });
        } finally {
            setAuditLoading(false);
        }
    };

    const commitAuditResult = async (result: any) => {
        setCommittingAudit(true);
        try {
            const res = await apiFetch('/api/v1/strategy/propose-from-lab', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ audit_result: result }),
            });
            const data = await res.json();
            if (!res.ok) {
                showMessage({ type: 'error', text: data.detail || 'Failed to commit proposal.' });
                return;
            }
            showMessage({ type: 'success', text: 'Proposal committed to Strategy Core!' });
            setIsAuditOpen(false);
        } catch (error) {
            showMessage({ type: 'error', text: 'Network error while committing proposal.' });
        } finally {
            setCommittingAudit(false);
        }
    };

    return {
        isAuditOpen,
        setIsAuditOpen,
        auditLoading,
        auditResult,
        setAuditResult,
        committingAudit,
        runAiAudit,
        commitAuditResult,
    };
}
