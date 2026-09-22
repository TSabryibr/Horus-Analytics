import { act, renderHook } from '@testing-library/react';

import { useReplay } from './useReplay';

describe('useReplay', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.restoreAllMocks();
    });

    it('submits campaign replay payloads to the campaign endpoint', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/replay/campaign/start') && init?.method === 'POST') {
                expect(JSON.parse(String(init.body))).toEqual({
                    start_date: '2026-05-12',
                    end_date: '2026-05-14',
                    speed: 20,
                    notify: false,
                    report: false,
                    reset_portfolio: false,
                    close_open_positions_end: false,
                    allow_missing_intraday_as_holidays: true,
                    live_channel_routing: true,
                    profile_id: 7,
                });
                return {
                    ok: true,
                    json: async () => ({ status: 'started', mode: 'CAMPAIGN' }),
                } as Response;
            }
            return { ok: true, json: async () => ({ status: 'IDLE' }) } as Response;
        }) as jest.Mock;

        const { result } = renderHook(() => useReplay({ apiBase: 'http://127.0.0.1:8000', selectedProfileId: 7 }));

        act(() => {
            result.current.setReplayMode('CAMPAIGN');
            result.current.setReplayStartDate('2026-05-12');
            result.current.setReplayEndDate('2026-05-14');
            result.current.setReplaySpeed('20');
            result.current.setReplayNotify(false);
            result.current.setReplayReport(false);
            result.current.setReplayResetPortfolio(false);
            result.current.setReplayTreatMissingDaysAsHolidays(true);
            result.current.setReplayLiveChannelRouting(true);
        });

        await act(async () => {
            await result.current.startReplay();
        });

        expect(global.fetch).toHaveBeenCalledWith(
            'http://127.0.0.1:8000/api/v1/replay/campaign/start',
            expect.objectContaining({ method: 'POST' })
        );
    });

    it('shows the backend campaign availability error when campaign start fails', async () => {
        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({
                status: 'error',
                message: 'Missing intraday records: 2026-05-13',
            }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() => useReplay({ apiBase: 'http://127.0.0.1:8000' }));

        act(() => {
            result.current.setReplayMode('CAMPAIGN');
            result.current.setReplayStartDate('2026-05-12');
            result.current.setReplayEndDate('2026-05-14');
        });

        await act(async () => {
            await result.current.startReplay();
        });

        expect(result.current.replayLoading).toBe(false);
        expect(result.current.replayError).toBe('Missing intraday records: 2026-05-13');
    });

    it('does not submit a duplicate start while a replay start is pending', async () => {
        let resolveStart: (() => void) | null = null;
        const pendingStart = new Promise<Response>((resolve) => {
            resolveStart = () => resolve({
                ok: true,
                json: async () => ({ status: 'started', mode: 'CAMPAIGN' }),
            } as Response);
        });
        let startCalls = 0;

        global.fetch = jest.fn((input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/replay/campaign/start') && init?.method === 'POST') {
                startCalls += 1;
                return pendingStart;
            }
            return Promise.resolve({ ok: true, json: async () => ({ status: 'IDLE' }) } as Response);
        }) as jest.Mock;

        const { result, unmount } = renderHook(() => useReplay({ apiBase: 'http://127.0.0.1:8000' }));

        act(() => {
            result.current.setReplayMode('CAMPAIGN');
            result.current.setReplayStartDate('2026-05-12');
            result.current.setReplayEndDate('2026-05-14');
        });

        let firstStart: Promise<void>;
        let secondStart: Promise<void>;
        await act(async () => {
            firstStart = result.current.startReplay();
            secondStart = result.current.startReplay();
            resolveStart?.();
            await Promise.all([firstStart, secondStart]);
        });

        expect(startCalls).toBe(1);
        unmount();
    });
});
