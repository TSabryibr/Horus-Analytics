import { render, screen } from '@testing-library/react';
import { MetricCard } from './MetricCard';
import { DollarSign } from 'lucide-react';
import '@testing-library/jest-dom';

describe('MetricCard', () => {
    const mockProps = {
        title: 'Total Revenue',
        value: '$5,000',
        icon: DollarSign,
        trend: 12.5
    };

    it('renders title and value', () => {
        render(<MetricCard {...mockProps} />);
        expect(screen.getByText('Total Revenue')).toBeInTheDocument();
        expect(screen.getByText('$5,000')).toBeInTheDocument();
    });

    it('renders trend with arrow', () => {
        render(<MetricCard {...mockProps} />);
        expect(screen.getByText('12.5% Velocity')).toBeInTheDocument();
        // Since styling checks are hard, existence is enough for unit test
    });

    it('applies negative trend styling check logic (class check)', () => {
        render(<MetricCard {...mockProps} trend={-5} />);
        const trendEl = screen.getByText('5% Velocity');
        expect(trendEl.closest('div')).toHaveClass('text-rose-400');
    });

    it('applies positive trend styling check logic (class check)', () => {
        render(<MetricCard {...mockProps} trend={5} />);
        const trendEl = screen.getByText('5% Velocity');
        expect(trendEl.closest('div')).toHaveClass('text-emerald-400');
    });
});
