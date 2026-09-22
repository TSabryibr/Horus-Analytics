import { fireEvent, render, screen } from '@testing-library/react';

import { WhaleChartModal } from './WhaleChartModal';

jest.mock('../../components/charts/InstitutionalChart', () => ({
    InstitutionalChart: () => <div data-testid="institutional-chart" />,
}));

describe('WhaleChartModal', () => {
    it('renders nothing when no ticker is selected', () => {
        const { container } = render(
            <WhaleChartModal
                chartData={[]}
                historyLoading={false}
                obvData={[]}
                onClose={jest.fn()}
                selectedTicker={null}
            />,
        );

        expect(container.firstChild).toBeNull();
    });

    it('renders loading and chart states and supports close', async () => {
        const onClose = jest.fn();
        const { rerender } = render(
            <WhaleChartModal
                chartData={[]}
                historyLoading
                obvData={[]}
                onClose={onClose}
                selectedTicker="COMI"
            />,
        );

        expect(screen.getByText('COMI')).toBeInTheDocument();

        rerender(
            <WhaleChartModal
                chartData={[{ time: '2026-03-18', open: 1, high: 2, low: 1, close: 2 }]}
                historyLoading={false}
                obvData={[{ time: '2026-03-18', value: 100 }]}
                onClose={onClose}
                selectedTicker="COMI"
            />,
        );

        expect(await screen.findByTestId('institutional-chart')).toBeInTheDocument();

        fireEvent.click(screen.getAllByRole('button')[0]);
        expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('renders the empty-history fallback', () => {
        render(
            <WhaleChartModal
                chartData={[]}
                historyLoading={false}
                obvData={[]}
                onClose={jest.fn()}
                selectedTicker="COMI"
            />,
        );

        expect(screen.getByText('No historical data available for analysis.')).toBeInTheDocument();
    });
});
