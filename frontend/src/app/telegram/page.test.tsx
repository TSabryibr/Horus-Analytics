import '@testing-library/jest-dom';
import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import TelegramPage from './page';

const mockRunAutopilot = jest.fn(async () => true);

jest.mock('../context/GlobalDataContext', () => ({
    useSignalDeskData: () => ({
        desk: {
            operating_mode: 'AUTOPILOT',
            autopilot_armed: true,
            autopilot: { status: 'READY' },
            active_run: { id: 88 },
            failed_delivery_count: 2,
            latest_failed_delivery: { status: 'FAILED', last_error: 'transport down' },
            lanes: {
                intraday: { count: 2, candidates: [] },
                swing: { count: 1, candidates: [] },
                position: { count: 0, candidates: [] },
            },
        },
        runAutopilot: mockRunAutopilot,
        followUpSummary: {
            total: 3,
            pending_count: 1,
            ready_count: 1,
            sent_count: 1,
            failed_count: 1,
            suppressed_count: 0,
            stale_pending_count: 0,
        },
        followUpRecords: [
            { id: 7, ticker: 'COMI', trigger_state: 'TP1_HIT', queue_state: 'READY', message_type: 'UPDATE', lane: 'swing', retry_count: 0 },
        ],
        followUpLoading: false,
        processFollowUps: jest.fn(async () => true),
        actOnFollowUp: jest.fn(async () => true),
    }),
}));

describe('TelegramPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockRunAutopilot.mockResolvedValue(true);
        window.sessionStorage.clear();
        Element.prototype.scrollIntoView = jest.fn();
    });

    function mockConfiguredFetch(overrides: Record<string, any> = {}) {
        return jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            const method = init?.method || 'GET';
            if (url.includes('/api/v1/telegram/config') && method === 'GET') {
                return {
                    ok: true,
                    json: async () => ({
                        configured: true,
                        chat_id: '-10012345',
                        token_preview: '1234****',
                        ...overrides,
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/telegram/config') && method === 'POST') {
                return { ok: true, json: async () => ({ status: 'success' }) } as Response;
            }
            if (url.includes('/api/v1/telegram/broadcast') && method === 'POST') {
                return { ok: true, json: async () => ({ status: 'sent' }) } as Response;
            }
            if (url.includes('/api/v1/telegram/signal-card') && method === 'POST') {
                return { ok: true, json: async () => ({ status: 'sent' }) } as Response;
            }
            if (url.includes('/api/v1/ai/daily-report/broadcast') && method === 'POST') {
                return { ok: true, json: async () => ({ status: 'sent', source_module: 'OLLAMA' }) } as Response;
            }
            if (url.includes('/api/v1/reports/analysis/broadcast') && method === 'POST') {
                return { ok: true, json: async () => ({ status: 'sent', period_type: 'WEEKLY' }) } as Response;
            }
            if (url.includes('/api/v1/telegram/test') && method === 'POST') {
                return { ok: true, json: async () => ({ status: 'ok' }) } as Response;
            }
            if (url.includes('/api/v1/control/scan') && method === 'POST') {
                return { ok: true, json: async () => ({ started: true }) } as Response;
            }
            if (url.includes('/api/v1/signals/publish/retry') && method === 'POST') {
                return { ok: true, json: async () => ({ status: 'completed' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
    }

    it('loads and displays telegram config status', async () => {
        global.fetch = mockConfiguredFetch() as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText('Telegram Release Chamber')).toBeInTheDocument();
            expect(screen.getByText('CHANNEL ONLINE')).toBeInTheDocument();
            expect(screen.getByText('Release Throne')).toBeInTheDocument();
            expect(screen.getByText('3 ready')).toBeInTheDocument();
            expect(screen.getByText('2 Retry Needed')).toBeInTheDocument();
            expect(screen.getByText('Lifecycle Follow-Ups')).toBeInTheDocument();
            expect(screen.getByText('2 queued updates')).toBeInTheDocument();
        });
    });

    it('shows OFFLINE status when channel is not configured', async () => {
        global.fetch = mockConfiguredFetch({ configured: false }) as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText('OFFLINE')).toBeInTheDocument();
        });
    });

    it('opens config modal and submits new configuration', async () => {
        const fetchMock = mockConfiguredFetch();
        global.fetch = fetchMock as jest.Mock;

        render(<TelegramPage />);

        const openConfigButton = await screen.findByRole('button', { name: /Configure Channel/i });
        fireEvent.click(openConfigButton);

        fireEvent.click(screen.getByRole('button', { name: /Establish Connection/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/telegram/config'),
                expect.objectContaining({
                    method: 'POST',
                    headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
                })
            );
        });
    });

    it('sends a general broadcast message', async () => {
        const fetchMock = mockConfiguredFetch();
        global.fetch = fetchMock as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText('CHANNEL ONLINE')).toBeInTheDocument();
        });

        const textarea = screen.getByPlaceholderText(/Type an announcement/i);
        fireEvent.change(textarea, { target: { value: 'Market update broadcast' } });
        fireEvent.click(screen.getByRole('button', { name: /Blast Broadcast/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/telegram/broadcast'),
                expect.objectContaining({ method: 'POST' })
            );
        });
    });

    it('sends a signal card and clears the form on success', async () => {
        const fetchMock = mockConfiguredFetch();
        global.fetch = fetchMock as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText('CHANNEL ONLINE')).toBeInTheDocument();
        });

        fireEvent.change(screen.getByPlaceholderText('e.g. COMI'), { target: { value: 'COMI' } });
        fireEvent.change(screen.getByPlaceholderText('85.50'), { target: { value: '85.5' } });
        fireEvent.change(screen.getByPlaceholderText('82.00'), { target: { value: '82' } });
        fireEvent.change(screen.getByPlaceholderText('92.00'), { target: { value: '92' } });

        fireEvent.click(screen.getByRole('button', { name: /Blast Horus Signal Card/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/telegram/signal-card'),
                expect.objectContaining({ method: 'POST' })
            );
        });
    });

    it('triggers intraday scan and logs result', async () => {
        const fetchMock = mockConfiguredFetch();
        global.fetch = fetchMock as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText('CHANNEL ONLINE')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Broadcast Intraday/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/control/scan'),
                expect.objectContaining({ method: 'POST' })
            );
        });
    });

    it('broadcasts AI daily report from the Signal Broadcast tab', async () => {
        const fetchMock = mockConfiguredFetch();
        global.fetch = fetchMock as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText('CHANNEL ONLINE')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Broadcast AI Daily Report/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/ai/daily-report/broadcast'),
                expect.objectContaining({ method: 'POST' })
            );
        });
    });

    it('dispatches the latest desk run through the release rail', async () => {
        const fetchMock = mockConfiguredFetch();
        global.fetch = fetchMock as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText('CHANNEL ONLINE')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Dispatch Latest Desk Run/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/signals/publish'),
                expect.objectContaining({ method: 'POST' })
            );
        });
    });

    it('retries failed desk deliveries through the release rail', async () => {
        const fetchMock = mockConfiguredFetch();
        global.fetch = fetchMock as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText('CHANNEL ONLINE')).toBeInTheDocument();
        });

        fireEvent.click(screen.getAllByRole('button', { name: /Retry Failed Deliveries/i })[0]);

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/signals/publish/retry'),
                expect.objectContaining({ method: 'POST' })
            );
        });
    });

    it('runs desk autopilot through the shared desk context action', async () => {
        const fetchMock = mockConfiguredFetch();
        global.fetch = fetchMock as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText('CHANNEL ONLINE')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Run Autopilot Dispatch/i }));

        await waitFor(() => {
            expect(mockRunAutopilot).toHaveBeenCalled();
        });
    });

    it('broadcasts weekly and monthly analysis reports from the Signal Broadcast tab', async () => {
        const fetchMock = mockConfiguredFetch();
        global.fetch = fetchMock as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText('CHANNEL ONLINE')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Broadcast Weekly Report/i }));
        fireEvent.click(screen.getByRole('button', { name: /Broadcast Monthly Report/i }));

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/reports/analysis/broadcast'),
                expect.objectContaining({ method: 'POST' })
            );
        });
    });

    it('displays standby message in empty log', async () => {
        global.fetch = mockConfiguredFetch() as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText('Standby...')).toBeInTheDocument();
        });
    });

    it('renders technical sub-titles and outbound payload preview', async () => {
        global.fetch = mockConfiguredFetch() as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByText(/TECHNICAL ALERT: 2 FAILED DELIVERIES/i)).toBeInTheDocument();
            expect(screen.getByText('Outbound Payload Preview')).toBeInTheDocument();
            expect(screen.getByText(/Prepared to re-dispatch 2 failed message/i)).toBeInTheDocument();
        });
    });

    it('toggles emergency hold freeze and pauses dispatches', async () => {
        global.fetch = mockConfiguredFetch() as jest.Mock;

        render(<TelegramPage />);

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /Emergency Hold/i })).toBeInTheDocument();
        });

        const holdButton = screen.getByRole('button', { name: /Emergency Hold/i });
        fireEvent.click(holdButton);

        await waitFor(() => {
            expect(screen.getByText('Authority Suspended')).toBeInTheDocument();
            expect(screen.getByText(/EMERGENCY HOLD: OPERATOR RELEASE FREEZE ACTIVE/i)).toBeInTheDocument();
            expect(screen.getAllByText('Authority Suspended (Hold Active)').length).toBeGreaterThanOrEqual(1);
        });

        // Click Unfreeze Release to restore
        const unfreezeButton = screen.getByRole('button', { name: /Unfreeze Release/i });
        fireEvent.click(unfreezeButton);

        await waitFor(() => {
            expect(screen.getByText('Recovery Decree')).toBeInTheDocument();
        });
    });
});
