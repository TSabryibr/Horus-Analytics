import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

import SystemBootOverlay from './SystemBootOverlay';
import { OPEN_SYSTEM_BOOT_EVENT, SYSTEM_BOOT_SESSION_KEY } from './systemBootModel';

const mockUsePathname = jest.fn();

jest.mock('next/navigation', () => ({
    usePathname: () => mockUsePathname(),
}));

jest.mock('next/image', () => {
    function MockNextImage({ alt, ...props }: { alt: string }) {
        return <img alt={alt} {...props} />;
    }
    return MockNextImage;
});

jest.mock('framer-motion', () => ({
    AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    motion: {
        div: ({
            children,
            animate,
            exit,
            initial,
            transition,
            whileHover,
            whileTap,
            ...props
        }: React.HTMLAttributes<HTMLDivElement> & Record<string, unknown>) => <div {...props}>{children}</div>,
        button: ({
            children,
            animate,
            exit,
            initial,
            transition,
            whileHover,
            whileTap,
            ...props
        }: React.ButtonHTMLAttributes<HTMLButtonElement> & Record<string, unknown>) => <button {...props}>{children}</button>,
    },
}));

function makeResponse(body: unknown) {
    return Promise.resolve({
        ok: true,
        json: async () => body,
    });
}

function makeReadyPayload(overrides: Record<string, unknown> = {}) {
    return {
        system_ready: true,
        message: 'System Operational',
        pipeline_state: 'FRESH',
        db_connected: true,
        freshness: { market_open: true },
        data_status: {
            status: 'OK',
            history: {
                ok: true,
                status: 'FRESH',
                kpis: { symbol_count: 84 },
            },
            intraday: {
                ok: true,
                status: 'LIVE',
                age_mins: 1,
            },
        },
        scheduler: {
            running: true,
            jobs: [{ id: 'sync' }],
        },
        telegram: {
            enabled: false,
            configured: false,
        },
        metrics: {
            total_signals: 104,
        },
        timestamp: '2026-03-31T09:12:00Z',
        ...overrides,
    };
}

describe('SystemBootOverlay', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockUsePathname.mockReturnValue('/');
        window.localStorage.clear();
        window.sessionStorage.clear();
        global.fetch = jest.fn();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    it('skips rendering for returning sessions on the home route', async () => {
        window.sessionStorage.setItem(SYSTEM_BOOT_SESSION_KEY, 'true');

        render(<SystemBootOverlay />);

        await waitFor(() => {
            expect(screen.queryByText(/Operational Boot Console/i)).not.toBeInTheDocument();
        });
    });

    it('does not render away from the home route', () => {
        mockUsePathname.mockReturnValue('/scanner');

        render(<SystemBootOverlay />);

        expect(screen.queryByText(/Operational Boot Console/i)).not.toBeInTheDocument();
    });

    it('lets the user enter the system once readiness checks pass', async () => {
        (global.fetch as jest.Mock).mockImplementation(() => makeResponse(makeReadyPayload()));

        render(<SystemBootOverlay />);

        const enterButton = await screen.findByRole('button', { name: /enter system/i });
        fireEvent.click(enterButton);

        await waitFor(() => {
            expect(window.sessionStorage.getItem(SYSTEM_BOOT_SESSION_KEY)).toBe('true');
            expect(screen.queryByText(/Operational Boot Console/i)).not.toBeInTheDocument();
        });
    });

    it('uses the lightweight boot-status health surface during startup', async () => {
        (global.fetch as jest.Mock).mockImplementation(() => makeResponse(makeReadyPayload()));

        render(<SystemBootOverlay />);

        await screen.findByRole('button', { name: /enter system/i });

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/system/boot-status'),
            expect.objectContaining({
                cache: 'no-store',
                signal: expect.any(AbortSignal),
            })
        );
    });

    it('stops the recurring poll loop once the console reaches a resolved ready state', async () => {
        jest.useFakeTimers();
        (global.fetch as jest.Mock).mockImplementation(() => makeResponse(makeReadyPayload()));

        render(<SystemBootOverlay />);

        await screen.findByRole('button', { name: /enter system/i });
        expect(global.fetch).toHaveBeenCalledTimes(1);

        await act(async () => {
            jest.advanceTimersByTime(4500);
        });

        expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('renders the Horus logo while the boot console is visible', async () => {
        (global.fetch as jest.Mock).mockImplementation(() => makeResponse(makeReadyPayload()));

        render(<SystemBootOverlay />);

        expect(await screen.findByAltText(/horus logo/i)).toBeInTheDocument();
    });

    it('advances progress while waiting for the first health sample', async () => {
        jest.useFakeTimers();
        (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => undefined));

        render(<SystemBootOverlay />);

        expect(await screen.findByText('12%')).toBeInTheDocument();

        await act(async () => {
            jest.advanceTimersByTime(1800);
        });

        await waitFor(() => {
            expect(screen.queryByText('12%')).not.toBeInTheDocument();
        });
    });

    it('falls back to an offline state when the first health sample times out', async () => {
        jest.useFakeTimers();
        (global.fetch as jest.Mock).mockImplementation((_url: string, options?: { signal?: AbortSignal }) => new Promise((_resolve, reject) => {
            options?.signal?.addEventListener('abort', () => {
                reject(new DOMException('The operation was aborted.', 'AbortError'));
            });
        }));

        render(<SystemBootOverlay />);

        await act(async () => {
            await jest.advanceTimersByTimeAsync(40000);
        });

        expect((await screen.findAllByText(/console offline/i)).length).toBeGreaterThan(0);
        expect(screen.getByRole('button', { name: /retry checks/i })).toBeInTheDocument();
    });

    it('shows degraded entry when a non-fatal check slips', async () => {
        (global.fetch as jest.Mock).mockImplementation(() => makeResponse(makeReadyPayload({
            system_ready: false,
            pipeline_state: 'STALE',
            data_status: {
                status: 'OK',
                history: {
                    ok: true,
                    status: 'FRESH',
                    kpis: { symbol_count: 84 },
                },
                intraday: {
                    ok: false,
                    status: 'STALE',
                    age_mins: 32,
                },
            },
        })));

        render(<SystemBootOverlay />);

        await waitFor(() => {
            expect(screen.getByText(/degraded entry available/i)).toBeInTheDocument();
        });

        expect(await screen.findByRole('button', { name: /enter degraded/i })).toBeInTheDocument();
        expect(screen.getAllByText(/intraday feed delayed/i).length).toBeGreaterThan(0);
    });

    it('automatically retries checks after a startup failure', async () => {
        (global.fetch as jest.Mock)
            .mockRejectedValueOnce(new Error('Backend unreachable'))
            .mockImplementation(() => makeResponse(makeReadyPayload()));

        render(<SystemBootOverlay />);

        await act(async () => {
            await new Promise((resolve) => window.setTimeout(resolve, 1300));
        });

        expect(await screen.findByRole('button', { name: /enter system/i })).toBeInTheDocument();
    });

    it('supports manual reopen even after the session marker is set', async () => {
        window.sessionStorage.setItem(SYSTEM_BOOT_SESSION_KEY, 'true');
        (global.fetch as jest.Mock).mockImplementation(() => makeResponse(makeReadyPayload()));

        render(<SystemBootOverlay />);

        await waitFor(() => {
            expect(screen.queryByText(/Operational Boot Console/i)).not.toBeInTheDocument();
        });

        fireEvent(window, new Event(OPEN_SYSTEM_BOOT_EVENT));

        expect(await screen.findByText(/manual inspection/i)).toBeInTheDocument();
        expect(await screen.findByRole('button', { name: /enter system/i })).toBeInTheDocument();
    });
});
