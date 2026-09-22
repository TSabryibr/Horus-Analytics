import { act, renderHook, waitFor } from '@testing-library/react';

import { useStrategyActions } from './useStrategyActions';

describe('useStrategyActions', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
        global.fetch = jest.fn() as jest.Mock;
    });

    it('applies strategy successfully and sets the AI success toast', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ status: 'applied' }),
        });

        const setErrorMsg = jest.fn();
        const setSuccessMsg = jest.fn();

        const { result } = renderHook(() =>
            useStrategyActions({
                manualMode: false,
                proposal: { id: 'strategy-1' } as any,
                refreshStrategy: jest.fn(),
                buildApplyPayload: () => ({ params: { RSI_MIN: 58 } }),
                setErrorMsg,
                setSuccessMsg,
            }),
        );

        await act(async () => {
            await result.current.applyStrategy();
        });

        await waitFor(() => {
            expect(result.current.applying).toBe(false);
        });

        expect(setErrorMsg).toHaveBeenCalledWith('');
        expect(setSuccessMsg).toHaveBeenCalledWith('Strategy Updated Successfully! Fenrir is active.');
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/strategy/apply'),
            expect.objectContaining({ method: 'POST' }),
        );
    });

    it('applies manual overrides successfully and sets the manual success toast', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ status: 'success' }),
        });

        const setErrorMsg = jest.fn();
        const setSuccessMsg = jest.fn();

        const { result } = renderHook(() =>
            useStrategyActions({
                manualMode: true,
                proposal: null,
                refreshStrategy: jest.fn(),
                buildApplyPayload: () => ({ params: { RSI_MIN: 60 }, manual: true }),
                setErrorMsg,
                setSuccessMsg,
            }),
        );

        await act(async () => {
            await result.current.applyStrategy();
        });

        expect(setSuccessMsg).toHaveBeenCalledWith('Manual Overrides Applied!');
        expect(result.current.applying).toBe(false);
    });

    it('reports API failure and network failure through the error setter', async () => {
        const setErrorMsg = jest.fn();
        const setSuccessMsg = jest.fn();
        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

        (global.fetch as jest.Mock)
            .mockResolvedValueOnce({
                ok: false,
                json: async () => ({ detail: 'Validation failed.' }),
            })
            .mockRejectedValueOnce(new TypeError('Failed to fetch'));

        const { result } = renderHook(() =>
            useStrategyActions({
                manualMode: false,
                proposal: { id: 'strategy-1' } as any,
                refreshStrategy: jest.fn(),
                buildApplyPayload: () => ({ params: { RSI_MIN: 58 } }),
                setErrorMsg,
                setSuccessMsg,
            }),
        );

        await act(async () => {
            await result.current.applyStrategy();
        });

        expect(setErrorMsg).toHaveBeenCalledWith('Validation failed.');

        await act(async () => {
            await result.current.applyStrategy();
        });

        expect(setErrorMsg).toHaveBeenCalledWith('Network error while applying strategy changes.');
        errorSpy.mockRestore();
    });

    it('passes refresh through unchanged', () => {
        const refreshStrategy = jest.fn();

        const { result } = renderHook(() =>
            useStrategyActions({
                manualMode: false,
                proposal: null,
                refreshStrategy,
                buildApplyPayload: () => null,
                setErrorMsg: jest.fn(),
                setSuccessMsg: jest.fn(),
            }),
        );

        act(() => {
            result.current.refresh();
        });

        expect(refreshStrategy).toHaveBeenCalledTimes(1);
    });
});
