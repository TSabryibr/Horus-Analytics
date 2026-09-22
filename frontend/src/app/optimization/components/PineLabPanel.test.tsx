import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { PineLabPanel } from './PineLabPanel';


jest.mock('@/app/components/PineProfileDetailsDialog', () => ({
    PineProfileDetailsDialog: () => null,
}));

jest.mock('@/app/components/pineRuntimeFeatures', () => ({
    deriveSupportedRuntimeFeatures: () => [],
}));


describe('PineLabPanel', () => {
    const importBacktestResult = {
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
    };

    const baseProps = {
        pineForm: {
            scriptSource: '//@version=5\nstrategy("Import")',
            market: 'EGX30',
            timeframe: '1D',
            dateFrom: '2026-01-01',
            dateTo: '2026-04-01',
            capital: 100000,
            commissionPct: 0.05,
            slippagePct: 0.1,
            profileName: '',
        },
        onChangeForm: jest.fn(),
        preflightResult: null,
        preflightLoading: false,
        onRunPreflight: jest.fn(),
        backtestResult: null,
        backtestLoading: false,
        onRunBacktest: jest.fn(),
        promotionLoading: false,
        activationLoading: false,
        createdProfile: null,
        profileRegistry: [],
        profileRegistryLoading: false,
        focusedProfileId: null,
        onCreateProfile: jest.fn(),
        onActivateProfile: jest.fn(),
        chartContent: null,
        importPreviewResult: {
            review_status: 'READY_FOR_REVIEW',
            translation: {
                mode: 'DETERMINISTIC_DRAFT',
                provider: 'LOCAL',
                fallback_used: true,
            },
            ignored_sections: [{ kind: 'plot', line: 7, source: 'plot(fast)' }],
            reduced_source_pack: {
                unresolved_references: [
                    {
                        role: 'long_entry',
                        name: 'longE',
                        line: 7,
                        expression: 'ta.crossover(fast, slow) and externalFilter',
                        references: ['externalFilter'],
                    },
                ],
            },
            rule_spec: {
                source: {
                    import_mode: 'LOGIC_IMPORT',
                },
                confidence: {
                    overall: 0.72,
                    per_signal: {
                        long_entry: 0.78,
                        short_entry: 0,
                        long_exit: 0.66,
                        short_exit: 0,
                    },
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
                warnings: ['Using deterministic draft translation. Review the generated rule spec before any backtest.'],
                signals: {
                    long_entry: { source_name: 'longE', status: 'mapped' },
                    short_entry: { source_name: null, status: 'missing' },
                    long_exit: { source_name: 'longX', status: 'mapped' },
                    short_exit: { source_name: null, status: 'missing' },
                },
                traceability: [{ role: 'long_entry', source_name: 'longE', line: 7 }],
            },
        },
        importPreviewLoading: false,
        onRunImportPreview: jest.fn(),
        signalOverrides: {},
        onChangeSignalOverride: jest.fn(),
        operatorApproved: false,
        onSetOperatorApproved: jest.fn(),
        importBacktestResult: null,
        importBacktestLoading: false,
        onRunImportBacktest: jest.fn(),
        importProfileLoading: false,
        onSaveImportedProfile: jest.fn(),
        importTranslationProvider: 'LOCAL',
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('switches into Logic Import mode and shows import preview controls and review output', () => {
        render(<PineLabPanel {...baseProps} />);

        fireEvent.click(screen.getByRole('button', { name: /Logic Import/i }));

        expect(screen.getByRole('button', { name: /Logic Import/i })).toHaveAttribute('aria-pressed', 'true');
        expect(screen.getByRole('button', { name: /Extract Rule Spec/i })).toBeInTheDocument();
        expect(screen.getByText(/Next Draft Engine: Local deterministic draft/i)).toBeInTheDocument();
        expect(screen.getByText(/Review Status/i)).toBeInTheDocument();
        expect(screen.getByText(/READY_FOR_REVIEW/i)).toBeInTheDocument();
        expect(screen.getByText(/Risk Summary/i)).toBeInTheDocument();
        expect(screen.getByText(/Missing Mappings: 2/i)).toBeInTheDocument();
        expect(screen.getByText(/Warnings: 1/i)).toBeInTheDocument();
        expect(screen.getAllByText(/Ignored Sections: 1/i).length).toBeGreaterThan(0);
        expect(screen.getByText(/Unresolved References: 1/i)).toBeInTheDocument();
        expect(screen.getByText(/longE -> externalFilter/i)).toBeInTheDocument();
        expect(screen.getByText(/Overall Confidence/i)).toBeInTheDocument();
        expect(screen.getByText(/72.0%/i)).toBeInTheDocument();
        expect(screen.getAllByText(/Derived from Pine variable `longE`/i).length).toBeGreaterThan(0);
        expect(screen.getByText(/Ignored Pine Sections/i)).toBeInTheDocument();
        expect(screen.getByText(/plot\(fast\)/i)).toBeInTheDocument();
        expect(screen.getByText(/Confidence: 78.0%/i)).toBeInTheDocument();
    });

    it('requires approval before import backtest and renders comparison after execution', () => {
        const onRunImportBacktest = jest.fn();

        function Harness() {
            const [operatorApproved, setOperatorApproved] = React.useState(false);
            return (
                <PineLabPanel
                    {...baseProps}
                    operatorApproved={operatorApproved}
                    onSetOperatorApproved={setOperatorApproved}
                    importBacktestResult={operatorApproved ? importBacktestResult : null}
                    onRunImportBacktest={onRunImportBacktest}
                />
            );
        }

        render(<Harness />);

        fireEvent.click(screen.getByRole('button', { name: /Logic Import/i }));

        expect(screen.getByRole('button', { name: /Run Import Backtest/i })).toBeDisabled();
        expect(screen.getByText(/Approve the imported rule spec to unlock import backtest\./i)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Approve Rule Spec/i }));

        expect(screen.getByRole('button', { name: /Run Import Backtest/i })).not.toBeDisabled();
        expect(screen.getByText(/Import backtest is ready to run\./i)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Run Import Backtest/i }));

        expect(onRunImportBacktest).toHaveBeenCalledTimes(1);
        expect(screen.getAllByText(/Import Backtest/i).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/\+6.20%/i).length).toBeGreaterThan(0);
        expect(screen.getByText(/Horus Core Comparison/i)).toBeInTheDocument();
    });

    it('renders editable signal mapping controls for review before approval', () => {
        const onChangeSignalOverride = jest.fn();

        render(
            <PineLabPanel
                {...baseProps}
                signalOverrides={{ long_entry: 'longE' }}
                onChangeSignalOverride={onChangeSignalOverride}
                importPreviewResult={{
                    ...baseProps.importPreviewResult,
                    reduced_source_pack: {
                        candidate_signals: [{ role: 'long_entry', name: 'longE' }],
                        definitions: [
                            { name: 'longE', expression: 'ta.crossover(fast, slow)', line: 5 },
                            { name: 'manualEntry', expression: 'close > ta.sma(close, 20)', line: 6 },
                        ],
                    },
                }}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /Logic Import/i }));
        fireEvent.change(screen.getByLabelText(/Long Entry Mapping/i), { target: { value: 'manualEntry' } });

        expect(onChangeSignalOverride).toHaveBeenCalledWith('long_entry', 'manualEntry');
        expect(screen.getByRole('button', { name: /Apply Review Edits/i })).toBeInTheDocument();
    });

    it('shows Ollama-assisted translator intent before the first extract when configured', () => {
        render(
            <PineLabPanel
                {...baseProps}
                importPreviewResult={null}
                importTranslationProvider="OLLAMA"
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /Logic Import/i }));

        expect(screen.getByText(/Next Draft Engine: Ollama-assisted translation/i)).toBeInTheDocument();
        expect(screen.getByText(/Current translator setting comes from Settings > Delivery & AI/i)).toBeInTheDocument();
    });

    it('shows the exact fallback reason when Ollama translation falls back to deterministic draft', () => {
        render(
            <PineLabPanel
                {...baseProps}
                importTranslationProvider="OLLAMA"
                importPreviewResult={{
                    ...baseProps.importPreviewResult,
                    translation: {
                        mode: 'DETERMINISTIC_DRAFT',
                        provider: 'LOCAL',
                        fallback_used: true,
                        attempted_provider: 'OLLAMA',
                        fallback_reason: 'Provider translation rejected: unknown source "inventedSignal".',
                    },
                }}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /Logic Import/i }));

        expect(screen.getByText(/AI Translator Fallback/i)).toBeInTheDocument();
        expect(screen.getByText(/Attempted: OLLAMA/i)).toBeInTheDocument();
        expect(screen.getByText(/Provider translation rejected: unknown source "inventedSignal"\./i)).toBeInTheDocument();
    });
});
