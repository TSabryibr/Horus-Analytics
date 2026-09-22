'use client';

import { useEffect, useState } from 'react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';
import { waitForSystemReady } from '../lib/systemReadiness';

export interface ManagedHoldingForm {
    id: number;
    ticker: string;
    shares: string;
    entry_price: string;
    total_cost: string;
    stop_loss: string;
    target_price: string;
    target_price_2?: string;
    currency: string;
    sector: string;
    notes: string;
}

export interface ManagementReportPosition {
    ticker: string;
    shares: number;
    entry_price: number;
    current_price: number;
    stop_loss: number;
    target_price: number;
    target_price_2: number;
    unrealized_pnl: number;
    unrealized_pnl_pct: number;
    action: string;
    action_reason: string;
    kelly_pct?: number;
    recommended_shares?: number;
    risk_reward_ratio?: number;
}

export interface ManagementReport {
    portfolio: { id: number; name: string; type: string; cash_egp: number; cash_usd: number };
    snapshot_at: string;
    summary: {
        open_positions: number;
        winners: number;
        losers: number;
        total_cost_basis: number;
        market_value: number;
        unrealized_pnl: number;
        unrealized_pnl_pct: number;
        action_items: number;
    };
    risk: {
        status: string;
        health_score: number;
        heat: number;
        recommendations: { type: string; severity: string; title: string; message: string }[];
    };
    positions: ManagementReportPosition[];
    action_items: ManagementReportPosition[];
}

interface UsePortfolioManagementArgs {
    activePortfolioId: number | null;
    refreshData: () => Promise<void> | void;
}

function toNumberOrUndefined(value: string) {
    const v = value.trim();
    if (!v) return undefined;
    const num = Number(v);
    return Number.isFinite(num) ? num : undefined;
}

export function usePortfolioManagement({ activePortfolioId, refreshData }: UsePortfolioManagementArgs) {
    const [managedHoldings, setManagedHoldings] = useState<ManagedHoldingForm[]>([]);
    const [managementLoading, setManagementLoading] = useState(false);
    const [managementMessage, setManagementMessage] = useState('');
    const [managementReport, setManagementReport] = useState<ManagementReport | null>(null);
    const [managementSendResult, setManagementSendResult] = useState<{
        status: string;
        chunks_total: number;
        chunks_sent: number;
        chunks_failed: number;
    } | null>(null);
    const [reportControls, setReportControls] = useState({
        include_positions: '15',
        chat_id: '',
        refresh_prices: true,
    });
    const [actionItemsPreviewLimit, setActionItemsPreviewLimit] = useState(15);

    useEffect(() => {
        let mounted = true;
        const loadPortfolioManagerDefaults = async () => {
            try {
                const res = await apiFetch('/api/v1/settings');
                const body = await readJsonSafe<any>(res);
                if (!res.ok || !mounted) return;
                const includePositions = Math.max(
                    1,
                    Math.min(
                        Number(body?.PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS ?? 15) || 15,
                        100
                    )
                );
                const refreshPrices = Boolean(body?.PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES ?? true);
                const previewLimit = Math.max(
                    1,
                    Math.min(
                        Number(body?.PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT ?? 15) || 15,
                        100
                    )
                );
                setReportControls((prev) => ({
                    ...prev,
                    include_positions: String(includePositions),
                    refresh_prices: refreshPrices,
                }));
                setActionItemsPreviewLimit(previewLimit);
            } catch (_e) {
                // keep local defaults when settings are unavailable
            }
        };
        void loadPortfolioManagerDefaults();
        return () => {
            mounted = false;
        };
    }, []);
    const ensureSystemReady = async () => {
        const ready = await waitForSystemReady();
        if (!ready) {
            setManagementMessage('System is still starting. Retry in a few seconds.');
            return false;
        }
        return true;
    };

    const fetchManagementReport = async (refreshPrices: boolean) => {
        if (!activePortfolioId) {
            setManagementMessage('No active user portfolio selected.');
            return;
        }
        if (!(await ensureSystemReady())) return;
        setManagementLoading(true);
        setManagementMessage('');
        try {
            const res = await apiFetch(
                `/api/v1/portfolio/management/report?portfolio_id=${activePortfolioId}&refresh_prices=${refreshPrices}`
            );
            const body = await readJsonSafe<any>(res);
            if (!res.ok) {
                setManagementMessage(body?.detail || body?.message || 'Failed to generate report.');
                return;
            }
            setManagementReport(body);
            setManagementMessage('Portfolio management report generated.');
        } catch (_e) {
            setManagementMessage('Network error while generating report.');
        } finally {
            setManagementLoading(false);
        }
    };

    const addManagedHoldingRow = () => {
        setManagedHoldings((prev) => [
            ...prev,
            {
                id: Date.now() + Math.floor(Math.random() * 1000),
                ticker: '',
                shares: '',
                entry_price: '',
                total_cost: '',
                stop_loss: '',
                target_price: '',
                target_price_2: '',
                currency: 'EGP',
                sector: '',
                notes: '',
            },
        ]);
    };

    const removeManagedHoldingRow = (id: number) => {
        setManagedHoldings((prev) => prev.filter((row) => row.id !== id));
    };

    const clearManagedHoldings = () => {
        setManagedHoldings([]);
    };

    const updateManagedHoldingRow = (id: number, field: keyof ManagedHoldingForm, value: string) => {
        setManagedHoldings((prev) => prev.map((row) => (row.id === id ? { ...row, [field]: value } : row)));
    };

    const handleManagementIntake = async () => {
        if (!activePortfolioId) {
            setManagementMessage('No active user portfolio selected.');
            return;
        }
        if (!(await ensureSystemReady())) return;
        const holdings = managedHoldings
            .filter((row) => row.ticker.trim())
            .map((row) => ({
                ticker: row.ticker.trim().toUpperCase(),
                shares: toNumberOrUndefined(row.shares),
                entry_price: toNumberOrUndefined(row.entry_price),
                total_cost: toNumberOrUndefined(row.total_cost),
                stop_loss: toNumberOrUndefined(row.stop_loss),
                target_price: toNumberOrUndefined(row.target_price),
                target_price_2: toNumberOrUndefined(row.target_price_2 || ''),
                currency: (row.currency || 'EGP').trim().toUpperCase(),
                sector: row.sector.trim() || undefined,
                notes: row.notes.trim() || undefined,
            }));

        if (holdings.length === 0) {
            setManagementMessage('Add at least one holding ticker before intake.');
            return;
        }

        setManagementLoading(true);
        setManagementMessage('');
        try {
            const res = await apiFetch('/api/v1/portfolio/management/intake', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    portfolio_id: activePortfolioId,
                    holdings,
                    refresh_prices: reportControls.refresh_prices,
                }),
            });
            const body = await readJsonSafe<any>(res);
            if (!res.ok) {
                if (res.status === 403) {
                    setManagementMessage(`Holdings intake blocked by WFA gate: ${pickApiMessage(body, 'One or more tickers are blocked for new entries.')}`);
                } else {
                    setManagementMessage(pickApiMessage(body, 'Holdings intake failed.'));
                }
                return;
            }
            const created = typeof body.created === 'number' ? body.created : 0;
            const updated = typeof body.updated === 'number' ? body.updated : 0;
            const intakeStatus = typeof body.status === 'string' ? body.status.toLowerCase() : '';
            const issues = Array.isArray(body.errors)
                ? body.errors.filter((item: any): item is string => typeof item === 'string' && item.trim().length > 0)
                : [];

            if (intakeStatus === 'partial' || issues.length > 0) {
                const preview = issues.slice(0, 3).join(' | ');
                const remainder = issues.length > 3 ? ` | +${issues.length - 3} more` : '';
                setManagementMessage(
                    `Partial intake. Created ${created}, Updated ${updated}, Issues ${issues.length}.` +
                    `${preview ? ` ${preview}${remainder}` : ''}`
                );
            } else {
                setManagementMessage(`Intake complete. Created ${created}, Updated ${updated}, Issues 0.`);
            }
            await refreshData();
            await fetchManagementReport(false);
        } catch (_e) {
            setManagementMessage('Network error during holdings intake.');
        } finally {
            setManagementLoading(false);
        }
    };

    const handleSendManagementReport = async () => {
        if (!activePortfolioId) {
            setManagementMessage('No active user portfolio selected.');
            return;
        }
        if (!(await ensureSystemReady())) return;
        setManagementLoading(true);
        setManagementMessage('');
        setManagementSendResult(null);
        try {
            const includePositions = Number(reportControls.include_positions) || 15;
            const res = await apiFetch('/api/v1/portfolio/management/report/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    portfolio_id: activePortfolioId,
                    include_positions: includePositions,
                    chat_id: reportControls.chat_id.trim() || null,
                    refresh_prices: reportControls.refresh_prices,
                }),
            });
            const body = await readJsonSafe<any>(res);
            if (!res.ok) {
                setManagementMessage(body?.detail || body?.message || 'Report send failed.');
                return;
            }
            setManagementSendResult({
                status: body.status,
                chunks_total: body.chunks_total,
                chunks_sent: body.chunks_sent,
                chunks_failed: body.chunks_failed,
            });
            setManagementMessage(`Report send status: ${body.status}. Sent ${body.chunks_sent}/${body.chunks_total} chunks.`);
            if (body.summary) {
                await fetchManagementReport(false);
            }
        } catch (_e) {
            setManagementMessage('Network error while sending report.');
        } finally {
            setManagementLoading(false);
        }
    };

    const handleDownloadTemplate = (format: 'xlsx' | 'csv' = 'xlsx') => {
        window.open(`/api/v1/portfolio/template?format=${format}`, '_blank');
    };

    const handleUploadIntakeFile = async (
        file: File,
        options?: {
            mode?: 'create_new' | 'sandbox' | 'overwrite';
            portfolioName?: string;
            cashEgp?: number;
            cashUsd?: number;
            onCreated?: (newId: number) => void;
        }
    ) => {
        const mode = options?.mode || 'create_new';
        if (mode === 'overwrite' && !activePortfolioId) {
            setManagementMessage('No active user portfolio selected for overwrite.');
            return;
        }
        if (!(await ensureSystemReady())) return;
        setManagementLoading(true);
        setManagementMessage('');
        try {
            const formData = new FormData();
            formData.append('file', file);
            const params = new URLSearchParams({
                mode,
                refresh_prices: String(reportControls.refresh_prices),
            });
            if (options?.portfolioName?.trim()) {
                params.set('portfolio_name', options.portfolioName.trim());
            }
            if (mode === 'overwrite' && activePortfolioId) {
                params.set('portfolio_id', String(activePortfolioId));
            }
            if (options?.cashEgp !== undefined && options.cashEgp > 0) {
                params.set('starting_cash_egp', String(options.cashEgp));
            }
            if (options?.cashUsd !== undefined && options.cashUsd > 0) {
                params.set('starting_cash_usd', String(options.cashUsd));
            }

            const res = await apiFetch(`/api/v1/portfolio/subscriber/import?${params.toString()}`, {
                method: 'POST',
                body: formData,
            });
            const body = await readJsonSafe<any>(res);
            if (!res.ok) {
                setManagementMessage(body?.detail || body?.message || 'Subscriber import failed.');
                return;
            }

            if (mode === 'sandbox') {
                if (body.report) {
                    setManagementReport(body.report);
                }
                setManagementMessage(
                    `Sandbox audit completed for "${body.portfolio_name || file.name}". 0 database changes made. Review metrics and action items below.`
                );
            } else if (mode === 'create_new') {
                if (body.report) {
                    setManagementReport(body.report);
                }
                const created = body.created ?? 0;
                const errCount = Array.isArray(body.errors) ? body.errors.length : 0;
                setManagementMessage(
                    `Subscriber portfolio "${body.portfolio_name}" created successfully with ${created} position(s)!${
                        errCount > 0 ? ` (${errCount} issue(s) skipped)` : ''
                    }`
                );
                await refreshData();
                if (body.portfolio_id && options?.onCreated) {
                    options.onCreated(body.portfolio_id);
                }
            } else {
                if (body.report) {
                    setManagementReport(body.report);
                }
                const created = body.created ?? 0;
                const updated = body.updated ?? 0;
                setManagementMessage(`Portfolio updated successfully! Created: ${created}, Updated: ${updated}.`);
                await refreshData();
            }
        } catch (_e) {
            setManagementMessage('Network error while uploading subscriber file.');
        } finally {
            setManagementLoading(false);
        }
    };

    return {
        managedHoldings,
        managementLoading,
        managementMessage,
        managementReport,
        managementSendResult,
        reportControls,
        actionItemsPreviewLimit,
        setReportControls,
        setManagementMessage,
        fetchManagementReport,
        addManagedHoldingRow,
        removeManagedHoldingRow,
        clearManagedHoldings,
        updateManagedHoldingRow,
        handleManagementIntake,
        handleUploadIntakeFile,
        handleDownloadTemplate,
        handleSendManagementReport,
    };
}
