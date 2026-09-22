import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import SectorPage from './page';

const sectorRows = [
    {
        ticker: 'BANKS',
        Sector: 'Banks',
        Status: 'LEADING',
        x: 1.2,
        y: 2.8,
        trail: [{ x: 0.8, y: 2.1 }, { x: 1.2, y: 2.8 }],
    },
    {
        ticker: 'REAL_ESTATE',
        Sector: 'Real Estate',
        Status: 'LAGGING',
        x: -1.5,
        y: -0.3,
        trail: [{ x: -1.0, y: 0.2 }, { x: -1.5, y: -0.3 }],
    },
];

const stockRows = [
    {
        ticker: 'COMI',
        Sector: 'Banks',
        Status: 'IMPROVING',
        x: 0.7,
        y: 0.9,
        trail: [{ x: 0.2, y: 0.4 }, { x: 0.7, y: 0.9 }],
    },
];

function mockFetchForSectors(sectors = sectorRows, stocks = stockRows) {
    return jest.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('/api/v1/rrg?view=sectors&trail=10')) {
            return { ok: true, json: async () => ({ status: 'success', data: sectors }) } as Response;
        }
        if (url.includes('/api/v1/rrg?view=stocks&trail=10')) {
            return { ok: true, json: async () => ({ status: 'success', data: stocks }) } as Response;
        }
        return { ok: true, json: async () => ({ status: 'success', data: [] }) } as Response;
    });
}

describe('SectorPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('loads sectors view and renders rankings', async () => {
        global.fetch = mockFetchForSectors() as jest.Mock;

        render(<SectorPage />);

        await waitFor(() => {
            expect(screen.getByText('Sector Rotation (RRG)')).toBeInTheDocument();
            expect(screen.getByText('Rankings (2)')).toBeInTheDocument();
            expect(screen.getAllByText('BANKS').length).toBeGreaterThan(0);
        });
    });

    it('renders status badges for each quadrant (LEADING / LAGGING)', async () => {
        global.fetch = mockFetchForSectors() as jest.Mock;

        render(<SectorPage />);

        await waitFor(() => {
            expect(screen.getAllByText('LEADING').length).toBeGreaterThan(0);
            expect(screen.getAllByText('LAGGING').length).toBeGreaterThan(0);
        });
    });

    it('shows RS ratio and momentum values with correct sign', async () => {
        global.fetch = mockFetchForSectors() as jest.Mock;

        render(<SectorPage />);

        await waitFor(() => {
            expect(screen.getByText('+2.80%')).toBeInTheDocument();
            expect(screen.getByText('+1.20')).toBeInTheDocument();
        });
    });

    it('switches to stocks view and fetches sector-filtered stocks', async () => {
        const fetchMock = mockFetchForSectors();
        global.fetch = fetchMock as jest.Mock;

        render(<SectorPage />);

        const stocksButton = await screen.findByRole('button', { name: /Stocks/i });
        fireEvent.click(stocksButton);

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/rrg?view=stocks&trail=10'));
            expect(screen.getAllByText('COMI').length).toBeGreaterThan(0);
        });

        fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Banks' } });

        await waitFor(() => {
            expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('view=stocks&trail=10&sector=Banks'));
        });
    });

    it('renders empty rankings table when API returns no data', async () => {
        global.fetch = mockFetchForSectors([], []) as jest.Mock;

        render(<SectorPage />);

        await waitFor(() => {
            expect(screen.getByText('Rankings (0)')).toBeInTheDocument();
        });
    });

    it('shows loading spinner on initial load', () => {
        // Never resolve the fetch so the loading state persists
        global.fetch = jest.fn(() => new Promise(() => { })) as jest.Mock;

        render(<SectorPage />);

        expect(screen.getByText(/Mapping the bifröst/i)).toBeInTheDocument();
    });

    it('shows loading text and handles API error gracefully', async () => {
        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        global.fetch = jest.fn(async () => { throw new TypeError('Network error'); }) as jest.Mock;

        render(<SectorPage />);

        // After error the loading state clears but no crash
        await waitFor(() => {
            expect(screen.getByText('Rankings (0)')).toBeInTheDocument();
        });

        errorSpy.mockRestore();
    });
});
