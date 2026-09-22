import { act, renderHook } from '@testing-library/react';

import { useWhaleChartModal } from './useWhaleChartModal';

const swrMock = jest.fn();

jest.mock('swr', () => ({
    __esModule: true,
    default: (...args: any[]) => swrMock(...args),
}));

describe('useWhaleChartModal', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        swrMock.mockReturnValue({
            data: null,
            isLoading: false,
        });
    });

    it('opens and closes the selected ticker and derives the SWR key', () => {
        const { result } = renderHook(() => useWhaleChartModal());

        expect(result.current.selectedTicker).toBeNull();
        expect(swrMock).toHaveBeenCalledWith(null, expect.any(Function));

        act(() => {
            result.current.openTicker('COMI');
        });

        expect(result.current.selectedTicker).toBe('COMI');
        expect(swrMock).toHaveBeenLastCalledWith(
            '/api/v1/data/ticker/COMI?limit=100&obv=true',
            expect.any(Function),
        );

        act(() => {
            result.current.closeTicker();
        });

        expect(result.current.selectedTicker).toBeNull();
    });

    it('maps history into chart and OBV series', () => {
        swrMock.mockReturnValue({
            data: [
                {
                    Date: '2026-03-18 00:00:00',
                    Open: 100,
                    High: 105,
                    Low: 98,
                    Close: 103,
                    OBV: 12345,
                },
            ],
            isLoading: false,
        });

        const { result } = renderHook(() => useWhaleChartModal('COMI'));

        expect(result.current.chartData).toEqual([
            { time: '2026-03-18', open: 100, high: 105, low: 98, close: 103 },
        ]);
        expect(result.current.obvData).toEqual([
            { time: '2026-03-18', value: 12345 },
        ]);
        expect(result.current.historyLoading).toBe(false);
    });
});
