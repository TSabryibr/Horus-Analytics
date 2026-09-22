import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import NewsClient from './NewsClient';

// -- Helpers ------------------------------------------------------------------
const refreshNews = jest.fn();

const fullNewsItem = {
    source: 'MockWire',
    title: 'Market rally continues',
    summary: 'Broad-based gains across sectors.',
    link: 'https://example.com/rally',
    tickers: ['COMI', 'HRHO'],
    gossip_score: 3,
};

const negativeNewsItem = {
    source: 'BearWire',
    title: 'Crash incoming',
    summary: 'Everything is falling.',
    link: 'https://example.com/crash',
    tickers: [],
    gossip_score: -2,
};

const neutralNewsItem = {
    source: 'NeutralWire',
    title: 'Boring day',
    summary: 'Nothing happened.',
    link: 'https://example.com/boring',
    tickers: ['ETEL'],
    gossip_score: 0,
};

function mockContext(overrides: Record<string, any> = {}) {
    return {
        news: [fullNewsItem, negativeNewsItem, neutralNewsItem],
        newsSentiment: {
            score: 78.5,
            regime: 'EUXUBERANT GREED',
            bull_count: 9,
            bear_count: 2,
        },
        newsLoading: false,
        refreshNews,
        ...overrides,
    };
}

let contextValue = mockContext();

jest.mock('../context/GlobalDataContext', () => ({
    useNewsData: () => contextValue,
}));

// -- Tests --------------------------------------------------------------------
describe('NewsPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        contextValue = mockContext();
    });

    // --- Bifrost Sentiment Panel -----------------------------------------
    it('renders bifrost score, regime, and bull/bear counts', () => {
        render(<NewsClient />);

        expect(screen.getByText('News Sentiment Analyzer')).toBeInTheDocument();
        expect(screen.getByText('EUXUBERANT GREED')).toBeInTheDocument();
        expect(screen.getByText('78.5 / 100')).toBeInTheDocument();
        expect(screen.getByText('Greed Hits')).toBeInTheDocument();
        expect(screen.getByText('9')).toBeInTheDocument();
        expect(screen.getByText('Fear Hits')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('falls back to neutral regime when sentiment is null', () => {
        contextValue = mockContext({ newsSentiment: null });
        render(<NewsClient />);

        expect(screen.getByText('BORING MORTALS')).toBeInTheDocument();
        expect(screen.getByText('50.0 / 100')).toBeInTheDocument();
    });

    // --- News Cards -----------------------------------------------------
    it('renders news cards with source, title, summary, and tickers', () => {
        render(<NewsClient />);

        expect(screen.getByText('MockWire')).toBeInTheDocument();
        expect(screen.getByText('Market rally continues')).toBeInTheDocument();
        expect(screen.getByText('Broad-based gains across sectors.')).toBeInTheDocument();
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
    });

    it('shows "Market Wide" for news items with no tickers', () => {
        render(<NewsClient />);

        expect(screen.getByText('Market Wide')).toBeInTheDocument();
    });

    it('renders external links for each news card', () => {
        render(<NewsClient />);

        const links = screen.getAllByRole('link');
        expect(links.length).toBe(3);
        expect(links[0]).toHaveAttribute('href', 'https://example.com/rally');
        expect(links[0]).toHaveAttribute('target', '_blank');
    });

    // --- Refresh ---------------------------------------------------------
    it('calls refreshNews when header button is clicked', () => {
        const { container } = render(<NewsClient />);
        const refreshButton = container.querySelector('button');
        expect(refreshButton).not.toBeNull();

        fireEvent.click(refreshButton as HTMLButtonElement);
        expect(refreshNews).toHaveBeenCalledTimes(1);
    });

    it('disables refresh button during loading', () => {
        contextValue = mockContext({ newsLoading: true });
        const { container } = render(<NewsClient />);
        const refreshButton = container.querySelector('button');

        expect(refreshButton).toBeDisabled();
    });
});
