import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import StatusPage from './page';
import { resetStatusRuntimeBootstrapCache } from './hooks/useStatusRuntime';
import { resetStatusSyncBootstrapCache } from './hooks/useStatusSync';

let pollingCallbacks: Array<() => Promise<void> | void> = [];
let pollingOptions: Array<Record<string, unknown>> = [];

jest.mock('@/hooks/usePolling', () => ({
    usePolling: (cb: () => Promise<void> | void, options: Record<string, unknown>) => {
        pollingCallbacks.push(cb);
        pollingOptions.push(options);
    },
}));

const baseStatusPayload = {
    system_ready: true,
    db_connected: true,
    message: 'Running...',
    alerts: {
        telegram: { configured: true }
    },
    scheduler: {
        running: true,
        jobs: [
            { id: 'scan-daily', trigger: 'cron', next_run: '09:00' },
            { id: 'monitor-live', trigger: 'interval', next_run: 'Asynchronous' },
        ],
    },
    signal_desk: {
        configured: true,
        operating_mode: 'AUTOPILOT',
        autopilot_armed: true,
        queued_candidate_count: 60,
        lanes: { intraday: 52, swing: 8, position: 0 },
    },
    signal_lifecycle: {
        total: 12,
        active_count: 4,
        ambiguous_count: 1,
        stale_active_count: 0,
        monitor_status: 'ATTENTION',
        latest_published_at: '2026-02-17T10:31:00',
    },
    signal_followups: {
        total: 6,
        pending_count: 1,
        ready_count: 2,
        failed_count: 1,
        suppressed_count: 1,
        stale_pending_count: 0,
        latest_created_at: '2026-02-17T11:00:00',
    },
    data_status: {
        history: { status: 'FRESH', last_updated: '2026-02-17 09:00', file_count: 120, age_hours: 1 },
        intraday: { status: 'LIVE', last_bar: '2026-02-17 10:31', age_mins: 1 },
    },
    metrics: { total_signals: 314, last_signal_date: '2026-02-17' },
};

const baseRuntimeUniversePayload = {
    summary: {
        tracked_count: 270,
        runtime_quarantined_count: 16,
        review_candidate_count: 11,
    },
    runtime_quarantined: [
        { ticker: 'ADIB_R3', reason: 'RIGHTS' },
        { ticker: 'MEGM', reason: 'DORMANT' },
    ],
    review_candidates: [
        { ticker: 'CPME', reason: 'SOURCE_STALE' },
        { ticker: 'TRTO', reason: 'SOURCE_STALE' },
    ],
};

describe('StatusPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        pollingCallbacks = [];
        pollingOptions = [];
        resetStatusRuntimeBootstrapCache();
        resetStatusSyncBootstrapCache();
    });

    it('renders system observability cards from backend payload', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return { ok: true, json: async () => baseStatusPayload } as Response;
            }
            if (url.includes('/api/v1/data/runtime-universe')) {
                return { ok: true, json: async () => baseRuntimeUniversePayload } as Response;
            }
            if (url.includes('/api/v1/data/sync/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<StatusPage />);

        await waitFor(() => {
            expect(screen.getByRole('heading', { name: /Observability Terminal/i })).toBeInTheDocument();
            expect(screen.getByText('Runtime State')).toBeInTheDocument();
            expect(screen.getByText('All Systems Go')).toBeInTheDocument();
            expect(screen.getByText('OPERATIONAL')).toBeInTheDocument();
            expect(screen.getByText('CONNECTED')).toBeInTheDocument();
            expect(screen.getByText('ACTIVE')).toBeInTheDocument();
            expect(screen.getByText('RUNNING')).toBeInTheDocument();
            expect(screen.getByText('Runtime Universe')).toBeInTheDocument();
            expect(screen.getByText('ADIB_R3')).toBeInTheDocument();
            expect(screen.getByText('TRTO')).toBeInTheDocument();
            expect(screen.getByText('Data Lake Freshness')).toBeInTheDocument();
            expect(screen.getByText('Signal Lifecycle + Queue')).toBeInTheDocument();
            expect(screen.getByText('Candidate Queue')).toBeInTheDocument();
            expect(screen.getByText('Job Scheduler Pipeline')).toBeInTheDocument();
        });
    });

    it('shows sync in progress message when data sync status is RUNNING', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return { ok: true, json: async () => baseStatusPayload } as Response;
            }
            if (url.includes('/api/v1/data/sync/status')) {
                return { ok: true, json: async () => ({ status: 'RUNNING' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<StatusPage />);

        await waitFor(() => {
            expect(screen.getByText('Syncing Data...')).toBeInTheDocument();
            expect(screen.getByText('Data sync in progress...')).toBeInTheDocument();
        });
    });

    it('surfaces provisioning runtime state before normal feed freshness is available', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return {
                    ok: true,
                    json: async () => ({
                        ...baseStatusPayload,
                        system_ready: false,
                        provisioning_status: 'RUNNING',
                        provisioning_completed_trading_days: 61,
                        provisioning_target_trading_days: 252,
                        data_status: null,
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/data/sync/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<StatusPage />);

        await waitFor(() => {
            expect(screen.getByText('Provisioning History')).toBeInTheDocument();
            expect(screen.getByText('PROVISIONING')).toBeInTheDocument();
            expect(screen.queryByText('Detecting Feed')).not.toBeInTheDocument();
        });
    });

    it('surfaces provisioning failure instead of generic detecting state', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return {
                    ok: true,
                    json: async () => ({
                        ...baseStatusPayload,
                        system_ready: false,
                        message: 'Startup provisioning failed.',
                        provisioning_status: 'ERROR',
                        provisioning_error: 'Insufficient historical data coverage',
                        data_status: null,
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/data/sync/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<StatusPage />);

        await waitFor(() => {
            expect(screen.getByText('Provisioning Failed')).toBeInTheDocument();
            expect(screen.getByText('FAILED')).toBeInTheDocument();
            expect(screen.getByText(/Provisioning Error: Insufficient historical data coverage/i)).toBeInTheDocument();
            expect(screen.queryByText('Detecting Feed')).not.toBeInTheDocument();
            expect(screen.queryByText('BOOTING')).not.toBeInTheDocument();
        });
    });

    it('starts data sync from action button and reflects started state', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return { ok: true, json: async () => baseStatusPayload } as Response;
            }
            if (url.includes('/api/v1/data/sync/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            if (url.includes('/api/v1/data/sync/start') && init?.method === 'POST') {
                return { ok: true, json: async () => ({ started: true }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<StatusPage />);

        const triggerButton = await screen.findByRole('button', { name: /Sync History \+ Intraday/i });
        fireEvent.click(triggerButton);

        await waitFor(() => {
            expect(screen.getByText('Data sync started.')).toBeInTheDocument();
            expect(triggerButton).toBeDisabled();
        });
    });

    it('handles already-running sync response from start endpoint', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return { ok: true, json: async () => baseStatusPayload } as Response;
            }
            if (url.includes('/api/v1/data/sync/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            if (url.includes('/api/v1/data/sync/start') && init?.method === 'POST') {
                return { ok: true, json: async () => ({ started: false, message: 'Data sync already running.' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<StatusPage />);

        const triggerButton = await screen.findByRole('button', { name: /Sync History \+ Intraday/i });
        fireEvent.click(triggerButton);

        await waitFor(() => {
            expect(screen.getByText('Data sync already running.')).toBeInTheDocument();
            expect(triggerButton).toBeDisabled();
        });
    });

    it('transitions RUNNING to COMPLETED and forces status refresh on sync poll', async () => {
        const syncStates = ['RUNNING', 'COMPLETED'];
        let fullStatusCalls = 0;

        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                fullStatusCalls += 1;
                return { ok: true, json: async () => baseStatusPayload } as Response;
            }
            if (url.includes('/api/v1/data/sync/status')) {
                const status = syncStates.shift() ?? 'IDLE';
                return { ok: true, json: async () => ({ status }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<StatusPage />);

        await waitFor(() => {
            expect(screen.getByText('Data sync in progress...')).toBeInTheDocument();
        });

        await act(async () => {
            await pollingCallbacks[1]?.();
        });

        await waitFor(() => {
            expect(screen.getByText('Data sync completed.')).toBeInTheDocument();
            expect(fullStatusCalls).toBeGreaterThanOrEqual(2);
        });
    });

    it('renders the observability shell immediately while full status is still loading', async () => {
        global.fetch = jest.fn((input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return new Promise<Response>(() => undefined);
            }
            if (url.includes('/api/v1/system/boot-status')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => ({
                        system_ready: true,
                        db_connected: true,
                        message: 'Data pipeline is fresh.',
                        pipeline_state: 'FRESH',
                        provisioning_status: 'IDLE',
                        freshness: { market_open: true, overall_ok: true },
                        scheduler: { running: true },
                        telegram: { configured: true },
                    }),
                } as Response);
            }
            if (url.includes('/api/v1/data/status')) {
                return Promise.resolve({ ok: true, json: async () => baseStatusPayload.data_status } as Response);
            }
            if (url.includes('/api/v1/data/sync/status')) {
                return Promise.resolve({ ok: true, json: async () => ({ status: 'IDLE' }) } as Response);
            }
            return Promise.resolve({ ok: true, json: async () => ({}) } as Response);
        }) as jest.Mock;

        render(<StatusPage />);

        expect(screen.getByRole('heading', { name: /Observability Terminal/i })).toBeInTheDocument();
        expect(screen.getByText('Runtime State')).toBeInTheDocument();
        expect(screen.getByText(/Sampling live status feed/i)).toBeInTheDocument();

        await waitFor(() => {
            expect(screen.getByText('All Systems Go')).toBeInTheDocument();
        }, { timeout: 3000 });
    });

    it('does not keep sync-status polling active while the page is idle', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return { ok: true, json: async () => baseStatusPayload } as Response;
            }
            if (url.includes('/api/v1/data/sync/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<StatusPage />);

        await waitFor(() => {
            expect(screen.getByText('All Systems Go')).toBeInTheDocument();
        });

        expect(pollingOptions[1]?.enabled).toBe(false);
    });

    it('avoids duplicate initial status requests under StrictMode', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return { ok: true, json: async () => baseStatusPayload } as Response;
            }
            if (url.includes('/api/v1/data/sync/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(
            <React.StrictMode>
                <StatusPage />
            </React.StrictMode>
        );

        await waitFor(() => {
            const fullStatusCalls = fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/system/full-status'));
            const syncStatusCalls = fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/data/sync/status'));

            expect(fullStatusCalls).toHaveLength(1);
            expect(syncStatusCalls).toHaveLength(1);
        });
    });

    it('reuses the initial status bootstrap requests across a fast remount', async () => {
        let resolveBootStatus: ((value: Response) => void) | null = null;
        let resolveDataStatus: ((value: Response) => void) | null = null;
        let resolveFullStatus: ((value: Response) => void) | null = null;
        let resolveSyncStatus: ((value: Response) => void) | null = null;

        const fetchMock = jest.fn((input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/boot-status')) {
                return new Promise<Response>((resolve) => {
                    resolveBootStatus = resolve;
                });
            }
            if (url.includes('/api/v1/data/status')) {
                return new Promise<Response>((resolve) => {
                    resolveDataStatus = resolve;
                });
            }
            if (url.includes('/api/v1/system/full-status')) {
                return new Promise<Response>((resolve) => {
                    resolveFullStatus = resolve;
                });
            }
            if (url.includes('/api/v1/data/sync/status')) {
                return new Promise<Response>((resolve) => {
                    resolveSyncStatus = resolve;
                });
            }
            return Promise.resolve({ ok: true, json: async () => ({}) } as Response);
        });
        global.fetch = fetchMock as jest.Mock;

        const first = render(<StatusPage />);
        first.unmount();

        render(<StatusPage />);

        const bootStatusCalls = fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/system/boot-status'));
        const dataStatusCalls = fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/data/status'));
        const fullStatusCalls = fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/system/full-status'));
        const syncStatusCalls = fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/data/sync/status'));

        expect(bootStatusCalls).toHaveLength(1);
        expect(dataStatusCalls).toHaveLength(1);
        expect(fullStatusCalls).toHaveLength(0);
        expect(syncStatusCalls).toHaveLength(1);

        await act(async () => {
            resolveBootStatus?.({
                ok: true,
                json: async () => ({
                    system_ready: true,
                    db_connected: true,
                    scheduler: { running: true },
                    telegram: { configured: true },
                }),
            } as Response);
            resolveDataStatus?.({ ok: true, json: async () => baseStatusPayload.data_status } as Response);
            await Promise.resolve();
        });

        await act(async () => {
            resolveFullStatus?.({ ok: true, json: async () => baseStatusPayload } as Response);
            resolveSyncStatus?.({ ok: true, json: async () => ({ status: 'IDLE' }) } as Response);
        });

        await waitFor(() => {
            expect(screen.getByText('All Systems Go')).toBeInTheDocument();
        });
    });
});
