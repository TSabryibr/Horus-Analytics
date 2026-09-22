import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import SeasonalityPage from './page';

const marketPayload = {
    status: 'success',
    top_historical_performers: [
        { ticker: 'COMI', avg_return: 3.2, win_rate: 64, best_month: 'APR' },
        { ticker: 'HRHO', avg_return: 2.1, win_rate: 55, best_month: 'JAN' },
    ],
};

const tickerPayload = (ticker: string) => ({
    status: 'success',
    ticker,
    verdict: {
        best_month: 'APR',
        worst_month: 'SEP',
        summary: `${ticker} tends to perform better in spring`,
    },
    months: [
        { label: 'Jan', average_return: 1.2, win_rate: 58, count: 10 },
        { label: 'Feb', average_return: -0.4, win_rate: 44, count: 10 },
    ],
});

function mockSeasonalityFetch(market = marketPayload) {
    return jest.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('/api/v1/seasonality/market')) {
            return { ok: true, json: async () => market } as Response;
        }
        if (url.includes('/api/v1/seasonality?ticker=')) {
            const match = url.match(/ticker=([A-Z]+)/);
            const ticker = match ? match[1] : 'COMI';
            return { ok: true, json: async () => tickerPayload(ticker) } as Response;
        }
        return { ok: true, json: async () => ({ status: 'error' }) } as Response;
    });
}

describe('SeasonalityPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('loads market and ticker seasonality on mount', async () => {
        global.fetch = mockSeasonalityFetch() as jest.Mock;

        render(<SeasonalityPage />);

        await waitFor(() => {
            expect(screen.getByText("Statistical Verdict")).toBeInTheDocument();
            expect(screen.getAllByText('COMI').length).toBeGreaterThan(0);
            expect(screen.getByText('Optimal Exit Month')).toBeInTheDocument();
            expect(screen.getByText('Danger Zone Month')).toBeInTheDocument();
        });
    });

    it('displays verdict card with best and worst months', async () => {
        global.fetch = mockSeasonalityFetch() as jest.Mock;

        render(<SeasonalityPage />);

        await waitFor(() => {
            // APR appears in both verdict card and top performers table
            expect(screen.getAllByText('APR').length).toBeGreaterThanOrEqual(1);
            expect(screen.getByText('SEP')).toBeInTheDocument();
        });
    });

    it('renders monthly breakdown grid with return data', async () => {
        global.fetch = mockSeasonalityFetch() as jest.Mock;

        render(<SeasonalityPage />);

        await waitFor(() => {
            // Monthly breakdown cards show avg return, win rate and sample count
            expect(screen.getAllByText('+1.2%').length).toBeGreaterThanOrEqual(1);
            expect(screen.getByText('-0.4%')).toBeInTheDocument();
            expect(screen.getByText('WR: 58%')).toBeInTheDocument();
            expect(screen.getAllByText('N=10').length).toBeGreaterThanOrEqual(1);
        });
    });

    it('shows top performers table with avg return and win rate', async () => {
        global.fetch = mockSeasonalityFetch() as jest.Mock;

        render(<SeasonalityPage />);

        await waitFor(() => {
            expect(screen.getByText('+3.2%')).toBeInTheDocument();
            expect(screen.getByText('64%')).toBeInTheDocument();
            expect(screen.getByText('HRHO')).toBeInTheDocument();
        });
    });

    it('requests uppercase ticker when searching and pressing Enter', async () => {
        const fetchMock = mockSeasonalityFetch();
        global.fetch = fetchMock as jest.Mock;

        render(<SeasonalityPage />);

        const searchInput = await screen.findByPlaceholderText('Search specific ticker...');
        fireEvent.change(searchInput, { target: { value: 'hrho' } });
        fireEvent.keyDown(searchInput, { key: 'Enter', code: 'Enter' });

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/seasonality?ticker=HRHO'));
            expect(screen.getAllByText('HRHO').length).toBeGreaterThan(0);
        });
    });

    it('handles API error gracefully without crashing', async () => {
        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        global.fetch = jest.fn(async () => { throw new TypeError('Network error'); }) as jest.Mock;

        render(<SeasonalityPage />);

        await waitFor(() => {
            // When ticker data fails, the empty state is shown
            expect(screen.getByText(/Search a ticker to reveal its ghost/i)).toBeInTheDocument();
        });

        errorSpy.mockRestore();
    });
});
