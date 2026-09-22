'use client';

import { useEffect, useMemo, useState } from 'react';
import clsx from 'clsx';
import {
    AlertTriangle,
    Archive,
    FileText,
    Link2,
    ListChecks,
    Pencil,
    Play,
    Plus,
    RefreshCw,
    Save,
    Send,
    ShieldCheck,
    UserRoundCheck,
    Users,
    X,
} from 'lucide-react';

import { apiFetch, pickApiMessage, readJsonSafe } from '@/lib/api';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';
import { IndustrialCard } from '@/app/components/custom/IndustrialCard';

type SubscriptionTier = 'SIGNALS_ONLY' | 'SIGNALS_PLUS_PORTFOLIO_RECS' | 'MANAGED_ADVISORY';
type ReportLanguage = 'EN' | 'AR';

type LinkedPortfolio = {
    id: number;
    name: string;
    type?: string;
    cash_egp?: number;
    cash_usd?: number;
};

type Delivery = {
    id?: number;
    client_id?: number;
    portfolio_id?: number | null;
    delivery_type?: string;
    status?: string;
    chat_id?: string | null;
    provider_message_id?: string | null;
    message_preview?: string | null;
    created_at?: string | null;
    sent_at?: string | null;
    last_error?: string | null;
    diagnosis?: {
        action_code?: string;
        severity?: string;
        operator_action?: string;
        technical_reason?: string;
    } | null;
};

type Subscriber = {
    id: number;
    name: string;
    is_active?: boolean;
    subscription_tier: SubscriptionTier | string;
    subscription_state: string;
    telegram_chat_id?: string | null;
    report_language?: ReportLanguage | string;
    risk_profile?: string;
    default_currency?: string;
    paid_until?: string | null;
    notes?: string | null;
    warnings?: string[];
    linked_portfolios?: LinkedPortfolio[];
    last_delivery?: Delivery | null;
};

type SubscribersPayload = {
    summary?: {
        total?: number;
        active?: number;
        renewal_due?: number;
        expired?: number;
        missing_chat?: number;
        advisory_enabled?: number;
        managed?: number;
    };
    subscribers?: Subscriber[];
};

type AdvisoryAction = {
    ticker: string;
    action: string;
    reason?: string;
    recommended_shares?: number | null;
    signal_match?: boolean;
};

type AdvisoryReport = {
    summary?: {
        action_items?: number;
        open_positions?: number;
        latest_recommendations?: number;
        risk_status?: string;
    };
    actions?: AdvisoryAction[];
};

type ReportState = {
    subscriberName: string;
    report: AdvisoryReport;
    telegramPreview?: string;
};

type ActivationAction = 'EDIT' | 'TEST_CHAT' | 'INSPECT_LEDGER' | 'SEND_REPORT' | 'READY';

type ActivationState = {
    status: 'READY' | 'ACTION' | 'BLOCKED';
    action: ActivationAction;
    actionLabel: string;
    reason: string;
    steps: Array<{
        label: string;
        state: 'READY' | 'PENDING' | 'BLOCKED';
    }>;
};

type SubscriberFormState = {
    name: string;
    subscription_tier: SubscriptionTier;
    telegram_chat_id: string;
    report_language: ReportLanguage;
    paid_until: string;
    risk_profile: 'CONSERVATIVE' | 'BALANCED' | 'AGGRESSIVE';
    default_currency: string;
    notes: string;
    is_active: boolean;
    portfolio_id: string;
    create_portfolio: boolean;
};

const EMPTY_FORM: SubscriberFormState = {
    name: '',
    subscription_tier: 'SIGNALS_ONLY',
    telegram_chat_id: '',
    report_language: 'EN',
    paid_until: '',
    risk_profile: 'BALANCED',
    default_currency: 'EGP',
    notes: '',
    is_active: true,
    portfolio_id: '',
    create_portfolio: false,
};

const TIER_LABELS: Record<string, string> = {
    SIGNALS_ONLY: 'Type 1 Signals',
    SIGNALS_PLUS_PORTFOLIO_RECS: 'Type 2 Portfolio Recs',
    MANAGED_ADVISORY: 'Type 3 Managed Advisory',
};

const REPORT_LANGUAGE_LABELS: Record<string, string> = {
    EN: 'English',
    AR: 'Arabic',
};

const STATE_CLASSES: Record<string, string> = {
    ACTIVE: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-100',
    RENEWAL_DUE: 'border-amber-300/30 bg-amber-300/10 text-amber-100',
    EXPIRED: 'border-rose-400/35 bg-rose-500/10 text-rose-100',
    INACTIVE: 'border-slate-400/25 bg-slate-500/10 text-slate-300',
};

function normalizeWarnings(subscriber: Subscriber) {
    const warnings = new Set(subscriber.warnings || []);
    if (subscriber.subscription_state === 'EXPIRED') warnings.add('SUBSCRIPTION_EXPIRED');
    if (!subscriber.telegram_chat_id) warnings.add('MISSING_CHAT');
    if (
        subscriber.subscription_tier !== 'SIGNALS_ONLY'
        && (!subscriber.linked_portfolios || subscriber.linked_portfolios.length === 0)
    ) {
        warnings.add('NO_LINKED_PORTFOLIO');
    }
    return Array.from(warnings);
}

function WarningTag({ warning }: { warning: string }) {
    const label = warning === 'SUBSCRIPTION_EXPIRED'
        ? '[EXPIRED]'
        : warning === 'MISSING_CHAT'
            ? '[MISSING CHAT]'
            : warning === 'NO_LINKED_PORTFOLIO'
                ? '[NO PORTFOLIO]'
                : warning === 'RENEWAL_DUE'
                    ? '[RENEWAL DUE]'
                    : `[${warning.replaceAll('_', ' ')}]`;

    return (
        <span className="inline-flex h-6 items-center border border-amber-300/20 bg-amber-300/8 px-2 text-[10px] font-black uppercase text-amber-100">
            {label}
        </span>
    );
}

function StatCell({ label, value, tone = 'neutral' }: { label: string; value: number | string; tone?: 'neutral' | 'warn' | 'ok' }) {
    return (
        <div className={clsx(
            'min-h-[74px] border px-4 py-3',
            tone === 'ok' && 'border-emerald-400/20 bg-emerald-400/8',
            tone === 'warn' && 'border-amber-300/20 bg-amber-300/8',
            tone === 'neutral' && 'border-white/10 bg-white/[0.035]',
        )}>
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-500">{label}</div>
            <div className="mt-2 text-2xl font-black text-slate-100">{value}</div>
        </div>
    );
}

function pickPortfolio(subscriber: Subscriber) {
    return subscriber.linked_portfolios?.[0] || null;
}

function deliveryFailureMessage(payload: { delivery?: Delivery } | unknown, fallback: string) {
    const delivery = (payload as { delivery?: Delivery })?.delivery;
    const reason = delivery?.last_error || fallback;
    const action = delivery?.diagnosis?.operator_action;
    return action ? `${reason}. ${action}` : reason;
}

function getActivationState(subscriber: Subscriber): ActivationState {
    const advisoryEnabled = subscriber.subscription_tier !== 'SIGNALS_ONLY';
    const portfolio = pickPortfolio(subscriber);
    const lastDeliveryStatus = subscriber.last_delivery?.status || '';
    const steps: ActivationState['steps'] = [
        {
            label: 'Record',
            state: subscriber.is_active === false || subscriber.subscription_state === 'INACTIVE' ? 'BLOCKED' : 'READY',
        },
        {
            label: 'Renewal',
            state: subscriber.subscription_state === 'EXPIRED' ? 'BLOCKED' : 'READY',
        },
        {
            label: 'Telegram',
            state: subscriber.telegram_chat_id ? 'READY' : 'BLOCKED',
        },
        {
            label: advisoryEnabled ? 'Portfolio' : 'Channel',
            state: !advisoryEnabled || portfolio ? 'READY' : 'BLOCKED',
        },
        {
            label: 'Delivery',
            state: lastDeliveryStatus === 'SENT' ? 'READY' : 'PENDING',
        },
    ];

    if (subscriber.is_active === false || subscriber.subscription_state === 'INACTIVE') {
        return {
            status: 'BLOCKED',
            action: 'EDIT',
            actionLabel: 'Activate record',
            reason: 'Subscriber is inactive.',
            steps,
        };
    }
    if (subscriber.subscription_state === 'EXPIRED') {
        return {
            status: 'BLOCKED',
            action: 'EDIT',
            actionLabel: 'Renew subscription',
            reason: 'Paid-until date has passed.',
            steps,
        };
    }
    if (!subscriber.telegram_chat_id) {
        return {
            status: 'BLOCKED',
            action: 'EDIT',
            actionLabel: 'Add chat ID',
            reason: 'Private Telegram route is missing.',
            steps,
        };
    }
    if (advisoryEnabled && !portfolio) {
        return {
            status: 'BLOCKED',
            action: 'EDIT',
            actionLabel: 'Link portfolio',
            reason: 'Portfolio advisory needs a USER portfolio.',
            steps,
        };
    }
    if (lastDeliveryStatus === 'FAILED') {
        return {
            status: 'ACTION',
            action: 'INSPECT_LEDGER',
            actionLabel: 'Inspect failure',
            reason: 'Last Telegram attempt failed.',
            steps,
        };
    }
    if (!subscriber.last_delivery) {
        return {
            status: 'ACTION',
            action: 'TEST_CHAT',
            actionLabel: 'Test chat',
            reason: 'Telegram route has not been verified.',
            steps,
        };
    }
    if (advisoryEnabled) {
        return {
            status: 'ACTION',
            action: 'SEND_REPORT',
            actionLabel: 'Send advisory',
            reason: 'Subscriber is ready for private advisory delivery.',
            steps,
        };
    }
    return {
        status: 'READY',
        action: 'READY',
        actionLabel: 'Ready',
        reason: 'Signals subscription is active.',
        steps,
    };
}

function ActivationStepTag({ step }: { step: ActivationState['steps'][number] }) {
    return (
        <span className={clsx(
            'inline-flex h-6 items-center border px-2 text-[10px] font-black uppercase tracking-[0.12em]',
            step.state === 'READY' && 'border-emerald-400/20 bg-emerald-400/8 text-emerald-100',
            step.state === 'PENDING' && 'border-amber-300/20 bg-amber-300/8 text-amber-100',
            step.state === 'BLOCKED' && 'border-rose-400/30 bg-rose-500/10 text-rose-100',
        )}>
            {step.label}
        </span>
    );
}

export default function SubscribersPage() {
    const [subscribers, setSubscribers] = useState<Subscriber[]>([]);
    const [portfolios, setPortfolios] = useState<LinkedPortfolio[]>([]);
    const [summary, setSummary] = useState<SubscribersPayload['summary']>({});
    const [loading, setLoading] = useState(true);
    const [busyId, setBusyId] = useState<number | null>(null);
    const [savingSubscriber, setSavingSubscriber] = useState(false);
    const [message, setMessage] = useState('');
    const [reportState, setReportState] = useState<ReportState | null>(null);
    const [deliverySubscriber, setDeliverySubscriber] = useState<Subscriber | null>(null);
    const [deliveries, setDeliveries] = useState<Delivery[]>([]);
    const [deliveryLoading, setDeliveryLoading] = useState(false);
    const [deliveryMessages, setDeliveryMessages] = useState<string[]>([]);
    const [provisioningOpen, setProvisioningOpen] = useState(false);
    const [editingSubscriber, setEditingSubscriber] = useState<Subscriber | null>(null);
    const [form, setForm] = useState<SubscriberFormState>(EMPTY_FORM);

    const refresh = async () => {
        setLoading(true);
        setMessage('');
        try {
            const [subscriberResponse, portfolioResponse] = await Promise.all([
                apiFetch('/api/v1/subscribers'),
                apiFetch('/api/v1/portfolios'),
            ]);
            const payload = await readJsonSafe<SubscribersPayload>(subscriberResponse);
            const portfolioPayload = await readJsonSafe<LinkedPortfolio[]>(portfolioResponse);
            if (!subscriberResponse.ok) {
                setMessage(pickApiMessage(payload, 'Subscriber ledger failed to load.'));
                return;
            }
            setSubscribers(payload.subscribers || []);
            setSummary(payload.summary || {});
            if (portfolioResponse.ok && Array.isArray(portfolioPayload)) {
                setPortfolios(portfolioPayload.filter((portfolio) => portfolio.type !== 'SYSTEM'));
            }
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Subscriber ledger failed to load.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refresh();
    }, []);

    const orderedSubscribers = useMemo(() => {
        const stateRank: Record<string, number> = { EXPIRED: 0, RENEWAL_DUE: 1, ACTIVE: 2, INACTIVE: 3 };
        return [...subscribers].sort((a, b) => {
            const stateDelta = (stateRank[a.subscription_state] ?? 9) - (stateRank[b.subscription_state] ?? 9);
            if (stateDelta !== 0) return stateDelta;
            return a.name.localeCompare(b.name);
        });
    }, [subscribers]);

    const openCreateForm = () => {
        setForm(EMPTY_FORM);
        setEditingSubscriber(null);
        setProvisioningOpen(true);
        setMessage('');
    };

    const openEditForm = (subscriber: Subscriber) => {
        setForm({
            name: subscriber.name || '',
            subscription_tier: subscriber.subscription_tier as SubscriptionTier,
            telegram_chat_id: subscriber.telegram_chat_id || '',
            report_language: (subscriber.report_language as ReportLanguage) || 'EN',
            paid_until: subscriber.paid_until || '',
            risk_profile: (subscriber.risk_profile as SubscriberFormState['risk_profile']) || 'BALANCED',
            default_currency: subscriber.default_currency || 'EGP',
            notes: subscriber.notes || '',
            is_active: subscriber.is_active !== false,
            portfolio_id: subscriber.linked_portfolios?.[0]?.id ? String(subscriber.linked_portfolios[0].id) : '',
            create_portfolio: false,
        });
        setEditingSubscriber(subscriber);
        setProvisioningOpen(true);
        setMessage('');
    };

    const updateForm = (field: keyof SubscriberFormState, value: string | boolean) => {
        setForm((current) => {
            if (field === 'subscription_tier') {
                const tier = value as SubscriptionTier;
                return {
                    ...current,
                    subscription_tier: tier,
                    create_portfolio: tier === 'SIGNALS_ONLY'
                        ? false
                        : (!editingSubscriber && !current.portfolio_id ? true : current.create_portfolio),
                };
            }
            if (field === 'portfolio_id' && value) {
                return { ...current, portfolio_id: String(value), create_portfolio: false };
            }
            if (field === 'create_portfolio' && value === true) {
                return { ...current, create_portfolio: true, portfolio_id: '' };
            }
            return { ...current, [field]: value };
        });
    };

    const submitSubscriberForm = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!form.name.trim()) {
            setMessage('Subscriber name is required.');
            return;
        }
        setSavingSubscriber(true);
        setMessage('');
        try {
            const editingId = editingSubscriber?.id;
            const shouldCreatePortfolio = form.create_portfolio && form.subscription_tier !== 'SIGNALS_ONLY';
            const requestedPortfolioId = form.portfolio_id ? Number(form.portfolio_id) : null;
            const response = await apiFetch(editingId ? `/api/v1/subscribers/${editingId}` : '/api/v1/subscribers', {
                method: editingId ? 'PATCH' : 'POST',
                body: JSON.stringify({
                    name: form.name.trim(),
                    subscription_tier: form.subscription_tier,
                    telegram_chat_id: form.telegram_chat_id.trim(),
                    report_language: form.report_language,
                    paid_until: form.paid_until,
                    risk_profile: form.risk_profile,
                    default_currency: form.default_currency.trim().toUpperCase() || 'EGP',
                    notes: form.notes,
                    is_active: form.is_active,
                    ...(editingId ? {} : {
                        portfolio_id: requestedPortfolioId,
                        create_portfolio: shouldCreatePortfolio,
                    }),
                }),
            });
            const payload = await readJsonSafe<{ subscriber?: Subscriber }>(response);
            if (!response.ok || !payload.subscriber) {
                setMessage(pickApiMessage(payload, 'Subscriber save failed.'));
                return;
            }
            const serverLinkedPortfolioId = payload.subscriber.linked_portfolios?.[0]?.id || null;
            let linkedPortfolioId = serverLinkedPortfolioId || requestedPortfolioId;
            if (shouldCreatePortfolio && !serverLinkedPortfolioId) {
                const portfolioName = form.name.trim();
                const portfolioResponse = await apiFetch('/api/v1/portfolios', {
                    method: 'POST',
                    body: JSON.stringify({ name: portfolioName, auto_manage: false }),
                });
                const portfolioPayload = await readJsonSafe<{ id?: number }>(portfolioResponse);
                if (!portfolioResponse.ok || !portfolioPayload.id) {
                    setMessage(pickApiMessage(portfolioPayload, 'Subscriber saved, but portfolio creation failed.'));
                    return;
                }
                linkedPortfolioId = portfolioPayload.id;
            }
            const existingPortfolioId = editingSubscriber?.linked_portfolios?.[0]?.id
                ? String(editingSubscriber.linked_portfolios[0].id)
                : '';
            if (linkedPortfolioId && String(linkedPortfolioId) !== existingPortfolioId && String(linkedPortfolioId) !== String(serverLinkedPortfolioId || '')) {
                const linkResponse = await apiFetch(`/api/v1/subscribers/${payload.subscriber.id}/portfolios`, {
                    method: 'POST',
                    body: JSON.stringify({ portfolio_id: linkedPortfolioId }),
                });
                const linkPayload = await readJsonSafe(linkResponse);
                if (!linkResponse.ok) {
                    setMessage(pickApiMessage(linkPayload, 'Subscriber saved, but portfolio link failed.'));
                    return;
                }
            }
            setProvisioningOpen(false);
            setEditingSubscriber(null);
            setForm(EMPTY_FORM);
            await refresh();
            setMessage(editingId ? `${payload.subscriber.name} updated.` : `${payload.subscriber.name} provisioned.`);
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Subscriber save failed.');
        } finally {
            setSavingSubscriber(false);
        }
    };

    const generateReport = async (subscriber: Subscriber) => {
        const portfolio = pickPortfolio(subscriber);
        if (!portfolio) {
            setMessage(`${subscriber.name} has no linked portfolio.`);
            return;
        }
        setBusyId(subscriber.id);
        setMessage('');
        try {
            const endpoint = `/api/v1/subscribers/${subscriber.id}/advisory-report?portfolio_id=${portfolio.id}`;
            const response = await apiFetch(endpoint);
            const payload = await readJsonSafe<{ report?: AdvisoryReport; telegram_preview?: string }>(response);
            if (!response.ok || !payload.report) {
                setMessage(pickApiMessage(payload, 'Advisory report failed.'));
                return;
            }
            setReportState({
                subscriberName: subscriber.name,
                report: payload.report,
                telegramPreview: payload.telegram_preview,
            });
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Advisory report failed.');
        } finally {
            setBusyId(null);
        }
    };

    const sendReport = async (subscriber: Subscriber) => {
        const portfolio = pickPortfolio(subscriber);
        if (!portfolio) {
            setMessage(`${subscriber.name} has no linked portfolio.`);
            return;
        }
        setBusyId(subscriber.id);
        setMessage('');
        try {
            const response = await apiFetch(`/api/v1/subscribers/${subscriber.id}/advisory-report/send`, {
                method: 'POST',
                body: JSON.stringify({ portfolio_id: portfolio.id }),
            });
            const payload = await readJsonSafe<{ delivery?: Delivery; report?: AdvisoryReport }>(response);
            const nextMessage = !response.ok
                ? pickApiMessage(payload, payload.delivery?.last_error || 'Report delivery failed.')
                : `Report sent to ${subscriber.name}.`;
            if (!response.ok) {
                setMessage(nextMessage);
            }
            if (payload.report) {
                setReportState({ subscriberName: subscriber.name, report: payload.report });
            }
            await refresh();
            setMessage(nextMessage);
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Report delivery failed.');
        } finally {
            setBusyId(null);
        }
    };

    const inspectDeliveries = async (subscriber: Subscriber) => {
        setDeliverySubscriber(subscriber);
        setDeliveryLoading(true);
        setDeliveryMessages([]);
        try {
            const response = await apiFetch(`/api/v1/subscribers/deliveries?client_id=${subscriber.id}&limit=20`);
            const payload = await readJsonSafe<{ deliveries?: Delivery[] }>(response);
            if (!response.ok) {
                setMessage(pickApiMessage(payload, 'Delivery history failed to load.'));
                return;
            }
            setDeliveries(payload.deliveries || []);
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Delivery history failed to load.');
        } finally {
            setDeliveryLoading(false);
        }
    };

    const retryDelivery = async (delivery: Delivery) => {
        if (!delivery.id) return;
        setDeliveryMessages((current) => current.filter((item) => !item.includes(`delivery ${delivery.id}`)));
        try {
            const response = await apiFetch(`/api/v1/subscribers/deliveries/${delivery.id}/retry`, { method: 'POST' });
            const payload = await readJsonSafe<{ delivery?: Delivery }>(response);
            if (!response.ok) {
                setDeliveryMessages((current) => [...current, pickApiMessage(payload, `Retry failed for delivery ${delivery.id}.`)]);
                return;
            }
            setDeliveryMessages((current) => [...current, `Retry sent for delivery ${delivery.id}.`]);
            if (payload.delivery) {
                setDeliveries((current) => [payload.delivery as Delivery, ...current]);
            }
            await refresh();
        } catch (error) {
            setDeliveryMessages((current) => [...current, error instanceof Error ? error.message : `Retry failed for delivery ${delivery.id}.`]);
        }
    };

    const sendChatTest = async (subscriber: Subscriber) => {
        setDeliverySubscriber(subscriber);
        setMessage('');
        try {
            const response = await apiFetch(`/api/v1/subscribers/${subscriber.id}/telegram-test/send`, { method: 'POST' });
            const payload = await readJsonSafe<{ delivery?: Delivery }>(response);
            if (!response.ok) {
                const nextMessage = deliveryFailureMessage(payload, `Chat test failed for ${subscriber.name}.`);
                setDeliveryMessages((current) => [...current, nextMessage]);
                if (payload.delivery) {
                    setDeliveries((current) => [payload.delivery as Delivery, ...current]);
                }
                await refresh();
                setDeliverySubscriber(subscriber);
                setMessage(nextMessage);
                return;
            }
            setDeliveryMessages((current) => [...current, `Chat test sent to ${subscriber.name}.`]);
            if (payload.delivery) {
                setDeliveries((current) => [payload.delivery as Delivery, ...current]);
            }
            await refresh();
            setDeliverySubscriber(subscriber);
        } catch (error) {
            setDeliveryMessages((current) => [...current, error instanceof Error ? error.message : `Chat test failed for ${subscriber.name}.`]);
        }
    };

    const archiveSubscriber = async (subscriber: Subscriber) => {
        if (subscriber.is_active === false || subscriber.subscription_state === 'INACTIVE') {
            setMessage(`${subscriber.name} is already archived.`);
            return;
        }
        setBusyId(subscriber.id);
        setMessage('');
        try {
            const response = await apiFetch(`/api/v1/subscribers/${subscriber.id}/archive`, { method: 'POST' });
            const payload = await readJsonSafe<{ subscriber?: Subscriber }>(response);
            if (!response.ok) {
                setMessage(pickApiMessage(payload, `Archive failed for ${subscriber.name}.`));
                return;
            }
            await refresh();
            setMessage(`${payload.subscriber?.name || subscriber.name} archived.`);
        } catch (error) {
            setMessage(error instanceof Error ? error.message : `Archive failed for ${subscriber.name}.`);
        } finally {
            setBusyId(null);
        }
    };

    const runActivationStep = (subscriber: Subscriber) => {
        const activation = getActivationState(subscriber);
        if (activation.action === 'EDIT') {
            openEditForm(subscriber);
            return;
        }
        if (activation.action === 'TEST_CHAT') {
            sendChatTest(subscriber);
            return;
        }
        if (activation.action === 'INSPECT_LEDGER') {
            inspectDeliveries(subscriber);
            return;
        }
        if (activation.action === 'SEND_REPORT') {
            sendReport(subscriber);
        }
    };

    return (
        <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 sm:px-6 lg:px-8">
            <div className="mx-auto flex max-w-[1520px] flex-col gap-5">
                <header className="flex flex-col gap-4 border-b border-white/10 pb-5 lg:flex-row lg:items-end lg:justify-between">
                    <div className="min-w-0">
                        <div className="flex items-center gap-3 text-cyan-200">
                            <Users className="h-5 w-5" />
                            <span className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-500">Commercial Console</span>
                        </div>
                        <h1 className="mt-3 text-3xl font-black tracking-normal text-white">Subscribers</h1>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        <IndustrialButton
                            type="button"
                            variant="primary"
                            onClick={openCreateForm}
                            aria-label="Add subscriber"
                        >
                            <Plus className="h-4 w-4" />
                            Add Subscriber
                        </IndustrialButton>
                        <IndustrialButton
                            type="button"
                            variant="secondary"
                            onClick={refresh}
                            disabled={loading}
                            aria-label="Refresh subscribers"
                        >
                            <RefreshCw className={clsx('h-4 w-4', loading && 'animate-spin')} />
                            Refresh
                        </IndustrialButton>
                    </div>
                </header>

                <section className="grid gap-3 md:grid-cols-5">
                    <StatCell label="Total" value={summary?.total ?? subscribers.length} />
                    <StatCell label="Active" value={summary?.active ?? 0} tone="ok" />
                    <StatCell label="Renewal Due" value={summary?.renewal_due ?? 0} tone="warn" />
                    <StatCell label="Expired" value={summary?.expired ?? 0} tone="warn" />
                    <StatCell label="Missing Chat" value={summary?.missing_chat ?? 0} tone="warn" />
                </section>

                {message && (
                    <div className="flex items-center gap-3 border border-amber-300/20 bg-amber-300/8 px-4 py-3 text-sm text-amber-100">
                        <AlertTriangle className="h-4 w-4 shrink-0" />
                        <span>{message}</span>
                    </div>
                )}

                <IndustrialCard
                    title="Client Activation"
                    subtitle="Next commercial move across records, Telegram, portfolio, and private delivery."
                    tone="secondary"
                    headerSlot={<ListChecks className="h-5 w-5 text-cyan-200" />}
                    contentClassName="p-0"
                >
                    {loading ? (
                        <div className="flex h-24 items-center justify-center text-cyan-200">
                            <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
                            <span className="text-xs font-black uppercase tracking-[0.18em]">Loading Activation</span>
                        </div>
                    ) : orderedSubscribers.length === 0 ? (
                        <div className="px-5 py-8 text-sm text-slate-500">No subscribers queued.</div>
                    ) : (
                        <div className="divide-y divide-white/10">
                            {orderedSubscribers.map((subscriber) => {
                                const activation = getActivationState(subscriber);
                                const blocked = activation.status === 'BLOCKED';
                                return (
                                    <article key={`activation-${subscriber.id}`} className="grid gap-4 px-4 py-4 xl:grid-cols-[minmax(0,260px)_1fr_minmax(180px,220px)_auto] xl:items-center">
                                        <div className="min-w-0">
                                            <div className="flex flex-wrap items-center gap-2">
                                                <span className={clsx(
                                                    'inline-flex h-6 items-center border px-2 text-[10px] font-black uppercase tracking-[0.14em]',
                                                    activation.status === 'READY' && 'border-emerald-400/25 bg-emerald-400/10 text-emerald-100',
                                                    activation.status === 'ACTION' && 'border-cyan-300/25 bg-cyan-300/8 text-cyan-100',
                                                    activation.status === 'BLOCKED' && 'border-rose-400/35 bg-rose-500/10 text-rose-100',
                                                )}>
                                                    {activation.status}
                                                </span>
                                                <h2 className="truncate text-sm font-black text-white">{subscriber.name}</h2>
                                            </div>
                                            <div className="mt-2 text-xs text-slate-500">{TIER_LABELS[subscriber.subscription_tier] || subscriber.subscription_tier}</div>
                                        </div>
                                        <div className="flex flex-wrap gap-2">
                                            {activation.steps.map((step) => (
                                                <ActivationStepTag key={`${subscriber.id}-${step.label}`} step={step} />
                                            ))}
                                        </div>
                                        <div className="min-w-0">
                                            <div className={clsx('text-xs font-black uppercase tracking-[0.16em]', blocked ? 'text-rose-100' : 'text-cyan-100')}>
                                                {activation.actionLabel}
                                            </div>
                                            <div className="mt-1 text-xs text-slate-500">{activation.reason}</div>
                                        </div>
                                        <IndustrialButton
                                            type="button"
                                            variant={blocked ? 'alert' : activation.action === 'READY' ? 'ghost' : 'primary'}
                                            size="sm"
                                            disabled={activation.action === 'READY' || busyId === subscriber.id}
                                            onClick={() => runActivationStep(subscriber)}
                                            aria-label={`Run ${subscriber.name} activation step`}
                                            title={activation.actionLabel}
                                        >
                                            <Play className="h-4 w-4" />
                                            Run
                                        </IndustrialButton>
                                    </article>
                                );
                            })}
                        </div>
                    )}
                </IndustrialCard>

                {provisioningOpen && (
                    <IndustrialCard
                        title="Subscriber Provisioning"
                        subtitle={editingSubscriber ? "Update tier, renewal state, Telegram route, and portfolio link." : "Create the commercial record, Telegram route, renewal date, and first portfolio link."}
                        tone="secondary"
                        headerSlot={(
                            <button
                                type="button"
                                className="inline-flex h-9 w-9 items-center justify-center border border-white/10 bg-white/[0.04] text-slate-300 hover:bg-white/[0.08]"
                                onClick={() => {
                                    setProvisioningOpen(false);
                                    setEditingSubscriber(null);
                                }}
                                aria-label="Close subscriber provisioning"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        )}
                    >
                        <form
                            className="grid gap-4 md:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-[minmax(220px,1.15fr)_minmax(220px,0.9fr)_minmax(250px,1fr)_minmax(170px,0.7fr)_minmax(170px,0.7fr)_minmax(240px,1fr)_minmax(220px,0.85fr)_auto]"
                            onSubmit={submitSubscriberForm}
                        >
                            <label className="grid min-w-0 gap-2 text-xs font-black uppercase tracking-[0.14em] text-slate-500">
                                Subscriber Name
                                <input
                                    className="h-11 w-full min-w-0 border border-white/10 bg-slate-950 px-3 text-sm font-bold normal-case tracking-normal text-white outline-none focus:border-cyan-300/40"
                                    value={form.name}
                                    onChange={(event) => updateForm('name', event.target.value)}
                                    placeholder="Client name"
                                />
                            </label>
                            <label className="grid min-w-0 gap-2 text-xs font-black uppercase tracking-[0.14em] text-slate-500">
                                Subscription Tier
                                <select
                                    className="h-11 w-full min-w-0 border border-white/10 bg-slate-950 px-3 text-sm font-bold normal-case tracking-normal text-white outline-none focus:border-cyan-300/40"
                                    value={form.subscription_tier}
                                    onChange={(event) => updateForm('subscription_tier', event.target.value as SubscriptionTier)}
                                >
                                    <option value="SIGNALS_ONLY">Type 1 Signals</option>
                                    <option value="SIGNALS_PLUS_PORTFOLIO_RECS">Type 2 Portfolio Recs</option>
                                    <option value="MANAGED_ADVISORY">Type 3 Managed Advisory</option>
                                </select>
                            </label>
                            <label className="grid min-w-0 gap-2 text-xs font-black uppercase tracking-[0.14em] text-slate-500">
                                Subscriber Private Chat ID
                                <input
                                    className="h-11 w-full min-w-0 border border-white/10 bg-slate-950 px-3 text-sm font-bold normal-case tracking-normal text-white outline-none focus:border-cyan-300/40"
                                    value={form.telegram_chat_id}
                                    onChange={(event) => updateForm('telegram_chat_id', event.target.value)}
                                    placeholder="1822794531 or -100..."
                                />
                            </label>
                            <label className="grid min-w-0 gap-2 text-xs font-black uppercase tracking-[0.14em] text-slate-500">
                                Report Language
                                <select
                                    className="h-11 w-full min-w-0 border border-white/10 bg-slate-950 px-3 text-sm font-bold normal-case tracking-normal text-white outline-none focus:border-cyan-300/40"
                                    value={form.report_language}
                                    onChange={(event) => updateForm('report_language', event.target.value as ReportLanguage)}
                                >
                                    <option value="EN">English</option>
                                    <option value="AR">Arabic</option>
                                </select>
                            </label>
                            <label className="grid min-w-0 gap-2 text-xs font-black uppercase tracking-[0.14em] text-slate-500">
                                Paid Until
                                <input
                                    type="date"
                                    className="h-11 w-full min-w-0 border border-white/10 bg-slate-950 px-3 text-sm font-bold normal-case tracking-normal text-white outline-none focus:border-cyan-300/40"
                                    value={form.paid_until}
                                    onChange={(event) => updateForm('paid_until', event.target.value)}
                                />
                            </label>
                            <label className="grid min-w-0 gap-2 text-xs font-black uppercase tracking-[0.14em] text-slate-500">
                                Linked Portfolio
                                <select
                                    className="h-11 w-full min-w-0 border border-white/10 bg-slate-950 px-3 text-sm font-bold normal-case tracking-normal text-white outline-none focus:border-cyan-300/40"
                                    value={form.portfolio_id}
                                    onChange={(event) => updateForm('portfolio_id', event.target.value)}
                                >
                                    <option value="">No portfolio</option>
                                    {portfolios.map((portfolio) => (
                                        <option key={portfolio.id} value={portfolio.id}>{portfolio.name}</option>
                                    ))}
                                </select>
                            </label>
                            <label className={clsx(
                                'grid min-h-[68px] min-w-0 gap-2 border px-3 py-2 text-xs font-black uppercase tracking-[0.14em] md:col-span-2 xl:col-span-2 2xl:col-span-1',
                                form.subscription_tier === 'SIGNALS_ONLY'
                                    ? 'border-white/5 bg-white/[0.02] text-slate-700'
                                    : 'border-cyan-300/20 bg-cyan-300/8 text-cyan-100',
                            )}>
                                Create User Portfolio
                                <span className="flex min-w-0 items-center gap-3 normal-case tracking-normal text-slate-300">
                                    <input
                                        type="checkbox"
                                        checked={form.create_portfolio}
                                        disabled={form.subscription_tier === 'SIGNALS_ONLY'}
                                        onChange={(event) => updateForm('create_portfolio', event.target.checked)}
                                        aria-label="Create user portfolio"
                                        className="h-5 w-5 accent-cyan-400"
                                    />
                                    <span className="min-w-0 text-xs leading-5">
                                        {form.subscription_tier === 'SIGNALS_ONLY'
                                            ? 'Available for Type 2 and Type 3'
                                            : `Auto-create: ${form.name.trim() || 'Client portfolio'}`}
                                    </span>
                                </span>
                            </label>
                            <IndustrialButton
                                type="submit"
                                variant="primary"
                                className="self-end justify-self-start 2xl:justify-self-end"
                                disabled={savingSubscriber}
                                aria-label="Save subscriber"
                            >
                                <Save className="h-4 w-4" />
                                Save
                            </IndustrialButton>
                        </form>
                    </IndustrialCard>
                )}

                <div className="grid gap-5 xl:grid-cols-[minmax(0,1.4fr)_minmax(380px,0.8fr)]">
                    <IndustrialCard
                        title="Subscriber Ledger"
                        subtitle="Tier, renewal state, Telegram route, portfolio link, and last delivery."
                        tone="rail"
                        contentClassName="p-0"
                    >
                        <div className="divide-y divide-white/10">
                            {loading && (
                                <div className="flex h-40 items-center justify-center text-cyan-200">
                                    <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
                                    <span className="text-xs font-black uppercase tracking-[0.18em]">Loading</span>
                                </div>
                            )}

                            {!loading && orderedSubscribers.length === 0 && (
                                <div className="px-5 py-10 text-sm text-slate-400">No subscribers registered.</div>
                            )}

                            {!loading && orderedSubscribers.map((subscriber) => {
                                const warnings = normalizeWarnings(subscriber);
                                const portfolio = pickPortfolio(subscriber);
                                const advisoryEnabled = subscriber.subscription_tier !== 'SIGNALS_ONLY';
                                const canSend = advisoryEnabled
                                    && Boolean(portfolio)
                                    && Boolean(subscriber.telegram_chat_id)
                                    && subscriber.subscription_state !== 'EXPIRED'
                                    && subscriber.subscription_state !== 'INACTIVE';

                                return (
                                    <article key={subscriber.id} className="grid gap-4 px-4 py-4 xl:grid-cols-[minmax(0,1fr)_minmax(240px,0.56fr)] xl:items-start">
                                        <div className="min-w-0 space-y-3">
                                            <div className="flex flex-wrap items-center gap-2">
                                                <h2 className="min-w-0 max-w-full truncate text-base font-black text-white">{subscriber.name}</h2>
                                                <span className={clsx('inline-flex h-6 items-center border px-2 text-[10px] font-black uppercase', STATE_CLASSES[subscriber.subscription_state] || STATE_CLASSES.INACTIVE)}>
                                                    {subscriber.subscription_state}
                                                </span>
                                                {warnings.map((warning) => <WarningTag key={warning} warning={warning} />)}
                                            </div>
                                            <div className="grid min-w-0 gap-2 text-xs text-slate-400 sm:grid-cols-3">
                                                <div className="min-w-0 border border-white/[0.06] bg-white/[0.025] px-3 py-2">
                                                    <div className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-600">Tier</div>
                                                    <div className="mt-1 min-w-0 leading-5 text-slate-200">{TIER_LABELS[subscriber.subscription_tier] || subscriber.subscription_tier}</div>
                                                </div>
                                                <div className="min-w-0 border border-white/[0.06] bg-white/[0.025] px-3 py-2">
                                                    <div className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-600">Telegram</div>
                                                    <div className="mt-1 min-w-0 break-all font-mono text-slate-200">{subscriber.telegram_chat_id || 'Missing'}</div>
                                                </div>
                                                <div className="min-w-0 border border-white/[0.06] bg-white/[0.025] px-3 py-2">
                                                    <div className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-600">Paid Until</div>
                                                    <div className="mt-1 min-w-0 text-slate-200">{subscriber.paid_until || 'Open'}</div>
                                                </div>
                                                <div className="min-w-0 border border-white/[0.06] bg-white/[0.025] px-3 py-2 sm:col-span-3">
                                                    <div className="text-[10px] font-black uppercase tracking-[0.16em] text-slate-600">Report Language</div>
                                                    <div className="mt-1 min-w-0 text-slate-200">{REPORT_LANGUAGE_LABELS[subscriber.report_language || 'EN'] || 'English'}</div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="grid min-w-0 gap-2 text-xs">
                                            <div className="flex min-w-0 items-center gap-2 text-slate-300">
                                                <Link2 className="h-4 w-4 shrink-0 text-cyan-300" />
                                                <span className="min-w-0 truncate">{portfolio ? portfolio.name : 'No linked portfolio'}</span>
                                            </div>
                                            <div className="flex min-w-0 items-center gap-2 text-slate-500">
                                                <ShieldCheck className="h-4 w-4 shrink-0" />
                                                <span className="min-w-0 truncate">Last delivery: {subscriber.last_delivery?.status || 'None'}</span>
                                            </div>
                                        </div>

                                        <div className="flex flex-wrap gap-2 border-t border-white/10 pt-3 xl:col-span-2 xl:justify-end">
                                            <IndustrialButton
                                                type="button"
                                                variant="ghost"
                                                size="sm"
                                                disabled={busyId === subscriber.id}
                                                onClick={() => inspectDeliveries(subscriber)}
                                                aria-label={`Inspect ${subscriber.name} deliveries`}
                                                title="Inspect delivery history"
                                            >
                                                <ShieldCheck className="h-4 w-4" />
                                                Ledger
                                            </IndustrialButton>
                                            <IndustrialButton
                                                type="button"
                                                variant="secondary"
                                                size="sm"
                                                disabled={!subscriber.telegram_chat_id || subscriber.subscription_state === 'EXPIRED' || busyId === subscriber.id}
                                                onClick={() => sendChatTest(subscriber)}
                                                aria-label={`Test ${subscriber.name} chat`}
                                                title="Send Telegram chat test"
                                            >
                                                <Send className="h-4 w-4" />
                                                Test
                                            </IndustrialButton>
                                            <IndustrialButton
                                                type="button"
                                                variant="ghost"
                                                size="sm"
                                                disabled={busyId === subscriber.id}
                                                onClick={() => openEditForm(subscriber)}
                                                aria-label={`Edit ${subscriber.name}`}
                                                title="Edit subscriber"
                                            >
                                                <Pencil className="h-4 w-4" />
                                                Edit
                                            </IndustrialButton>
                                            <IndustrialButton
                                                type="button"
                                                variant="alert"
                                                size="sm"
                                                disabled={subscriber.is_active === false || subscriber.subscription_state === 'INACTIVE' || busyId === subscriber.id}
                                                onClick={() => archiveSubscriber(subscriber)}
                                                aria-label={`Archive ${subscriber.name}`}
                                                title="Archive subscriber"
                                            >
                                                <Archive className="h-4 w-4" />
                                                Archive
                                            </IndustrialButton>
                                            <IndustrialButton
                                                type="button"
                                                variant="secondary"
                                                size="sm"
                                                disabled={!advisoryEnabled || !portfolio || busyId === subscriber.id}
                                                onClick={() => generateReport(subscriber)}
                                                aria-label={`Generate ${subscriber.name} advisory`}
                                                title="Generate advisory report"
                                            >
                                                <FileText className="h-4 w-4" />
                                                Generate
                                            </IndustrialButton>
                                            <IndustrialButton
                                                type="button"
                                                variant="primary"
                                                size="sm"
                                                disabled={!canSend || busyId === subscriber.id}
                                                onClick={() => sendReport(subscriber)}
                                                aria-label={`Send ${subscriber.name} advisory`}
                                                title="Send advisory report"
                                            >
                                                <Send className="h-4 w-4" />
                                                Send
                                            </IndustrialButton>
                                        </div>
                                    </article>
                                );
                            })}
                        </div>
                    </IndustrialCard>

                    <IndustrialCard
                        title="Advisory Preview"
                        subtitle="Generated report actions before private Telegram delivery."
                        tone="primary"
                        headerSlot={<UserRoundCheck className="h-5 w-5 text-amber-200" />}
                    >
                        {!reportState ? (
                            <div className="flex min-h-[360px] items-center justify-center border border-dashed border-white/10 bg-black/15 p-6 text-center text-sm text-slate-500">
                                No report generated in this session.
                            </div>
                        ) : (
                            <div className="space-y-5">
                                <div className="border border-amber-300/15 bg-amber-300/8 px-4 py-3">
                                    <div className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-200">Current Report</div>
                                    <div className="mt-2 text-lg font-black text-white">{reportState.subscriberName}</div>
                                    <div className="mt-1 text-sm text-slate-300">
                                        {reportState.report.summary?.action_items ?? 0} action item(s)
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    {(reportState.report.actions || []).map((action) => (
                                        <div key={`${action.ticker}-${action.action}`} className="grid gap-2 border border-white/10 bg-white/[0.035] px-3 py-3 sm:grid-cols-[90px_150px_1fr]">
                                            <div className="font-black text-cyan-100">{action.ticker}</div>
                                            <div className="text-xs font-black uppercase tracking-[0.12em] text-amber-100">{action.action}</div>
                                            <div className="text-sm text-slate-400">{action.reason || 'No rationale supplied.'}</div>
                                        </div>
                                    ))}
                                </div>

                                {reportState.telegramPreview && (
                                    <pre dir="auto" className="max-h-64 overflow-auto border border-white/10 bg-black/35 p-4 text-xs leading-5 text-slate-300">
                                        {reportState.telegramPreview}
                                    </pre>
                                )}
                            </div>
                        )}
                    </IndustrialCard>
                </div>

                <IndustrialCard
                    title="Delivery Ledger"
                    subtitle="Telegram attempts, failed errors, previews, and retry controls."
                    tone="secondary"
                    headerSlot={deliverySubscriber ? (
                        <span className="border border-cyan-300/20 bg-cyan-300/8 px-2 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-cyan-100">
                            {deliverySubscriber.name}
                        </span>
                    ) : undefined}
                >
                    {!deliverySubscriber ? (
                        <div className="border border-dashed border-white/10 bg-black/15 p-6 text-sm text-slate-500">
                            Select a subscriber ledger to inspect delivery history.
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {deliveryMessages.length > 0 && (
                                <div className="grid gap-2">
                                    {deliveryMessages.map((item, index) => (
                                        <div key={`${item}-${index}`} className="border border-cyan-300/20 bg-cyan-300/8 px-3 py-2 text-sm text-cyan-100">
                                            {item}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {deliveryLoading && (
                                <div className="flex h-24 items-center justify-center text-cyan-200">
                                    <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
                                    <span className="text-xs font-black uppercase tracking-[0.18em]">Loading Deliveries</span>
                                </div>
                            )}

                            {!deliveryLoading && deliveries.length === 0 && (
                                <div className="border border-white/10 bg-white/[0.035] px-4 py-5 text-sm text-slate-500">
                                    No delivery attempts recorded for this subscriber.
                                </div>
                            )}

                            {!deliveryLoading && deliveries.map((delivery) => {
                                const previewLines = (delivery.message_preview || '').split('\n').filter(Boolean);
                                return (
                                    <article key={delivery.id || `${delivery.delivery_type}-${delivery.created_at}`} className="grid gap-4 border border-white/10 bg-white/[0.035] p-4 lg:grid-cols-[160px_1fr_auto]">
                                        <div className="space-y-2">
                                            <div className={clsx(
                                                'inline-flex h-7 items-center border px-2 text-[10px] font-black uppercase',
                                                delivery.status === 'SENT'
                                                    ? 'border-emerald-400/25 bg-emerald-400/10 text-emerald-100'
                                                    : delivery.status === 'FAILED'
                                                        ? 'border-rose-400/35 bg-rose-500/10 text-rose-100'
                                                        : 'border-amber-300/25 bg-amber-300/10 text-amber-100',
                                            )}>
                                                {delivery.status || 'UNKNOWN'}
                                            </div>
                                            <div className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-600">
                                                #{delivery.id} {delivery.delivery_type || 'DELIVERY'}
                                            </div>
                                            <div className="text-xs text-slate-500">{delivery.created_at || 'No timestamp'}</div>
                                        </div>
                                        <div className="min-w-0 space-y-2">
                                            {delivery.last_error && (
                                                <div className="text-sm font-bold text-rose-100">{delivery.last_error}</div>
                                            )}
                                            {delivery.diagnosis?.operator_action && (
                                                <div className="border border-amber-300/20 bg-amber-300/8 px-3 py-2 text-sm text-amber-100">
                                                    <span className="font-black uppercase tracking-[0.12em] text-amber-200">
                                                        {delivery.diagnosis.action_code || 'DELIVERY_ACTION'}
                                                    </span>
                                                    <span className="ml-2">{delivery.diagnosis.operator_action}</span>
                                                </div>
                                            )}
                                            <div className="max-h-24 overflow-auto border border-white/10 bg-black/25 p-3 text-xs leading-5 text-slate-300">
                                                {previewLines.length > 0
                                                    ? previewLines.map((line) => <div key={`${delivery.id}-${line}`}>{line}</div>)
                                                    : 'No preview captured.'}
                                            </div>
                                        </div>
                                        <div className="flex flex-wrap items-start gap-2 lg:justify-end">
                                            {delivery.status === 'FAILED' && (
                                                <IndustrialButton
                                                    type="button"
                                                    variant="alert"
                                                    size="sm"
                                                    onClick={() => retryDelivery(delivery)}
                                                    aria-label={`Retry failed delivery ${delivery.id}`}
                                                >
                                                    <RefreshCw className="h-4 w-4" />
                                                    Retry
                                                </IndustrialButton>
                                            )}
                                        </div>
                                    </article>
                                );
                            })}
                        </div>
                    )}
                </IndustrialCard>
            </div>
        </main>
    );
}
