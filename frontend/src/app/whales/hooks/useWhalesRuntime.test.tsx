import { act, renderHook } from '@testing-library/react';

import { useWhalesRuntime } from './useWhalesRuntime';

const refreshWhales = jest.fn();

function mockContext(overrides: Record<string, any> = {}) {
    return {
        whales: {
            candidates: [
                {
                    Ticker: 'COMI',
                    Sector: 'Banks',
                    Signal: 'ACCUMULATION',
                    Last_Price: 103.2567,
                    Strength: 1.82,
                },
                {
                    Ticker: 'HRHO',
                    Sector: 'Industrials',
                    Signal: 'DISTRIBUTION',
                    Last_Price: 37.1599,
                    Strength: 1.21,
                },
                {
                    Ticker: 'SWDY',
                    Sector: 'Banks',
                    Signal: 'ACCUMULATION',
                    Last_Price: undefined,
                    Strength: 0.77,
                },
            ],
        },
        whalesLoading: false,
        refreshWhales,
        ...overrides,
    };
}

let contextValue = mockContext();

jest.mock('../../context/GlobalDataContext', () => ({
    useWhalesData: () => contextValue,
}));

describe('useWhalesRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        contextValue = mockContext();
    });

    it('exposes loading state, filtered candidates, and sorted sector summaries', () => {
        const { result } = renderHook(() => useWhalesRuntime());

        expect(result.current.isLoading).toBe(false);
        expect(result.current.filteredWhales).toHaveLength(3);
        expect(result.current.sortedSectors).toEqual([
            { name: 'Banks', count: 2, accumulation: 2, distribution: 0 },
            { name: 'Industrials', count: 1, accumulation: 0, distribution: 1 },
        ]);
    });

    it('filters by ticker and sector case-insensitively', () => {
        const { result } = renderHook(() => useWhalesRuntime());

        act(() => {
            result.current.setFilter('comi');
        });

        expect(result.current.filteredWhales.map((candidate) => candidate.Ticker)).toEqual(['COMI']);

        act(() => {
            result.current.setFilter('bank');
        });

        expect(result.current.filteredWhales.map((candidate) => candidate.Ticker)).toEqual(['COMI', 'SWDY']);
    });

    it('truncates prices using the current display contract', () => {
        const { result } = renderHook(() => useWhalesRuntime());

        expect(result.current.truncatePrice(103.2567)).toBe('103.256');
        expect(result.current.truncatePrice(37.1599)).toBe('37.159');
        expect(result.current.truncatePrice(undefined)).toBe('0.000');
    });
});
