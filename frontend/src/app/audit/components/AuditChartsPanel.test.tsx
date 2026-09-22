import { render, screen } from '@testing-library/react';

import type { Strategy } from '@/types/domain';

import { AuditChartsPanel } from './AuditChartsPanel';

jest.mock('recharts', () => {
    const MockContainer = () => <div data-testid="mock-recharts-container" />;
    return {
        ResponsiveContainer: MockContainer,
        AreaChart: MockContainer,
        Area: () => null,
        XAxis: () => null,
        YAxis: () => null,
        Tooltip: () => null,
        CartesianGrid: () => null,
        Legend: () => null,
    };
});

const strategies: Strategy[] = [
    {
        name: 'Falcon',
        win_rate: 64,
        total_trades: 12,
        count: 12,
        equity_curve: [
            { date: '2026-03-16', value: 0 },
            { date: '2026-03-17', value: 1.2 },
        ],
    },
];

describe('AuditChartsPanel', () => {
    it('renders the benchmarking surface and chart container', () => {
        render(
            <AuditChartsPanel
                comparisonData={[{ name: 0, Falcon: 0 }, { name: 1, Falcon: 1.2 }]}
                strategies={strategies}
                colors={['#3b82f6']}
            />
        );

        expect(screen.getByText('Strategic Benchmarking')).toBeInTheDocument();
        expect(screen.getByText('Alpha')).toBeInTheDocument();
        expect(screen.getByTestId('mock-recharts-container')).toBeInTheDocument();
    });
});
