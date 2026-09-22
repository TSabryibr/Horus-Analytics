import { renderHook } from '@testing-library/react';
import useSWR from 'swr';
import { useMarketRuntime } from './useMarketRuntime';

// ── Mocks ────────────────────────────────────────────────────────────────────
jest.mock('swr', () => ({
    __esModule: true,
    default: jest.fn(),
}));

jest.mock('../lib/marketTransforms', () => ({
    normalizeTrapsPayload: jest.fn().mockImplementation((val) => val),
    fetchOracleBundle: jest.fn(),
}));

jest.mock('../syncTimestamps', () => ({
    extractSyncTimestamp: jest.fn().mockReturnValue('2026-03-19'),
}));

// ── Tests ────────────────────────────────────────────────────────────────────
describe('useMarketRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Default SWR mock per hook call
        (useSWR as jest.Mock).mockReturnValue({
            data: null,
            isLoading: false,
            mutate: jest.fn(),
        });
    });

    it('returns default context value with initial states', () => {
        const { result } = renderHook(() => useMarketRuntime());

        expect(result.current.sectors).toEqual([]);
        expect(result.current.whales).toBeNull();
        expect(result.current.loading.sectors).toBe(false);
        expect(result.current.lastUpdated.sectors).toBe('2026-03-19');
    });

    it('aggregates loading states correctly', () => {
        (useSWR as jest.Mock).mockImplementation((key) => {
            if (key === '/api/v1/sectors') return { data: null, isLoading: true, mutate: jest.fn() };
            return { data: null, isLoading: false, mutate: jest.fn() };
        });

        const { result } = renderHook(() => useMarketRuntime());

        expect(result.current.loading.sectors).toBe(true);
        expect(result.current.loading.whales).toBe(false);
    });

    it('maps data successfully', () => {
        (useSWR as jest.Mock).mockImplementation((key) => {
            if (key === '/api/v1/sectors') return { data: [{ Ticker: 'COMI' }], isLoading: false, mutate: jest.fn() };
            return { data: null, isLoading: false, mutate: jest.fn() };
        });

        const { result } = renderHook(() => useMarketRuntime());

        expect(result.current.sectors).toHaveLength(1);
    });

    it('only enables scoped market keys for a targeted route', () => {
        renderHook(() =>
            useMarketRuntime({
                enabled: true,
                scope: {
                    sectors: false,
                    whales: false,
                    arbitrage: true,
                    traps: false,
                    strategy: false,
                    oracle: false,
                },
            })
        );

        const keys = (useSWR as jest.Mock).mock.calls.map((call) => call[0]);
        expect(keys).toEqual([
            null,
            null,
            '/api/v1/arbitrage',
            null,
            null,
            null,
        ]);
    });
});
