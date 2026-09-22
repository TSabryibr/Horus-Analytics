import { renderHook, act } from '@testing-library/react';
import { useLiveDashboard } from './useLiveDashboard';

// Mock all internal dependency hooks to avoid network calls and focus on orchestration mapping rules
jest.mock('./useLiveRuntime', () => ({
    useLiveRuntime: () => ({
        ticker: 'COMI',
        setTicker: jest.fn(),
        tickers: ['COMI', 'HRHO'],
        data: [{ Low: 90, High: 100, Close: 95, Volume: 100 }, { Low: 95, High: 105, Close: 102, Volume: 200 }],
        loading: false,
        refreshing: false,
        error: null,
        setError: jest.fn(),
        lastUpdate: '10:00 AM',
        fetchData: jest.fn(),
    })
}));

jest.mock('./useLiveAnalytics', () => ({
    useLiveAnalytics: () => ({
        analyticsData: [{ Ticker: 'COMI', Signal_Score: 85 }],
        analyticsLoading: false,
        fetchAnalytics: jest.fn(),
    })
}));

jest.mock('./useLiveControls', () => ({
    useLiveControls: () => ({
        liveStatus: { market_open: true },
        liveRunning: true,
        marketOpen: true,
        liveLastUpdate: '10:00 AM',
        fetchLiveStatus: jest.fn(),
        handleLiveFeedAction: jest.fn(),
    })
}));

jest.mock('./useSovereignAlerts', () => ({
    useSovereignAlerts: () => ({
        sovereignAlerts: [],
        dismissSovereignAlert: jest.fn(),
        wsConnected: true,
    })
}));

jest.mock('@/hooks/usePolling', () => ({
    usePolling: jest.fn()
}));

describe('useLiveDashboard', () => {
    it('structures props predictably matching component requirements', () => {
        const { result } = renderHook(() => useLiveDashboard());
        
        // Assert shell composition props
        expect(result.current.shellProps.ticker).toBe('COMI');
        expect(result.current.shellProps.marketOpen).toBe(true);
        expect(result.current.shellProps.autoRefreshEnabled).toBe(true);
        
        // Assert chart extraction metrics
        expect(result.current.chartProps.ticker).toBe('COMI');
        expect(result.current.chartProps.hasData).toBe(true);
        expect(result.current.chartProps.yDomain).toEqual([88.5, 106.5]); // Range is 105-90=15. Pad=1.5 -> [88.5, 106.5]
        
        // Assert status panel metrics computation
        expect(result.current.statusProps.lastPrice).toBe('102.000');
        expect(result.current.statusProps.priceChangePositive).toBe(true);
        expect(result.current.statusProps.volumeLabel).toBe('200');
        
        // Assert analytics mapping
        expect(result.current.analyticsProps.radarItems[0].Ticker).toBe('COMI');
    });

    it('toggles radar and refreshes state', () => {
        const { result } = renderHook(() => useLiveDashboard());
        expect(result.current.shellProps.showRadar).toBe(false);

        act(() => {
            result.current.shellProps.onToggleRadar();
        });
        expect(result.current.shellProps.showRadar).toBe(true);
    });

    it('selects ticker and hides radar synchronously', () => {
        const { result } = renderHook(() => useLiveDashboard());
        act(() => {
            result.current.shellProps.onToggleRadar(); // sets to true
        });
        expect(result.current.shellProps.showRadar).toBe(true);

        act(() => {
            result.current.analyticsProps.onSelectTicker('HRHO');
        });
        expect(result.current.shellProps.showRadar).toBe(false);
    });
});
