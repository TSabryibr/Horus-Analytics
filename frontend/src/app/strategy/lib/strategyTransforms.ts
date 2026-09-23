import { StrategyProposal } from '@/types/domain';

export const defaultManualParams = {
    RSI_MIN: 55,
    RSI_MAX: 85,
    VOL_SPIKE: 1.5,
    MOMENTUM: 2.5,
    SL_PCT: 1.5,
    TP1_PCT: 4.0,
};

export function buildParamsFromStrategyChanges(changes: StrategyProposal['changes'] | undefined) {
    const params: Record<string, string | number | boolean> = {};
    if (!changes) return params;

    changes.forEach((change) => {
        if (!change.changed) return;
        const key = String(change.parameter ?? '').trim();
        if (!key) return;
        const value = change.new_value;
        if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
            params[key] = value;
        }
    });

    return params;
}

export function buildStrategyApplyPayload({
    manualMode,
    manualParams,
    proposal,
}: {
    manualMode: boolean;
    manualParams: Record<string, string | number | boolean>;
    proposal: StrategyProposal | null;
}): { params: Record<string, string | number | boolean>; manual?: boolean } | null {
    if (manualMode) {
        return { params: manualParams, manual: true };
    }
    if (!proposal) return null;

    const proposedSettings = proposal.proposed_settings;
    if (proposedSettings && typeof proposedSettings === 'object') {
        const params: Record<string, string | number | boolean> = {};
        Object.entries(proposedSettings).forEach(([key, value]) => {
            const normalizedKey = key.trim();
            if (!normalizedKey) return;
            if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
                params[normalizedKey] = value;
            }
        });
        if (Object.keys(params).length > 0) {
            return { params };
        }
    }

    const fallbackParams = buildParamsFromStrategyChanges(proposal.changes);
    if (Object.keys(fallbackParams).length > 0) {
        return { params: fallbackParams };
    }

    return null;
}

export function getStrategyRegimeColor(regime: string) {
    if (!regime) return 'text-gray-400';
    if (regime.includes('BULLISH')) return 'text-emerald-400 border-emerald-500/50 bg-emerald-900/10';
    if (regime.includes('BEARISH')) return 'text-red-400 border-red-500/50 bg-red-900/10';
    return 'text-yellow-400 border-yellow-500/50 bg-yellow-900/10';
}
