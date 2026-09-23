import { z } from 'zod';

export type ReportPeriod = 'weekly' | 'monthly';

// ── Zod schemas ──────────────────────────────────────────────────────────────
const breakdownItemSchema = z.object({
    key: z.string().optional(),
    published_count: z.number().optional(),
    fill_rate_pct: z.number().optional(),
    tp1_hit_rate_pct: z.number().optional(),
    full_win_rate_pct: z.number().optional(),
    stop_loss_rate_pct: z.number().optional(),
    avg_realized_pnl_pct: z.number().optional(),
}).passthrough();

export const analysisResponseSchema = z.object({
    status: z.string().optional(),
    period_type: z.string().optional(),
    period_start: z.string().optional(),
    period_end: z.string().optional(),
    generated_at: z.string().optional(),
    cached: z.boolean().optional(),
    cache_ttl_sec: z.number().optional(),
    cache_age_sec: z.number().optional(),
    market_summary: z.object({
        regime_start: z.string().optional(),
        regime_end: z.string().optional(),
        period_return_pct: z.number().optional(),
        breadth_change_pct: z.number().optional(),
        volatility_context: z.string().optional(),
        key_shifts: z.array(z.string()).optional(),
    }).passthrough().optional(),
    signal_review: z.object({
        review_source: z.string().optional(),
        run_count: z.number().optional(),
        signals_generated: z.number().optional(),
        published_signals: z.number().optional(),
        closed_outcomes: z.number().optional(),
        open_outcomes: z.number().optional(),
        no_trade_outcomes: z.number().optional(),
        win_rate_pct: z.number().optional(),
        avg_pnl_pct: z.number().optional(),
        expectancy_pct: z.number().optional(),
        fill_rate_pct: z.number().optional(),
        expiry_rate_pct: z.number().optional(),
        tp1_hit_rate_pct: z.number().optional(),
        full_win_rate_pct: z.number().optional(),
        stop_loss_rate_pct: z.number().optional(),
        avg_time_to_open_hours: z.number().optional(),
        avg_time_to_resolution_hours: z.number().optional(),
        followup_total: z.number().optional(),
        followup_sent_rate_pct: z.number().optional(),
        followup_failure_rate_pct: z.number().optional(),
        followup_avg_retry_count: z.number().optional(),
        followup_pending_count: z.number().optional(),
        followup_suppressed_count: z.number().optional(),
        lane_breakdown: z.array(breakdownItemSchema).optional(),
        source_module_breakdown: z.array(breakdownItemSchema).optional(),
        operating_mode_breakdown: z.array(breakdownItemSchema).optional(),
        what_worked: z.array(z.string()).optional(),
        what_failed: z.array(z.string()).optional(),
    }).passthrough().optional(),
    recommendations: z.array(z.string()).optional(),
    warnings: z.array(z.string()).optional(),
    notes: z.array(z.string()).optional(),
}).passthrough();

export type AnalysisResponse = z.infer<typeof analysisResponseSchema>;

// ── Extractors ───────────────────────────────────────────────────────────────

export function getWeeklyReportMarketSummary(data: AnalysisResponse | null) {
    return data?.market_summary || {};
}

export function getWeeklyReportSignalReview(data: AnalysisResponse | null) {
    return data?.signal_review || {};
}

export function getWeeklyReportKeyShifts(data: AnalysisResponse | null) {
    return getWeeklyReportMarketSummary(data).key_shifts || [];
}

export function getWeeklyReportWorked(data: AnalysisResponse | null) {
    return getWeeklyReportSignalReview(data).what_worked || [];
}

export function getWeeklyReportFailed(data: AnalysisResponse | null) {
    return getWeeklyReportSignalReview(data).what_failed || [];
}

export function getWeeklyReportWarnings(data: AnalysisResponse | null) {
    return data?.warnings || [];
}

export function getWeeklyReportNotes(data: AnalysisResponse | null) {
    return data?.notes || [];
}

export function getWeeklyReportRecommendations(data: AnalysisResponse | null) {
    return data?.recommendations || [];
}

export function getWeeklyReportCacheInfo(data: AnalysisResponse | null) {
    if (!data) return null;
    return {
        cached: data.cached ?? false,
        ttlSec: data.cache_ttl_sec ?? null,
        ageSec: data.cache_age_sec ?? null,
    };
}
