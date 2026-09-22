import { act, renderHook, waitFor } from '@testing-library/react';

import { useHomeRuntime } from './useHomeRuntime';

const mockUsePortfolioData = jest.fn();
const mockUseDashboardData = jest.fn();
const mockUseSignalDeskData = jest.fn();
const mockUseSWR = jest.fn();

jest.mock('../context/GlobalDataContext', () => ({
    usePortfolioData: () => mockUsePortfolioData(),
    useDashboardData: () => mockUseDashboardData(),
    useSignalDeskData: () => mockUseSignalDeskData(),
}));

jest.mock('swr', () => ({
    __esModule: true,
    default: (...args: unknown[]) => mockUseSWR(...args),
}));

describe('useHomeRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('refreshes dashboard data for the active portfolio and groups recent archives by date', async () => {
        const refreshDashboard = jest.fn(async () => undefined);
        const now = new Date();
        const recentDate = new Date(now);
        recentDate.setDate(now.getDate() - 5);
        const staleDate = new Date(now);
        staleDate.setDate(now.getDate() - 40);

        mockUsePortfolioData.mockReturnValue({
            activePortfolioId: 7,
        });
        mockUseDashboardData.mockReturnValue({
            dashboard: {
                metrics: { total_trades: 3, total_pnl: 1500, win_rate: 66, profit_factor: 1.7 },
                curve: [{ date: '2026-03-18', equity: 100000 }],
                signals: [{ ticker: 'COMI', signal_type: 'BUY', price: 101, score: 4, date: '2026-03-18' }],
                health: { win_rate: 62, avg_gain: 4.2 },
                dataSource: 'LIVE',
                loading: false,
                error: null,
            },
            refreshDashboard,
        });
        mockUseSignalDeskData.mockReturnValue({
            desk: {
                operating_mode: 'AI_ASSIST',
                autopilot_armed: true,
                failed_delivery_count: 1,
                latest_failed_delivery: { status: 'FAILED', last_error: 'transport down' },
                lanes: {
                    intraday: { count: 1, candidates: [{ ticker: 'COMI' }] },
                    swing: { count: 1, candidates: [{ ticker: 'HRHO' }] },
                    position: { count: 0, candidates: [] },
                },
            },
            deskLoading: false,
            deskError: null,
            followUpSummary: {
                total: 3,
                pending_count: 1,
                ready_count: 1,
                sent_count: 1,
                failed_count: 1,
                suppressed_count: 0,
                stale_pending_count: 0,
            },
            refreshDesk: jest.fn(async () => undefined),
        });
        mockUseSWR.mockImplementation((key: string | null) => ({
            data: key
                ? [
                    { ticker: 'COMI', signal_type: 'BUY', price: 100, score: 8, date: recentDate.toISOString() },
                    { ticker: 'HRHO', signal_type: 'SELL', price: 40, score: 5, date: staleDate.toISOString() },
                  ]
                : undefined,
        }));

        const { result } = renderHook(() => useHomeRuntime());

        await waitFor(() => {
            expect(refreshDashboard).toHaveBeenCalledTimes(1);
            expect(result.current.hasMetrics).toBe(true);
            expect(result.current.isSourceLoading).toBe(false);
            expect(result.current.signalDesk.operatingMode).toBe('AI_ASSIST');
            expect(result.current.signalDesk.autopilotArmed).toBe(true);
            expect(result.current.signalDesk.intradayCount).toBe(1);
            expect(result.current.signalDesk.swingCount).toBe(1);
            expect(result.current.signalDesk.failedDeliveryCount).toBe(1);
            expect(result.current.signalDesk.followUps.pendingCount).toBe(1);
            expect(result.current.signalDesk.followUps.failedCount).toBe(1);
        });

        act(() => {
            result.current.setShowArchives(true);
        });

        await waitFor(() => {
            expect(Object.keys(result.current.archivesByDate)).toEqual([recentDate.toISOString().split('T')[0]]);
            expect(result.current.archivesByDate[recentDate.toISOString().split('T')[0]]).toHaveLength(1);
        });
    });
});
