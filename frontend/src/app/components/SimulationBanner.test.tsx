import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import SimulationBanner from './SimulationBanner';

let latestPollingCallback: (() => Promise<void> | void) | null = null;

jest.mock('@/hooks/usePolling', () => ({
    usePolling: (cb: () => Promise<void> | void) => {
        latestPollingCallback = cb;
    },
}));

describe('SimulationBanner', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        latestPollingCallback = null;
    });

    it('does not render when simulation is inactive', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/simulate/status')) {
                return { ok: true, json: async () => ({ active: false, date: null }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { container } = render(<SimulationBanner />);
        await act(async () => {
            await latestPollingCallback?.();
        });

        await waitFor(() => {
            expect(container.firstChild).toBeNull();
        });
    });

    it('renders active banner and date when simulation is active', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/simulate/status')) {
                return { ok: true, json: async () => ({ active: true, date: '2024-01-15' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<SimulationBanner />);
        await act(async () => {
            await latestPollingCallback?.();
        });

        await waitFor(() => {
            expect(screen.getByText('Time Travel Active')).toBeInTheDocument();
            expect(screen.getByText(/Viewing market state as of/i)).toBeInTheDocument();
            expect(screen.getByText('2024-01-15')).toBeInTheDocument();
        });
    });

    it('stops simulation and reloads when Exit Simulation is clicked', async () => {
        const removeItemSpy = jest.spyOn(Storage.prototype, 'removeItem');
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/simulate/status')) {
                return { ok: true, json: async () => ({ active: true, date: '2024-01-15' }) } as Response;
            }
            if (url.includes('/api/v1/simulate/stop') && init?.method === 'POST') {
                return { ok: true, json: async () => ({ status: 'stopped' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<SimulationBanner />);
        await act(async () => {
            await latestPollingCallback?.();
        });

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /Exit Simulation/i })).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Exit Simulation/i }));

        await waitFor(() => {
            expect(removeItemSpy).toHaveBeenCalledWith('horus.dashboard.cache.v1');
        });

        consoleErrorSpy.mockRestore();
        removeItemSpy.mockRestore();
    });

    it('suppresses expected offline polling errors', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        global.fetch = jest.fn(async () => {
            throw new TypeError('Failed to fetch');
        }) as jest.Mock;

        const { container } = render(<SimulationBanner />);
        await act(async () => {
            await latestPollingCallback?.();
        });

        await waitFor(() => {
            expect(container.firstChild).toBeNull();
        });
        expect(consoleErrorSpy).not.toHaveBeenCalled();
        consoleErrorSpy.mockRestore();
    });
});
