import { useMemo, useState } from 'react';

import { dedupeReportLines, getSignalColor, normalizeReportLine } from '../lib/oracleTransforms';

export type OracleIndex = 'EGX30' | 'EGX70' | 'EGX100';

export function useOracleRuntime(oracle: any) {
    const [activeIndex, setActiveIndex] = useState<OracleIndex>('EGX30');

    const macro = useMemo(() => {
        if (activeIndex === 'EGX30') return oracle?.macro;
        if (activeIndex === 'EGX70') return oracle?.macro70;
        return oracle?.macro100;
    }, [activeIndex, oracle]);

    const squeeze = oracle?.squeeze;
    const candidates = useMemo(() => {
        const payload = squeeze as { candidates?: any[]; Candidates?: any[] } | undefined;
        return payload ? payload.candidates || payload.Candidates || [] : [];
    }, [squeeze]);

    const aiReport = oracle?.ai_report as any;
    const directionLabel = String(aiReport?.market_direction?.label || 'NEUTRAL').toUpperCase();
    const directionConfidence = Number(aiReport?.market_direction?.confidence || 0);
    const directionColor =
        directionLabel === 'BULLISH'
            ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
            : directionLabel === 'BEARISH'
                ? 'text-rose-400 bg-rose-500/10 border-rose-500/30'
                : 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    const generatedAt = aiReport?.generated_at ? new Date(aiReport.generated_at).toLocaleString() : null;
    const sourceModule = String(aiReport?.source_module || aiReport?.source || 'local');
    const sourceModuleUpper = sourceModule.toUpperCase();
    const sourceProvider =
        sourceModuleUpper === 'LOCAL' ||
            sourceModule.startsWith('local:') ||
            sourceModule.startsWith('rule_engine:') ||
            sourceModule === 'rule_based'
            ? 'LOCAL'
            : 'OLLAMA';
    const sourceProviderColor =
        sourceProvider === 'OLLAMA'
            ? 'text-sky-300 bg-sky-500/10 border-sky-500/30'
            : 'text-slate-300 bg-slate-500/10 border-slate-500/30';
    const sourceModuleColor = sourceProvider === 'OLLAMA' ? 'text-sky-300' : 'text-slate-300';
    const reportMode = String(aiReport?.report_mode || '').toUpperCase();
    const cacheTtlSec = Number(aiReport?.cache_ttl_sec || 0);
    const cacheAgeSec = Number(aiReport?.cache_age_sec || 0);
    const fallbackReason = aiReport?.fallback_reason ? String(aiReport.fallback_reason) : '';
    const lifecycleBadgeLabel =
        reportMode === 'OLLAMA'
            ? 'Generated with Ollama'
            : reportMode === 'OLLAMA_FALLBACK' || (Boolean(aiReport?.degraded) && Boolean(fallbackReason))
                ? 'Local fallback'
                : '';
    const lifecycleBadgeTone =
        lifecycleBadgeLabel === 'Generated with Ollama'
            ? 'text-sky-300 bg-sky-500/10 border-sky-500/30'
            : lifecycleBadgeLabel === 'Local fallback'
                ? 'text-amber-300 bg-amber-500/10 border-amber-500/30'
                : '';
    const freshnessScore = Number(aiReport?.data_freshness?.score || 0);
    const freshnessLabel = String(aiReport?.data_freshness?.label || 'N/A').toUpperCase();
    const freshnessColor =
        freshnessLabel === 'FRESH'
            ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/30'
            : freshnessLabel === 'WARM'
                ? 'text-amber-300 bg-amber-500/10 border-amber-500/30'
                : 'text-rose-300 bg-rose-500/10 border-rose-500/30';

    const summaryLines = useMemo(
        () => dedupeReportLines((aiReport?.daily_report?.summary || []) as string[]).slice(0, 12),
        [aiReport]
    );
    const summaryKeys = useMemo(() => new Set(summaryLines.map(normalizeReportLine)), [summaryLines]);
    const crossTabFindings = useMemo(
        () =>
            dedupeReportLines((aiReport?.daily_report?.cross_tab_findings || []) as string[])
                .filter((line) => !summaryKeys.has(normalizeReportLine(line)))
                .slice(0, 10),
        [aiReport, summaryKeys]
    );
    const overlapKeys = useMemo(
        () => new Set([...summaryLines, ...crossTabFindings].map(normalizeReportLine)),
        [summaryLines, crossTabFindings]
    );
    const directionReasoning = useMemo(
        () =>
            dedupeReportLines((aiReport?.market_direction?.reasoning || []) as string[])
                .filter((line) => !overlapKeys.has(normalizeReportLine(line)))
                .slice(0, 10),
        [aiReport, overlapKeys]
    );
    const macroSignalColor = useMemo(() => getSignalColor(macro?.signal || ''), [macro?.signal]);
    const chartData = useMemo(() => {
        if (!macro?.price_history) return [];
        return Object.keys(macro.price_history).map((date) => ({
            date: new Date(Number(date)).toLocaleDateString(),
            price: macro.price_history[date],
            breadth: macro.breadth_history?.[date],
        }));
    }, [macro]);

    return {
        activeIndex,
        setActiveIndex,
        macro,
        squeeze,
        candidates,
        aiReport,
        directionLabel,
        directionConfidence,
        directionColor,
        generatedAt,
        sourceModule,
        sourceProvider,
        sourceProviderColor,
        sourceModuleColor,
        lifecycleBadgeLabel,
        lifecycleBadgeTone,
        cacheTtlSec,
        cacheAgeSec,
        fallbackReason,
        freshnessScore,
        freshnessLabel,
        freshnessColor,
        summaryLines,
        crossTabFindings,
        directionReasoning,
        macroSignalColor,
        chartData,
    };
}
