import React from 'react';
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import OptimizationPage from './page';

const mockUsePolling = jest.fn();

jest.mock('@/hooks/usePolling', () => ({
    usePolling: (...args: unknown[]) => mockUsePolling(...args),
}));

jest.mock('../components/charts/OptimizationEquityChart', () => {
    function MockOptimizationEquityChart() {
        return <div data-testid="mock-optimization-chart" />;
    }
    return MockOptimizationEquityChart;
});

const backtestSuccessPayload = {
    metrics: {
        total_return: 12.34,
        final_value: 224680,
        trade_count: 18,
    },
    equity_curve: [
        { date: '2025-01-01', equity: 200000 },
        { date: '2025-02-01', equity: 208000 },
        { date: '2025-03-01', equity: 224680 },
    ],
};

async function openPineLabAndWaitForEmptyRegistry() {
    fireEvent.click(screen.getByRole('button', { name: /Pine Lab/i }));

    await waitFor(() => {
        expect(screen.getByText(/Profile Registry/i)).toBeInTheDocument();
        expect(screen.getByText(/No Pine scanner profiles match this filter yet./i)).toBeInTheDocument();
    });
}

describe('OptimizationPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockUsePolling.mockClear();
        window.history.pushState({}, '', '/optimization');
        jest.spyOn(console, 'error').mockImplementation((...args) => {
            const [firstArg] = args;
            if (typeof firstArg === 'string' && firstArg.includes('not wrapped in act')) {
                return;
            }
        });
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    it('disables optimizer polling when page loads in Backtester mode', () => {
        global.fetch = jest.fn(async () => ({ ok: true, json: async () => ({ status: 'IDLE' }) } as Response)) as jest.Mock;
        render(<OptimizationPage />);
        expect(mockUsePolling).toHaveBeenCalledWith(
            expect.any(Function),
            expect.objectContaining({ enabled: false })
        );
    });

    it('runs simulator and renders KPI cards on success', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/backtest') && init?.method === 'POST') {
                return { ok: true, json: async () => backtestSuccessPayload } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        fireEvent.click(screen.getByRole('button', { name: /Init_Backtest/i }));

        await waitFor(() => {
            expect(screen.getByText('Total_Yield')).toBeInTheDocument();
            expect(screen.getByText('+12.34%')).toBeInTheDocument();
            expect(screen.getByText('Apply_Config')).toBeInTheDocument();
        });
    });

    it('loads Pine profiles in Backtester mode, requires a selection, and warns on DRAFT profiles', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [
                            {
                                profile_id: 7,
                                profile_name: 'Draft Pine Breakout',
                                profile_state: 'DRAFT',
                                market: 'EGX70',
                                timeframe: '1W',
                            },
                            {
                                profile_id: 8,
                                profile_name: 'Ready Pine Trend',
                                profile_state: 'READY',
                                market: 'EGX30',
                                timeframe: '1D',
                            },
                        ],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            if (url.includes('/api/v1/strategy/backtest') && init?.method === 'POST') {
                return { ok: true, json: async () => backtestSuccessPayload } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<OptimizationPage />);

        fireEvent.click(screen.getByRole('button', { name: /Pine Profile/i }));

        await waitFor(() => {
            expect(screen.getByLabelText(/Saved Pine Profile/i)).toBeInTheDocument();
            expect(screen.getByText(/Draft Pine Breakout/i)).toBeInTheDocument();
        });

        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/strategy/pine/scanner-profiles'))).toHaveLength(1);
        expect(screen.getByRole('button', { name: /Init_Backtest/i })).toBeDisabled();

        fireEvent.change(screen.getByLabelText(/Saved Pine Profile/i), { target: { value: '7' } });

        await waitFor(() => {
            expect(screen.getByText(/Draft profile: this Pine strategy has not passed promotion gates yet./i)).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /Init_Backtest/i })).not.toBeDisabled();
            expect(screen.getByDisplayValue('EGX70')).toBeInTheDocument();
            expect(screen.getByDisplayValue('1W')).toBeInTheDocument();
        });
    });

    it('runs the selected Pine profile from Backtester mode and labels Pine-sourced results', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [
                            {
                                profile_id: 7,
                                profile_name: 'Draft Pine Breakout',
                                profile_state: 'DRAFT',
                                market: 'EGX70',
                                timeframe: '1W',
                            },
                        ],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/scanner-profile/7')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        profile: {
                            profile_id: 7,
                            profile_name: 'Draft Pine Breakout',
                            profile_state: 'DRAFT',
                            market: 'EGX70',
                            timeframe: '1W',
                        },
                        script_source: '//@version=5\nstrategy("Draft Pine Breakout")',
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/backtest') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        metrics: {
                            total_return: 6.2,
                            final_value: 106200,
                            trade_count: 5,
                        },
                        compatibility: {
                            readiness: 'READY',
                            compatibility_score: 92,
                        },
                        rankings: {
                            performance_score: 78,
                            combined_score: 62,
                        },
                        alignment: {
                            alignment_score: 25,
                        },
                        equity_curve: [{ date: '2026-01-01', equity: 100000 }],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<OptimizationPage />);

        fireEvent.click(screen.getByRole('button', { name: /Pine Profile/i }));

        await waitFor(() => {
            expect(screen.getByLabelText(/Saved Pine Profile/i)).toBeInTheDocument();
            expect(screen.getByText(/Draft Pine Breakout/i)).toBeInTheDocument();
        });

        fireEvent.change(screen.getByLabelText(/Saved Pine Profile/i), { target: { value: '7' } });

        await waitFor(() => {
            expect(screen.getByText(/Draft profile: this Pine strategy has not passed promotion gates yet./i)).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /Init_Backtest/i })).not.toBeDisabled();
        });

        fireEvent.click(screen.getByRole('button', { name: /Init_Backtest/i }));

        await waitFor(() => {
            expect(screen.getByText(/Backtest Source: Pine Profile/i)).toBeInTheDocument();
            expect(screen.getByText(/Profile: Draft Pine Breakout/i)).toBeInTheDocument();
            expect(screen.getByText(/Profile State: DRAFT/i)).toBeInTheDocument();
            expect(screen.getByText(/Pine Research Summary/i)).toBeInTheDocument();
            expect(screen.getByText(/Readiness: READY/i)).toBeInTheDocument();
            expect(screen.getByText(/Compatibility: 92.00/i)).toBeInTheDocument();
            expect(screen.getByText(/Performance: 78.00/i)).toBeInTheDocument();
            expect(screen.getByText(/Alignment: 25.00/i)).toBeInTheDocument();
            expect(screen.getByText(/Combined: 62.00/i)).toBeInTheDocument();
            expect(screen.getByText(/\+6.20%/i)).toBeInTheDocument();
            expect(screen.queryByRole('button', { name: /Apply_Config/i })).not.toBeInTheDocument();
        });

        const pineBacktestCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/api/v1/strategy/pine/backtest'));
        expect(pineBacktestCall).toBeTruthy();
        expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/strategy/pine/scanner-profile/7'))).toBe(true);

        const pinePayload = JSON.parse(String((pineBacktestCall?.[1] as RequestInit)?.body ?? '{}'));
        expect(pinePayload).toEqual({
            script_source: '//@version=5\nstrategy("Draft Pine Breakout")',
            market: 'EGX70',
            timeframe: '1W',
            date_from: expect.any(String),
            date_to: expect.any(String),
            capital: 100000,
            commission_pct: 0.05,
            slippage_pct: 0.1,
        });
    });

    it('shows simulator error banner when backtest fails', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/backtest') && init?.method === 'POST') {
                return { ok: false, json: async () => ({ message: 'Simulation failed on backend.' }) } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        fireEvent.click(screen.getByRole('button', { name: /Init_Backtest/i }));

        await waitFor(() => {
            expect(screen.getByText('Simulation failed on backend.')).toBeInTheDocument();
        });

        consoleErrorSpy.mockRestore();
    });

    it('opens confirm dialog and applies settings from simulator', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/backtest') && init?.method === 'POST') {
                return { ok: true, json: async () => backtestSuccessPayload } as Response;
            }
            if (url.includes('/api/v1/strategy/apply') && init?.method === 'POST') {
                return { ok: true, json: async () => ({ status: 'success' }) } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        fireEvent.click(screen.getByRole('button', { name: /Init_Backtest/i }));

        await waitFor(() => {
            expect(screen.getByText('Apply_Config')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Apply_Config/i }));

        await waitFor(() => {
            expect(screen.getByText('Overwrite system settings?')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /Apply Settings/i })).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Apply Settings/i }));

        await waitFor(() => {
            expect(screen.getByText('Settings applied successfully.')).toBeInTheDocument();
        });
    });

    it('shows optimizer start error in Genetic AI mode when start fails', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/start') && init?.method === 'POST') {
                return { ok: false, json: async () => ({ detail: 'Optimizer is unavailable.' }) } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        fireEvent.click(screen.getByRole('button', { name: /AI Optimizer/i }));
        fireEvent.click(screen.getByRole('button', { name: /Execute_Optimization/i }));

        await waitFor(() => {
            expect(screen.getByText('Optimizer is unavailable.')).toBeInTheDocument();
        });

        consoleErrorSpy.mockRestore();
    });

    it('backtests an optimizer candidate in Strategy Lab when Test_Matrix is selected', async () => {
        window.history.pushState({}, '', '/optimization?mode=OPTIMIZER');
        mockUsePolling.mockImplementation((callback: () => Promise<void>, options: { enabled?: boolean }) => {
            if (options.enabled) {
                void callback();
            }
        });
        const candidateParams = {
            RSI_MIN: 45,
            RSI_MAX: 80,
            VOL_SPIKE: 2.0,
            MOMENTUM: 3.0,
            SL_PCT: 2.0,
            TP1_PCT: 6.0,
            MAX_POSITIONS: 5,
            TRAILING_STOP_ENABLED: true,
            TRAILING_STOP_TYPE: 'PERCENT',
            TRAILING_STOP_VALUE: 2.5,
        };
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/status')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'COMPLETED',
                        progress: 100,
                        result: [
                            {
                                score: 88.4,
                                win_rate: 61.2,
                                avg_return: 2.4,
                                trades: 27,
                                params: candidateParams,
                            },
                        ],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/backtest') && init?.method === 'POST') {
                return { ok: true, json: async () => backtestSuccessPayload } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<OptimizationPage />);

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /Test_Matrix/i })).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Test_Matrix/i }));

        await waitFor(() => {
            expect(screen.getByText('+12.34%')).toBeInTheDocument();
        });

        const backtestCall = fetchMock.mock.calls.find(([input, init]) =>
            String(input).includes('/api/v1/strategy/backtest') && init?.method === 'POST'
        );
        expect(backtestCall).toBeTruthy();
        const body = JSON.parse(String((backtestCall?.[1] as RequestInit)?.body ?? '{}'));
        expect(body.params).toEqual(candidateParams);
    });

    it('renders cost model assumptions returned by backtest', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/backtest') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        ...backtestSuccessPayload,
                        assumptions: { commission_pct: 0.05, slippage_pct: 0.5 }
                    })
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);
        fireEvent.click(screen.getByRole('button', { name: /Init_Backtest/i }));

        await waitFor(() => {
            expect(screen.getByText(/COMM_MODEL: 0.05%/i)).toBeInTheDocument();
            expect(screen.getByText(/SLIP_TARGET: 0.50%/i)).toBeInTheDocument();
        });
    });

    it('runs Pine preflight and Pine backtest from Pine Lab mode', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/preflight') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        script_type: 'STRATEGY',
                        readiness: 'READY',
                        compatibility_score: 92,
                        detected_entries: ['strategy.entry('],
                        detected_exits: ['strategy.close('],
                        unsupported_features: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/backtest') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        config: { market: 'EGX30', capital: 100000 },
                        metrics: { total_return: 8.5, final_value: 108500, trade_count: 4, win_rate: 75 },
                        compatibility: { readiness: 'READY', compatibility_score: 92 },
                        alignment: { alignment_score: 25 },
                        rankings: { performance_score: 78, combined_score: 62 },
                        equity_curve: [{ date: '2025-01-01', equity: 100000 }],
                        trades: [{ ticker: 'COMI', pnl: 1200 }],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        await openPineLabAndWaitForEmptyRegistry();

        fireEvent.change(screen.getByLabelText(/Pine Script Source/i), {
            target: {
                value: '//@version=5\nstrategy("Fast Slow")\nstrategy.entry("Long", strategy.long)\nstrategy.close("Long")',
            },
        });
        fireEvent.change(screen.getByLabelText(/Profile Name/i), {
            target: { value: 'EGX Breakout Pine' },
        });

        fireEvent.click(screen.getByRole('button', { name: /Run Preflight/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/Readiness: READY/i).length).toBeGreaterThan(0);
            expect(screen.getAllByText(/Compatibility Score: 92/i).length).toBeGreaterThan(0);
        });

        fireEvent.click(screen.getByRole('button', { name: /Run Pine Backtest/i }));

        await waitFor(() => {
            expect(screen.getByText(/Pine Return/i)).toBeInTheDocument();
            expect(screen.getByText(/\+8.50%/i)).toBeInTheDocument();
            expect(screen.getAllByText(/Combined Score/i).length).toBeGreaterThan(0);
            expect(screen.getAllByText(/62.00/i).length).toBeGreaterThan(0);
        });
    });

    it('runs Pine logic import preview from Pine Lab mode and renders the review draft', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/import-preview') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        import_mode: 'LOGIC_IMPORT',
                        review_status: 'READY_FOR_REVIEW',
                        translation: {
                            mode: 'DETERMINISTIC_DRAFT',
                            provider: 'LOCAL',
                            fallback_used: true,
                        },
                        reduced_source_pack: {
                            candidate_signals: [{ role: 'long_entry', name: 'longE' }],
                        },
                        ignored_sections: [{ kind: 'plot', line: 7, source: 'plot(fast)' }],
                        rule_spec: {
                            human_summary: {
                                long_entry: 'Derived from Pine variable `longE`: ta.crossover(fast, slow)',
                            },
                            signals: {
                                long_entry: { source_name: 'longE', status: 'mapped' },
                                short_entry: { source_name: null, status: 'missing' },
                                long_exit: { source_name: 'longX', status: 'mapped' },
                                short_exit: { source_name: null, status: 'missing' },
                            },
                            warnings: ['Using deterministic draft translation. Review the generated rule spec before any backtest.'],
                            traceability: [{ role: 'long_entry', source_name: 'longE', line: 4 }],
                        },
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<OptimizationPage />);

        await openPineLabAndWaitForEmptyRegistry();

        fireEvent.change(screen.getByLabelText(/Pine Script Source/i), {
            target: {
                value: '//@version=5\nindicator("Import")\nfast = ta.ema(close, 9)\nslow = ta.ema(close, 21)\nlongE = ta.crossover(fast, slow)\nlongX = ta.crossunder(fast, slow)\nplot(fast)',
            },
        });

        fireEvent.click(screen.getByRole('button', { name: /Logic Import/i }));
        fireEvent.click(screen.getByRole('button', { name: /Extract Rule Spec/i }));

        await waitFor(() => {
            expect(screen.getByText(/Review Status/i)).toBeInTheDocument();
            expect(screen.getByText(/READY_FOR_REVIEW/i)).toBeInTheDocument();
            expect(screen.getAllByText(/Derived from Pine variable `longE`/i).length).toBeGreaterThan(0);
            expect(screen.getByText(/Ignored Pine Sections/i)).toBeInTheDocument();
            expect(screen.getAllByText(/plot\(fast\)/i).length).toBeGreaterThan(0);
        });

        const importCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/api/v1/strategy/pine/import-preview'));
        expect(importCall).toBeTruthy();
        expect(JSON.parse(String((importCall?.[1] as RequestInit)?.body ?? '{}'))).toEqual({
            script_source: '//@version=5\nindicator("Import")\nfast = ta.ema(close, 9)\nslow = ta.ema(close, 21)\nlongE = ta.crossover(fast, slow)\nlongX = ta.crossunder(fast, slow)\nplot(fast)',
            market: 'EGX30',
            timeframe: '1D',
            date_from: expect.any(String),
            date_to: expect.any(String),
        });
    });

    it('approves a Pine logic import rule spec and runs import backtest from Pine Lab mode', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/import-preview') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        import_mode: 'LOGIC_IMPORT',
                        review_status: 'READY_FOR_REVIEW',
                        translation: {
                            mode: 'DETERMINISTIC_DRAFT',
                            provider: 'LOCAL',
                            fallback_used: true,
                        },
                        reduced_source_pack: {
                            candidate_signals: [{ role: 'long_entry', name: 'longE' }],
                        },
                        ignored_sections: [],
                        rule_spec: {
                            source: {
                                import_mode: 'LOGIC_IMPORT',
                            },
                            execution_plan: {
                                execution_mode: 'LONG_ONLY',
                                definitions: {
                                    longE: { node_type: 'CALL', name: 'ta.crossover', args: [] },
                                    longX: { node_type: 'CALL', name: 'ta.crossunder', args: [] },
                                },
                                entry_expression: { node_type: 'VARIABLE_REF', name: 'longE' },
                                exit_expression: { node_type: 'VARIABLE_REF', name: 'longX' },
                            },
                            human_summary: {
                                long_entry: 'Derived from Pine variable `longE`: ta.crossover(fast, slow)',
                            },
                            signals: {
                                long_entry: { source_name: 'longE', status: 'mapped' },
                                short_entry: { source_name: null, status: 'missing' },
                                long_exit: { source_name: 'longX', status: 'mapped' },
                                short_exit: { source_name: null, status: 'missing' },
                            },
                            warnings: ['Using deterministic draft translation. Review the generated rule spec before any backtest.'],
                            traceability: [{ role: 'long_entry', source_name: 'longE', line: 4 }],
                        },
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/import-backtest') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        import_mode: 'LOGIC_IMPORT',
                        backtest_source: 'IMPORTED_RULE_SPEC',
                        metrics: {
                            total_return: 6.2,
                            final_value: 106200,
                            trade_count: 5,
                            win_rate: 60,
                            max_drawdown: 2.5,
                            quality_score: 1.4,
                        },
                        comparison: {
                            horus_core: {
                                status: 'available',
                                metrics: {
                                    total_return: 3.5,
                                    trade_count: 3,
                                },
                            },
                            winner_by_metric: {
                                total_return: 'IMPORTED',
                                trade_count: 'IMPORTED',
                            },
                        },
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<OptimizationPage />);

        await openPineLabAndWaitForEmptyRegistry();

        fireEvent.change(screen.getByLabelText(/Pine Script Source/i), {
            target: {
                value: '//@version=5\nindicator("Import")\nfast = ta.ema(close, 9)\nslow = ta.ema(close, 21)\nlongE = ta.crossover(fast, slow)\nlongX = ta.crossunder(fast, slow)',
            },
        });

        fireEvent.click(screen.getByRole('button', { name: /Logic Import/i }));
        fireEvent.click(screen.getByRole('button', { name: /Extract Rule Spec/i }));

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /Approve Rule Spec/i })).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Approve Rule Spec/i }));
        fireEvent.click(screen.getByRole('button', { name: /Run Import Backtest/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/Import Backtest/i).length).toBeGreaterThan(0);
            expect(screen.getAllByText(/\+6.20%/i).length).toBeGreaterThan(0);
            expect(screen.getByText(/Horus Core Comparison/i)).toBeInTheDocument();
        });

        const importBacktestCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/api/v1/strategy/pine/import-backtest'));
        expect(importBacktestCall).toBeTruthy();
        expect(JSON.parse(String((importBacktestCall?.[1] as RequestInit)?.body ?? '{}'))).toEqual({
            rule_spec: expect.any(Object),
            operator_approved: true,
            market: 'EGX30',
            timeframe: '1D',
            date_from: expect.any(String),
            date_to: expect.any(String),
            capital: 100000,
            commission_pct: 0.05,
            slippage_pct: 0.1,
        });
    });

    it('applies manual review edits to the import preview before approval', async () => {
        let previewCallCount = 0;
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/import-preview') && init?.method === 'POST') {
                previewCallCount += 1;
                const body = JSON.parse(String(init?.body));
                if (previewCallCount === 1) {
                    expect(body.signal_overrides ?? {}).toEqual({});
                    return {
                        ok: true,
                        json: async () => ({
                            status: 'success',
                            import_mode: 'LOGIC_IMPORT',
                            signal_overrides: {},
                            review_status: 'READY_FOR_REVIEW',
                            translation: {
                                mode: 'DETERMINISTIC_DRAFT',
                                provider: 'LOCAL',
                                fallback_used: true,
                            },
                            reduced_source_pack: {
                                candidate_signals: [{ role: 'long_entry', name: 'longE' }],
                                definitions: [
                                    { name: 'longE', expression: 'ta.crossover(fast, slow)', line: 5 },
                                    { name: 'manualEntry', expression: 'close > ta.sma(close, 20)', line: 6 },
                                    { name: 'longX', expression: 'ta.crossunder(fast, slow)', line: 7 },
                                ],
                            },
                            ignored_sections: [],
                            rule_spec: {
                                source: { import_mode: 'LOGIC_IMPORT' },
                                execution_plan: {
                                    execution_mode: 'LONG_ONLY',
                                    definitions: {
                                        longE: { node_type: 'CALL', name: 'ta.crossover', args: [] },
                                        longX: { node_type: 'CALL', name: 'ta.crossunder', args: [] },
                                    },
                                    entry_expression: { node_type: 'VARIABLE_REF', name: 'longE' },
                                    exit_expression: { node_type: 'VARIABLE_REF', name: 'longX' },
                                },
                                human_summary: {
                                    long_entry: 'Derived from Pine variable `longE`: ta.crossover(fast, slow)',
                                },
                                signals: {
                                    long_entry: { source_name: 'longE', status: 'mapped' },
                                    short_entry: { source_name: null, status: 'missing' },
                                    long_exit: { source_name: 'longX', status: 'mapped' },
                                    short_exit: { source_name: null, status: 'missing' },
                                },
                                warnings: [],
                                traceability: [{ role: 'long_entry', source_name: 'longE', line: 5 }],
                            },
                        }),
                    } as Response;
                }

                expect(body.signal_overrides).toEqual({
                    long_entry: 'manualEntry',
                });
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        import_mode: 'LOGIC_IMPORT',
                        signal_overrides: {
                            long_entry: 'manualEntry',
                        },
                        review_status: 'READY_FOR_REVIEW',
                        translation: {
                            mode: 'DETERMINISTIC_DRAFT',
                            provider: 'LOCAL',
                            fallback_used: true,
                        },
                        reduced_source_pack: {
                            candidate_signals: [{ role: 'long_entry', name: 'longE' }],
                            definitions: [
                                { name: 'longE', expression: 'ta.crossover(fast, slow)', line: 5 },
                                { name: 'manualEntry', expression: 'close > ta.sma(close, 20)', line: 6 },
                                { name: 'longX', expression: 'ta.crossunder(fast, slow)', line: 7 },
                            ],
                        },
                        ignored_sections: [],
                        rule_spec: {
                            source: { import_mode: 'LOGIC_IMPORT' },
                            execution_plan: {
                                execution_mode: 'LONG_ONLY',
                                definitions: {
                                    manualEntry: { node_type: 'COMPARE', operator: '>', left: { node_type: 'SERIES_REF', name: 'close' }, right: { node_type: 'LITERAL', value: 0 } },
                                    longX: { node_type: 'CALL', name: 'ta.crossunder', args: [] },
                                },
                                entry_expression: { node_type: 'VARIABLE_REF', name: 'manualEntry' },
                                exit_expression: { node_type: 'VARIABLE_REF', name: 'longX' },
                            },
                            human_summary: {
                                long_entry: 'Derived from Pine variable `manualEntry`: close > ta.sma(close, 20)',
                            },
                            signals: {
                                long_entry: { source_name: 'manualEntry', status: 'mapped' },
                                short_entry: { source_name: null, status: 'missing' },
                                long_exit: { source_name: 'longX', status: 'mapped' },
                                short_exit: { source_name: null, status: 'missing' },
                            },
                            warnings: ['Applied override for long_entry: using Pine definition `manualEntry`.'],
                            traceability: [{ role: 'long_entry', source_name: 'manualEntry', line: 6 }],
                        },
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<OptimizationPage />);

        await openPineLabAndWaitForEmptyRegistry();

        fireEvent.change(screen.getByLabelText(/Pine Script Source/i), {
            target: {
                value: '//@version=5\nindicator("Import")\nfast = ta.ema(close, 9)\nslow = ta.ema(close, 21)\nmanualEntry = close > ta.sma(close, 20)\nlongE = ta.crossover(fast, slow)\nlongX = ta.crossunder(fast, slow)',
            },
        });

        fireEvent.click(screen.getByRole('button', { name: /Logic Import/i }));
        fireEvent.click(screen.getByRole('button', { name: /Extract Rule Spec/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/Derived from Pine variable `longE`/i).length).toBeGreaterThan(0);
            expect(screen.getByLabelText(/Long Entry Mapping/i)).toBeInTheDocument();
        });

        fireEvent.change(screen.getByLabelText(/Long Entry Mapping/i), { target: { value: 'manualEntry' } });
        fireEvent.click(screen.getByRole('button', { name: /Apply Review Edits/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/Derived from Pine variable `manualEntry`/i).length).toBeGreaterThan(0);
            expect(screen.getByText(/Applied override for long_entry/i)).toBeInTheDocument();
        });
    });

    it('saves an approved imported profile after a successful import backtest', async () => {
        let savedProfiles: Array<Record<string, any>> = [];

        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: savedProfiles,
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/import-preview') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        import_mode: 'LOGIC_IMPORT',
                        review_status: 'READY_FOR_REVIEW',
                        translation: {
                            mode: 'DETERMINISTIC_DRAFT',
                            provider: 'LOCAL',
                            fallback_used: true,
                        },
                        reduced_source_pack: {
                            candidate_signals: [{ role: 'long_entry', name: 'longE' }],
                            definitions: [
                                { name: 'longE', expression: 'ta.crossover(fast, slow)', line: 5 },
                                { name: 'longX', expression: 'ta.crossunder(fast, slow)', line: 6 },
                            ],
                        },
                        ignored_sections: [],
                        rule_spec: {
                            source: { import_mode: 'LOGIC_IMPORT' },
                            execution_plan: {
                                execution_mode: 'LONG_ONLY',
                                definitions: {
                                    longE: { node_type: 'CALL', name: 'ta.crossover', args: [] },
                                    longX: { node_type: 'CALL', name: 'ta.crossunder', args: [] },
                                },
                                entry_expression: { node_type: 'VARIABLE_REF', name: 'longE' },
                                exit_expression: { node_type: 'VARIABLE_REF', name: 'longX' },
                            },
                            human_summary: {
                                long_entry: 'Derived from Pine variable `longE`: ta.crossover(fast, slow)',
                            },
                            signals: {
                                long_entry: { source_name: 'longE', status: 'mapped' },
                                short_entry: { source_name: null, status: 'missing' },
                                long_exit: { source_name: 'longX', status: 'mapped' },
                                short_exit: { source_name: null, status: 'missing' },
                            },
                            warnings: ['Using deterministic draft translation. Review the generated rule spec before any backtest.'],
                            traceability: [{ role: 'long_entry', source_name: 'longE', line: 5 }],
                            confidence: { overall: 0.72 },
                        },
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/import-backtest') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        import_mode: 'LOGIC_IMPORT',
                        backtest_source: 'IMPORTED_RULE_SPEC',
                        metrics: {
                            total_return: 6.2,
                            final_value: 106200,
                            trade_count: 5,
                            win_rate: 60,
                            max_drawdown: 2.5,
                            quality_score: 1.4,
                        },
                        rankings: {
                            performance_score: 71,
                            alignment_score: 74,
                            combined_score: 72,
                        },
                        comparison: {
                            horus_core: {
                                status: 'available',
                                metrics: {
                                    total_return: 3.5,
                                    trade_count: 3,
                                },
                            },
                            winner_by_metric: {
                                total_return: 'IMPORTED',
                                trade_count: 'IMPORTED',
                            },
                        },
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/import-profile') && init?.method === 'POST') {
                const body = JSON.parse(String(init?.body));
                expect(body).toEqual({
                    profile_name: 'Imported EGX Logic',
                    script_source: '//@version=5\nindicator("Import")\nfast = ta.ema(close, 9)\nslow = ta.ema(close, 21)\nlongE = ta.crossover(fast, slow)\nlongX = ta.crossunder(fast, slow)',
                    rule_spec: expect.any(Object),
                    operator_approved: true,
                    market: 'EGX30',
                    timeframe: '1D',
                    backtest_summary: {
                        total_return: 6.2,
                        final_value: 106200,
                        trade_count: 5,
                        win_rate: 60,
                        max_drawdown: 2.5,
                        quality_score: 1.4,
                    },
                    ranking_summary: {
                        performance_score: 71,
                        alignment_score: 74,
                        combined_score: 72,
                    },
                });
                savedProfiles = [
                    {
                        profile_id: 31,
                        profile_name: 'Imported EGX Logic',
                        market: 'EGX30',
                        timeframe: '1D',
                        profile_state: 'READY',
                        source_type: 'PINE_LOGIC_IMPORT',
                        is_active: false,
                        created_at: '2026-04-04T12:00:00',
                        ready_at: '2026-04-04T12:00:00',
                        activated_at: null,
                        activation_count: 0,
                        activation_history: [],
                        ranking_summary: { combined_score: 72, performance_score: 70, alignment_score: 76 },
                        backtest_summary: { total_return: 6.2, trade_count: 5, win_rate: 60, max_drawdown: 2.5 },
                        promotion_summary: { failed_gates: [] },
                    },
                ];
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        profile_id: 31,
                        profile_name: 'Imported EGX Logic',
                        profile_state: 'READY',
                        source_type: 'PINE_LOGIC_IMPORT',
                        created_at: '2026-04-04T12:00:00',
                        ready_at: '2026-04-04T12:00:00',
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<OptimizationPage />);

        await openPineLabAndWaitForEmptyRegistry();

        fireEvent.change(screen.getByLabelText(/Pine Script Source/i), {
            target: {
                value: '//@version=5\nindicator("Import")\nfast = ta.ema(close, 9)\nslow = ta.ema(close, 21)\nlongE = ta.crossover(fast, slow)\nlongX = ta.crossunder(fast, slow)',
            },
        });
        fireEvent.change(screen.getByLabelText(/Profile Name/i), {
            target: { value: 'Imported EGX Logic' },
        });

        fireEvent.click(screen.getByRole('button', { name: /Logic Import/i }));
        fireEvent.click(screen.getByRole('button', { name: /Extract Rule Spec/i }));

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /Approve Rule Spec/i })).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Approve Rule Spec/i }));
        fireEvent.click(screen.getByRole('button', { name: /Run Import Backtest/i }));

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /Save Imported Profile/i })).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Save Imported Profile/i }));

        await waitFor(() => {
            expect(screen.getByText(/saved successfully for reuse/i)).toBeInTheDocument();
            expect(screen.getByText(/Profile State: READY/i)).toBeInTheDocument();
            expect(screen.getAllByText(/Imported EGX Logic/i).length).toBeGreaterThan(0);
            expect(screen.getAllByText(/Logic Import/i).length).toBeGreaterThan(0);
        });
    });

    it('shows Pine runtime support limits in diagnostics and blocks backtest after a blocked preflight', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/preflight') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        script_type: 'STRATEGY',
                        readiness: 'BLOCKED',
                        compatibility_score: 0,
                        detected_entries: ['strategy.entry('],
                        detected_exits: ['strategy.close('],
                        unsupported_features: ['Pine backtest currently supports crossover/crossunder strategies built on ta.sma(close, N) or ta.ema(close, N).'],
                        messages: ['Pine script is blocked until unsupported or ambiguous behavior is resolved.'],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        await openPineLabAndWaitForEmptyRegistry();

        fireEvent.change(screen.getByLabelText(/Pine Script Source/i), {
            target: {
                value: '//@version=5\nstrategy("EMA Trend")\nstrategy.entry("Long", strategy.long)\nstrategy.close("Long")',
            },
        });

        fireEvent.click(screen.getByRole('button', { name: /Run Preflight/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/Readiness: BLOCKED/i).length).toBeGreaterThan(0);
            expect(screen.getByText(/Pine backtest currently supports crossover\/crossunder strategies built on ta\.sma\(close, N\) or ta\.ema\(close, N\)\./i)).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /Run Pine Backtest/i })).toBeDisabled();
        });
    });

    it('shows supported runtime features for RSI and MACD tuple strategies in Pine diagnostics', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/preflight') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        script_type: 'STRATEGY',
                        readiness: 'READY',
                        compatibility_score: 92,
                        detected_entries: ['strategy.entry('],
                        detected_exits: ['strategy.close('],
                        supported_nodes: ['request.security', 'ta.rsi', 'ta.atr', 'ta.highest', 'ta.lowest', 'ta.wma', 'ta.vwma', 'ta.linreg', 'ta.alma', 'ta.macd', 'ta.crossover', 'ta.crossunder'],
                        blocked_reasons: [],
                        plan: {
                            execution_mode: 'LONG_ONLY',
                            definitions: {
                                macdLine: {
                                    node_type: 'TUPLE_ITEM',
                                    source: { node_type: 'CALL', name: 'ta.macd' },
                                },
                                signalLine: {
                                    node_type: 'TUPLE_ITEM',
                                    source: { node_type: 'CALL', name: 'ta.macd' },
                                },
                                longCondition: {
                                    node_type: 'COMPARE',
                                },
                            },
                            entry_expression: { node_type: 'VARIABLE_REF', name: 'longCondition' },
                            exit_expression: { node_type: 'VARIABLE_REF', name: 'exitCondition' },
                        },
                        unsupported_features: [],
                        messages: ['Pine strategy matches the current Horus runtime support rules.'],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        await openPineLabAndWaitForEmptyRegistry();

        fireEvent.change(screen.getByLabelText(/Pine Script Source/i), {
            target: {
                value: '//@version=5\nstrategy("MACD RSI")\nstrategy.entry("Long", strategy.long)\nstrategy.close("Long")',
            },
        });

        fireEvent.click(screen.getByRole('button', { name: /Run Preflight/i }));

        await waitFor(() => {
            expect(screen.getByText(/Supported Runtime Features/i)).toBeInTheDocument();
            expect(screen.getByText(/Same-symbol higher-timeframe security imports/i)).toBeInTheDocument();
            expect(screen.getByText(/RSI threshold and boolean conditions/i)).toBeInTheDocument();
            expect(screen.getByText(/ATR threshold conditions/i)).toBeInTheDocument();
            expect(screen.getByText(/Highest\/lowest breakout conditions/i)).toBeInTheDocument();
            expect(screen.getByText(/WMA\/VWMA trend conditions/i)).toBeInTheDocument();
            expect(screen.getByText(/Linear regression trend conditions/i)).toBeInTheDocument();
            expect(screen.getByText(/ALMA smoothing conditions/i)).toBeInTheDocument();
            expect(screen.getByText(/MACD tuple crossover\/crossunder/i)).toBeInTheDocument();
        });
    });

    it('creates and activates a ready Pine scanner profile from Pine Lab', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/preflight') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        script_type: 'STRATEGY',
                        readiness: 'READY',
                        compatibility_score: 92,
                        detected_entries: ['strategy.entry('],
                        detected_exits: ['strategy.close('],
                        supported_nodes: ['ta.rsi', 'ta.atr', 'ta.highest', 'ta.lowest', 'ta.wma', 'ta.vwma', 'ta.linreg', 'ta.alma', 'ta.macd', 'ta.crossover', 'ta.crossunder'],
                        plan: {
                            execution_mode: 'LONG_ONLY',
                            definitions: {
                                macdLine: {
                                    node_type: 'TUPLE_ITEM',
                                    source: { node_type: 'CALL', name: 'ta.macd' },
                                },
                            },
                        },
                        unsupported_features: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/backtest') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        config: { market: 'EGX30', capital: 100000 },
                        metrics: { total_return: 8.5, final_value: 108500, trade_count: 4, win_rate: 75 },
                        compatibility: { readiness: 'READY', compatibility_score: 92 },
                        alignment: { alignment_score: 25 },
                        rankings: { performance_score: 78, combined_score: 62 },
                        equity_curve: [{ date: '2025-01-01', equity: 100000 }],
                        trades: [{ ticker: 'COMI', pnl: 1200 }],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/create-scanner-profile') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        profile_id: 11,
                        profile_name: 'EGX Breakout Pine',
                        profile_state: 'READY',
                        promotion_summary: { market: 'EGX30', timeframe: '1D' },
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/activate-scanner-profile') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        profile_id: 11,
                        profile_name: 'EGX Breakout Pine',
                        profile_state: 'ACTIVE',
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<OptimizationPage />);

        await openPineLabAndWaitForEmptyRegistry();
        fireEvent.change(screen.getByLabelText(/Pine Script Source/i), {
            target: {
                value: '//@version=5\nstrategy("Fast Slow")\nstrategy.entry("Long", strategy.long)\nstrategy.close("Long")',
            },
        });
        fireEvent.change(screen.getByLabelText(/Profile Name/i), {
            target: { value: 'EGX Breakout Pine' },
        });

        fireEvent.click(screen.getByRole('button', { name: /Run Preflight/i }));
        await waitFor(() => {
            expect(screen.getAllByText(/Readiness: READY/i).length).toBeGreaterThan(0);
        });

        fireEvent.click(screen.getByRole('button', { name: /Run Pine Backtest/i }));
        await waitFor(() => {
            expect(screen.getByText(/\+8.50%/i)).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Create Scanner Profile/i }));
        await waitFor(() => {
            expect(screen.getByText(/created successfully/i)).toBeInTheDocument();
            expect(screen.getByText(/Profile State: READY/i)).toBeInTheDocument();
        });

        const createCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/api/v1/strategy/pine/create-scanner-profile'));
        expect(createCall).toBeTruthy();
        const createPayload = JSON.parse(String((createCall?.[1] as RequestInit)?.body ?? '{}'));
        expect(createPayload.compatibility_summary.supported_nodes).toEqual(
            expect.arrayContaining(['ta.rsi', 'ta.macd', 'ta.crossover', 'ta.crossunder'])
        );
        expect(createPayload.compatibility_summary.plan?.definitions?.macdLine?.node_type).toBe('TUPLE_ITEM');

        fireEvent.click(screen.getByRole('button', { name: /Activate Scanner Profile/i }));
        await waitFor(() => {
            expect(screen.getByText(/now active in Scanner/i)).toBeInTheDocument();
            expect(screen.getByText(/Profile State: ACTIVE/i)).toBeInTheDocument();
        });
    });

    it('shows draft gate reasons when a Pine profile does not qualify for activation', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/preflight') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        script_type: 'STRATEGY',
                        readiness: 'READY',
                        compatibility_score: 92,
                        detected_entries: ['strategy.entry('],
                        detected_exits: ['strategy.close('],
                        unsupported_features: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/backtest') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        config: { market: 'EGX30', capital: 100000 },
                        metrics: { total_return: -2.5, final_value: 97500, trade_count: 1, win_rate: 0, max_drawdown: 42 },
                        compatibility: { readiness: 'READY', compatibility_score: 61 },
                        alignment: { alignment_score: 20 },
                        rankings: { performance_score: 25, combined_score: 45 },
                        equity_curve: [{ date: '2025-01-01', equity: 100000 }],
                        trades: [{ ticker: 'COMI', pnl: -2500 }],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/create-scanner-profile') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        profile_id: 21,
                        profile_name: 'Weak EGX Pine',
                        profile_state: 'DRAFT',
                        promotion_summary: {
                            market: 'EGX30',
                            timeframe: '1D',
                            failed_gates: ['compatibility_score', 'combined_score', 'trade_count'],
                            thresholds: {
                                compatibility_score: 70,
                                combined_score: 60,
                                trade_count: 3,
                            },
                            actuals: {
                                compatibility_score: 61,
                                combined_score: 45,
                                trade_count: 1,
                            },
                        },
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        await openPineLabAndWaitForEmptyRegistry();
        fireEvent.change(screen.getByLabelText(/Pine Script Source/i), {
            target: {
                value: '//@version=5\nstrategy("Weak Pine")\nstrategy.entry("Long", strategy.long)\nstrategy.close("Long")',
            },
        });
        fireEvent.change(screen.getByLabelText(/Profile Name/i), {
            target: { value: 'Weak EGX Pine' },
        });

        fireEvent.click(screen.getByRole('button', { name: /Run Preflight/i }));
        await waitFor(() => {
            expect(screen.getAllByText(/Readiness: READY/i).length).toBeGreaterThan(0);
        });

        fireEvent.click(screen.getByRole('button', { name: /Run Pine Backtest/i }));
        await waitFor(() => {
            expect(screen.getByText(/-2.50%/i)).toBeInTheDocument();
        });

        fireEvent.click(screen.getByRole('button', { name: /Create Scanner Profile/i }));
        await waitFor(() => {
            expect(screen.getByText(/created successfully, but it stayed DRAFT/i)).toBeInTheDocument();
            expect(screen.getByText(/Profile State: DRAFT/i)).toBeInTheDocument();
            expect(screen.getByText(/Activation is blocked until the failed promotion gates are fixed./i)).toBeInTheDocument();
            expect(screen.getAllByText(/Compatibility score below ready threshold/i).length).toBeGreaterThan(0);
            expect(screen.getAllByText(/Combined score below ready threshold/i).length).toBeGreaterThan(0);
            expect(screen.getAllByText(/Trade count below ready minimum/i).length).toBeGreaterThan(0);
            expect(screen.getByText(/Actual: 61.00/i)).toBeInTheDocument();
            expect(screen.getByText(/Required: >= 70.00/i)).toBeInTheDocument();
            expect(screen.getByText(/Actual: 45.00/i)).toBeInTheDocument();
            expect(screen.getByText(/Required: >= 60.00/i)).toBeInTheDocument();
            expect(screen.getByText(/Actual: 1/i)).toBeInTheDocument();
            expect(screen.getByText(/Required: >= 3/i)).toBeInTheDocument();
        });
    });

    it('loads Pine profile registry, filters by state, and activates a ready profile from the list', async () => {
        let registryProfiles: any[] = [
            {
                profile_id: 1,
                profile_name: 'Draft Pine Mean Revert',
                market: 'EGX30',
                timeframe: '1D',
                profile_state: 'DRAFT',
                is_active: false,
                created_at: '2026-03-28T08:00:00',
                ready_at: null,
                activated_at: null,
                activation_count: 0,
                activation_history: [],
                ranking_summary: { combined_score: 48 },
                backtest_summary: { total_return: -1.2 },
                promotion_summary: {
                    failed_gates: ['compatibility_score', 'trade_count'],
                },
            },
            {
                profile_id: 2,
                profile_name: 'Ready Pine Breakout',
                market: 'EGX70',
                timeframe: '1D',
                profile_state: 'READY',
                is_active: false,
                created_at: '2026-03-29T09:15:00',
                ready_at: '2026-03-29T09:20:00',
                activated_at: null,
                activation_count: 0,
                activation_history: [],
                ranking_summary: { combined_score: 94 },
                backtest_summary: { total_return: 9.4 },
                promotion_summary: {
                    failed_gates: [],
                },
            },
            {
                profile_id: 3,
                profile_name: 'Active Pine Trend',
                market: 'EGX100',
                timeframe: '1W',
                profile_state: 'ACTIVE',
                is_active: true,
                created_at: '2026-03-27T07:00:00',
                ready_at: '2026-03-27T07:10:00',
                activated_at: '2026-03-30T08:30:00',
                activation_count: 1,
                activation_history: [
                    {
                        event_type: 'ACTIVATED',
                        activated_at: '2026-03-30T08:30:00',
                        previous_active_profile_id: null,
                        previous_active_profile_name: null,
                    },
                ],
                ranking_summary: { combined_score: 81 },
                backtest_summary: { total_return: 12.8 },
                promotion_summary: {
                    failed_gates: [],
                },
            },
        ];

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                const activeProfile = registryProfiles.find((profile) => profile.profile_state === 'ACTIVE');
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: activeProfile?.profile_id ?? null,
                        profiles: registryProfiles,
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/activate-scanner-profile') && init?.method === 'POST') {
                registryProfiles = registryProfiles.map((profile) => {
                    if (profile.profile_id === 2) {
                        return {
                            ...profile,
                            profile_state: 'ACTIVE',
                            is_active: true,
                            activated_at: '2026-03-30T09:45:00',
                            activation_count: 1,
                            activation_history: [
                                {
                                    event_type: 'ACTIVATED',
                                    activated_at: '2026-03-30T09:45:00',
                                    previous_active_profile_id: 3,
                                    previous_active_profile_name: 'Active Pine Trend',
                                },
                            ],
                        };
                    }
                    if (profile.profile_id === 3) {
                        return {
                            ...profile,
                            profile_state: 'READY',
                            is_active: false,
                        };
                    }
                    return profile;
                });
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        profile_id: 2,
                        profile_name: 'Ready Pine Breakout',
                        profile_state: 'ACTIVE',
                        created_at: '2026-03-29T09:15:00',
                        ready_at: '2026-03-29T09:20:00',
                        activated_at: '2026-03-30T09:45:00',
                        activation_count: 1,
                        activation_history: [
                            {
                                event_type: 'ACTIVATED',
                                activated_at: '2026-03-30T09:45:00',
                                previous_active_profile_id: 3,
                                previous_active_profile_name: 'Active Pine Trend',
                            },
                        ],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        fireEvent.click(screen.getByRole('button', { name: /Pine Lab/i }));

        await waitFor(() => {
            expect(screen.getByText(/Profile Registry/i)).toBeInTheDocument();
            expect(screen.getAllByText(/Draft Pine Mean Revert/i).length).toBeGreaterThan(0);
            expect(screen.getAllByText(/Ready Pine Breakout/i).length).toBeGreaterThan(0);
            expect(screen.getAllByText(/Active Pine Trend/i).length).toBeGreaterThan(0);
            expect(screen.getByText(/Created: 2026-03-29 09:15/i)).toBeInTheDocument();
            expect(screen.getByText(/Ready: 2026-03-29 09:20/i)).toBeInTheDocument();
            expect(screen.getByText(/Activated: 2026-03-30 08:30/i)).toBeInTheDocument();
            expect(screen.getByText(/Activations: 1/i)).toBeInTheDocument();
        });

        expect(screen.getByText(/Profile Sort/i)).toBeInTheDocument();
        {
            const active = screen.getByText('Active Pine Trend');
            const ready = screen.getByText('Ready Pine Breakout');
            expect(active.compareDocumentPosition(ready) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
        }

        fireEvent.click(screen.getByRole('button', { name: /Highest Score/i }));

        await waitFor(() => {
            const ready = screen.getByText('Ready Pine Breakout');
            const active = screen.getByText('Active Pine Trend');
            expect(ready.compareDocumentPosition(active) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
        });

        fireEvent.click(screen.getByRole('button', { name: /Recent Activation/i }));

        await waitFor(() => {
            const active = screen.getByText('Active Pine Trend');
            const ready = screen.getByText('Ready Pine Breakout');
            expect(active.compareDocumentPosition(ready) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
        });

        fireEvent.click(screen.getByRole('button', { name: /^Ready$/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/Ready Pine Breakout/i).length).toBeGreaterThan(0);
            expect(screen.queryAllByText(/Draft Pine Mean Revert/i)).toHaveLength(0);
            expect(screen.queryAllByText(/Active Pine Trend/i)).toHaveLength(0);
        });

        fireEvent.click(screen.getByRole('button', { name: /Activate Ready Pine Breakout/i }));

        await waitFor(() => {
            expect(screen.getByText(/now active in Scanner/i)).toBeInTheDocument();
            expect(screen.getAllByText(/Active/i).length).toBeGreaterThan(0);
            expect(screen.getByText(/Activated: 2026-03-30 09:45/i)).toBeInTheDocument();
            expect(screen.getByText(/Last Activation/i)).toBeInTheDocument();
            expect(screen.getByText(/replaced Active Pine Trend/i)).toBeInTheDocument();
        });
    });

    it('opens Pine Lab from query params and highlights the targeted registry profile', async () => {
        window.history.pushState({}, '', '/optimization?mode=PINE_LAB&profileId=2');

        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: 3,
                        profiles: [
                            {
                                profile_id: 2,
                                profile_name: 'Ready Pine Breakout',
                                market: 'EGX70',
                                timeframe: '1D',
                                profile_state: 'READY',
                                is_active: false,
                                created_at: '2026-03-29T09:15:00',
                                ready_at: '2026-03-29T09:20:00',
                                activated_at: null,
                                activation_count: 0,
                                activation_history: [],
                                ranking_summary: { combined_score: 94 },
                                backtest_summary: { total_return: 9.4 },
                                promotion_summary: {
                                    failed_gates: [],
                                },
                            },
                            {
                                profile_id: 3,
                                profile_name: 'Active Pine Trend',
                                market: 'EGX100',
                                timeframe: '1W',
                                profile_state: 'ACTIVE',
                                is_active: true,
                                created_at: '2026-03-27T07:00:00',
                                ready_at: '2026-03-27T07:10:00',
                                activated_at: '2026-03-30T08:30:00',
                                activation_count: 1,
                                activation_history: [],
                                ranking_summary: { combined_score: 81 },
                                backtest_summary: { total_return: 12.8 },
                                promotion_summary: {
                                    failed_gates: [],
                                },
                            },
                        ],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /Pine Lab/i })).toHaveAttribute('aria-pressed', 'true');
            expect(screen.getByText(/Profile Registry/i)).toBeInTheDocument();
            expect(screen.getByText(/Focused from Scanner/i)).toBeInTheDocument();
            expect(screen.getAllByText(/Ready Pine Breakout/i).length).toBeGreaterThan(0);
        });
    });

    it('opens shared Pine profile details from the Pine Lab registry', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [
                            {
                                profile_id: 14,
                                profile_name: 'Registry Deep Dive Pine',
                                market: 'EGX30',
                                timeframe: '1D',
                                profile_state: 'READY',
                                is_active: false,
                                created_at: '2026-03-28T08:00:00',
                                ready_at: '2026-03-28T09:10:00',
                                activated_at: null,
                                activation_count: 0,
                                activation_history: [],
                                ranking_summary: {
                                    combined_score: 87,
                                    performance_score: 82,
                                    alignment_score: 69,
                                    recommended: true,
                                },
                                backtest_summary: {
                                    total_return: 10.3,
                                    trade_count: 5,
                                    win_rate: 60,
                                    max_drawdown: 8.4,
                                },
                                compatibility_summary: {
                                    readiness: 'READY',
                                    compatibility_score: 90,
                                    messages: ['Detected strategy.entry and strategy.close flow'],
                                    supported_nodes: ['request.security', 'ta.rsi', 'ta.atr', 'ta.highest', 'ta.lowest', 'ta.wma', 'ta.vwma', 'ta.linreg', 'ta.alma', 'ta.macd', 'ta.crossover', 'ta.crossunder'],
                                    plan: {
                                        execution_mode: 'LONG_ONLY',
                                        definitions: {
                                            macdLine: {
                                                node_type: 'TUPLE_ITEM',
                                                source: { node_type: 'CALL', name: 'ta.macd' },
                                            },
                                        },
                                    },
                                },
                                promotion_summary: {
                                    failed_gates: [],
                                    thresholds: {
                                        compatibility_score: 70,
                                        combined_score: 60,
                                        trade_count: 3,
                                        total_return: 0,
                                        max_drawdown: 35,
                                    },
                                    actuals: {
                                        readiness: 'READY',
                                        compatibility_score: 90,
                                        combined_score: 87,
                                        trade_count: 5,
                                        total_return: 10.3,
                                        max_drawdown: 8.4,
                                    },
                                },
                            },
                        ],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        fireEvent.click(screen.getByRole('button', { name: /Pine Lab/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/Registry Deep Dive Pine/i).length).toBeGreaterThan(0);
        });

        fireEvent.click(screen.getByRole('button', { name: /View Details Registry Deep Dive Pine/i }));

        const dialog = screen.getByRole('dialog', { name: /Pine profile details/i });
        expect(dialog).toBeInTheDocument();
        expect(within(dialog).getByText(/Registry Deep Dive Pine/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/Recommendation: Promote to scanner/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/Detected strategy.entry and strategy.close flow/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/^Combined Score: 87.0$/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/Supported Runtime Features/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/Same-symbol higher-timeframe security imports/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/RSI threshold and boolean conditions/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/ATR threshold conditions/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/Highest\/lowest breakout conditions/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/WMA\/VWMA trend conditions/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/Linear regression trend conditions/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/ALMA smoothing conditions/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/MACD tuple crossover\/crossunder/i)).toBeInTheDocument();
    });

    it('does not reload the Pine profile registry when typing into the Pine form', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<OptimizationPage />);

        await openPineLabAndWaitForEmptyRegistry();

        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/strategy/pine/scanner-profiles'))).toHaveLength(1);

        fireEvent.change(screen.getByLabelText(/Pine Script Source/i), {
            target: { value: '//@version=5\nstrategy("Typed Pine")\nstrategy.entry("Long", strategy.long)' },
        });

        await waitFor(() => {
            expect(screen.getByDisplayValue(/Typed Pine/i)).toBeInTheDocument();
        });

        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/strategy/pine/scanner-profiles'))).toHaveLength(1);
    });

    it('shows the configured Pine import translator mode inside Pine Lab before extraction', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/settings')) {
                return {
                    ok: true,
                    text: async () => JSON.stringify({ PINE_IMPORT_TRANSLATION_PROVIDER: 'OLLAMA' }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/pine/scanner-profiles')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        active_profile_id: null,
                        profiles: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/strategy/status')) {
                return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<OptimizationPage />);

        await openPineLabAndWaitForEmptyRegistry();
        fireEvent.click(screen.getByRole('button', { name: /Logic Import/i }));

        expect(screen.getByText(/Next Draft Engine: Ollama-assisted translation/i)).toBeInTheDocument();
    });
});
