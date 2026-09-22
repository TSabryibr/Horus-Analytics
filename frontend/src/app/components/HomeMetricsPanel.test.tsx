import { render, screen } from '@testing-library/react';
import { HomeMetricsBar } from './HomeMetricsBar';

describe('HomeMetricsBar', () => {
    it('renders metric cards when metrics are available', () => {
        render(
            <HomeMetricsBar
                health={{ win_rate: 62, avg_gain: 4.2 }}
                isSourceLoading={false}
                metrics={{ total_pnl: 1500, win_rate: 66, profit_factor: 1.7 }}
            />
        );

        expect(screen.getByText('VALUATION')).toBeInTheDocument();
        expect(screen.getByText('VARIANCE')).toBeInTheDocument();
        expect(screen.getByText('ALPHA')).toBeInTheDocument();
        expect(screen.getByText('PRECISION')).toBeInTheDocument();
    });

    it('renders loading skeletons while the source is loading', () => {
        const { container } = render(
            <HomeMetricsBar
                health={null}
                isSourceLoading
                metrics={null}
            />
        );

        expect(container.querySelectorAll('.animate-pulse')).toHaveLength(4);
    });

    it('does not show strategy precision when portfolio telemetry is empty', () => {
        render(
            <HomeMetricsBar
                health={{ win_rate: 66.4, avg_gain: 1.91 }}
                isSourceLoading={false}
                metrics={{ total_pnl: 0, win_rate: 0, profit_factor: 0, total_trades: 0 }}
            />
        );

        expect(screen.getByText('PRECISION')).toBeInTheDocument();
        expect(screen.queryByText('66.4%')).not.toBeInTheDocument();
        expect(screen.queryByText('+1.91%')).not.toBeInTheDocument();
    });
});
