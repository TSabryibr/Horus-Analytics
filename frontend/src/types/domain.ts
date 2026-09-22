export interface Strategy {
    name: string;
    win_rate: number;
    total_trades: number;
    profit_factor?: number;
    equity_curve: Array<{ date: string; value: number }>;
    conversion_rate?: number;
    expected_value?: number;
    id?: string;
    status?: string;
    description?: string;
    count?: number;
    max_drawdown?: number;
}

export interface Position {
    ticker: string;
    entry_price: number;
    current_price?: number;
    shares: number;
    status: 'OPEN' | 'CLOSED';
    pnl?: number;
    pnl_pct?: number;
    entry_date?: string;
    exit_date?: string;
    stop_loss?: number;
    target_price?: number;
    target_price_2?: number;
    tp1_hit?: boolean;
    portfolio_id?: number | string;
    pnl_usd?: number;
    pnl_usd_pct?: number;
    signal_id?: string;
}

export interface AuditLog {
    id?: string;
    timestamp: string;
    action: string;
    details: string;
    strategy?: string;
    severity?: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
    metadata?: Record<string, unknown>;
    date: string;
    ticker: string;
    entry_price: number;
    pnl_history?: Record<string, number>;
    converted?: boolean;
}

export interface AnalyticsMetric {
    label: string;
    value: number | string;
    change?: number;
    trend?: 'up' | 'down' | 'neutral';
}

export interface StrategyProposal {
    id: string;
    strategy_name: string;
    proposed_settings?: Record<string, string | number | boolean>;
    changes: Array<{
        parameter: string;
        old_value: string | number;
        new_value: string | number;
        changed: boolean;
    }>;
    status: 'PENDING' | 'APPLIED' | 'REJECTED';
    timestamp: string;
    regime: string;
    regime_score: number;
    volatility: string;
    volatility_value: number;
    reasoning: string;
}

export interface PriceActionCatalogStrategy {
    strategy_id: string;
    display_name: string;
    family: 'INTRADAY' | 'SWING' | 'POSITION';
    summary: string;
    regime: string;
    status: 'DRAFT' | 'READY' | 'RESEARCH';
    warning_only: boolean;
    long_entry_allowed: boolean;
    data_gate?: string | null;
    required_data: string[];
    entry_conditions: string[];
    confirmation_conditions: string[];
    avoidance_rules: string[];
    exit_rules: string[];
    risk_model: string;
    source_attributions: Array<{
        title: string;
        filename: string;
        concept: string;
    }>;
}

export interface PriceActionCatalogResponse {
    status: string;
    count: number;
    counts_by_family: Record<string, number>;
    strategies: PriceActionCatalogStrategy[];
}

export interface PriceActionSignalPreview {
    signal_type: 'BUY' | 'BUY_CANDIDATE' | 'WARNING_ONLY' | 'BLOCKED';
    timeframe_family: 'INTRADAY' | 'SWING' | 'POSITION';
    ticker: string;
    setup_name: string;
    strategy_id: string;
    explanation: string;
    score: number;
    entry_price?: number | null;
    stop_loss?: number | null;
    target_1?: number | null;
    target_2?: number | null;
    confirmations: string[];
    warnings: string[];
    avoidance_flags: string[];
}

export interface PriceActionEvaluateResponse {
    status: string;
    ticker: string;
    signal_count: number;
    signals: PriceActionSignalPreview[];
}

export interface PriceActionBacktestResponse {
    status: string;
    config: {
        strategy_id: string;
        strategy_name: string;
        market: string;
        timeframe: string;
        date_from: string;
        date_to: string;
        capital: number;
        commission_pct: number;
        slippage_pct: number;
    };
    compatibility: {
        readiness: string;
        compatibility_score: number;
        messages: string[];
    };
    metrics: {
        trade_count: number;
        win_rate: number;
        total_return: number;
        final_value: number;
        max_drawdown: number;
        profit_factor: number;
        expectancy: number;
        liquidity_coverage: number;
        warning_conflict_rate: number;
        evaluated_tickers: number;
    };
    ranking: {
        performance_score: number;
        alignment_score: number;
        combined_score: number;
        recommended: boolean;
    };
    promotion_summary: {
        profile_state: string;
        failed_gates: string[];
        thresholds: Record<string, number>;
        actuals: Record<string, string | number>;
    };
    trades: Array<{
        ticker: string;
        entry_date: string;
        exit_date: string;
        entry_price: number;
        exit_price: number;
        pnl: number;
        pnl_pct: number;
        reason: string;
        signal_type: string;
    }>;
}

export interface ReconciledTrade {
    trade_id: number;
    ticker: string;
    signal_id: string;
    currency: string;
    date_executed?: string | null;
    shares: number;
    actual_entry: number;
    theoretical_entry: number;
    slippage_nominal: number;
    slippage_pct: number;
    actual_exit: number;
    decay_pct: number;
    actual_pnl_pct: number;
}

export interface SlippageReportResponse {
    average_slippage_pct: number;
    reconciled_trades_count: number;
    trades: ReconciledTrade[];
    error?: string;
}

export interface LifecycleSummary {
    active_count?: number;
    ambiguous_count?: number;
    total?: number;
    by_state?: Record<string, number>;
    by_lane?: Record<string, number>;
}

export interface FollowUpSummary {
    pending_count?: number;
    ready_count?: number;
    failed_count?: number;
    suppressed_count?: number;
    destination_counts?: Record<string, number>;
    service_tier_counts?: Record<string, number>;
}

export interface SignalStateArchive {
    signal_id: string;
    ticker: string;
    timestamp: string;
    final_status: string;
    signal_score: number;
    filter_snapshot_json: string;
    kill_reason?: string | null;
}
