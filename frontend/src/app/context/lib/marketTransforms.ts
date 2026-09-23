import { apiFetch, readJsonSafe } from '@/lib/api';
import { Trap } from '@/types';

/**
 * Special fetcher for Oracle (POST requests bundle).
 */
export async function fetchOracleBundle({ forceRefresh = false, provider }: { forceRefresh?: boolean, provider?: 'OLLAMA' } = {}) {
    const [macroRes, macro70Res, macro100Res, squeezeRes] = await Promise.all([
        apiFetch('/api/v1/prediction', { method: 'POST', body: JSON.stringify({ mode: 'MACRO', index: 'EGX30' }), headers: { 'Content-Type': 'application/json' } }),
        apiFetch('/api/v1/prediction', { method: 'POST', body: JSON.stringify({ mode: 'MACRO', index: 'EGX70' }), headers: { 'Content-Type': 'application/json' } }),
        apiFetch('/api/v1/prediction', { method: 'POST', body: JSON.stringify({ mode: 'MACRO', index: 'EGX100' }), headers: { 'Content-Type': 'application/json' } }),
        apiFetch('/api/v1/prediction', { method: 'POST', body: JSON.stringify({ mode: 'SQUEEZE' }), headers: { 'Content-Type': 'application/json' } }),
    ]);
    const macroJson = await readJsonSafe<any>(macroRes);
    const macro70Json = await readJsonSafe<any>(macro70Res);
    const macro100Json = await readJsonSafe<any>(macro100Res);
    const squeezeJson = await readJsonSafe<any>(squeezeRes);

    const aiPath = provider
        ? `/api/v1/ai/daily-report?provider=${provider}`
        : (
            forceRefresh
                ? '/api/v1/ai/daily-report?force_refresh=true&use_llm=true'
                : '/api/v1/ai/daily-report?use_llm=true'
        );
    const aiReportRes = await apiFetch(aiPath);
    const aiReportJson = await readJsonSafe<any>(aiReportRes);

    return {
        macro: macroJson.status === 'success' ? macroJson.data : null,
        macro70: macro70Json.status === 'success' ? macro70Json.data : null,
        macro100: macro100Json.status === 'success' ? macro100Json.data : null,
        squeeze: squeezeJson.status === 'success' ? squeezeJson.data : null,
        ai_report: aiReportJson.status === 'success' ? aiReportJson : null,
    };
}

/**
 * Normalizes complex traps payload (nested vs flat payloads).
 */
export function normalizeTrapsPayload(raw: unknown): { bull_traps: Trap[]; bear_traps: Trap[] } | null {
    if (!raw || typeof raw !== 'object') {
        return null;
    }

    const source = raw as Record<string, unknown>;
    const nested = source.data && typeof source.data === 'object'
        ? (source.data as Record<string, unknown>)
        : null;

    const trapsSource =
        (Array.isArray(source.bull_traps) || Array.isArray(source.bear_traps))
            ? source
            : (
                nested && (Array.isArray(nested.bull_traps) || Array.isArray(nested.bear_traps))
                    ? nested
                    : null
            );

    if (!trapsSource) {
        return null;
    }

    return {
        bull_traps: Array.isArray(trapsSource.bull_traps) ? (trapsSource.bull_traps as Trap[]) : [],
        bear_traps: Array.isArray(trapsSource.bear_traps) ? (trapsSource.bear_traps as Trap[]) : [],
    };
}
