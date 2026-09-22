'use client';

import { useCallback, useEffect, useState } from 'react';
import { apiFetch, readJsonSafe } from '@/lib/api';

export interface SystemMetrics {
    win_rate: number;
    avg_pnl_pct: number;
    total_pnl: number;
    profit_factor: number;
    max_drawdown: number;
    avg_holding_days: number;
    total_trades: number;
}

export interface SystemSummary {
    open_positions: number;
    winners: number;
    losers: number;
    best_trade: number;
    worst_trade: number;
}

export interface SignalQualityMetrics {
    generated_count: number;
    active_count: number;
    filled_count: number;
    pending_count: number;
    skipped_count: number;
    failed_count: number;
    no_fill_count: number;
    fill_rate: number;
    no_fill_rate: number;
    no_trade_rate: number;
    outcome_distribution: Record<string, number>;
    execution_state_distribution: Record<string, number>;
}

export interface SystemPerformance {
    portfolio: {
        id: number;
        name: string;
        type: string;
    };
    scope?: 'LANE_EXECUTION' | 'STRATEGY_ATTRIBUTION' | string;
    metrics: SystemMetrics;
    summary: SystemSummary;
    signal_quality?: SignalQualityMetrics;
    attribution?: {
        strategy_profile_names: string[];
        execution_portfolio_ids: number[];
        lanes: string[];
    };
}

export interface SystemComparisonResult {
    count: number;
    portfolios: SystemPerformance[];
}

export interface ExecutionHistoryItem {
    id: number;
    ticker: string;
    state: string;
    trigger: string;
    planned_entry: number;
    actual_entry: number;
    gap_pct: number;
    current_sl: number;
    current_tp: number;
    close_reason: string;
    trade_id: number;
    details: any;
    trailing: any;
    execution_portfolio_id?: number;
    execution_portfolio_name?: string;
    strategy_portfolio_id?: number;
    strategy_portfolio_name?: string;
    lane?: string;
    scan_type?: string;
    strategy_profile_name?: string;
    strategy_source_type?: string;
    created_at: string;
    updated_at: string;
}

export function useSystemPerformance({ activePortfolioId }: { activePortfolioId: number | null }) {
    const [performance, setPerformance] = useState<SystemPerformance | null>(null);
    const [comparison, setComparison] = useState<SystemComparisonResult | null>(null);
    const [executionHistory, setExecutionHistory] = useState<ExecutionHistoryItem[]>([]);
    const [loading, setLoading] = useState(false);

    const refreshSystemData = useCallback(async () => {
        setLoading(true);
        try {
            // Always fetch the system comparison
            const compRes = await apiFetch('/api/v1/portfolio/system-comparison');
            if (compRes.ok) {
                const compJson = await readJsonSafe<SystemComparisonResult>(compRes);
                setComparison(compJson);
            }

            if (!activePortfolioId) {
                setPerformance(null);
                setExecutionHistory([]);
                return;
            }

            const [perfRes, execRes] = await Promise.all([
                apiFetch(`/api/v1/portfolio/performance/${activePortfolioId}`),
                apiFetch(`/api/v1/portfolio/execution-history/${activePortfolioId}?limit=100`)
            ]);

            if (perfRes.ok) {
                const perfJson = await readJsonSafe<SystemPerformance>(perfRes);
                setPerformance(perfJson);
            } else {
                setPerformance(null);
            }

            if (execRes.ok) {
                const execJson = await readJsonSafe<ExecutionHistoryItem[]>(execRes);
                setExecutionHistory(execJson || []);
            } else {
                setExecutionHistory([]);
            }
        } catch (error) {
            console.error('System Performance fetch error:', error);
            setPerformance(null);
            setExecutionHistory([]);
        } finally {
            setLoading(false);
        }
    }, [activePortfolioId]);

    useEffect(() => {
        void refreshSystemData();
    }, [refreshSystemData]);

    return {
        performance,
        comparison,
        executionHistory,
        loading,
        refreshSystemData
    };
}
