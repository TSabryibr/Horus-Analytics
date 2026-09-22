'use client';

import { useState } from 'react';

export type SimulationBacktestResult = {
    strategy_id: string;
    market: string;
    start_date: string;
    end_date: string;
    capital: number;
    commission: number;
    slippage: number;
    equity_curve: number[];
    trades: Array<Record<string, any>>;
    total_return: number;
    sharpe: number | null;
    sortino: number | null;
    calmar: number | null;
    max_drawdown: number;
    profit_factor: number;
    expectancy: number;
    win_rate: number;
    trade_count: number;
};

export type PriceActionCatalogItem = {
    strategy_id: string;
    display_name?: string;
};

type UseSimulationBacktestOptions = {
    apiBase: string;
};

export function useSimulationBacktest({ apiBase }: UseSimulationBacktestOptions) {
    const [backtestLoading, setBacktestLoading] = useState(false);
    const [backtestError, setBacktestError] = useState<string | null>(null);
    const [backtestResult, setBacktestResult] = useState<SimulationBacktestResult | null>(null);
    const [strategyCatalog, setStrategyCatalog] = useState<PriceActionCatalogItem[]>([]);
    const [strategyId, setStrategyId] = useState('ascending_triangle_breakout');
    const [backtestMarket, setBacktestMarket] = useState('EGX30');
    const [backtestStartDate, setBacktestStartDate] = useState('');
    const [backtestEndDate, setBacktestEndDate] = useState('');
    const [backtestCapital, setBacktestCapital] = useState('100000');
    const [backtestCommission, setBacktestCommission] = useState('0.05');
    const [backtestSlippage, setBacktestSlippage] = useState('0.1');

    const loadStrategyCatalog = async () => {
        try {
            const res = await fetch(`${apiBase}/api/v1/strategy/price-action/catalog?include_warning_only=false`);
            const json = await res.json();
            if (res.ok && json.status === 'success') {
                const strategies = Array.isArray(json.strategies) ? json.strategies : [];
                setStrategyCatalog(strategies);
                if (strategies.length > 0 && !strategies.some((item: any) => item.strategy_id === strategyId)) {
                    setStrategyId(strategies[0].strategy_id);
                }
            }
        } catch (error) {
            console.error('Failed to load strategy catalog:', error);
        }
    };

    const runBacktest = async () => {
        setBacktestLoading(true);
        setBacktestError(null);
        try {
            const payload = {
                strategy_id: strategyId,
                market: backtestMarket,
                start_date: backtestStartDate,
                end_date: backtestEndDate,
                capital: parseFloat(backtestCapital) || 100000,
                commission: parseFloat(backtestCommission) || 0.05,
                slippage: parseFloat(backtestSlippage) || 0.1,
            };

            const fetchBacktest = async (path: string, bodyPayload: Record<string, any>) => {
                const response = await fetch(`${apiBase}${path}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bodyPayload),
                });
                return response;
            };

            let res = await fetchBacktest('/api/v1/simulation/backtest', payload);
            if (res.status === 404 || res.status === 405) {
                // Backward-compatible fallback to existing strategy endpoint.
                res = await fetchBacktest('/api/v1/strategy/price-action/backtest', {
                    strategy_id: strategyId,
                    market: backtestMarket,
                    date_from: backtestStartDate,
                    date_to: backtestEndDate,
                    capital: payload.capital,
                    commission_pct: payload.commission,
                    slippage_pct: payload.slippage,
                });
            }

            const json = await res.json().catch(() => ({}));
            if (json.status === 'success' && json.data) {
                setBacktestResult(json.data);
            } else if (res.ok && json.metrics && json.equity_curve) {
                // Normalize existing strategy backtest endpoint shape.
                setBacktestResult({
                    strategy_id: strategyId,
                    market: backtestMarket,
                    start_date: backtestStartDate,
                    end_date: backtestEndDate,
                    capital: payload.capital,
                    commission: payload.commission,
                    slippage: payload.slippage,
                    equity_curve: json.equity_curve || [],
                    trades: json.trades || [],
                    total_return: Number(json.metrics?.total_return || 0),
                    sharpe: null,
                    sortino: null,
                    calmar: null,
                    max_drawdown: Number(json.metrics?.max_drawdown || 0),
                    profit_factor: Number(json.metrics?.profit_factor || 0),
                    expectancy: Number(json.metrics?.expectancy || 0),
                    win_rate: Number(json.metrics?.win_rate || 0),
                    trade_count: Number(json.metrics?.trade_count || 0),
                });
            } else {
                setBacktestError(json.detail || json.message || res.statusText || 'Backtest failed.');
            }
        } catch (error) {
            setBacktestError('Backtest failed.');
            console.error('Backtest error:', error);
        } finally {
            setBacktestLoading(false);
        }
    };

    return {
        backtestLoading,
        backtestError,
        backtestResult,
        strategyCatalog,
        strategyId,
        setStrategyId,
        backtestMarket,
        setBacktestMarket,
        backtestStartDate,
        setBacktestStartDate,
        backtestEndDate,
        setBacktestEndDate,
        backtestCapital,
        setBacktestCapital,
        backtestCommission,
        setBacktestCommission,
        backtestSlippage,
        setBacktestSlippage,
        loadStrategyCatalog,
        runBacktest,
    };
}
