import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import SimulationPage from './page';

jest.mock('recharts', () => {
    const MockContainer = () => <div data-testid="mock-recharts-container" />;
    return {
        ResponsiveContainer: MockContainer,
        LineChart: MockContainer,
        BarChart: MockContainer,
        Line: () => null,
        Bar: MockContainer,
        XAxis: () => null,
        YAxis: () => null,
        Tooltip: () => null,
        CartesianGrid: () => null,
        Cell: () => null,
    };
});

describe('SimulationPage', () => {
    const basePayload = (url: string) => {
        if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
            return { status: 'success', profiles: [], active_profile_id: null };
        }
        if (url.includes('/api/v1/strategy/price-action/catalog')) {
            return { status: 'success', strategies: [] };
        }
        return {};
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    const waitForInitialSimulationLoads = async () => {
        await waitFor(() => {
            const urls = ((global.fetch as jest.Mock).mock.calls || []).map(([input]) => String(input));
            expect(urls.some((url) => url.includes('/api/v1/replay/status'))).toBe(true);
            expect(urls.some((url) => url.includes('/api/v1/strategy/pine/scanner-profiles'))).toBe(true);
            expect(urls.some((url) => url.includes('/api/v1/strategy/price-action/catalog'))).toBe(true);
        });
        await waitFor(() => expect(screen.getByRole('combobox')).toBeEnabled());
        await act(async () => {
            await Promise.resolve();
        });
    };

    it('renders page header and both tab buttons', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => ({
            ok: true,
            json: async () => basePayload(String(input)),
        } as Response)) as jest.Mock;
        render(<SimulationPage />);
        await waitForInitialSimulationLoads();

        expect(screen.getByRole('heading', { name: /Quant Simulator/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Black Swan Crash/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Ragnarok Total Liquidation/i })).toBeInTheDocument();
    });

    it('runs crash simulation and renders scenario results', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/stress-test') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        data: {
                            crash_date: '2020-03-15',
                            market_impact: -12.8,
                            worst_affected: [{ Ticker: 'COMI', 'Total_Drop_%': -18.2 }],
                            least_affected: [{ Ticker: 'HRHO', Current_Price: 37.2, Final_Price: 35.9, 'Total_Drop_%': -3.5 }],
                        },
                    }),
                } as Response;
            }
            return { ok: true, json: async () => basePayload(url) } as Response;
        }) as jest.Mock;

        render(<SimulationPage />);
        await waitForInitialSimulationLoads();
        fireEvent.click(screen.getByRole('button', { name: /Black Swan Crash/i }));
        fireEvent.click((await screen.findAllByRole('button', { name: /EXECUTE_ANALYSIS/i }))[0]);

        await waitFor(() => {
            expect(screen.getByText('2020-03-15')).toBeInTheDocument();
            expect(screen.getByText('Vulnerability Spectrum')).toBeInTheDocument();
            expect(screen.getByText('Defensive Outliers')).toBeInTheDocument();
            expect(screen.getByText('HRHO')).toBeInTheDocument();
        });
    });

    it('runs ragnarok simulation and renders result cards', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/ragnarok') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        data: {
                            expected_value: 1050000,
                            var_95: 820000,
                            loss_probability: 20,
                            ruin_probability: 15.5,
                            ruin_threshold_pct: 50,
                            ruin_floor: 500000,
                            starting_value: 1000000,
                            iterations: 1000,
                            days: 20,
                            assets_count: 5,
                            assets_used: ['COMI', 'HRHO'],
                            plot_paths: [[1000000, 1020000, 1040000], [1000000, 980000, 940000]],
                        },
                    }),
                } as Response;
            }
            return { ok: true, json: async () => basePayload(url) } as Response;
        }) as jest.Mock;

        render(<SimulationPage />);
        await waitForInitialSimulationLoads();
        fireEvent.click(screen.getByRole('button', { name: /Ragnarok Total Liquidation/i }));
        fireEvent.click((await screen.findAllByRole('button', { name: /EXECUTE_ANALYSIS/i }))[0]);

        await waitFor(() => {
            expect(screen.getByText('Expected Value')).toBeInTheDocument();
            expect(screen.getByText('95% VaR Floor')).toBeInTheDocument();
            expect(screen.getByText('1000 Paths')).toBeInTheDocument();
            expect(screen.getByText('Probabilistic Trajectories')).toBeInTheDocument();
        });
    });

    it('selects different index for crash simulator', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => ({
            ok: true,
            json: async () => basePayload(String(input)),
        } as Response)) as jest.Mock;

        render(<SimulationPage />);
        await waitForInitialSimulationLoads();
        fireEvent.click(screen.getByRole('button', { name: /Black Swan Crash/i }));

        const egx70Button = await screen.findByRole('button', { name: 'EGX70' });
        fireEvent.click(egx70Button);
        expect(egx70Button).toHaveClass('text-red-400');
    });
});
