import { act, renderHook, waitFor } from '@testing-library/react';

import { usePortfolioManagement } from './usePortfolioManagement';

describe('usePortfolioManagement', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('fetches the management report and maps success state', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/settings')) {
                return {
                    ok: true,
                    json: async () => ({
                        PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS: 15,
                        PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES: true,
                        PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT: 15,
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/system/boot-status')) {
                return { ok: true, json: async () => ({ system_ready: true, pipeline_state: 'FRESH' }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/management/report?portfolio_id=7&refresh_prices=true')) {
                return {
                    ok: true,
                    json: async () => ({
                        portfolio: { id: 7, name: 'Main', type: 'USER', cash_egp: 1, cash_usd: 0 },
                        snapshot_at: '2026-03-17T00:00:00Z',
                        summary: {
                            open_positions: 2,
                            winners: 1,
                            losers: 1,
                            total_cost_basis: 100,
                            market_value: 110,
                            unrealized_pnl: 10,
                            unrealized_pnl_pct: 10,
                            action_items: 1,
                        },
                        risk: {
                            status: 'SAFE',
                            health_score: 91,
                            heat: 12,
                            recommendations: [],
                        },
                        positions: [],
                        action_items: [],
                    }),
                } as Response;
            }
            throw new Error(`Unexpected fetch: ${url}`);
        }) as jest.Mock;

        const { result } = renderHook(() =>
            usePortfolioManagement({
                activePortfolioId: 7,
                refreshData: jest.fn(async () => undefined),
            })
        );

        await act(async () => {
            await result.current.fetchManagementReport(true);
        });

        await waitFor(() => {
            expect(result.current.managementReport?.risk.health_score).toBe(91);
            expect(result.current.managementMessage).toBe('Portfolio management report generated.');
        });
    });

    it('blocks intake when there are no valid holdings', async () => {
        const { result } = renderHook(() =>
            usePortfolioManagement({
                activePortfolioId: 7,
                refreshData: jest.fn(async () => undefined),
            })
        );

        await act(async () => {
            await result.current.handleManagementIntake();
        });

        expect(result.current.managementMessage).toBe('Add at least one holding ticker before intake.');
    });

    it('submits holdings intake and refreshes runtime plus report state', async () => {
        const refreshData = jest.fn(async () => undefined);

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/settings')) {
                return {
                    ok: true,
                    json: async () => ({
                        PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS: 15,
                        PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES: true,
                        PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT: 15,
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/system/boot-status')) {
                return { ok: true, json: async () => ({ system_ready: true, pipeline_state: 'FRESH' }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/management/intake') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({ status: 'success', created: 1, updated: 0, errors: [] }),
                } as Response;
            }
            if (url.includes('/api/v1/portfolio/management/report?portfolio_id=7&refresh_prices=false')) {
                return {
                    ok: true,
                    json: async () => ({
                        portfolio: { id: 7, name: 'Main', type: 'USER', cash_egp: 1, cash_usd: 0 },
                        snapshot_at: '2026-03-17T00:00:00Z',
                        summary: {
                            open_positions: 1,
                            winners: 1,
                            losers: 0,
                            total_cost_basis: 100,
                            market_value: 110,
                            unrealized_pnl: 10,
                            unrealized_pnl_pct: 10,
                            action_items: 0,
                        },
                        risk: {
                            status: 'SAFE',
                            health_score: 95,
                            heat: 10,
                            recommendations: [],
                        },
                        positions: [],
                        action_items: [],
                    }),
                } as Response;
            }
            throw new Error(`Unexpected fetch: ${url}`);
        }) as jest.Mock;

        const { result } = renderHook(() =>
            usePortfolioManagement({
                activePortfolioId: 7,
                refreshData,
            })
        );

        act(() => {
            result.current.addManagedHoldingRow();
        });

        await waitFor(() => {
            expect(result.current.managedHoldings).toHaveLength(1);
        });

        const rowId = result.current.managedHoldings[0].id;

        act(() => {
            result.current.updateManagedHoldingRow(rowId, 'ticker', 'COMI');
            result.current.updateManagedHoldingRow(rowId, 'shares', '100');
            result.current.updateManagedHoldingRow(rowId, 'entry_price', '90');
        });

        await act(async () => {
            await result.current.handleManagementIntake();
        });

        await waitFor(() => {
            expect(refreshData).toHaveBeenCalled();
            expect(result.current.managementMessage).toBe('Portfolio management report generated.');
            expect(result.current.managementReport?.risk.health_score).toBe(95);
        });
    });

    it('sends the management report and records the send summary', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/settings')) {
                return {
                    ok: true,
                    json: async () => ({
                        PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS: 15,
                        PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES: true,
                        PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT: 15,
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/system/boot-status')) {
                return { ok: true, json: async () => ({ system_ready: true, pipeline_state: 'FRESH' }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/management/report/send') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'sent',
                        chunks_total: 2,
                        chunks_sent: 2,
                        chunks_failed: 0,
                        summary: true,
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/portfolio/management/report?portfolio_id=7&refresh_prices=false')) {
                return {
                    ok: true,
                    json: async () => ({
                        portfolio: { id: 7, name: 'Main', type: 'USER', cash_egp: 1, cash_usd: 0 },
                        snapshot_at: '2026-03-17T00:00:00Z',
                        summary: {
                            open_positions: 1,
                            winners: 1,
                            losers: 0,
                            total_cost_basis: 100,
                            market_value: 110,
                            unrealized_pnl: 10,
                            unrealized_pnl_pct: 10,
                            action_items: 0,
                        },
                        risk: {
                            status: 'SAFE',
                            health_score: 95,
                            heat: 10,
                            recommendations: [],
                        },
                        positions: [],
                        action_items: [],
                    }),
                } as Response;
            }
            throw new Error(`Unexpected fetch: ${url}`);
        }) as jest.Mock;

        const { result } = renderHook(() =>
            usePortfolioManagement({
                activePortfolioId: 7,
                refreshData: jest.fn(async () => undefined),
            })
        );

        act(() => {
            result.current.setReportControls({
                include_positions: '20',
                chat_id: '123',
                refresh_prices: true,
            });
        });

        await act(async () => {
            await result.current.handleSendManagementReport();
        });

        await waitFor(() => {
            expect(result.current.managementSendResult).toEqual({
                status: 'sent',
                chunks_total: 2,
                chunks_sent: 2,
                chunks_failed: 0,
            });
            expect(result.current.managementMessage).toBe('Portfolio management report generated.');
        });
    });
});
