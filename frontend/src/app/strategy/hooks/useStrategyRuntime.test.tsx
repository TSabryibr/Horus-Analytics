import { act, renderHook } from '@testing-library/react';

import { useStrategyRuntime } from './useStrategyRuntime';

const refreshStrategy = jest.fn();

const proposal = {
    id: 'strategy-1',
    strategy_name: 'Fenrir',
    proposed_settings: {
        RSI_MIN: 58,
        VOL_SPIKE: 1.8,
    },
    changes: [
        { parameter: 'RSI_MIN', old_value: 55, new_value: 58, changed: true },
        { parameter: 'SL_PCT', old_value: 1.5, new_value: 1.5, changed: false },
    ],
    status: 'PENDING' as const,
    timestamp: '2026-03-18T12:00:00Z',
    regime: 'BULLISH',
    regime_score: 8.4,
    volatility: 'ELEVATED',
    volatility_value: 2.1,
    reasoning: 'Momentum and breadth are aligned.',
};

let contextValue = {
    strategy: proposal,
    strategyLoading: false,
    refreshStrategy,
};

jest.mock('../../context/GlobalDataContext', () => ({
    useStrategyData: () => contextValue,
}));

describe('useStrategyRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        contextValue = {
            strategy: proposal,
            strategyLoading: false,
            refreshStrategy,
        };
    });

    it('exposes context state and shapes apply payload from proposed settings', () => {
        const { result } = renderHook(() => useStrategyRuntime());

        expect(result.current.proposal).toEqual(proposal);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.manualMode).toBe(false);
        expect(result.current.buildApplyPayload()).toEqual({
            params: {
                RSI_MIN: 58,
                VOL_SPIKE: 1.8,
            },
        });
        expect(result.current.getRegimeColor('BULLISH')).toContain('text-emerald-400');
    });

    it('toggles manual mode and uses manual params in the apply payload', () => {
        const { result } = renderHook(() => useStrategyRuntime());

        act(() => {
            result.current.toggleManualMode();
            result.current.updateManualParam('RSI_MIN', 60);
        });

        expect(result.current.manualMode).toBe(true);
        expect(result.current.manualParams.RSI_MIN).toBe(60);
        expect(result.current.buildApplyPayload()).toEqual({
            params: {
                ...result.current.manualParams,
            },
            manual: true,
        });
    });

    it('falls back to changed proposal entries when proposed settings are missing', () => {
        contextValue = {
            strategy: {
                ...proposal,
                proposed_settings: undefined,
                changes: [
                    { parameter: 'RSI_MIN', old_value: 55, new_value: 58, changed: true },
                    { parameter: 'SL_PCT', old_value: 1.5, new_value: 1.5, changed: false },
                ],
            },
            strategyLoading: false,
            refreshStrategy,
        };

        const { result } = renderHook(() => useStrategyRuntime());

        expect(result.current.buildApplyPayload()).toEqual({
            params: {
                RSI_MIN: 58,
            },
        });
        expect(result.current.getRegimeColor('SIDEWAYS')).toContain('text-yellow-400');
    });

    it('returns null payload when no proposal exists and manual mode is off', () => {
        contextValue = {
            strategy: null,
            strategyLoading: true,
            refreshStrategy,
        };

        const { result } = renderHook(() => useStrategyRuntime());

        expect(result.current.proposal).toBeNull();
        expect(result.current.isLoading).toBe(true);
        expect(result.current.buildApplyPayload()).toBeNull();
        expect(result.current.getRegimeColor('')).toContain('text-gray-400');
    });
});
