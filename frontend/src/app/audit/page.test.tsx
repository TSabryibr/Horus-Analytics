import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import AuditPage from './page';

jest.mock('./components/StrategyCard', () => ({
    StrategyCard: ({ strat }: { strat: { name: string } }) => <div data-testid="mock-strategy-card">{strat.name}</div>,
}));

jest.mock('recharts', () => {
    const MockContainer = () => <div data-testid="mock-recharts-container" />;
    return {
        ResponsiveContainer: MockContainer,
        LineChart: MockContainer,
        Line: () => null,
        XAxis: () => null,
        YAxis: () => null,
        Tooltip: () => null,
        CartesianGrid: () => null,
        Legend: () => null,
        AreaChart: MockContainer,
        Area: () => null,
    };
});

const auditPayload = {
    status: 'success',
    strategies: [
        {
            name: 'Falcon',
            win_rate: 64,
            conversion_rate: 41,
            expected_value: 1.8,
            count: 12,
            equity_curve: [0, 1.2, 2.1],
        },
        {
            name: 'Wolf',
            win_rate: 58,
            conversion_rate: 35,
            expected_value: 1.1,
            count: 9,
            equity_curve: [0, 0.7, 1.4],
        },
    ],
    logs: [
        {
            date: '2026-02-16',
            ticker: 'COMI',
            strategy: 'Falcon',
            entry_price: 102.4,
            pnl_history: { '1D': 0.5, '3D': 1.0, '5D': 2.1 },
            converted: true,
        },
        {
            date: '2026-02-15',
            ticker: 'HRHO',
            strategy: 'Wolf',
            entry_price: 37.2,
            pnl_history: { '1D': -0.6, '3D': -1.1, '5D': -1.8 },
            converted: false,
        },
    ],
};

describe('AuditPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('loads audit data and renders strategy cards + logs', async () => {
        global.fetch = jest.fn(async () => {
            return { ok: true, json: async () => auditPayload } as Response;
        }) as jest.Mock;

        render(<AuditPage />);

        await waitFor(() => {
            expect(screen.getByText('Audit Trail')).toBeInTheDocument();
            expect(screen.getByText('Performance Ledger')).toBeInTheDocument();
            expect(screen.getByText('Follow-Up Delivery Ledger')).toBeInTheDocument();
            expect(screen.getAllByTestId('mock-strategy-card').length).toBe(2);
            expect(screen.getByText('COMI')).toBeInTheDocument();
            expect(screen.getByText('HRHO')).toBeInTheDocument();
        });
    });

    it('filters logs by selected strategy', async () => {
        global.fetch = jest.fn(async () => {
            return { ok: true, json: async () => auditPayload } as Response;
        }) as jest.Mock;

        render(<AuditPage />);

        const filterSelect = await screen.findByDisplayValue('All Strategies');
        fireEvent.change(filterSelect, { target: { value: 'Falcon' } });

        await waitFor(() => {
            expect(screen.getByText('COMI')).toBeInTheDocument();
            expect(screen.queryByText('HRHO')).not.toBeInTheDocument();
        });
    });

    it('shows profit badge for positive 5D return and loss badge for negative', async () => {
        global.fetch = jest.fn(async () => {
            return { ok: true, json: async () => auditPayload } as Response;
        }) as jest.Mock;

        render(<AuditPage />);

        await waitFor(() => {
            expect(screen.getByText('Profit')).toBeInTheDocument();
            expect(screen.getByText('Loss')).toBeInTheDocument();
        });
    });

    it('shows Traded badge for converted and Ignored for non-converted', async () => {
        global.fetch = jest.fn(async () => {
            return { ok: true, json: async () => auditPayload } as Response;
        }) as jest.Mock;

        render(<AuditPage />);

        await waitFor(() => {
            expect(screen.getByText('Traded')).toBeInTheDocument();
            expect(screen.getByText('Ignored')).toBeInTheDocument();
        });
    });

    it('renders global precision and strategy health radar', async () => {
        global.fetch = jest.fn(async () => {
            return { ok: true, json: async () => auditPayload } as Response;
        }) as jest.Mock;

        render(<AuditPage />);

        await waitFor(() => {
            expect(screen.getByText('Global Precision')).toBeInTheDocument();
            expect(screen.getByText('Strategy Health Radar')).toBeInTheDocument();
            // Average win rate: (64 + 58) / 2 = 61
            expect(screen.getByText('61%')).toBeInTheDocument();
        });
    });

    it('switches day filters and re-fetches data', async () => {
        const fetchMock = jest.fn(async () => {
            return { ok: true, json: async () => auditPayload } as Response;
        });
        global.fetch = fetchMock as jest.Mock;

        render(<AuditPage />);

        await waitFor(() => {
            expect(screen.getByText('Audit Trail')).toBeInTheDocument();
        });

        const btn30 = screen.getByRole('button', { name: '30D' });
        fireEvent.click(btn30);

        await waitFor(() => {
            const hasAuditDaysCall = fetchMock.mock.calls.some(
                (call) => typeof call[0] === 'string' && call[0].includes('/api/v1/audit?days=30'),
            );
            expect(hasAuditDaysCall).toBe(true);
        });
    });

    it('shows loading state on initial load', () => {
        global.fetch = jest.fn(() => new Promise(() => { })) as jest.Mock;

        render(<AuditPage />);

        expect(screen.getByText(/Consulting the ravens/i)).toBeInTheDocument();
    });
});
