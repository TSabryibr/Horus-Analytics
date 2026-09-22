import { render, screen } from '@testing-library/react';
import { NewsSentimentPanel } from './NewsSentimentPanel';

describe('NewsSentimentPanel', () => {
    const mockProps = {
        score: 78.5,
        regime: 'EUXUBERANT GREED',
        regimeClass: 'text-amber-300 border-amber-500/30 bg-amber-500/10',
        barColorClass: 'bg-amber-400',
        bullHits: 9,
        bearHits: 2,
    };

    it('renders bifrost score, regime, and bull/bear counts', () => {
        render(<NewsSentimentPanel {...mockProps} />);

        expect(screen.getByText('News Sentiment Analyzer')).toBeInTheDocument();
        expect(screen.getByText('EUXUBERANT GREED')).toBeInTheDocument();
        expect(screen.getByText('78.5 / 100')).toBeInTheDocument();
        expect(screen.getByText('Greed Hits')).toBeInTheDocument();
        expect(screen.getByText('9')).toBeInTheDocument();
        expect(screen.getByText('Fear Hits')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('applies regime styling classes from props', () => {
        render(<NewsSentimentPanel {...mockProps} />);
        const regimeBadge = screen.getByText('EUXUBERANT GREED');
        expect(regimeBadge).toHaveClass('text-amber-300');
    });

    it('applies progress bar color from props', () => {
        const { container } = render(<NewsSentimentPanel {...mockProps} />);
        // Find the bar div (inner child of width-capped container)
        // L74: <div className={clsx("h-2 transition-all duration-700", barColorClass)}
        const bars = container.querySelectorAll('.h-2');
        const coloredBar = Array.from(bars).find(b => b.classList.contains('bg-amber-400'));
        expect(coloredBar).toBeDefined();
    });
});
