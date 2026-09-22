import { fireEvent, render, screen } from '@testing-library/react';

import type { Strategy } from '@/types/domain';

import { AuditSummaryPanel } from './AuditSummaryPanel';

jest.mock('./StrategyCard', () => ({
    StrategyCard: ({ strat }: { strat: { name: string } }) => <div data-testid="mock-strategy-card">{strat.name}</div>,
}));

const strategies: Strategy[] = [
    {
        name: 'Falcon',
        win_rate: 64,
        total_trades: 12,
        conversion_rate: 41,
        expected_value: 1.8,
        count: 12,
        equity_curve: [],
    },
    {
        name: 'Wolf',
        win_rate: 58,
        total_trades: 9,
        conversion_rate: 35,
        expected_value: 1.1,
        count: 9,
        equity_curve: [],
    },
];

describe('AuditSummaryPanel', () => {
    it('renders summary metrics, strategy radar, and cards', () => {
        const scrollIntoView = jest.fn();
        const getElementByIdSpy = jest.spyOn(document, 'getElementById').mockReturnValue({
            scrollIntoView,
        } as unknown as HTMLElement);

        render(<AuditSummaryPanel strategies={strategies} colors={['#3b82f6', '#10b981']} />);

        expect(screen.getByText('Global Precision')).toBeInTheDocument();
        expect(screen.getByText('61%')).toBeInTheDocument();
        expect(screen.getByText('Strategy Health Radar')).toBeInTheDocument();
        expect(screen.getAllByTestId('mock-strategy-card')).toHaveLength(2);

        fireEvent.click(screen.getByRole('button', { name: /View Full Intelligence/i }));
        expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });

        getElementByIdSpy.mockRestore();
    });
});
