import { renderHook } from '@testing-library/react';
import { useTrapsRuntime } from './useTrapsRuntime';
import { useTrapsData } from '../../context/GlobalDataContext';

jest.mock('../../context/GlobalDataContext', () => ({
    useTrapsData: jest.fn(),
}));

describe('useTrapsRuntime', () => {
    it('initializes with context data and empty fallbacks', () => {
        (useTrapsData as jest.Mock).mockReturnValue({
            traps: null,
            trapsLoading: false,
            refreshTraps: jest.fn(),
        });

        const { result } = renderHook(() => useTrapsRuntime());

        expect(result.current.isLoading).toBe(false);
        expect(result.current.bullTraps).toEqual([]);
        expect(result.current.bearTraps).toEqual([]);
        expect(result.current.hasAnyTraps).toBe(false);
    });

    it('exposes bull and bear traps when data is present', () => {
        (useTrapsData as jest.Mock).mockReturnValue({
            traps: {
                bull_traps: [{ Ticker: 'COMI' }],
                bear_traps: [{ Ticker: 'HRHO' }],
            },
            trapsLoading: true,
            refreshTraps: jest.fn(),
        });

        const { result } = renderHook(() => useTrapsRuntime());

        expect(result.current.isLoading).toBe(true);
        expect(result.current.bullTraps).toHaveLength(1);
        expect(result.current.bearTraps).toHaveLength(1);
        expect(result.current.hasAnyTraps).toBe(true);
    });

    it('identifies partial traps', () => {
        (useTrapsData as jest.Mock).mockReturnValue({
            traps: {
                bull_traps: [],
                bear_traps: [{ Ticker: 'HRHO' }],
            },
            trapsLoading: false,
            refreshTraps: jest.fn(),
        });

        const { result } = renderHook(() => useTrapsRuntime());

        expect(result.current.hasAnyTraps).toBe(true);
    });
});
