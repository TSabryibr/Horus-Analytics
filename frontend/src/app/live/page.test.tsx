import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import LiveMonitorPage from './page';
import { GlobalDataProvider } from '../context/GlobalDataContext';
import { __resetLiveContextCachesForTests } from '../context/LiveContext';

const mockUsePathname = jest.fn();

jest.mock('next/navigation', () => ({
    usePathname: () => mockUsePathname(),
}));

jest.mock('@/hooks/usePolling', () => ({
    usePolling: () => {},
}));

jest.mock('lightweight-charts', () => {
    const fitContent = jest.fn();
    const priceScaleApplyOptions = jest.fn();
    const addSeries = jest.fn(() => ({
        setData: jest.fn(),
    }));

    const chartApi = {
        addSeries,
        applyOptions: jest.fn(),
        remove: jest.fn(),
        priceScale: jest.fn(() => ({
            applyOptions: priceScaleApplyOptions,
        })),
        timeScale: jest.fn(() => ({
            fitContent,
        })),
        subscribeCrosshairMove: jest.fn(),
        unsubscribeCrosshairMove: jest.fn(),
    };

    return {
        ColorType: {
            Solid: 'solid',
        },
        CrosshairMode: {
            Normal: 0,
        },
        CandlestickSeries: { type: 'candlestick' },
        HistogramSeries: { type: 'histogram' },
        LineSeries: { type: 'line' },
        createChart: jest.fn(() => chartApi),
    };
}, { virtual: true });


const analyticsPayload = [
    {
        Ticker: 'COMI',
        Status: 'HIGH CONVICTION',
        Signal_Score: 9,
        Price: 104.25,
        Risk_Reward_Ratio: 2.8,
        Resistance_20D: 110.5,
        Key_Resistance_1: 112.4,
    },
];

const intradayPayload = [
    {
        Date: '2026-02-17T09:30:00Z',
        Open: 101,
        High: 103,
        Low: 100,
        Close: 102,
        Volume: 15000,
    },
    {
        Date: '2026-02-17T09:31:00Z',
        Open: 102,
        High: 104,
        Low: 101,
        Close: 103,
        Volume: 18000,
    },
];

const baseFetch = async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes('/api/v1/data/tickers')) {
        return { ok: true, json: async () => ['COMI', 'HRHO'] } as Response;
    }
    if (url.includes('/api/v1/analytics')) {
        return { ok: true, json: async () => analyticsPayload } as Response;
    }
    if (url.includes('/api/v1/data/intraday/')) {
        return { ok: true, json: async () => intradayPayload } as Response;
    }
    if (url.includes('/api/v1/live/status')) {
        return {
            ok: true,
            json: async () => ({ status: 'success', running: false, market_open: true, last_update: null }),
        } as Response;
    }
    if (url.includes('/api/v1/portfolio/list')) {
        return { ok: true, json: async () => [] } as Response;
    }
    return { ok: true, json: async () => ({}) } as Response;
};

describe('LiveMonitorPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        __resetLiveContextCachesForTests();
        mockUsePathname.mockReturnValue('/live');
    });

    it('loads intraday KPI values after a manual refresh', async () => {
        global.fetch = jest.fn(baseFetch) as jest.Mock;

        render(
            <GlobalDataProvider>
                <LiveMonitorPage />
            </GlobalDataProvider>
        );

        fireEvent.click(screen.getByTitle(/Force refresh/i));

        await waitFor(() => {
            expect(screen.getByText('103.000')).toBeInTheDocument();
            expect(screen.getByText(/COMI intraday 1m \(2 bars\)/i)).toBeInTheDocument();
        });
    });

    it('shows market-closed error when live feed start is blocked', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/live/start') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'market_closed',
                        running: false,
                        market_open: false,
                        message: 'Market is closed. Live feed start is blocked outside EGX hours.',
                    }),
                } as Response;
            }
            return baseFetch(input);
        }) as jest.Mock;

        render(
            <GlobalDataProvider>
                <LiveMonitorPage />
            </GlobalDataProvider>
        );

        const startButton = await screen.findByRole('button', { name: /Start Feed/i });
        fireEvent.click(startButton);

        await waitFor(() => {
            expect(screen.getByText('Market is closed. Live feed start is blocked outside EGX hours.')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /Market Closed/i })).toBeInTheDocument();
        });
    });

    it('renders radar cards from analytics payload', async () => {
        global.fetch = jest.fn(baseFetch) as jest.Mock;

        render(
            <GlobalDataProvider>
                <LiveMonitorPage />
            </GlobalDataProvider>
        );

        const radarButton = await screen.findByRole('button', { name: /Radar/i });
        fireEvent.click(radarButton);

        await waitFor(() => {
            expect(screen.getByText('SCORE 9')).toBeInTheDocument();
            expect(screen.getByText('RR 2.8X')).toBeInTheDocument();
        });
    });

    it('switches control from Start Feed to Stop Feed after successful start', async () => {
        let statusCallCount = 0;
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/live/start') && init?.method === 'POST') {
                return { ok: true, json: async () => ({ status: 'success', running: true, market_open: true }) } as Response;
            }
            if (url.includes('/api/v1/live/stop') && init?.method === 'POST') {
                return { ok: true, json: async () => ({ status: 'success', running: false, market_open: true }) } as Response;
            }
            if (url.includes('/api/v1/live/status')) {
                statusCallCount += 1;
                return {
                    ok: true,
                    json: async () =>
                        statusCallCount === 1
                            ? { status: 'success', running: true, market_open: true }
                            : { status: 'success', running: false, market_open: true },
                } as Response;
            }
            return baseFetch(input);
        }) as jest.Mock;

        render(
            <GlobalDataProvider>
                <LiveMonitorPage />
            </GlobalDataProvider>
        );

        const startButton = await screen.findByRole('button', { name: /Start Feed/i });
        fireEvent.click(startButton);

        const stopButton = await screen.findByRole('button', { name: /Stop Feed/i });
        fireEvent.click(stopButton);

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /Start Feed/i })).toBeInTheDocument();
        });
    });
});
