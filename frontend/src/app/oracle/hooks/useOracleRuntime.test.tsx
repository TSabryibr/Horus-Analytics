import { act, renderHook } from '@testing-library/react';

import { useOracleRuntime } from './useOracleRuntime';

const oraclePayload = {
    macro: {
        signal: 'BULLISH',
        correlation: 0.74,
        message: 'Breadth confirms index trend.',
        price_history: {
            '1708128000000': 25000,
            '1708214400000': 25120,
        },
        breadth_history: {
            '1708128000000': 58.2,
            '1708214400000': 61.1,
        },
    },
    macro70: {
        signal: 'BEARISH',
        correlation: -0.12,
        message: 'Breadth is fading.',
        price_history: {
            '1708128000000': 12000,
        },
        breadth_history: {
            '1708128000000': 41.4,
        },
    },
    squeeze: {
        status: 'found',
        count: 1,
        Candidates: [{ Ticker: 'HRHO', Sector: 'Industrials', Price: 37.8, BandWidth: 0.0122 }],
    },
    ai_report: {
        report_mode: 'LOCAL',
        source_module: 'local:oracle',
        cache_ttl_sec: 300,
        cache_age_sec: 12,
        market_direction: {
            label: 'bullish',
            confidence: 71,
            reasoning: ['Confluence builds', 'Confluence builds', 'Unique risk'],
        },
        daily_report: {
            summary: [' Alpha  ', 'alpha', 'Beta'],
            cross_tab_findings: ['beta', 'Gamma', 'Gamma'],
        },
        data_freshness: {
            score: 82,
            label: 'fresh',
        },
    },
};

describe('useOracleRuntime', () => {
    it('switches the active index and selects the matching macro payload', () => {
        const { result } = renderHook(() => useOracleRuntime(oraclePayload as any));

        expect(result.current.activeIndex).toBe('EGX30');
        expect(result.current.macro?.signal).toBe('BULLISH');
        expect(result.current.chartData).toHaveLength(2);

        act(() => {
            result.current.setActiveIndex('EGX70');
        });

        expect(result.current.activeIndex).toBe('EGX70');
        expect(result.current.macro?.signal).toBe('BEARISH');
        expect(result.current.chartData).toHaveLength(1);
    });

    it('dedupes summary lines and filters overlaps from cross-tab findings and reasoning', () => {
        const { result } = renderHook(() => useOracleRuntime(oraclePayload as any));

        expect(result.current.summaryLines).toEqual(['Alpha', 'Beta']);
        expect(result.current.crossTabFindings).toEqual(['Gamma']);
        expect(result.current.directionReasoning).toEqual(['Confluence builds', 'Unique risk']);
    });

    it('normalizes provider, freshness, and squeeze candidates with sane fallbacks', () => {
        const { result } = renderHook(() => useOracleRuntime(oraclePayload as any));

        expect(result.current.sourceProvider).toBe('LOCAL');
        expect(result.current.freshnessLabel).toBe('FRESH');
        expect(result.current.directionLabel).toBe('BULLISH');
        expect(result.current.candidates).toEqual(oraclePayload.squeeze.Candidates);
        expect(result.current.lifecycleBadgeLabel).toBe('');
    });

    it('maps successful Ollama reports to a generated-with-ollama badge', () => {
        const payload = {
            ...oraclePayload,
            ai_report: {
                ...oraclePayload.ai_report,
                report_mode: 'OLLAMA',
                source_module: 'OLLAMA',
            },
        };

        const { result } = renderHook(() => useOracleRuntime(payload as any));

        expect(result.current.lifecycleBadgeLabel).toBe('Generated with Ollama');
        expect(result.current.lifecycleBadgeTone).toContain('text-sky-300');
    });

    it('maps Ollama fallback reports to a local fallback badge', () => {
        const payload = {
            ...oraclePayload,
            ai_report: {
                ...oraclePayload.ai_report,
                report_mode: 'OLLAMA_FALLBACK',
                source_module: 'LOCAL',
                degraded: true,
                fallback_reason: 'Ollama service failed to start.',
            },
        };

        const { result } = renderHook(() => useOracleRuntime(payload as any));

        expect(result.current.lifecycleBadgeLabel).toBe('Local fallback');
        expect(result.current.lifecycleBadgeTone).toContain('text-amber-300');
    });
});
