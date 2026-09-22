import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { OptimizationResultsPanel } from './OptimizationResultsPanel';

describe('OptimizationResultsPanel', () => {
    it('renders KPI cards, assumptions, and forwards audit/apply actions', () => {
        const onRunAiAudit = jest.fn();
        const onPromptApply = jest.fn();

        render(
            <OptimizationResultsPanel
                simResult={{
                    metrics: {
                        total_return: 12.34,
                        final_value: 224680,
                        trade_count: 18,
                    },
                    assumptions: {
                        commission_pct: 0.05,
                        slippage_pct: 0.5,
                    },
                    equity_curve: [{ date: '2025-01-01', equity: 200000 }],
                }}
                simParams={{ RSI_MIN: 55 }}
                auditLoading={false}
                onRunAiAudit={onRunAiAudit}
                onPromptApply={onPromptApply}
                chartContent={<div data-testid="mock-optimization-chart" />}
            />
        );

        expect(screen.getByText('Total_Yield')).toBeInTheDocument();
        expect(screen.getByText('+12.34%')).toBeInTheDocument();
        expect(screen.getByText(/COMM_MODEL: 0.05%/i)).toBeInTheDocument();
        expect(screen.getByTestId('mock-optimization-chart')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Run AI Audit/i }));
        fireEvent.click(screen.getByRole('button', { name: /Apply_Config/i }));

        expect(onRunAiAudit).toHaveBeenCalled();
        expect(onPromptApply).toHaveBeenCalledWith({ RSI_MIN: 55 });
    });

    it('labels Pine profile results and hides Horus-only deployment actions', () => {
        const onRunAiAudit = jest.fn();
        const onPromptApply = jest.fn();

        render(
            <OptimizationResultsPanel
                simResult={{
                    metrics: {
                        total_return: 6.2,
                        final_value: 106200,
                        trade_count: 5,
                    },
                    source_metadata: {
                        backtest_source: 'PINE_PROFILE',
                        profile_name: 'Draft Pine Breakout',
                        profile_state: 'DRAFT',
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
                }}
                simParams={{ RSI_MIN: 55 }}
                auditLoading={false}
                onRunAiAudit={onRunAiAudit}
                onPromptApply={onPromptApply}
                chartContent={<div data-testid="mock-optimization-chart" />}
            />
        );

        expect(screen.getByText(/Backtest Source: Pine Profile/i)).toBeInTheDocument();
        expect(screen.getByText(/Profile: Draft Pine Breakout/i)).toBeInTheDocument();
        expect(screen.getByText(/Profile State: DRAFT/i)).toBeInTheDocument();
        expect(screen.getByText(/Pine Research Summary/i)).toBeInTheDocument();
        expect(screen.getByText(/Readiness: READY/i)).toBeInTheDocument();
        expect(screen.getByText(/Compatibility: 92.00/i)).toBeInTheDocument();
        expect(screen.getByText(/Performance: 78.00/i)).toBeInTheDocument();
        expect(screen.getByText(/Alignment: 25.00/i)).toBeInTheDocument();
        expect(screen.getByText(/Combined: 62.00/i)).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Apply_Config/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Run AI Audit/i })).not.toBeInTheDocument();
    });

    it('shows fallback placeholders when Pine research summary fields are missing', () => {
        render(
            <OptimizationResultsPanel
                simResult={{
                    metrics: {
                        total_return: 1.1,
                        final_value: 101100,
                        trade_count: 2,
                    },
                    source_metadata: {
                        backtest_source: 'PINE_PROFILE',
                        profile_name: 'Sparse Pine',
                        profile_state: 'READY',
                    },
                    equity_curve: [{ date: '2026-01-01', equity: 100000 }],
                }}
                simParams={{ RSI_MIN: 55 }}
                auditLoading={false}
                onRunAiAudit={jest.fn()}
                onPromptApply={jest.fn()}
                chartContent={<div data-testid="mock-optimization-chart" />}
            />
        );

        expect(screen.getByText(/Pine Research Summary/i)).toBeInTheDocument();
        expect(screen.getByText(/Readiness: --/i)).toBeInTheDocument();
        expect(screen.getByText(/Compatibility: --/i)).toBeInTheDocument();
        expect(screen.getByText(/Performance: --/i)).toBeInTheDocument();
        expect(screen.getByText(/Alignment: --/i)).toBeInTheDocument();
        expect(screen.getByText(/Combined: --/i)).toBeInTheDocument();
    });
});
