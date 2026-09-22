import { act, renderHook, waitFor } from '@testing-library/react';

import type { PineLabForm } from './usePineBacktest';
import { usePineLogicImport } from './usePineLogicImport';


describe('usePineLogicImport', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
    });

    it('runs the Pine import-preview endpoint and stores a reviewable result', async () => {
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

        global.fetch = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
            const body = JSON.parse(String(init?.body));
            expect(body).toEqual({
                script_source: pineForm.scriptSource,
                market: 'EGX30',
                timeframe: '1D',
                date_from: '2026-01-01',
                date_to: '2026-04-01',
            });
            return {
                ok: true,
                text: async () =>
                    JSON.stringify({
                        status: 'success',
                        import_mode: 'LOGIC_IMPORT',
                        review_status: 'READY_FOR_REVIEW',
                        translation: {
                            mode: 'DETERMINISTIC_DRAFT',
                            provider: 'LOCAL',
                            fallback_used: true,
                        },
                        reduced_source_pack: {
                            candidate_signals: [{ role: 'long_entry', name: 'longCondition' }],
                        },
                        ignored_sections: [],
                        rule_spec: {
                            human_summary: {
                                long_entry: 'Derived from Pine variable `longCondition`: close > ta.sma(close, 20)',
                            },
                            signals: {
                                long_entry: { source_name: 'longCondition', status: 'mapped' },
                                short_entry: { source_name: null, status: 'missing' },
                                long_exit: { source_name: null, status: 'missing' },
                                short_exit: { source_name: null, status: 'missing' },
                            },
                            warnings: ['Using deterministic draft translation. Review the generated rule spec before any backtest.'],
                            traceability: [{ role: 'long_entry', source_name: 'longCondition', line: 2 }],
                        },
                    }),
            } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => usePineLogicImport({ pineForm, showMessage, enabled: true }));

        await act(async () => {
            await result.current.runImportPreview();
        });

        await waitFor(() => {
            expect(result.current.importPreviewLoading).toBe(false);
            expect(result.current.importPreviewResult?.review_status).toBe('READY_FOR_REVIEW');
        });

        expect(showMessage).toHaveBeenCalledWith(null);
    });

    it('sends manual signal overrides when re-extracting the Pine import preview', async () => {
        const showMessage = jest.fn();
        const pineForm: PineLabForm = {
            scriptSource: '//@version=5\nindicator("Import")\nmanualEntry = close > ta.sma(close, 20)\n',
            market: 'EGX30',
            timeframe: '1D',
            dateFrom: '2026-01-01',
            dateTo: '2026-04-01',
            capital: 100000,
            commissionPct: 0.05,
            slippagePct: 0.1,
            profileName: '',
        };

        global.fetch = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
            const body = JSON.parse(String(init?.body));
            expect(body).toEqual({
                script_source: pineForm.scriptSource,
                market: 'EGX30',
                timeframe: '1D',
                date_from: '2026-01-01',
                date_to: '2026-04-01',
                signal_overrides: {
                    long_entry: 'manualEntry',
                },
            });
            return {
                ok: true,
                text: async () =>
                    JSON.stringify({
                        status: 'success',
                        import_mode: 'LOGIC_IMPORT',
                        signal_overrides: {
                            long_entry: 'manualEntry',
                        },
                        review_status: 'READY_FOR_REVIEW',
                        rule_spec: {
                            human_summary: {
                                long_entry: 'Derived from Pine variable `manualEntry`: close > ta.sma(close, 20)',
                            },
                            signals: {
                                long_entry: { source_name: 'manualEntry', status: 'mapped' },
                                short_entry: { source_name: null, status: 'missing' },
                                long_exit: { source_name: null, status: 'missing' },
                                short_exit: { source_name: null, status: 'missing' },
                            },
                        },
                    }),
            } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => usePineLogicImport({ pineForm, showMessage, enabled: true }));

        act(() => {
            result.current.setSignalOverride('long_entry', 'manualEntry');
        });

        await act(async () => {
            await result.current.runImportPreview();
        });

        await waitFor(() => {
            expect(result.current.importPreviewLoading).toBe(false);
            expect(result.current.importPreviewResult?.signal_overrides?.long_entry).toBe('manualEntry');
            expect(result.current.signalOverrides.long_entry).toBe('manualEntry');
        });
    });
});
