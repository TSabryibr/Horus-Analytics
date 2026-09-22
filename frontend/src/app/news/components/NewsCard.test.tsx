import { render, screen } from '@testing-library/react';
import { NewsCard } from './NewsCard';

describe('NewsCard', () => {
    const mockProps = {
        source: 'MockWire',
        title: 'Market rally continues',
        summary: 'Broad-based gains across sectors.',
        link: 'https://example.com/rally',
        tickers: ['COMI', 'HRHO'],
        gossipScore: 3,
    };

    it('renders news cards with source, title, summary, and tickers', () => {
        render(<NewsCard {...mockProps} />);

        expect(screen.getByText('MockWire')).toBeInTheDocument();
        expect(screen.getByText('Market rally continues')).toBeInTheDocument();
        expect(screen.getByText('Broad-based gains across sectors.')).toBeInTheDocument();
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
    });

    it('shows "Market Wide" for news items with no tickers', () => {
        render(<NewsCard {...mockProps} tickers={[]} />);

        expect(screen.getByText('Market Wide')).toBeInTheDocument();
    });

    it('renders external links with correct attributes', () => {
        render(<NewsCard {...mockProps} />);

        const links = screen.getAllByRole('link');
        expect(links.length).toBe(1);
        expect(links[0]).toHaveAttribute('href', 'https://example.com/rally');
        expect(links[0]).toHaveAttribute('target', '_blank');
        expect(links[0]).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('renders sentiment icon and score badge with correct color', () => {
        const { container } = render(<NewsCard {...mockProps} />);
        
        const scoreBadge = screen.getByText(/Score:\s\+3/);
        expect(scoreBadge).toHaveClass('text-green-500');
        
        // Lucide trending-up icon check (Lucide icons set a specific class name or SVG data)
        const icon = container.querySelector('svg.lucide-trending-up');
        expect(icon).toBeInTheDocument();
    });

    it('renders neutral badge for zero score', () => {
        render(<NewsCard {...mockProps} gossipScore={0} />);
        const scoreBadge = screen.getByText(/Score:\s0/);
        expect(scoreBadge).toHaveClass('text-gray-400');
    });
});
