import { fireEvent, render, screen } from '@testing-library/react';

import { PriceActionLabPanel } from './PriceActionLabPanel';

const baseStrategy = {
    strategy_id: 'ascending_triangle_breakout',
    display_name: 'Ascending Triangle Breakout',
    family: 'SWING' as const,
    summary: 'Bullish continuation through flat resistance.',
    regime: 'BULLISH_CONTINUATION',
    status: 'DRAFT' as const,
    warning_only: false,
    long_entry_allowed: true,
    data_gate: null,
    required_data: ['daily_ohlcv'],
    entry_conditions: ['Breakout close'],
    confirmation_conditions: ['Volume confirmation'],
    avoidance_rules: ['Immediate failure'],
    exit_rules: ['ATR stop'],
    risk_model: 'STRUCTURAL_STOP',
    source_attributions: [],
};

describe('PriceActionLabPanel', () => {
    it('renders catalog items and dispatches primary actions', () => {
        const onEvaluate = jest.fn();
        const onBacktest = jest.fn();
        const onPromote = jest.fn();
        const onActivate = jest.fn();

        render(
            <PriceActionLabPanel
                actionError=""
                actionSuccess=""
                backtestResult={null}
                busyAction={null}
                capital={100000}
                catalogError=""
                catalogLoading={false}
                dateFrom="2025-01-01"
                dateTo="2025-12-31"
                familyFilter="SWING"
                filteredCatalog={[baseStrategy]}
                market="EGX30"
                profileName="EGX Price Action Pack"
                promotedProfile={{ profile_id: 7, profile_name: 'Promoted Profile', source_type: 'PRICE_ACTION', market: 'EGX30', timeframe: '1D', profile_state: 'READY' }}
                selectedStrategy={baseStrategy}
                selectedStrategyId={baseStrategy.strategy_id}
                signals={[]}
                ticker="COMI"
                onActivate={onActivate}
                onBacktest={onBacktest}
                onEvaluate={onEvaluate}
                onPromote={onPromote}
                onReloadCatalog={jest.fn()}
                setCapital={jest.fn()}
                setDateFrom={jest.fn()}
                setDateTo={jest.fn()}
                setFamilyFilter={jest.fn()}
                setMarket={jest.fn()}
                setProfileName={jest.fn()}
                setSelectedStrategyId={jest.fn()}
                setTicker={jest.fn()}
            />,
        );

        expect(screen.getByText('Price Action Lab')).toBeInTheDocument();
        expect(screen.getAllByText('Ascending Triangle Breakout')).toHaveLength(2);

        fireEvent.click(screen.getByRole('button', { name: /^Evaluate$/i }));
        fireEvent.click(screen.getByRole('button', { name: /^Backtest$/i }));
        fireEvent.click(screen.getByRole('button', { name: /^Promote$/i }));
        fireEvent.click(screen.getByRole('button', { name: /^Activate$/i }));

        expect(onEvaluate).toHaveBeenCalledTimes(1);
        expect(onBacktest).toHaveBeenCalledTimes(1);
        expect(onPromote).toHaveBeenCalledTimes(1);
        expect(onActivate).toHaveBeenCalledTimes(1);
    });

    it('renders backtest metrics and promotion state', () => {
        render(
            <PriceActionLabPanel
                actionError=""
                actionSuccess="Backtest completed."
                backtestResult={{
                    status: 'success',
                    config: {
                        strategy_id: baseStrategy.strategy_id,
                        strategy_name: baseStrategy.display_name,
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
                        compatibility_score: 88,
                        messages: ['Daily EGX OHLCV backtest completed.'],
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
                        performance_score: 82,
                        alignment_score: 77,
                        combined_score: 80,
                        recommended: true,
                    },
                    promotion_summary: {
                        profile_state: 'READY',
                        failed_gates: [],
                        thresholds: {},
                        actuals: {},
                    },
                    trades: [],
                }}
                busyAction={null}
                capital={100000}
                catalogError=""
                catalogLoading={false}
                dateFrom="2025-01-01"
                dateTo="2025-12-31"
                familyFilter="SWING"
                filteredCatalog={[baseStrategy]}
                market="EGX30"
                profileName="EGX Price Action Pack"
                promotedProfile={null}
                selectedStrategy={baseStrategy}
                selectedStrategyId={baseStrategy.strategy_id}
                signals={[]}
                ticker="COMI"
                onActivate={jest.fn()}
                onBacktest={jest.fn()}
                onEvaluate={jest.fn()}
                onPromote={jest.fn()}
                onReloadCatalog={jest.fn()}
                setCapital={jest.fn()}
                setDateFrom={jest.fn()}
                setDateTo={jest.fn()}
                setFamilyFilter={jest.fn()}
                setMarket={jest.fn()}
                setProfileName={jest.fn()}
                setSelectedStrategyId={jest.fn()}
                setTicker={jest.fn()}
            />,
        );

        expect(screen.getByText('Backtest completed.')).toBeInTheDocument();
        expect(screen.getByText('12.50%')).toBeInTheDocument();
        expect(screen.getByText(/All gates passed/)).toBeInTheDocument();
        expect(screen.getByText('PASSED ⚡')).toBeInTheDocument();
        expect(screen.getByText('READY')).toBeInTheDocument();
    });
});
