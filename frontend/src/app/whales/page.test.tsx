import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import WhalesPage from './page';

// ── Helpers ──────────────────────────────────────────────────────────────────
const refreshWhales = jest.fn();
const mockPromoteCandidate = jest.fn();

function mockContext(overrides: Record<string, any> = {}) {
    return {
        whales: {
            candidates: [
                {
                    Ticker: 'COMI',
                    Sector: 'Banks',
                    Signal: 'ACCUMULATION',
                    Last_Price: 103.25,
                    Strength: 1.82,
                },
                {
                    Ticker: 'HRHO',
                    Sector: 'Industrials',
                    Signal: 'DISTRIBUTION',
                    Last_Price: 37.15,
                    Strength: 1.21,
                },
            ],
        },
        whalesLoading: false,
        refreshWhales,
        ...overrides,
    };
}

let contextValue = mockContext();

jest.mock('../context/GlobalDataContext', () => ({
    useWhalesData: () => contextValue,
    useSignalDeskData: () => ({
        promoteCandidate: mockPromoteCandidate,
    }),
}));
jest.mock('../components/charts/InstitutionalChart', () => ({
    InstitutionalChart: () => <div data-testid="institutional-chart" />,
}));

// ── Tests ────────────────────────────────────────────────────────────────────
describe('WhalesPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        contextValue = mockContext();
        mockPromoteCandidate.mockResolvedValue(true);
    });

    // ─── Rendering & Data Display ────────────────────────────────────────
    it('renders whale candidates with ticker, sector, price, and strength', () => {
        render(<WhalesPage />);

        expect(screen.getByText('COMI')).toBeInTheDocument();
        // 'Banks' appears in both the candidate card and the sector grid
        expect(screen.getAllByText('Banks').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('103.250')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
        expect(screen.getAllByText('Industrials').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('37.150')).toBeInTheDocument();
    });

    it('displays correct signal badges (ACCUMULATION / DISTRIBUTION)', () => {
        render(<WhalesPage />);

        expect(screen.getByText('ACCUMULATION')).toBeInTheDocument();
        expect(screen.getByText('DISTRIBUTION')).toBeInTheDocument();
    });

    it('shows signal-specific detail text per card', () => {
        render(<WhalesPage />);

        expect(screen.getByText('Whales Buying')).toBeInTheDocument();
        expect(screen.getByText('Whales Selling')).toBeInTheDocument();
    });

    // ─── Status Card ────────────────────────────────────────────────────
    it('displays sonar status with candidate count and sector count', () => {
        render(<WhalesPage />);

        expect(screen.getByText('Sonar Range: Full Market')).toBeInTheDocument();
        expect(screen.getByText('Detected 2 stocks with significant volume/price divergence across 2 sectors.')).toBeInTheDocument();
    });

    // ─── Sector Summary Grid ─────────────────────────────────────────────
    it('renders sector summary grid with accumulation / distribution split', () => {
        render(<WhalesPage />);

        // Sector names appear in both candidate cards and top grid
        expect(screen.getAllByText('Banks').length).toBeGreaterThanOrEqual(2);
        expect(screen.getAllByText('Industrials').length).toBeGreaterThanOrEqual(2);
    });

    // ─── Filter ──────────────────────────────────────────────────────────
    it('filters by ticker case-insensitively', () => {
        render(<WhalesPage />);

        fireEvent.change(screen.getByPlaceholderText('Filter by ticker or sector...'), { target: { value: 'comi' } });

        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.queryByText('HRHO')).not.toBeInTheDocument();
    });

    it('filters by sector name', () => {
        render(<WhalesPage />);

        fireEvent.change(screen.getByPlaceholderText('Filter by ticker or sector...'), { target: { value: 'bank' } });

        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.queryByText('HRHO')).not.toBeInTheDocument();
    });

    // ─── Refresh ─────────────────────────────────────────────────────────
    it('calls refreshWhales when header button is clicked', () => {
        const { container } = render(<WhalesPage />);
        const refreshButton = container.querySelector('button');
        expect(refreshButton).not.toBeNull();

        fireEvent.click(refreshButton as HTMLButtonElement);
        expect(refreshWhales).toHaveBeenCalledTimes(1);
    });

    it('promotes a whale candidate into the signal desk lanes', () => {
        render(<WhalesPage />);

        fireEvent.click(screen.getAllByRole('button', { name: /Swing/i })[0]);

        expect(mockPromoteCandidate).toHaveBeenCalledWith(
            expect.objectContaining({
                lane: 'SWING',
                ticker: 'COMI',
                side: 'BUY',
                entry_price: 103.25,
                source_module: 'WHALES',
            }),
        );
    });
});
