import { act, renderHook, waitFor } from '@testing-library/react';

import { useOptimizerControl } from './useOptimizerControl';

const mockUsePolling = jest.fn();

jest.mock('@/hooks/usePolling', () => ({
    usePolling: (...args: unknown[]) => mockUsePolling(...args),
}));

describe('useOptimizerControl', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
        mockUsePolling.mockClear();
    });

    it('disables polling when the page is not in optimizer mode', () => {
        const showMessage = jest.fn();

        renderHook(() => useOptimizerControl({ mode: 'SIMULATOR', showMessage }));

        expect(mockUsePolling).toHaveBeenCalledWith(
            expect.any(Function),
            expect.objectContaining({ enabled: false })
        );
    });

    it('starts the optimizer and marks the status as preparing on success', async () => {
        const showMessage = jest.fn();
        global.fetch = jest.fn(async (_input: RequestInfo | URL) => ({
            ok: true,
            json: async () => ({ index: 'EGX30' }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useOptimizerControl({ mode: 'OPTIMIZER', showMessage }));

        act(() => {
            result.current.setOptIndex('EGX30');
        });

        await act(async () => {
            await result.current.runOptimizer();
        });

        await waitFor(() => {
            expect(result.current.optLoading).toBe(true);
            expect(String(result.current.optStatus?.status)).toBe('PREPARING');
        });

        expect(showMessage).toHaveBeenCalledWith(null);
    });

    it('reports the backend error message when optimizer start fails', async () => {
        const showMessage = jest.fn();
        global.fetch = jest.fn(async (_input: RequestInfo | URL) => ({
            ok: false,
            json: async () => ({ detail: 'Optimizer is unavailable.' }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useOptimizerControl({ mode: 'OPTIMIZER', showMessage }));

        await act(async () => {
            await result.current.runOptimizer();
        });

        expect(showMessage).toHaveBeenCalledWith({
            type: 'error',
            text: 'Optimizer is unavailable.',
        });
    });
});
