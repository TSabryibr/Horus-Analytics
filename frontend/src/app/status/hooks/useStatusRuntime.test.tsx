import React, { StrictMode } from 'react';
import { act, renderHook, waitFor } from '@testing-library/react';

import { resetStatusRuntimeBootstrapCache, useStatusRuntime } from './useStatusRuntime';

const baseStatusPayload = {
    system_ready: true,
    db_connected: true,
    message: 'Running...',
    alerts: {
        telegram: { configured: true },
    },
    scheduler: {
        running: true,
        jobs: [
            { id: 'scan-daily', trigger: 'cron', next_run: '09:00' },
        ],
    },
    data_status: {
        source: { intraday_provider: 'directfn' },
        history: { status: 'FRESH', last_updated: '2026-03-17', file_count: 120, ok: true },
        intraday: { status: 'LIVE', last_bar: '2026-03-18 10:31', age_mins: 1, ok: true },
    },
    metrics: { total_signals: 314, last_signal_date: '2026-03-17' },
};

const baseRuntimeUniversePayload = {
    summary: {
        tracked_count: 270,
        runtime_quarantined_count: 16,
        review_candidate_count: 11,
        counts_by_reason: {
            ACTIVE: 259,
            RIGHTS: 12,
            DORMANT: 4,
            SOURCE_STALE: 11,
        },
    },
    runtime_quarantined: [
        { ticker: 'ADIB_R3', reason: 'RIGHTS' },
        { ticker: 'MEGM', reason: 'DORMANT' },
    ],
    review_candidates: [
        { ticker: 'CPME', reason: 'SOURCE_STALE' },
        { ticker: 'TRTO', reason: 'SOURCE_STALE' },
    ],
};

describe('useStatusRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        jest.setSystemTime(new Date('2026-03-18T12:00:00Z'));
        jest.spyOn(console, 'error').mockImplementation(() => {});
        resetStatusRuntimeBootstrapCache();
    });

    afterEach(() => {
        jest.useRealTimers();
        jest.restoreAllMocks();
    });

    it('loads full status data and shapes runtime metadata', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return { ok: true, json: async () => baseStatusPayload } as Response;
            }
            if (url.includes('/api/v1/data/runtime-universe')) {
                return { ok: true, json: async () => baseRuntimeUniversePayload } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useStatusRuntime());

        expect(result.current.lastRefresh).toBeNull();

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.status?.system_ready).toBe(true);
            expect(result.current.runtimeState.label).toBe('All Systems Go');
            expect(result.current.sourceEngine).toBe('DirectFN Feed');
            expect(result.current.driftValue).toBe('1 Minutes');
            expect(result.current.historySymbolCount).toBe(120);
            expect(result.current.historyAgeHours).toBeGreaterThan(0);
            expect(result.current.status?.runtime_universe?.summary?.runtime_quarantined_count).toBe(16);
        });
    });

    it('refreshes status data and updates the last refresh timestamp', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return { ok: true, json: async () => baseStatusPayload } as Response;
            }
            if (url.includes('/api/v1/data/runtime-universe')) {
                return { ok: true, json: async () => baseRuntimeUniversePayload } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useStatusRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        const firstRefresh = result.current.lastRefresh.getTime();
        jest.setSystemTime(new Date('2026-03-18T12:05:00Z'));

        await act(async () => {
            await result.current.fetchStatus();
        });

        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/system/full-status'))).toHaveLength(2);
        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/data/runtime-universe'))).toHaveLength(2);
        expect(result.current.lastRefresh.getTime()).toBeGreaterThan(firstRefresh);
    });

    it('handles fetch failures without leaving loading stuck', async () => {
        global.fetch = jest.fn(async () => ({ ok: false } as Response)) as jest.Mock;

        const { result } = renderHook(() => useStatusRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.status).toBeNull();
        expect(result.current.runtimeState.label).toBe('Detecting Feed');
        expect(result.current.sourceEngine).toBe('Unknown');
    });

    it('falls back to boot and data status feeds when full status is unavailable', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return { ok: false } as Response;
            }
            if (url.includes('/api/v1/system/boot-status')) {
                return {
                    ok: true,
                    json: async () => ({
                        system_ready: true,
                        db_connected: true,
                        message: 'Data pipeline is fresh.',
                        pipeline_state: 'FRESH',
                        provisioning_status: 'IDLE',
                        freshness: { market_open: true, overall_ok: true },
                        scheduler: { running: true },
                        telegram: { configured: true },
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/data/status')) {
                return { ok: true, json: async () => baseStatusPayload.data_status } as Response;
            }
            if (url.includes('/api/v1/data/runtime-universe')) {
                return { ok: true, json: async () => baseRuntimeUniversePayload } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useStatusRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.status?.system_ready).toBe(true);
            expect(result.current.status?.db_connected).toBe(true);
            expect(result.current.status?.scheduler?.running).toBe(true);
            expect(result.current.status?.data_status?.intraday?.status).toBe('LIVE');
            expect(result.current.runtimeState.label).toBe('All Systems Go');
            expect(result.current.sourceEngine).toBe('DirectFN Feed');
        });

        expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/system/boot-status'))).toBe(true);
        expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/data/status'))).toBe(true);
    });

    it('hydrates from boot and data status feeds when full status is slow', async () => {
        const fetchMock = jest.fn((input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return new Promise<Response>(() => undefined);
            }
            if (url.includes('/api/v1/system/boot-status')) {
                return Promise.resolve({
                    ok: true,
                    json: async () => ({
                        system_ready: true,
                        db_connected: true,
                        message: 'Data pipeline is fresh.',
                        pipeline_state: 'FRESH',
                        provisioning_status: 'IDLE',
                        freshness: { market_open: true, overall_ok: true },
                        scheduler: { running: true },
                        telegram: { configured: true },
                    }),
                } as Response);
            }
            if (url.includes('/api/v1/data/status')) {
                return Promise.resolve({ ok: true, json: async () => baseStatusPayload.data_status } as Response);
            }
            if (url.includes('/api/v1/data/runtime-universe')) {
                return Promise.resolve({ ok: true, json: async () => baseRuntimeUniversePayload } as Response);
            }
            return Promise.resolve({ ok: true, json: async () => ({}) } as Response);
        });
        global.fetch = fetchMock as jest.Mock;

        const { result } = renderHook(() => useStatusRuntime());

        await act(async () => {
            await Promise.resolve();
            await Promise.resolve();
        });

        await act(async () => {
            jest.advanceTimersByTime(1500);
            await Promise.resolve();
            await Promise.resolve();
        });

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.status?.system_ready).toBe(true);
            expect(result.current.status?.data_status?.intraday?.status).toBe('LIVE');
            expect(result.current.runtimeState.label).toBe('All Systems Go');
        });

        expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/system/boot-status'))).toBe(true);
        expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/v1/data/status'))).toBe(true);
    });

    it('treats closed-session history completeness as fresh even when intraday is stale', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({
                ...baseStatusPayload,
                pipeline_state: 'FRESH',
                freshness: { market_open: false },
                data_status: {
                    ...baseStatusPayload.data_status,
                    history: { status: 'FRESH', last_updated: '2026-03-26', file_count: 120, ok: true },
                    intraday: { status: 'STALE', last_bar: '2026-03-26 14:29', age_mins: 2500, ok: false },
                },
            }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useStatusRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
            expect(result.current.runtimeState.label).toBe('All Systems Go');
        });
    });

    it('avoids duplicate initial full-status requests under StrictMode', async () => {
        const fetchMock = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/full-status')) {
                return { ok: true, json: async () => baseStatusPayload } as Response;
            }
            if (url.includes('/api/v1/data/runtime-universe')) {
                return { ok: true, json: async () => baseRuntimeUniversePayload } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <StrictMode>{children}</StrictMode>
        );

        const { result } = renderHook(() => useStatusRuntime(), { wrapper });

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/system/full-status'))).toHaveLength(1);
        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/data/runtime-universe'))).toHaveLength(1);
    });

    it('reuses the initial bootstrap request across a fast remount', async () => {
        let resolveBootFetch: ((value: Response) => void) | null = null;
        let resolveDataStatusFetch: ((value: Response) => void) | null = null;
        let resolveFullStatusFetch: ((value: Response) => void) | null = null;
        let resolveRuntimeFetch: ((value: Response) => void) | null = null;
        const fetchMock = jest.fn((input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/boot-status')) {
                return new Promise<Response>((resolve) => {
                    resolveBootFetch = resolve;
                });
            }
            if (url.includes('/api/v1/data/status')) {
                return new Promise<Response>((resolve) => {
                    resolveDataStatusFetch = resolve;
                });
            }
            if (url.includes('/api/v1/system/full-status')) {
                return new Promise<Response>((resolve) => {
                    resolveFullStatusFetch = resolve;
                });
            }
            if (url.includes('/api/v1/data/runtime-universe')) {
                return new Promise<Response>((resolve) => {
                    resolveRuntimeFetch = resolve;
                });
            }
            return Promise.resolve({ ok: true, json: async () => ({}) } as Response);
        });
        global.fetch = fetchMock as jest.Mock;

        const first = renderHook(() => useStatusRuntime());
        first.unmount();

        const second = renderHook(() => useStatusRuntime());

        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/system/boot-status'))).toHaveLength(1);
        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/data/status'))).toHaveLength(1);

        await act(async () => {
            resolveBootFetch?.({
                ok: true,
                json: async () => ({
                    system_ready: true,
                    db_connected: true,
                    scheduler: { running: true },
                    telegram: { configured: true },
                }),
            } as Response);
            resolveDataStatusFetch?.({ ok: true, json: async () => baseStatusPayload.data_status } as Response);
            await Promise.resolve();
        });

        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/system/full-status'))).toHaveLength(1);

        await act(async () => {
            resolveFullStatusFetch?.({ ok: true, json: async () => baseStatusPayload } as Response);
            await Promise.resolve();
        });

        expect(fetchMock.mock.calls.filter(([input]) => String(input).includes('/api/v1/data/runtime-universe'))).toHaveLength(1);

        await act(async () => {
            resolveRuntimeFetch?.({ ok: true, json: async () => baseRuntimeUniversePayload } as Response);
            await Promise.resolve();
        });

        await waitFor(() => {
            expect(second.result.current.loading).toBe(false);
            expect(second.result.current.status?.system_ready).toBe(true);
            expect(second.result.current.status?.runtime_universe?.summary?.review_candidate_count).toBe(11);
        });
    });

    it('suppresses expected offline bootstrap fetch errors', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        global.fetch = jest.fn(async () => {
            throw new TypeError('Failed to fetch');
        }) as jest.Mock;

        const { result } = renderHook(() => useStatusRuntime());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(result.current.status).toBeNull();
        expect(consoleErrorSpy).not.toHaveBeenCalled();
        consoleErrorSpy.mockRestore();
    });
});
