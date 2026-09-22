import { fireEvent, render, screen } from '@testing-library/react';

import type { AuditLog, Strategy } from '@/types/domain';

import { AuditLedgerPanel } from './AuditLedgerPanel';

const strategies: Strategy[] = [
    {
        name: 'Falcon',
        win_rate: 64,
        total_trades: 12,
        count: 12,
        equity_curve: [],
    },
    {
        name: 'Wolf',
        win_rate: 58,
        total_trades: 9,
        count: 9,
        equity_curve: [],
    },
];

const logs: AuditLog[] = [
    {
        timestamp: '2026-03-18T10:00:00Z',
        action: 'BUY',
        details: 'Opened COMI',
        date: '2026-03-18',
        ticker: 'COMI',
        strategy: 'Falcon',
        entry_price: 102.4,
        pnl_history: { '1D': 0.5, '3D': 1.0, '5D': 2.1 },
        converted: true,
    },
    {
        timestamp: '2026-03-17T10:00:00Z',
        action: 'SELL',
        details: 'Closed HRHO',
        date: '2026-03-17',
        ticker: 'HRHO',
        strategy: 'Wolf',
        entry_price: 37.2,
        pnl_history: { '1D': -0.6, '3D': -1.1, '5D': -1.8 },
        converted: false,
    },
];

describe('AuditLedgerPanel', () => {
    it('renders logs, filters by strategy, and expands row details', () => {
        const setFilter = jest.fn();
        const setExpandedRow = jest.fn();

        const { rerender } = render(
            <AuditLedgerPanel
                strategies={strategies}
                logs={logs}
                filter="ALL"
                setFilter={setFilter}
                expandedRow={null}
                setExpandedRow={setExpandedRow}
            />
        );

        expect(screen.getByText('Performance Ledger')).toBeInTheDocument();
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();

        fireEvent.change(screen.getByDisplayValue('All Strategies'), { target: { value: 'Falcon' } });
        expect(setFilter).toHaveBeenCalledWith('Falcon');

        fireEvent.click(screen.getByText('COMI'));
        expect(setExpandedRow).toHaveBeenCalledWith(1);

        rerender(
            <AuditLedgerPanel
                strategies={strategies}
                logs={logs}
                filter="Falcon"
                setFilter={setFilter}
                expandedRow={0}
                setExpandedRow={setExpandedRow}
            />
        );

        expect(screen.getByText('Entry Price')).toBeInTheDocument();
        expect(screen.queryByText('HRHO')).not.toBeInTheDocument();
        expect(screen.getByText('Profit')).toBeInTheDocument();
    });
});
