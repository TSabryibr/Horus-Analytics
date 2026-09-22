import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import TrapsPage from './page';

// ── Helpers ──────────────────────────────────────────────────────────────────
const refreshTraps = jest.fn();
const mockPromoteCandidate = jest.fn();

function mockContext(overrides: Record<string, any> = {}) {
    return {
        traps: {
            bull_traps: [
                {
                    Ticker: 'COMI',
                    Date: '2026-02-17',
                    Price: 103.2,
                    'Fakeout_Depth_%': 5.2,
                    Details: 'Breakout failed above resistance.',
                },
            ],
            bear_traps: [
                {
                    Ticker: 'HRHO',
                    Date: '2026-02-17',
                    Price: 37.8,
                    'Fakeout_Depth_%': 1.9,
                    Details: 'Breakdown reversed with demand spike.',
                },
            ],
        },
        trapsLoading: false,
        refreshTraps,
        ...overrides,
    };
}

let contextValue = mockContext();

jest.mock('../context/GlobalDataContext', () => ({
    useTrapsData: () => contextValue,
    usePortfolioData: () => ({
        activePortfolioId: 1,
        portfolios: [{ id: 1, name: 'Horus', type: 'USER' }],
    }),
    useSignalDeskData: () => ({
        promoteCandidate: mockPromoteCandidate,
    }),
}));

// ── Tests ────────────────────────────────────────────────────────────────────
describe('TrapsPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        contextValue = mockContext();
        mockPromoteCandidate.mockResolvedValue(true);
    });

    // ─── Rendering & Data Display ────────────────────────────────────────
    it('renders bull and bear traps with ticker, date, price, and fakeout %', () => {
        render(<TrapsPage />);

        // Section headings
        expect(screen.getByText('Bull Traps (Defensive / Sell)')).toBeInTheDocument();
        expect(screen.getByText('Bear Traps (Springboard / Buy)')).toBeInTheDocument();
        // Tickers
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
        // Dates (both share the same date so use getAllByText)
        expect(screen.getAllByText('2026-02-17').length).toBe(2);
        // Fakeout depth
        expect(screen.getByText('-5.2% Fakeout')).toBeInTheDocument();
        expect(screen.getByText(/SEVERE TRAP/i)).toBeInTheDocument();
        expect(screen.getByText('+1.9% Rebound')).toBeInTheDocument();
        // Details
        expect(screen.getByText('Breakout failed above resistance.')).toBeInTheDocument();
        expect(screen.getByText('Breakdown reversed with demand spike.')).toBeInTheDocument();
    });

    // ─── Empty States ────────────────────────────────────────────────────
    it('shows "The Market is Honest Today" when both arrays are empty', () => {
        contextValue = mockContext({ traps: { bull_traps: [], bear_traps: [] } });
        render(<TrapsPage />);

        expect(screen.getByText('The Market is Honest Today')).toBeInTheDocument();
        expect(screen.getByText('No major traps detected in the last window.')).toBeInTheDocument();
    });

    it('shows individual empty messages when only one category is empty', () => {
        contextValue = mockContext({ traps: { bull_traps: [], bear_traps: [{ Ticker: 'HRHO', Date: '2026-02-17', Price: 37.8, 'Fakeout_Depth_%': 1.9, Details: 'Breakdown reversed.' }] } });
        render(<TrapsPage />);

        // Not the "honest market" banner (one side has data)
        expect(screen.queryByText('The Market is Honest Today')).not.toBeInTheDocument();
        // But bull side shows its empty message
        expect(screen.getByText('No Bull Traps found')).toBeInTheDocument();
    });

    // ─── Null Safety ─────────────────────────────────────────────────────
    it('handles null traps from context gracefully', () => {
        contextValue = mockContext({ traps: null });
        render(<TrapsPage />);

        expect(screen.getByText('The Market is Honest Today')).toBeInTheDocument();
    });

    // ─── Refresh ─────────────────────────────────────────────────────────
    it('calls refreshTraps when header button is clicked', () => {
        const { container } = render(<TrapsPage />);
        const refreshButton = container.querySelector('button');
        expect(refreshButton).not.toBeNull();

        fireEvent.click(refreshButton as HTMLButtonElement);
        expect(refreshTraps).toHaveBeenCalledTimes(1);
    });

    it('disables refresh button during loading', () => {
        contextValue = mockContext({ trapsLoading: true });
        const { container } = render(<TrapsPage />);
        const refreshButton = container.querySelector('button');

        expect(refreshButton).toBeDisabled();
    });

    it('promotes a trap signal into the desk lanes', () => {
        render(<TrapsPage />);

        fireEvent.click(screen.getAllByRole('button', { name: /Position/i })[0]);

        expect(mockPromoteCandidate).toHaveBeenCalledWith(
            expect.objectContaining({
                lane: 'POSITION',
                ticker: 'COMI',
                side: 'SELL',
                entry_price: 103.2,
                source_module: 'TRAPS',
            }),
        );
    });
});
