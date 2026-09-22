import { renderHook, act, waitFor } from '@testing-library/react';
import { useArbitrageRuntime } from './useArbitrageRuntime';

const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockMirrors = [
    { Leader: 'COMI', Follower: 'HRHO', Lag: 2, Confidence: 81.2, Type: 'Positive', ZScore: 2.5 },
    { Leader: 'ETEL', Follower: 'FWRY', Lag: 1, Confidence: 71.4, Type: 'Negative', ZScore: -1.5 },
];

function mockJsonResponse(payload: any, ok: boolean = true) {
    return Promise.resolve({
        ok,
        statusText: ok ? 'OK' : 'Bad Request',
        text: async () => JSON.stringify(payload),
    });
}

describe('useArbitrageRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockFetch.mockResolvedValue(mockJsonResponse({ mirrors: mockMirrors }));
    });

    it('loads the default arbitrage universe on mount', async () => {
        const { result } = renderHook(() => useArbitrageRuntime());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.universe).toBe('default');
        expect(result.current.filteredMirrors).toHaveLength(2);
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/arbitrage'),
            expect.objectContaining({
                headers: expect.any(Headers),
            }),
        );
    });

    it('switches to extended universe and refetches data', async () => {
        mockFetch
            .mockResolvedValueOnce(mockJsonResponse({ mirrors: mockMirrors }))
            .mockResolvedValueOnce(mockJsonResponse({ mirrors: [mockMirrors[1]] }));

        const { result } = renderHook(() => useArbitrageRuntime());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        act(() => {
            result.current.setUniverse('extended');
        });

        await waitFor(() => expect(result.current.universe).toBe('extended'));
        await waitFor(() => expect(result.current.filteredMirrors).toHaveLength(1));

        expect(mockFetch).toHaveBeenLastCalledWith(
            expect.stringContaining('/api/v1/arbitrage?universe=extended'),
            expect.objectContaining({
                headers: expect.any(Headers),
            }),
        );
    });

    it('refreshes the current universe on demand', async () => {
        const { result } = renderHook(() => useArbitrageRuntime());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        act(() => {
            result.current.onRefresh();
        });

        await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(2));
        expect(mockFetch).toHaveBeenLastCalledWith(
            expect.stringContaining('/api/v1/arbitrage'),
            expect.objectContaining({
                headers: expect.any(Headers),
            }),
        );
    });

    it('updates filter state and filtered mirrors', async () => {
        const { result } = renderHook(() => useArbitrageRuntime());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        act(() => {
            result.current.setFilter('HRHO');
        });

        expect(result.current.filter).toBe('HRHO');
        expect(result.current.filteredMirrors).toHaveLength(1);
        expect(result.current.filteredMirrors[0].Follower).toBe('HRHO');
    });

    it('handles execute success flow', async () => {
        mockFetch
            .mockResolvedValueOnce(mockJsonResponse({ mirrors: mockMirrors }))
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({ message: 'Executed spread on HRHO' }),
            });

        const { result } = renderHook(() => useArbitrageRuntime());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await act(async () => {
            await result.current.onExecute(mockMirrors[0], 0);
        });

        expect(mockFetch).toHaveBeenLastCalledWith('/api/v1/execute-arbitrage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                leader: 'COMI',
                follower: 'HRHO',
                type: 'Positive',
                z_score: 2.5,
                stop_loss_pct: 1.5,
                take_profit_pct: 2.5,
            }),
        });
        expect(result.current.executing[0]).toBe(false);
        expect(result.current.actionStatus).toEqual({
            id: 0,
            msg: 'Executed spread on HRHO',
            type: 'success',
        });
    });

    it('handles execute failure flow from valid JSON but non-ok response', async () => {
        mockFetch
            .mockResolvedValueOnce(mockJsonResponse({ mirrors: mockMirrors }))
            .mockResolvedValueOnce({
                ok: false,
                json: async () => ({ detail: 'Follower already open' }),
            });

        const { result } = renderHook(() => useArbitrageRuntime());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await act(async () => {
            await result.current.onExecute(mockMirrors[0], 0);
        });

        expect(result.current.executing[0]).toBe(false);
        expect(result.current.actionStatus).toEqual({
            id: 0,
            msg: 'Follower already open',
            type: 'error',
        });
    });

    it('handles network error flow', async () => {
        mockFetch
            .mockResolvedValueOnce(mockJsonResponse({ mirrors: mockMirrors }))
            .mockRejectedValueOnce(new Error('Network error'));

        const { result } = renderHook(() => useArbitrageRuntime());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await act(async () => {
            await result.current.onExecute(mockMirrors[0], 0);
        });

        expect(result.current.executing[0]).toBe(false);
        expect(result.current.actionStatus).toEqual({
            id: 0,
            msg: 'Network error',
            type: 'error',
        });
    });

    it('handles undefined ZScore in execution payload', async () => {
        mockFetch
            .mockResolvedValueOnce(mockJsonResponse({ mirrors: mockMirrors }))
            .mockResolvedValueOnce({ ok: true, json: async () => ({}) });

        const mirrorNoZScore = { ...mockMirrors[0], ZScore: undefined };

        const { result } = renderHook(() => useArbitrageRuntime());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await act(async () => {
            await result.current.onExecute(mirrorNoZScore, 1);
        });

        expect(mockFetch).toHaveBeenLastCalledWith('/api/v1/execute-arbitrage', expect.objectContaining({
            body: expect.stringContaining('"z_score":0'),
        }));
    });
});
