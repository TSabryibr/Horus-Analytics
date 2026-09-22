import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import StrategyPage from './page';

// ── Mock recharts ────────────────────────────────────────────────────────────
jest.mock('recharts', () => ({
    AreaChart: ({ children }: any) => <div data-testid="area-chart">{children}</div>,
    Area: () => null,
    XAxis: () => null,
    YAxis: () => null,
    Tooltip: () => null,
    ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
}));

// ── Helpers ──────────────────────────────────────────────────────────────────
const refreshStrategy = jest.fn();
const priceActionCatalog = {
    status: 'success',
    count: 2,
    counts_by_family: { SWING: 2 },
    strategies: [
        {
            strategy_id: 'ascending_triangle_breakout',
            display_name: 'Ascending Triangle Breakout',
            family: 'SWING',
            summary: 'Bullish continuation through flat resistance.',
            regime: 'BULLISH_CONTINUATION',
            status: 'DRAFT',
            warning_only: false,
            long_entry_allowed: true,
            required_data: ['daily_ohlcv'],
            entry_conditions: ['Breakout close'],
            confirmation_conditions: ['Volume'],
            avoidance_rules: ['Immediate failure'],
            exit_rules: ['ATR stop'],
            risk_model: 'STRUCTURAL_STOP',
            source_attributions: [],
        },
        {
            strategy_id: 'failed_breakout_warning',
            display_name: 'Failed Breakout Rejection',
            family: 'SWING',
            summary: 'Warning-only breakout failure.',
            regime: 'FAILED_CONTINUATION',
            status: 'DRAFT',
            warning_only: true,
            long_entry_allowed: false,
            required_data: ['daily_ohlcv'],
            entry_conditions: ['Failure'],
            confirmation_conditions: ['Rejection'],
            avoidance_rules: ['Avoid'],
            exit_rules: ['Warning only'],
            risk_model: 'WARNING_ONLY',
            source_attributions: [],
        },
    ],
};

const proposal = {
    regime: 'BULLISH',
    regime_score: 8.4,
    volatility: 'ELEVATED',
    volatility_value: 2.1,
    reasoning: 'Momentum and breadth are aligned.',
    changes: [
        { parameter: 'RSI_MIN', old_value: 55, new_value: 58, changed: true },
        { parameter: 'SL_PCT', old_value: 1.5, new_value: 1.5, changed: false },
    ],
};

function mockContext(overrides: Record<string, any> = {}) {
    return {
        strategy: proposal,
        strategyLoading: false,
        refreshStrategy,
        ...overrides,
    };
}

let contextValue = mockContext();

jest.mock('../context/GlobalDataContext', () => ({
    useStrategyData: () => contextValue,
}));

// ── Tests ────────────────────────────────────────────────────────────────────
describe('StrategyPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        contextValue = mockContext();
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/price-action/catalog')) {
                return {
                    ok: true,
                    text: async () => JSON.stringify(priceActionCatalog),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/apply')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'applied' }),
                } as Response;
            }
            return {
                ok: true,
                json: async () => ({ status: 'success' }),
                text: async () => JSON.stringify({ status: 'success' }),
            } as Response;
        }) as jest.Mock;
    });

    // ─── Rendering & Data Display ────────────────────────────────────────
    it('renders regime, volatility, reasoning, and proposed changes', async () => {
        render(<StrategyPage />);

        await screen.findByText('Price Action Lab');

        expect(screen.getByText('Strategy Configuration')).toBeInTheDocument();
        expect(screen.getByText('BULLISH')).toBeInTheDocument();
        expect(screen.getByText('Score: 8.4/10')).toBeInTheDocument();
        expect(screen.getByText('ELEVATED')).toBeInTheDocument();
        expect(screen.getByText('2.1%')).toBeInTheDocument();
        expect(screen.getByText(/Momentum and breadth are aligned\./)).toBeInTheDocument();
        // Proposed changes
        expect(screen.getByText('RSI_MIN')).toBeInTheDocument();
        expect(screen.getByText('58')).toBeInTheDocument();
        expect(screen.getByText('Price Action Lab')).toBeInTheDocument();
    });

    it('shows "Apply Strategy Changes" button when changes exist', async () => {
        render(<StrategyPage />);

        expect(await screen.findByText('Apply Strategy Changes')).toBeInTheDocument();
    });

    it('shows "System is already optimized" when no changes are flagged', async () => {
        contextValue = mockContext({
            strategy: {
                ...proposal,
                changes: [
                    { parameter: 'RSI_MIN', old_value: 55, new_value: 55, changed: false },
                    { parameter: 'SL_PCT', old_value: 1.5, new_value: 1.5, changed: false },
                ],
            },
        });
        render(<StrategyPage />);

        expect(await screen.findByText('System is already optimized')).toBeInTheDocument();
    });

    // ─── Manual Mode ────────────────────────────────────────────────────
    it('toggles between AI Mode and Manual Mode', async () => {
        render(<StrategyPage />);

        expect(await screen.findByText('Proposed Laws (Parameters)')).toBeInTheDocument();

        // Switch to Manual
        fireEvent.click(screen.getByRole('button', { name: /AI Mode/i }));

        expect(screen.getByText('Manual Overrides')).toBeInTheDocument();
        expect(screen.getByText('Apply Manual Overrides')).toBeInTheDocument();
    });

    it('applies manual overrides and shows success toast', async () => {
        (global.fetch as jest.Mock).mockImplementation(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/price-action/catalog')) {
                return {
                    ok: true,
                    text: async () => JSON.stringify(priceActionCatalog),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/apply')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'success' }),
                } as Response;
            }
            return {
                ok: true,
                json: async () => ({ status: 'success' }),
                text: async () => JSON.stringify({ status: 'success' }),
            } as Response;
        });

        render(<StrategyPage />);

        await screen.findByText('Price Action Lab');
        fireEvent.click(screen.getByRole('button', { name: /AI Mode/i }));
        fireEvent.click(screen.getByRole('button', { name: /Apply Manual Overrides/i }));

        await waitFor(() => {
            expect(screen.getByText('Manual Overrides Applied!')).toBeInTheDocument();
        });

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/strategy/apply'),
            expect.objectContaining({ method: 'POST' })
        );
    });

    // ─── Apply in AI Mode ───────────────────────────────────────────────
    it('applies AI proposal and shows success toast', async () => {
        render(<StrategyPage />);

        await screen.findByText('Price Action Lab');
        fireEvent.click(screen.getByRole('button', { name: /Apply Strategy Changes/i }));

        await waitFor(() => {
            expect(screen.getByText('Strategy Updated Successfully! Fenrir is active.')).toBeInTheDocument();
        });

        const fetchCall = (global.fetch as jest.Mock).mock.calls.find(([input]) => String(input).includes('/api/v1/strategy/apply'));
        expect(fetchCall).toBeDefined();
        const requestInit = fetchCall[1] as RequestInit;
        const requestBody = JSON.parse(String(requestInit.body ?? '{}'));
        expect(requestBody).toEqual({
            params: {
                RSI_MIN: 58,
            },
        });
    });

    // ─── Error Paths ────────────────────────────────────────────────────
    it('shows error toast when API returns failure', async () => {
        (global.fetch as jest.Mock).mockImplementation(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/price-action/catalog')) {
                return {
                    ok: true,
                    text: async () => JSON.stringify(priceActionCatalog),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/apply')) {
                return {
                    ok: false,
                    json: async () => ({ detail: 'Validation failed.' }),
                } as Response;
            }
            return {
                ok: true,
                json: async () => ({ status: 'success' }),
                text: async () => JSON.stringify({ status: 'success' }),
            } as Response;
        });

        render(<StrategyPage />);

        await screen.findByText('Price Action Lab');
        fireEvent.click(screen.getByRole('button', { name: /Apply Strategy Changes/i }));

        await waitFor(() => {
            expect(screen.getByText('Validation failed.')).toBeInTheDocument();
        });
    });

    it('shows network error toast when fetch throws', async () => {
        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        (global.fetch as jest.Mock).mockImplementation(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/price-action/catalog')) {
                return {
                    ok: true,
                    text: async () => JSON.stringify(priceActionCatalog),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/apply')) {
                throw new TypeError('Failed to fetch');
            }
            return {
                ok: true,
                json: async () => ({ status: 'success' }),
                text: async () => JSON.stringify({ status: 'success' }),
            } as Response;
        });

        render(<StrategyPage />);

        await screen.findByText('Price Action Lab');
        fireEvent.click(screen.getByRole('button', { name: /Apply Strategy Changes/i }));

        await waitFor(() => {
            expect(screen.getByText('Network error while applying strategy changes.')).toBeInTheDocument();
        });
        errorSpy.mockRestore();
    });

    it('runs a price-action backtest from the lab surface', async () => {
        (global.fetch as jest.Mock).mockImplementation(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/price-action/catalog')) {
                return {
                    ok: true,
                    text: async () => JSON.stringify(priceActionCatalog),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/price-action/backtest')) {
                return {
                    ok: true,
                    text: async () => JSON.stringify({
                        status: 'success',
                        config: {
                            strategy_id: 'ascending_triangle_breakout',
                            strategy_name: 'Ascending Triangle Breakout',
                            market: 'EGX30',
                            timeframe: '1D',
                            date_from: '2025-01-01',
                            date_to: '2025-12-31',
                            capital: 100000,
                            commission_pct: 0.05,
                            slippage_pct: 0.1,
                        },
                        compatibility: {
                            readiness: 'READY',
                            compatibility_score: 85,
                            messages: ['ok'],
                        },
                        metrics: {
                            trade_count: 4,
                            win_rate: 75,
                            total_return: 12.5,
                            final_value: 112500,
                            max_drawdown: 3.2,
                            profit_factor: 1.8,
                            expectancy: 2500,
                            liquidity_coverage: 0.9,
                            warning_conflict_rate: 0.1,
                            evaluated_tickers: 5,
                        },
                        ranking: {
                            performance_score: 80,
                            alignment_score: 75,
                            combined_score: 78,
                            recommended: true,
                        },
                        promotion_summary: {
                            profile_state: 'READY',
                            failed_gates: [],
                            thresholds: {},
                            actuals: {},
                        },
                        trades: [],
                    }),
                } as Response;
            }
            return {
                ok: true,
                json: async () => ({ status: 'applied' }),
                text: async () => JSON.stringify({ status: 'applied' }),
            } as Response;
        });

        render(<StrategyPage />);

        await screen.findByText('Price Action Lab');
        fireEvent.click(await screen.findByRole('button', { name: /Backtest/i }));

        await waitFor(() => {
            expect(screen.getByText((content) => content.includes('12.50%'))).toBeInTheDocument();
            expect(screen.getByText('Backtest completed for Ascending Triangle Breakout.')).toBeInTheDocument();
        });
    });

    // ─── Refresh ────────────────────────────────────────────────────────
    it('triggers strategy refresh from header action', async () => {
        render(<StrategyPage />);

        await screen.findByText('Price Action Lab');
        // The refresh button is the second button (first is the mode toggle)
        const buttons = screen.getAllByRole('button');
        const refreshBtn = buttons.find(b => !b.textContent?.includes('Mode') && !b.textContent?.includes('Unleash') && !b.textContent?.includes('Apply'));
        expect(refreshBtn).toBeDefined();

        fireEvent.click(refreshBtn!);
        expect(refreshStrategy).toHaveBeenCalledTimes(1);
    });
});
