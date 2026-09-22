import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import ScannerPage from './page';

const mockPromoteCandidate = jest.fn();

jest.mock('@/hooks/usePolling', () => ({
    usePolling: () => {},
}));

jest.mock('../context/GlobalDataContext', () => ({
    useSignalDeskData: () => ({
        promoteCandidate: mockPromoteCandidate,
    }),
}));

const completedScannerPayload = {
    regime: 'BULLISH',
    breadth: 62.5,
    signals_count: 1,
    signals: [
        {
            Ticker: 'COMI',
            Signal_Type: 'BUY',
            Signal_Setup: 'BREAKOUT',
            Conviction: 'HIGH',
            Entry_Price: 104.5,
            Stop_Loss: 99.9,
            Target_Price: 110.0,
            Target_Price_2: 114.0,
            Score: 4.2,
            Volume_x: 2.3,
        },
    ],
};

describe('ScannerPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockPromoteCandidate.mockResolvedValue(true);
    });

    it('shows idle empty state before any scan data is available', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/scanner/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<ScannerPage />);

        await waitFor(() => {
            expect(screen.getByText('Ready for Mission Control')).toBeInTheDocument();
            expect(screen.getByText('Initialize a scan to begin market telemetry.')).toBeInTheDocument();
        });
    });

    it('hydrates table when backend status is COMPLETED with result', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/scanner/status')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'COMPLETED', result: completedScannerPayload }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<ScannerPage />);

        await waitFor(() => {
            expect(screen.getByText('Market Regime')).toBeInTheDocument();
            expect(screen.getByText('BULLISH')).toBeInTheDocument();
            expect(screen.getByText('Signals Found')).toBeInTheDocument();
            expect(screen.getAllByText('COMI').length).toBeGreaterThan(0);
            expect(screen.getByText('BUY')).toBeInTheDocument();
        });
    });

    it('starts a scan when Initialize Scan is clicked', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/scanner/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            if (url.includes('/api/v1/scanner/start') && init?.method === 'POST') {
                return { ok: true, json: async () => ({ started: true }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<ScannerPage />);

        const button = await screen.findByRole('button', { name: /Initialize Scan/i });
        fireEvent.click(button);

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/scanner/start?index=ALL&intraday=false'),
                expect.objectContaining({ method: 'POST' })
            );
            expect(screen.getByRole('button', { name: /Starting.../i })).toBeDisabled();
        });
    });

    it('shows fallback API error when scan trigger fails with empty payload', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/scanner/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            if (url.includes('/api/v1/scanner/start') && init?.method === 'POST') {
                return { ok: false, json: async () => ({}) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        render(<ScannerPage />);

        const button = await screen.findByRole('button', { name: /Initialize Scan/i });
        fireEvent.click(button);

        await waitFor(() => {
            expect(screen.getByText('Connection Error')).toBeInTheDocument();
            expect(screen.getByText('Failed to start scan.')).toBeInTheDocument();
        });

        consoleErrorSpy.mockRestore();
    });

    it('shows stale-mode message when readiness gate blocks scanner start', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/scanner/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            if (url.includes('/api/v1/scanner/start') && init?.method === 'POST') {
                return {
                    ok: false,
                    json: async () => ({
                        status: 'stale_mode',
                        message: 'Read-only stale mode is active.',
                        pipeline_state: 'SYNCING',
                    }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        render(<ScannerPage />);

        const button = await screen.findByRole('button', { name: /Initialize Scan/i });
        fireEvent.click(button);

        await waitFor(() => {
            expect(screen.getByText('Read-Only Stale Mode')).toBeInTheDocument();
            expect(screen.getByText('Read-only stale mode is active. (SYNCING)')).toBeInTheDocument();
        });

        consoleErrorSpy.mockRestore();
    });

    it('loads Pine scanner profiles and starts the selected profile', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/scanner/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        profiles: [
                            {
                                profile_id: 7,
                                profile_name: 'EGX Breakout Pine',
                                source_type: 'PINE',
                                market: 'EGX30',
                                timeframe: '1D',
                                profile_state: 'DRAFT',
                            },
                        ],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/scanner/start') && init?.method === 'POST') {
                return { ok: true, json: async () => ({ started: true }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<ScannerPage />);

        await screen.findByRole('option', { name: 'EGX Breakout Pine' });
        const strategySelect = await screen.findByLabelText('Scanner Strategy');
        fireEvent.change(strategySelect, { target: { value: '7' } });

        const button = await screen.findByRole('button', { name: /Initialize Scan/i });
        fireEvent.click(button);

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/scanner/start'),
                expect.objectContaining({ method: 'POST' }),
            );
            const startCall = fetchMock.mock.calls.find(([url, init]) => String(url).includes('/api/v1/scanner/start') && init?.method === 'POST');
            expect(startCall).toBeTruthy();
            expect(String(startCall?.[0])).toContain('profile_id=7');
        });
    });
});
