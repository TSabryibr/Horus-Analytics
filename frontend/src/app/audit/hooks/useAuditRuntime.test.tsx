import { act, renderHook, waitFor } from '@testing-library/react';

import { useAuditRuntime } from './useAuditRuntime';

const auditPayload = {
    status: 'success',
    strategies: [
        {
            name: 'Falcon',
            win_rate: 64,
            conversion_rate: 41,
            expected_value: 1.8,
            count: 12,
            equity_curve: [0, 1.2, 2.1],
        },
        {
            name: 'Wolf',
            win_rate: 58,
            conversion_rate: 35,
            expected_value: 1.1,
            count: 9,
            equity_curve: [0, 0.7, 1.4],
        },
    ],
    logs: [
        {
            date: '2026-02-16',
            ticker: 'COMI',
            strategy: 'Falcon',
            entry_price: 102.4,
            pnl_history: { '1D': 0.5, '3D': 1.0, '5D': 2.1 },
            converted: true,
        },
    ],
};

describe('useAuditRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('loads audit payload and shapes comparison data', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/signals/lifecycle')) {
                return { ok: true, json: async () => ({ summary: { active_count: 2 }, lifecycles: [{ id: 3, ticker: 'COMI', state: 'OPEN', lane: 'swing' }] }) } as Response;
            }
            if (url.includes('/api/v1/signals/followups')) {
                return { ok: true, json: async () => ({ summary: { ready_count: 1 }, followups: [{ id: 7, ticker: 'COMI', trigger_state: 'TP1_HIT', queue_state: 'READY', message_type: 'UPDATE', lane: 'swing' }] }) } as Response;
            }
            return { ok: true, json: async () => auditPayload } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useAuditRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.audit?.status).toBe('success');
            expect(result.current.lifecycleRows).toHaveLength(1);
            expect(result.current.followUpRows).toHaveLength(1);
            expect(result.current.comparisonData).toHaveLength(3);
            expect(result.current.comparisonData[1]?.Falcon).toBe(1.2);
            expect(result.current.comparisonData[2]?.Wolf).toBe(1.4);
        });
    });

    it('re-fetches when the selected day range changes', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/signals/lifecycle')) {
                return { ok: true, json: async () => ({ summary: {}, lifecycles: [] }) } as Response;
            }
            if (url.includes('/api/v1/signals/followups')) {
                return { ok: true, json: async () => ({ summary: {}, followups: [] }) } as Response;
            }
            return { ok: true, json: async () => auditPayload } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useAuditRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        fetchMock.mockClear();

        act(() => {
            result.current.setDays(30);
        });

        await waitFor(() => {
            const hasAuditDaysCall = fetchMock.mock.calls.some(
                (call) => typeof call[0] === 'string' && call[0].includes('/api/v1/audit?days=30'),
            );
            expect(hasAuditDaysCall).toBe(true);
        });
    });

    it('exports the current ledger as CSV rows', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/signals/lifecycle')) {
                return { ok: true, json: async () => ({ summary: {}, lifecycles: [] }) } as Response;
            }
            if (url.includes('/api/v1/signals/followups')) {
                return { ok: true, json: async () => ({ summary: {}, followups: [] }) } as Response;
            }
            return { ok: true, json: async () => auditPayload } as Response;
        }) as jest.Mock;

        const createObjectURLSpy = jest.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test');
        const revokeObjectURLSpy = jest.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
        const appendSpy = jest.spyOn(document.body, 'appendChild');
        const removeSpy = jest.spyOn(document.body, 'removeChild');

        const click = jest.fn();
        const setAttribute = jest.fn();
        const originalCreateElement = document.createElement.bind(document);
        const createElementSpy = jest.spyOn(document, 'createElement').mockImplementation(((tagName: string) => {
            if (tagName.toLowerCase() === 'a') {
                const anchor = originalCreateElement('a');
                anchor.click = click;
                anchor.setAttribute = setAttribute;
                return anchor;
            }
            return originalCreateElement(tagName);
        }) as typeof document.createElement);

        const { result } = renderHook(() => useAuditRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        act(() => {
            result.current.handleExport();
        });

        expect(createObjectURLSpy).toHaveBeenCalled();
        expect(setAttribute).toHaveBeenCalledWith('download', expect.stringContaining('horus_audit_report_'));
        expect(click).toHaveBeenCalledTimes(1);
        expect(appendSpy).toHaveBeenCalled();
        expect(removeSpy).toHaveBeenCalled();

        createElementSpy.mockRestore();
        createObjectURLSpy.mockRestore();
        revokeObjectURLSpy.mockRestore();
    });

    it('suppresses expected offline fetch errors', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        global.fetch = jest.fn(async () => {
            throw new TypeError('Failed to fetch');
        }) as jest.Mock;

        const { result } = renderHook(() => useAuditRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(consoleErrorSpy).not.toHaveBeenCalled();
        consoleErrorSpy.mockRestore();
    });

    it('posts lifecycle overrides and refreshes the ledger', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/signals/lifecycle/5/override')) {
                return { ok: true, json: async () => ({ lifecycle: { id: 5, ticker: 'COMI', state: 'TP2_HIT', lane: 'swing' } }) } as Response;
            }
            if (url.includes('/api/v1/signals/lifecycle')) {
                return { ok: true, json: async () => ({ summary: { active_count: 0 }, lifecycles: [{ id: 5, ticker: 'COMI', state: 'TP2_HIT', lane: 'swing' }] }) } as Response;
            }
            if (url.includes('/api/v1/signals/followups')) {
                return { ok: true, json: async () => ({ summary: {}, followups: [] }) } as Response;
            }
            return { ok: true, json: async () => auditPayload } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useAuditRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        await act(async () => {
            await result.current.overrideLifecycle(5, { action: 'MARK_TP2' });
        });

        expect(fetchMock).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/signals/lifecycle/5/override'),
            expect.objectContaining({ method: 'POST' }),
        );
    });

    it('posts follow-up queue actions and refreshes the queue', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/signals/followups/7/action')) {
                return { ok: true, json: async () => ({ followup: { id: 7, ticker: 'COMI', queue_state: 'SENT' } }) } as Response;
            }
            if (url.includes('/api/v1/signals/lifecycle')) {
                return { ok: true, json: async () => ({ summary: {}, lifecycles: [] }) } as Response;
            }
            if (url.includes('/api/v1/signals/followups')) {
                return { ok: true, json: async () => ({ summary: {}, followups: [{ id: 7, ticker: 'COMI', trigger_state: 'TP1_HIT', queue_state: 'SENT', message_type: 'UPDATE', lane: 'swing' }] }) } as Response;
            }
            return { ok: true, json: async () => auditPayload } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useAuditRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        await act(async () => {
            await result.current.actOnFollowUp(7, 'SEND_NOW');
        });

        expect(fetchMock).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/signals/followups/7/action'),
            expect.objectContaining({ method: 'POST' }),
        );
    });
});
