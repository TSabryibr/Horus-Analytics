/**
 * Unit tests for useNewsRuntime.ts.
 * Verifies score normalization and data proxying from the global context.
 */

import { renderHook } from '@testing-library/react';
import { useNewsRuntime } from './useNewsRuntime';

// -- Mock Context Setup -----------------------------------------------------

const mockRefresh = jest.fn();

let mockContextValue: any = {
    news: [{ title: 'Test', source: 'MockWire' }],
    newsSentiment: {
        score: 75.5,
        regime: 'EUXUBERANT GREED',
        bull_count: 5,
        bear_count: 1,
    },
    newsLoading: false,
    refreshNews: mockRefresh,
};

jest.mock('../../context/GlobalDataContext', () => ({
    useNewsData: () => mockContextValue,
}));

// -- Tests --------------------------------------------------------------------

describe('useNewsRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockContextValue = {
            news: [{ title: 'Test', source: 'MockWire' }],
            newsSentiment: {
                score: 75.5,
                regime: 'EUXUBERANT GREED',
                bull_count: 5,
                bear_count: 1,
            },
            newsLoading: false,
            refreshNews: mockRefresh,
        };
    });

    it('proxies news data and refresh from context', () => {
        const { result } = renderHook(() => useNewsRuntime());

        expect(result.current.news).toHaveLength(1);
        expect(result.current.newsLoading).toBe(false);
        expect(typeof result.current.onRefresh).toBe('function');
        result.current.onRefresh();
        expect(mockRefresh).toHaveBeenCalled();
    });

    it('pre-computes normalized sentiment scores', () => {
        const { result } = renderHook(() => useNewsRuntime());

        expect(result.current.bifrostScore).toBe(75.5);
        expect(result.current.bifrostRegime).toBe('EUXUBERANT GREED');
        expect(result.current.bifrostBull).toBe(5);
        expect(result.current.bifrostBear).toBe(1);
    });

    it('falls back to default neutral scores when sentiment is missing', () => {
        // override mock output for this specific test
        mockContextValue = {
            news: [],
            newsSentiment: null, // Critical missing state
            newsLoading: false,
            refreshNews: jest.fn(),
        };

        const { result } = renderHook(() => useNewsRuntime());

        expect(result.current.bifrostScore).toBe(50);
        expect(result.current.bifrostRegime).toBe('BORING MORTALS');
        expect(result.current.bifrostBull).toBe(0);
        expect(result.current.bifrostBear).toBe(0);
    });
});
