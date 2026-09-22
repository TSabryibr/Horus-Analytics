export interface Signal {
    ticker: string;
    date: string;
    signal_type: string;
    price: number;
    score: number;
    source?: string;
    [key: string]: string | number | boolean | undefined | null;
}

export interface Position {
    id?: number;
    ticker: string;
    shares: number;
    entry_price: number;
    current_price: number;
    pnl: number;
    pnl_pct: number;
    status: string;
    portfolio_id?: number;
    currency?: string;
    risk_status?: string;
    stop_loss?: number;
    target_price?: number;
    target_price_2?: number;
    target1?: number;
    target2?: number;
    tp1_hit?: boolean;
    entry_date?: string | null;
    exit_date?: string | null;
    pnl_usd?: number;
    pnl_usd_pct?: number;
    signal_id?: string;
    sector?: string;
    notes?: string;
}

export interface PortfolioIntakeResult {
    status: 'completed' | 'partial' | string;
    portfolio_id: number;
    created: number;
    updated: number;
    errors: string[];
    report_summary?: {
        open_positions?: number;
        winners?: number;
        losers?: number;
        total_cost_basis?: number;
        market_value?: number;
        unrealized_pnl?: number;
        unrealized_pnl_pct?: number;
        action_items?: number;
    };
}

export interface Portfolio {
    id: number;
    name: string;
    type: string;
    positions: Position[];
}

export interface WhaleCandidate {
    Ticker: string;
    Sector: string;
    Signal: string;
    Strength: number;
    Price_Trend?: string;
    Volume_Trend?: string;
    Last_Price?: number;
    Flow_EGP_Millions?: number;
    Support_Anchor?: number;
    Resistance_Anchor?: number;
}

export interface SectorStat {
    Sector: string;
    Momentum: number;
    Rotation_Score: number;
    Trend: string;
    Volume_Flow?: number;
}

export interface Trap {
    Ticker: string;
    Date: string;
    Price: number;
    'Fakeout_Depth_%': number;
    Volume?: number;
    Avg_Volume?: number;
    Details?: string;
    Wick_Ratio?: number;
}

export interface AuditLog {
    timestamp: string;
    level: string;
    message: string;
    module: string;
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

export interface ArbitrageMirror {
    Ticker: string;
    Lead_Ticker: string;
    Correlation: number;
    Lag_Days: number;
    Signal: string;
}

export interface NewsItem {
    Source?: string;
    source?: string; // Support both cases
    Headline?: string;
    title?: string;
    Sentiment?: "Positive" | "Negative" | "Neutral";
    Date?: string;
    URL?: string;
    link?: string;
    summary?: string;
    tickers?: string[];
    gossip_score?: number;
}

export interface BifrostSentiment {
    score: number;
    regime: string;
    bull_count?: number;
    bear_count?: number;
    total_hits?: number;
    sample_size?: number;
}

export interface AiMarketDirection {
    label: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    confidence: number;
    time_horizon: string;
    reasoning: string[];
}

export interface AiRecommendation {
    ticker: string;
    action: 'BUY' | 'SELL' | 'HOLD' | 'WATCH';
    confidence: number;
    risk: string;
    rationale: string;
    entry_zone: string;
    stop_loss: string;
    take_profit: string;
    horizon: string;
}

export interface AiDailyReport {
    status: string;
    generated_at: string;
    source: string;
    source_module?: string;
    report_mode?: 'LOCAL' | 'OLLAMA' | 'OLLAMA_FALLBACK' | string;
    fallback_reason?: string;
    degraded?: boolean;
    ollama_start_attempted?: boolean;
    ollama_ready?: boolean;
    ollama_shutdown_attempted?: boolean;
    ollama_shutdown_ok?: boolean;
    ollama_lifecycle_reason?: string | null;
    cached?: boolean;
    cache_ttl_sec?: number;
    cache_age_sec?: number;
    llm_error?: string;
    data_freshness?: {
        score: number;
        label: 'FRESH' | 'WARM' | 'STALE' | string;
        max_age_sec?: number;
        ages_sec?: Record<string, number | null>;
    };
    headline: string;
    market_direction: AiMarketDirection;
    daily_report: {
        summary: string[];
        cross_tab_findings: string[];
    };
    recommendations: AiRecommendation[];
    risk_warnings: string[];
    next_checklist: string[];
    shadow_context?: {
        rollout_mode?: string;
        supportive_whale_alignments: number;
        whale_conflicts: number;
        high_trap_risk_count: number;
        severe_trap_risk_count: number;
        top_trap_risk_reasons?: Record<string, number>;
        threshold_analysis?: {
            rollout_mode?: string;
            would_review_count: number;
            would_block_count: number;
            top_block_reasons?: Record<string, number>;
        };
        top_supportive_names?: Array<{ ticker: string; whale_signal?: string; whale_strength?: number; score?: number; trap_risk_band?: string }>;
        top_conflicted_or_high_risk_names?: Array<{ ticker: string; trap_risk_band?: string; trap_risk_score?: number; trap_risk_reason?: string; whale_alignment?: string; score?: number }>;
    };
    promotion_context?: {
        market_segments?: Record<string, {
            previous_active_profile?: string;
            new_active_profile?: string;
            rollback_profile?: string;
            promotion_scope?: string;
            promotion_rationale?: string;
            promotion_evidence?: Record<string, unknown>;
        }>;
    };
    input_snapshot?: Record<string, unknown>;
}

export interface OracleData {
    macro: {
        Cycle: string;
        Health_Score: number;
        Outlook: string;
        Reasons?: string[];
        price_history: Record<string, number>;
        breadth_history: Record<string, number>;
        signal: string;
        correlation: number;
        message: string;
    } | null;
    macro70?: {
        Cycle: string;
        Health_Score: number;
        Outlook: string;
        Reasons?: string[];
        price_history: Record<string, number>;
        breadth_history: Record<string, number>;
        signal: string;
        correlation: number;
        message: string;
    } | null;
    macro100?: {
        Cycle: string;
        Health_Score: number;
        Outlook: string;
        Reasons?: string[];
        price_history: Record<string, number>;
        breadth_history: Record<string, number>;
        signal: string;
        correlation: number;
        message: string;
    } | null;
    squeeze: {
        Candidates: Array<{ Ticker: string; Probability: number; Sector?: string; Price?: number; BandWidth?: number }>;
        Market_Condition?: string;
        status?: string;
        count?: number;
    } | null;
    ai_report?: AiDailyReport | null;
}

export interface GlobalDataState {
    news: NewsItem[];
    newsSentiment: BifrostSentiment | null;
    sectors: SectorStat[];
    whales: { candidates: WhaleCandidate[] } | null;
    arbitrage: { mirrors: ArbitrageMirror[] } | null;
    traps: { bull_traps: Trap[], bear_traps: Trap[] } | null;
    strategy: StrategyProposal | null;
    oracle: OracleData | null;
}

export interface HealthDiagnosis {
    ticker: string;
    signals: string[];
    risk_level?: string;
}

export interface PortfolioHealth {
    status: string;
    diagnoses: HealthDiagnosis[];
}

export interface MetricData {
    total_trades: number;
    total_pnl: number;
    unrealized_pnl: number;
    win_rate: number;
    profit_factor: number;
}

export interface EquityPoint {
    date: string;
    equity: number;
}

export interface SystemHealth {
    win_rate: number;
    avg_gain: number;
}

export type DashboardDataSource = 'LIVE' | 'FALLBACK' | 'LOADING';

export interface DashboardState {
    metrics: MetricData | null;
    curve: EquityPoint[];
    signals: Signal[];
    health: SystemHealth | null;
    dataSource: DashboardDataSource;
    loading: boolean;
    error: string | null;
    portfolioId: number | null;
    lastSync: Date | null;
}

export interface ScannerSignal {
    Ticker: string;
    Signal_Type: string;
    Signal_Setup?: string;
    Conviction?: string;
    Entry_Price: number;
    Stop_Loss: number;
    Target_Price: number;
    Target_Price_2?: number;
    Score: number;
    Volume_x: number;
    VSA_Valid?: boolean | null;
    Volume_Mult_20?: number | null;
    Validation_Profile?: string | null;
    Route_Profile?: string | null;
    Liquidity_Tier?: string | null;
    Sector_RS_14?: number | null;
    Routing_Reason?: string | null;
    Whale_Signal?: string | null;
    Whale_Strength?: number | null;
    Whale_Alignment?: string | null;
    Whale_Reason?: string | null;
    Trap_Risk?: string | number | null;
    Trap_Risk_Score?: number | null;
    Trap_Risk_Band?: string | null;
    Trap_Risk_Reason?: string | null;
    Enforcement_State?: string | null;
    Enforcement_Visibility?: string | null;
    Enforcement_Reason?: string | null;
    Enforcement_Notes?: string | null;
    Enforcement_Profile?: string | null;
    Expected_Slippage_Pct?: number | null;
    Execution_Cap_Shares?: number | null;
}

export interface ScannerStrategyProfileAudit {
    profile_id?: number;
    profile_name: string;
    source_type: string;
    market: string;
    timeframe: string;
    profile_state?: string;
    created_at?: string | null;
    ready_at?: string | null;
    activated_at?: string | null;
    activation_count?: number;
    backtest_summary?: {
        total_return?: number;
        trade_count?: number;
        win_rate?: number;
        max_drawdown?: number;
    };
    compatibility_summary?: {
        readiness?: string;
        compatibility_score?: number;
        messages?: string[];
    };
    promotion_summary?: {
        profile_state?: string;
        failed_gates?: string[];
        thresholds?: Record<string, number>;
        actuals?: Record<string, string | number>;
    };
    ranking_summary?: {
        performance_score?: number;
        alignment_score?: number;
        combined_score?: number;
        recommended?: boolean;
    };
    activation_history?: Array<{
        event_type: string;
        activated_at: string;
        previous_state?: string | null;
        previous_active_profile_id?: number | null;
        previous_active_profile_name?: string | null;
    }>;
}

export interface ScannerData {
    regime: string;
    breadth: number;
    signals_count: number;
    signals: ScannerSignal[];
    strategy_profile?: ScannerStrategyProfileAudit;
    whale_trap_diagnostics?: {
        rollout_mode?: string;
        supportive_whale_alignments: number;
        whale_conflicts: number;
        high_trap_risk_count: number;
        severe_trap_risk_count: number;
        top_trap_risk_reasons?: Record<string, number>;
        threshold_analysis?: {
            rollout_mode?: string;
            would_review_count: number;
            would_block_count: number;
            top_block_reasons?: Record<string, number>;
        };
    };
    enforcement_diagnostics?: {
        rollout_mode?: string;
        allow_count: number;
        watch_only_count: number;
        block_count: number;
        counts_by_reason?: Record<string, number>;
        counts_by_profile?: Record<string, { allow_count: number; watch_only_count: number; block_count: number }>;
        counts_by_market_segment?: Record<string, { allow_count: number; watch_only_count: number; block_count: number }>;
    };
    calibration_diagnostics?: {
        rollout_mode?: string;
        market_segments?: Record<string, {
            active_enforcement_profile: string;
            previous_active_profile?: string;
            new_active_profile?: string;
            rollback_profile?: string;
            promotion_scope?: string;
            promotion_rationale?: string;
            promotion_evidence?: Record<string, unknown>;
            candidate_calibration_profiles: string[];
            calibration_summary: {
                baseline_counts: { allow_count: number; watch_only_count: number; block_count: number };
                candidates: Record<string, {
                    counts: { allow_count: number; watch_only_count: number; block_count: number };
                    deltas: {
                        allow_delta: number;
                        watch_only_delta: number;
                        block_delta: number;
                        reason_deltas?: Record<string, number>;
                    };
                    top_delta_reasons?: Array<{ reason: string; delta: number }>;
                    top_reclassified_names?: Array<{
                        ticker: string;
                        baseline_state: string;
                        candidate_state: string;
                        baseline_reason: string;
                        candidate_reason: string;
                        market_segment?: string;
                    }>;
                }>;
            };
        }>;
        top_delta_reasons?: Array<{ reason: string; delta: number }>;
        top_reclassified_names?: Array<{
            ticker: string;
            baseline_state: string;
            candidate_state: string;
            baseline_reason: string;
            candidate_reason: string;
            market_segment?: string;
        }>;
    };
}

export interface AnalyticsItem {
    [key: string]: string | number | boolean | undefined | null; // Allow indexing for sorting
    Ticker: string;
    Price: number;
    Signal_Score: number;
    Status: string;
    Trend: 'BULLISH' | 'BEARISH';
    RSI: number;
    Target_1: number;
    Target_2: number;
    Risk_Reward_Ratio: number;
    Stop_Loss: number;
    Avg_Turnover_M: number;
    ATR: number;
    Institutional_Signal?: string;
}

export interface AddPositionPayload {
    ticker: string;
    shares: number;
    price: number;
    sl: number | null;
    target_price: number | null;
    target_price_2: number | null;
    date: string | null;
    portfolio_id: number;
}

export interface UpdatePositionPayload {
    ticker: string;
    sl: number | null;
    target_price: number | null;
    target_price_2: number | null;
    portfolio_id: number;
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

export interface SignalStateArchive {
    signal_id: string;
    ticker: string;
    timestamp: string;
    final_status: string;
    signal_score: number;
    filter_snapshot_json: string;
    kill_reason?: string | null;
}
