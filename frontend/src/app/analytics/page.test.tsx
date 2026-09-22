import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import AnalyticsPage from './page';

const mockPromoteCandidate = jest.fn();

jest.mock('../context/GlobalDataContext', () => ({
    useSignalDeskData: () => ({
        promoteCandidate: mockPromoteCandidate,
    }),
}));

const analyticsRows = [
    {
        Ticker: 'COMI',
        Price: 102.25,
        Signal_Score: 4,
        Status: 'WATCHLIST',
        Trend: 'BULLISH',
        RSI: 48,
        Target_1: 106,
        Target_2: 108,
        Risk_Reward_Ratio: 1.8,
        Stop_Loss: 99,
        Avg_Turnover_M: 12,
        ATR: 2.4,
    },
    {
        Ticker: 'HRHO',
        Price: 38.75,
        Signal_Score: 9,
        Status: 'HIGH CONVICTION BUY',
        Trend: 'BULLISH',
        RSI: 61,
        Target_1: 40,
        Target_2: 42,
        Risk_Reward_Ratio: 2.9,
        Stop_Loss: 36.5,
        Avg_Turnover_M: 8,
        ATR: 1.6,
    },
];

describe('AnalyticsPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockPromoteCandidate.mockResolvedValue(true);
    });

    it('loads analytics rows on mount', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/analytics')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'COMPLETED',
                        last_updated: '2026-02-17T12:00:00Z',
                        data: analyticsRows,
                    }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<AnalyticsPage />);

        await waitFor(() => {
            expect(screen.getByText('COMI')).toBeInTheDocument();
            expect(screen.getByText('HRHO')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /Run Fresh Scan/i })).toBeInTheDocument();
        });
    });

    it('search overrides score filter', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/analytics')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'COMPLETED',
                        data: analyticsRows,
                    }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<AnalyticsPage />);

        await waitFor(() => {
            expect(screen.getByText('COMI')).toBeInTheDocument();
            expect(screen.getByText('HRHO')).toBeInTheDocument();
        });

        const slider = screen.getByRole('slider');
        fireEvent.change(slider, { target: { value: '8' } });

        await waitFor(() => {
            expect(screen.queryByText('COMI')).not.toBeInTheDocument();
            expect(screen.getByText('HRHO')).toBeInTheDocument();
        });

        const searchInput = screen.getByPlaceholderText('Search Ticker...');
        fireEvent.change(searchInput, { target: { value: 'COMI' } });

        await waitFor(() => {
            expect(screen.getByText('COMI')).toBeInTheDocument();
            expect(screen.queryByText('HRHO')).not.toBeInTheDocument();
        });
    });

    it('sorts by score descending when score header is clicked twice', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/analytics')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'COMPLETED',
                        data: analyticsRows,
                    }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        const { container } = render(<AnalyticsPage />);

        await waitFor(() => {
            expect(screen.getByText('COMI')).toBeInTheDocument();
            expect(screen.getByText('HRHO')).toBeInTheDocument();
        });

        const scoreHeader = screen.getByText('Score');
        fireEvent.click(scoreHeader);
        fireEvent.click(scoreHeader);

        await waitFor(() => {
            const firstTickerCell = container.querySelector('tbody tr td');
            expect(firstTickerCell).not.toBeNull();
            expect(firstTickerCell?.textContent).toContain('HRHO');
        });
    });

    it('promotes analytics candidates into the desk lanes', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/analytics')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'COMPLETED',
                        data: analyticsRows,
                    }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<AnalyticsPage />);

        await waitFor(() => {
            expect(screen.getByText('HRHO')).toBeInTheDocument();
        });

        fireEvent.click(screen.getAllByRole('button', { name: /Intraday/i })[1]);

        expect(mockPromoteCandidate).toHaveBeenCalledWith(
            expect.objectContaining({
                lane: 'INTRADAY',
                ticker: 'HRHO',
                entry_price: 38.75,
                stop_loss: 36.5,
                target_price: 40,
                source_module: 'ANALYTICS',
            }),
        );
    });
});
