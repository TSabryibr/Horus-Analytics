import { fireEvent, render, screen } from '@testing-library/react';

import { defaultAnalyticsColumns } from '../lib/analyticsTransforms';
import { AnalyticsTable } from './AnalyticsTable';

const rows = [
    {
        Ticker: 'COMI',
        Price: 102.25,
        Signal_Score: 8.5,
        Status: 'HIGH CONVICTION',
        Trend: 'BULLISH' as const,
        RSI: 48,
        Target_1: 106,
        Target_2: 108,
        Risk_Reward_Ratio: 1.8,
        Stop_Loss: 99,
        Avg_Turnover_M: 12,
        ATR: 2.4,
    },
];

describe('AnalyticsTable', () => {
    it('renders the loading and empty branches', () => {
        const { rerender } = render(
            <AnalyticsTable
                columns={defaultAnalyticsColumns}
                loading
                onBroadcast={jest.fn()}
                onRequestSort={jest.fn()}
                rows={[]}
            />
        );

        expect(screen.getByText('Loading Analytics...')).toBeInTheDocument();

        rerender(
            <AnalyticsTable
                columns={defaultAnalyticsColumns}
                loading={false}
                onBroadcast={jest.fn()}
                onRequestSort={jest.fn()}
                rows={[]}
            />
        );

        expect(screen.getByText('No stocks match your filters.')).toBeInTheDocument();
    });

    it('renders row content and delegates sort interactions', () => {
        const onRequestSort = jest.fn();

        render(
            <AnalyticsTable
                columns={defaultAnalyticsColumns}
                loading={false}
                onBroadcast={jest.fn()}
                onRequestSort={onRequestSort}
                rows={rows}
            />
        );

        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText(/HIGH CONVICTION ⚡/i)).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: /sort by score/i }));

        expect(onRequestSort).toHaveBeenCalledWith('Signal_Score');
    });
});
