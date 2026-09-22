import '@testing-library/jest-dom';
import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import SubscribersPage from './page';

const fetchMock = jest.fn();

jest.mock('@/lib/api', () => ({
    apiFetch: (...args: unknown[]) => fetchMock(...args),
    readJsonSafe: async (response: any) => response.json(),
    pickApiMessage: (data: any, fallback: string) => data?.detail || data?.message || fallback,
}));

function jsonResponse(body: unknown, ok = true, status = 200) {
    return {
        ok,
        status,
        statusText: ok ? 'OK' : 'ERROR',
        json: async () => body,
    };
}

describe('SubscribersPage', () => {
    let includeProvisionedSubscriber = false;
    let managedTier = 'MANAGED_ADVISORY';
    let managedPaidUntil = '2026-06-20';
    let archivedSubscriber = false;
    let managedChatTestFails = false;
    let createdPortfolioId: number | null = null;

    beforeEach(() => {
        jest.clearAllMocks();
        includeProvisionedSubscriber = false;
        managedTier = 'MANAGED_ADVISORY';
        managedPaidUntil = '2026-06-20';
        archivedSubscriber = false;
        managedChatTestFails = false;
        createdPortfolioId = null;
        fetchMock.mockImplementation((endpoint: string, options?: RequestInit) => {
            if (endpoint === '/api/v1/subscribers/1/archive' && options?.method === 'POST') {
                archivedSubscriber = true;
                return Promise.resolve(jsonResponse({
                    status: 'archived',
                    subscriber: {
                        id: 1,
                        name: 'Managed Client',
                        is_active: false,
                        subscription_tier: managedTier,
                        subscription_state: 'INACTIVE',
                        telegram_chat_id: '-100111',
                        report_language: 'EN',
                        paid_until: managedPaidUntil,
                        linked_portfolios: [{ id: 7, name: 'Managed Portfolio', type: 'USER' }],
                        last_delivery: { status: 'SENT', created_at: '2026-05-20T12:00:00' },
                    },
                }));
            }

            if (endpoint === '/api/v1/subscribers/1' && options?.method === 'PATCH') {
                const body = JSON.parse(String(options.body || '{}'));
                managedTier = body.subscription_tier;
                managedPaidUntil = body.paid_until;
                return Promise.resolve(jsonResponse({
                    status: 'updated',
                    subscriber: {
                        id: 1,
                        name: 'Managed Client',
                        subscription_tier: managedTier,
                        subscription_state: 'ACTIVE',
                        telegram_chat_id: '-100111',
                        report_language: body.report_language || 'EN',
                        paid_until: managedPaidUntil,
                        linked_portfolios: [{ id: 7, name: 'Managed Portfolio', type: 'USER' }],
                        last_delivery: { status: 'SENT', created_at: '2026-05-20T12:00:00' },
                    },
                }));
            }

            if (endpoint === '/api/v1/subscribers/deliveries?client_id=1&limit=20') {
                return Promise.resolve(jsonResponse({
                    count: 1,
                    deliveries: [
                        {
                            id: 91,
                            client_id: 1,
                            portfolio_id: 7,
                            delivery_type: 'PORTFOLIO_ADVISORY',
                            subscription_tier: 'MANAGED_ADVISORY',
                            channel: 'TELEGRAM',
                            status: 'FAILED',
                            chat_id: '-100111',
                            message_preview: 'HORUS PORTFOLIO ADVISORY REPORT\nCOMI HOLD_WITH_SIGNAL',
                            last_error: 'telegram down',
                            diagnosis: {
                                action_code: 'SUBSCRIBER_MUST_START_BOT',
                                operator_action: 'Ask subscriber to open the bot and press Start, then retry delivery.',
                            },
                            created_at: '2026-05-20T12:00:00',
                        },
                    ],
                }));
            }

            if (endpoint === '/api/v1/subscribers/deliveries/91/retry') {
                return Promise.resolve(jsonResponse({
                    status: 'sent',
                    retried_delivery_id: 91,
                    delivery: {
                        id: 92,
                        client_id: 1,
                        portfolio_id: 7,
                        delivery_type: 'PORTFOLIO_ADVISORY',
                        status: 'SENT',
                        provider_message_id: '992',
                        created_at: '2026-05-20T12:05:00',
                    },
                }));
            }

            if (endpoint === '/api/v1/subscribers/1/telegram-test/send') {
                if (managedChatTestFails) {
                    return Promise.resolve(jsonResponse({
                        status: 'failed',
                        delivery: {
                            id: 95,
                            client_id: 1,
                            delivery_type: 'TELEGRAM_CHAT_TEST',
                            status: 'FAILED',
                            chat_id: '1822794531',
                            last_error: 'Bad Request: chat not found',
                            diagnosis: {
                                action_code: 'CHAT_ID_NOT_FOUND',
                                operator_action: 'Verify the stored Telegram chat ID and ensure the bot is a member of that chat or channel.',
                            },
                            created_at: '2026-05-20T12:08:00',
                        },
                    }, false, 502));
                }
                return Promise.resolve(jsonResponse({
                    status: 'sent',
                    delivery: {
                        id: 93,
                        client_id: 1,
                        delivery_type: 'TELEGRAM_CHAT_TEST',
                        status: 'SENT',
                        provider_message_id: '993',
                        created_at: '2026-05-20T12:06:00',
                    },
                }));
            }

            if (endpoint === '/api/v1/subscribers') {
                if (options?.method === 'POST') {
                    const body = JSON.parse(String(options.body || '{}'));
                    const linkedPortfolios = body.create_portfolio
                        ? [{ id: 45, name: body.name, type: 'USER' }]
                        : [];
                    if (body.create_portfolio) {
                        createdPortfolioId = 45;
                    }
                    return Promise.resolve(jsonResponse({
                        status: 'created',
                        subscriber: {
                            id: 44,
                            name: body.name || 'VIP Signals Client',
                            subscription_tier: body.subscription_tier || 'MANAGED_ADVISORY',
                            subscription_state: 'ACTIVE',
                            telegram_chat_id: body.telegram_chat_id || '-100999',
                            report_language: body.report_language || 'EN',
                            paid_until: body.paid_until || '2026-07-20',
                            linked_portfolios: linkedPortfolios,
                            last_delivery: null,
                        },
                    }));
                }
                const subscribers = [
                    {
                        id: 1,
                        name: 'Managed Client',
                        is_active: !archivedSubscriber,
                        subscription_tier: managedTier,
                        subscription_state: archivedSubscriber ? 'INACTIVE' : 'ACTIVE',
                        telegram_chat_id: '-100111',
                        report_language: 'EN',
                        paid_until: managedPaidUntil,
                        linked_portfolios: [{ id: 7, name: 'Managed Portfolio', type: 'USER' }],
                        last_delivery: { status: 'SENT', created_at: '2026-05-20T12:00:00' },
                    },
                    {
                        id: 2,
                        name: 'Expired Client',
                        subscription_tier: 'SIGNALS_PLUS_PORTFOLIO_RECS',
                        subscription_state: 'EXPIRED',
                        telegram_chat_id: '-100222',
                        report_language: 'EN',
                        paid_until: '2026-01-01',
                        linked_portfolios: [{ id: 8, name: 'Expired Portfolio', type: 'USER' }],
                        last_delivery: null,
                    },
                    {
                        id: 3,
                        name: 'No Chat Client',
                        subscription_tier: 'SIGNALS_ONLY',
                        subscription_state: 'ACTIVE',
                        telegram_chat_id: null,
                        report_language: 'AR',
                        paid_until: '2026-06-20',
                        linked_portfolios: [],
                        last_delivery: null,
                    },
                ];
                if (includeProvisionedSubscriber) {
                    subscribers.push({
                        id: 44,
                        name: 'VIP Signals Client',
                        subscription_tier: 'MANAGED_ADVISORY',
                        subscription_state: 'ACTIVE',
                        telegram_chat_id: '-100999',
                        report_language: 'AR',
                        paid_until: '2026-07-20',
                        linked_portfolios: [{ id: createdPortfolioId || 7, name: createdPortfolioId ? 'VIP Signals Client' : 'Managed Portfolio', type: 'USER' }],
                        last_delivery: null,
                    });
                }
                return Promise.resolve(jsonResponse({
                    summary: {
                        total: subscribers.length,
                        active: includeProvisionedSubscriber ? 2 : 1,
                        expired: 1,
                        renewal_due: 1,
                        missing_chat: 1,
                    },
                    subscribers,
                }));
            }

            if (endpoint === '/api/v1/portfolios') {
                if (options?.method === 'POST') {
                    createdPortfolioId = 45;
                    return Promise.resolve(jsonResponse({
                        status: 'created',
                        id: createdPortfolioId,
                    }));
                }
                return Promise.resolve(jsonResponse([
                    { id: 7, name: 'Managed Portfolio', type: 'USER' },
                    { id: 8, name: 'Expired Portfolio', type: 'USER' },
                    ...(createdPortfolioId ? [{ id: createdPortfolioId, name: 'VIP Signals Client', type: 'USER' }] : []),
                ]));
            }

            if (endpoint === '/api/v1/subscribers/44/portfolios') {
                includeProvisionedSubscriber = true;
                return Promise.resolve(jsonResponse({
                    status: 'linked',
                    subscriber: {
                        id: 44,
                        name: 'VIP Signals Client',
                        linked_portfolios: [{ id: createdPortfolioId || 7, name: createdPortfolioId ? 'VIP Signals Client' : 'Managed Portfolio', type: 'USER' }],
                    },
                }));
            }

            if (endpoint === '/api/v1/subscribers/1/advisory-report?portfolio_id=7') {
                return Promise.resolve(jsonResponse({
                    report: {
                        summary: { action_items: 2 },
                        actions: [
                            { ticker: 'COMI', action: 'HOLD_WITH_SIGNAL', reason: 'Latest signal supports the position.' },
                        ],
                    },
                    telegram_preview: 'PORTFOLIO ADVISORY REPORT\nAdvisory only.',
                }));
            }

            if (endpoint === '/api/v1/subscribers/1/advisory-report/send') {
                return Promise.resolve(jsonResponse({
                    status: 'sent',
                    report: {
                        summary: { action_items: 2 },
                        actions: [
                            { ticker: 'COMI', action: 'HOLD_WITH_SIGNAL', reason: 'Latest signal supports the position.' },
                        ],
                    },
                    delivery: {
                        id: 94,
                        client_id: 1,
                        portfolio_id: 7,
                        delivery_type: 'PORTFOLIO_ADVISORY',
                        status: 'SENT',
                        provider_message_id: '994',
                        created_at: '2026-05-20T12:07:00',
                    },
                }));
            }

            return Promise.resolve(jsonResponse({}, true));
        });
    });

    it('shows subscriber health states and generates an advisory report', async () => {
        render(<SubscribersPage />);

        expect(await screen.findByText('Subscribers')).toBeInTheDocument();
        expect((await screen.findAllByText('Managed Client')).length).toBeGreaterThan(0);
        expect(screen.getByText('[EXPIRED]')).toBeInTheDocument();
        expect(screen.getByText('[MISSING CHAT]')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /generate managed client advisory/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith('/api/v1/subscribers/1/advisory-report?portfolio_id=7');
            expect(screen.getByText('COMI')).toBeInTheDocument();
            expect(screen.getByText('HOLD_WITH_SIGNAL')).toBeInTheDocument();
        });
    });

    it('creates a subscriber and links the selected portfolio', async () => {
        render(<SubscribersPage />);

        expect((await screen.findAllByText('Managed Client')).length).toBeGreaterThan(0);

        fireEvent.click(screen.getByRole('button', { name: /add subscriber/i }));
        fireEvent.change(screen.getByLabelText(/subscriber name/i), { target: { value: 'VIP Signals Client' } });
        fireEvent.change(screen.getByLabelText(/subscription tier/i), { target: { value: 'MANAGED_ADVISORY' } });
        fireEvent.change(screen.getByLabelText(/subscriber private chat id/i), { target: { value: '-100999' } });
        fireEvent.change(screen.getByLabelText(/report language/i), { target: { value: 'AR' } });
        fireEvent.change(screen.getByLabelText(/paid until/i), { target: { value: '2026-07-20' } });
        fireEvent.change(screen.getByLabelText(/linked portfolio/i), { target: { value: '7' } });

        fireEvent.click(screen.getByRole('button', { name: /save subscriber/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith('/api/v1/subscribers', expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({
                    name: 'VIP Signals Client',
                    subscription_tier: 'MANAGED_ADVISORY',
                    telegram_chat_id: '-100999',
                    report_language: 'AR',
                    paid_until: '2026-07-20',
                    risk_profile: 'BALANCED',
                    default_currency: 'EGP',
                    notes: '',
                    is_active: true,
                    portfolio_id: 7,
                    create_portfolio: false,
                }),
            }));
            expect(fetchMock).toHaveBeenCalledWith('/api/v1/subscribers/44/portfolios', expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({ portfolio_id: 7 }),
            }));
            expect(screen.getAllByText('VIP Signals Client').length).toBeGreaterThan(0);
        });
    });

    it('creates and links a new user portfolio during Type 3 provisioning', async () => {
        render(<SubscribersPage />);

        expect((await screen.findAllByText('Managed Client')).length).toBeGreaterThan(0);

        fireEvent.click(screen.getByRole('button', { name: /add subscriber/i }));
        fireEvent.change(screen.getByLabelText(/subscriber name/i), { target: { value: 'VIP Signals Client' } });
        fireEvent.change(screen.getByLabelText(/subscription tier/i), { target: { value: 'MANAGED_ADVISORY' } });
        fireEvent.change(screen.getByLabelText(/subscriber private chat id/i), { target: { value: '-100999' } });
        fireEvent.change(screen.getByLabelText(/report language/i), { target: { value: 'AR' } });
        fireEvent.change(screen.getByLabelText(/paid until/i), { target: { value: '2026-07-20' } });

        expect(screen.getByLabelText(/create user portfolio/i)).toBeChecked();

        fireEvent.click(screen.getByRole('button', { name: /save subscriber/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith('/api/v1/subscribers', expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({
                    name: 'VIP Signals Client',
                    subscription_tier: 'MANAGED_ADVISORY',
                    telegram_chat_id: '-100999',
                    report_language: 'AR',
                    paid_until: '2026-07-20',
                    risk_profile: 'BALANCED',
                    default_currency: 'EGP',
                    notes: '',
                    is_active: true,
                    portfolio_id: null,
                    create_portfolio: true,
                }),
            }));
            expect(fetchMock).not.toHaveBeenCalledWith('/api/v1/portfolios', expect.anything());
        });
    });

    it('edits tier and renewal date for an existing subscriber', async () => {
        render(<SubscribersPage />);

        expect((await screen.findAllByText('Managed Client')).length).toBeGreaterThan(0);

        fireEvent.click(screen.getByRole('button', { name: /edit managed client/i }));
        fireEvent.change(screen.getByLabelText(/subscription tier/i), { target: { value: 'SIGNALS_PLUS_PORTFOLIO_RECS' } });
        fireEvent.change(screen.getByLabelText(/report language/i), { target: { value: 'AR' } });
        fireEvent.change(screen.getByLabelText(/paid until/i), { target: { value: '2026-08-31' } });
        fireEvent.click(screen.getByRole('button', { name: /save subscriber/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith('/api/v1/subscribers/1', expect.objectContaining({
                method: 'PATCH',
                body: JSON.stringify({
                    name: 'Managed Client',
                    subscription_tier: 'SIGNALS_PLUS_PORTFOLIO_RECS',
                    telegram_chat_id: '-100111',
                    report_language: 'AR',
                    paid_until: '2026-08-31',
                    risk_profile: 'BALANCED',
                    default_currency: 'EGP',
                    notes: '',
                    is_active: true,
                }),
            }));
            expect(screen.getByText('2026-08-31')).toBeInTheDocument();
        });
    });

    it('loads delivery history, retries a failed delivery, and sends a chat test', async () => {
        render(<SubscribersPage />);

        expect((await screen.findAllByText('Managed Client')).length).toBeGreaterThan(0);

        fireEvent.click(screen.getByRole('button', { name: /inspect managed client deliveries/i }));

        expect(await screen.findByText('telegram down')).toBeInTheDocument();
        expect(screen.getByText(/Ask subscriber to open the bot/i)).toBeInTheDocument();
        expect(screen.getByText('HORUS PORTFOLIO ADVISORY REPORT')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /retry failed delivery 91/i }));
        fireEvent.click(screen.getByRole('button', { name: /test managed client chat/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith('/api/v1/subscribers/deliveries?client_id=1&limit=20');
            expect(fetchMock).toHaveBeenCalledWith('/api/v1/subscribers/deliveries/91/retry', expect.objectContaining({
                method: 'POST',
            }));
            expect(fetchMock).toHaveBeenCalledWith('/api/v1/subscribers/1/telegram-test/send', expect.objectContaining({
                method: 'POST',
            }));
            expect(screen.getByText(/Retry sent for delivery 91/i)).toBeInTheDocument();
            expect(screen.getByText(/Chat test sent to Managed Client/i)).toBeInTheDocument();
        });
    });

    it('shows the Telegram provider reason when a subscriber chat test fails', async () => {
        managedChatTestFails = true;

        render(<SubscribersPage />);

        expect((await screen.findAllByText('Managed Client')).length).toBeGreaterThan(0);

        fireEvent.click(screen.getByRole('button', { name: /test managed client chat/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/Bad Request: chat not found/i).length).toBeGreaterThan(0);
            expect(screen.getAllByText(/Verify the stored Telegram chat ID/i).length).toBeGreaterThan(0);
        });
    });

    it('surfaces the next activation move and runs it from the checklist', async () => {
        render(<SubscribersPage />);

        expect(await screen.findByText('Client Activation')).toBeInTheDocument();
        expect(await screen.findByText('Send advisory')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /run managed client activation step/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith('/api/v1/subscribers/1/advisory-report/send', expect.objectContaining({
                method: 'POST',
                body: JSON.stringify({ portfolio_id: 7 }),
            }));
            expect(screen.getByText(/Report sent to Managed Client/i)).toBeInTheDocument();
        });
    });

    it('archives a subscriber while keeping the ledger visible', async () => {
        render(<SubscribersPage />);

        expect((await screen.findAllByText('Managed Client')).length).toBeGreaterThan(0);

        fireEvent.click(screen.getByRole('button', { name: /archive managed client/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith('/api/v1/subscribers/1/archive', expect.objectContaining({
                method: 'POST',
            }));
            expect(screen.getByText(/Managed Client archived/i)).toBeInTheDocument();
            expect(screen.getAllByText('INACTIVE').length).toBeGreaterThan(0);
        });
    });
});
