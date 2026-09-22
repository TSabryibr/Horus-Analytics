import { act, renderHook, waitFor } from '@testing-library/react';

import { useOptimizationAudit } from './useOptimizationAudit';

describe('useOptimizationAudit', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
    });

    it('opens the audit drawer with the returned audit result on success', async () => {
        const showMessage = jest.fn();
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({
                analysis: {
                    robustness_score: 88,
                    suggested_parameters: { RSI_MIN: 52 },
                },
            }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useOptimizationAudit({ showMessage }));

        await act(async () => {
            await result.current.runAiAudit();
        });

        await waitFor(() => {
            expect(result.current.auditLoading).toBe(false);
            expect(result.current.isAuditOpen).toBe(true);
            expect(result.current.auditResult?.analysis?.robustness_score).toBe(88);
        });
    });

    it('commits the audit result and closes the drawer on success', async () => {
        const showMessage = jest.fn();
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/strategy/propose-from-lab')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'success' }),
                } as Response;
            }
            return {
                ok: true,
                json: async () => ({
                    analysis: {
                        robustness_score: 88,
                        suggested_parameters: { RSI_MIN: 52 },
                    },
                }),
            } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useOptimizationAudit({ showMessage }));

        act(() => {
            result.current.setAuditResult({ analysis: { suggested_parameters: { RSI_MIN: 52 } } });
            result.current.setIsAuditOpen(true);
        });

        await act(async () => {
            await result.current.commitAuditResult({ analysis: { suggested_parameters: { RSI_MIN: 52 } } });
        });

        expect(result.current.committingAudit).toBe(false);
        expect(result.current.isAuditOpen).toBe(false);
        expect(showMessage).toHaveBeenCalledWith({
            type: 'success',
            text: 'Proposal committed to Strategy Core!',
        });
    });
});
