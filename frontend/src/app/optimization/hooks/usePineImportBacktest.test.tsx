import { act, renderHook, waitFor } from '@testing-library/react';

import type { PineLabForm } from './usePineBacktest';
import { usePineImportBacktest } from './usePineImportBacktest';


describe('usePineImportBacktest', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
    });

    it('runs the Pine import-backtest endpoint with an approved rule spec and stores the result', async () => {
        const showMessage = jest.fn();
        const pineForm: PineLabForm = {
            scriptSource: '//@version=5\nstrategy("Import")\nlongCondition = close > ta.sma(close, 20)\n',
            market: 'EGX30',
            timeframe: '1D',
            dateFrom: '2026-01-01',
            dateTo: '2026-04-01',
            capital: 100000,
            commissionPct: 0.05,
            slippagePct: 0.1,
            profileName: '',
        };
        const importPreviewResult = {
            review_status: 'READY_FOR_REVIEW',
            rule_spec: {
                source: {
                    import_mode: 'LOGIC_IMPORT',
                },
                execution_plan: {
                    execution_mode: 'LONG_ONLY',
                    definitions: {
                        longCondition: { node_type: 'COMPARE', operator: '>', left: { node_type: 'SERIES_REF', name: 'close' }, right: { node_type: 'LITERAL', value: 0 } },
                        exitCondition: { node_type: 'COMPARE', operator: '<', left: { node_type: 'SERIES_REF', name: 'close' }, right: { node_type: 'LITERAL', value: 0 } },
                    },
                    entry_expression: { node_type: 'VARIABLE_REF', name: 'longCondition' },
                    exit_expression: { node_type: 'VARIABLE_REF', name: 'exitCondition' },
                },
            },
        };

        global.fetch = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
            const body = JSON.parse(String(init?.body));
            expect(body).toEqual({
                rule_spec: importPreviewResult.rule_spec,
                operator_approved: true,
                market: 'EGX30',
                timeframe: '1D',
                date_from: '2026-01-01',
                date_to: '2026-04-01',
                capital: 100000,
                commission_pct: 0.05,
                slippage_pct: 0.1,
            });
            return {
                ok: true,
                text: async () =>
                    JSON.stringify({
                        status: 'success',
                        import_mode: 'LOGIC_IMPORT',
                        backtest_source: 'IMPORTED_RULE_SPEC',
                        metrics: {
                            total_return: 5.2,
                            trade_count: 4,
                        },
                    }),
            } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => usePineImportBacktest({ pineForm, importPreviewResult, showMessage, enabled: true }));

        act(() => {
            result.current.setOperatorApproved(true);
        });

        await act(async () => {
            await result.current.runImportBacktest();
        });

        await waitFor(() => {
            expect(result.current.importBacktestLoading).toBe(false);
            expect(result.current.importBacktestResult?.backtest_source).toBe('IMPORTED_RULE_SPEC');
        });

        expect(showMessage).toHaveBeenCalledWith(null);
    });
});
