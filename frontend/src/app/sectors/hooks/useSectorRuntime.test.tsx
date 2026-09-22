import { act, renderHook, waitFor } from '@testing-library/react';

import { useSectorRuntime } from './useSectorRuntime';

const sectorRows = [
    {
        ticker: 'BANKS',
        Sector: 'Banks',
        Status: 'LEADING',
        x: 1.2,
        y: 2.8,
        trail: [{ x: 0.8, y: 2.1 }, { x: 1.2, y: 2.8 }],
    },
    {
        ticker: 'REAL_ESTATE',
        Sector: 'Real Estate',
        Status: 'LAGGING',
        x: -1.5,
        y: -0.3,
        trail: [{ x: -1.0, y: 0.2 }, { x: -1.5, y: -0.3 }],
    },
];

const stockRows = [
    {
        ticker: 'COMI',
        Sector: 'Banks',
        Status: 'IMPROVING',
        x: 0.7,
        y: 0.9,
        trail: [{ x: 0.2, y: 0.4 }, { x: 0.7, y: 0.9 }],
    },
];

describe('useSectorRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.spyOn(console, 'error').mockImplementation(() => { });
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    it('loads sectors data and exposes sorted rankings and quadrant counts', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: 'success', data: sectorRows }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useSectorRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.data).toHaveLength(2);
            expect(result.current.sortedData.map((item) => item.ticker)).toEqual(['BANKS', 'REAL_ESTATE']);
            expect(result.current.quadrantCounts.LEADING).toBe(1);
            expect(result.current.quadrantCounts.LAGGING).toBe(1);
        });
    });

    it('refetches stocks data and applies the sector query when selected', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('view=stocks')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'success', data: stockRows }),
                } as Response;
            }
            return {
                ok: true,
                json: async () => ({ status: 'success', data: sectorRows }),
            } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useSectorRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        act(() => {
            result.current.setViewMode('stocks');
        });

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/rrg?view=stocks&trail=10'));
            expect(result.current.data).toEqual(stockRows);
        });

        act(() => {
            result.current.setSelectedSector('Banks');
        });

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('view=stocks&trail=10&sector=Banks'));
        });
    });

    it('clears loading on fetch failure without crashing the hook', async () => {
        global.fetch = jest.fn(async () => {
            throw new TypeError('Network error');
        }) as jest.Mock;

        const { result } = renderHook(() => useSectorRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.data).toEqual([]);
        expect(result.current.sortedData).toEqual([]);
        expect(result.current.quadrantCounts.LEADING).toBe(0);
    });

    it('suppresses expected offline fetch errors', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        global.fetch = jest.fn(async () => {
            throw new TypeError('Failed to fetch');
        }) as jest.Mock;

        const { result } = renderHook(() => useSectorRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(consoleErrorSpy).not.toHaveBeenCalled();
        consoleErrorSpy.mockRestore();
    });
});
