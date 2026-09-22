import '@testing-library/jest-dom';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { SeasonalityVerdictCard } from './SeasonalityVerdictCard';

describe('SeasonalityVerdictCard', () => {
    const mockTickerStats = {
        ticker: 'COMI',
        verdict: {
            best_month: 'APR',
            worst_month: 'SEP',
            summary: 'Trend summary for COMI',
        },
    };

    it('renders verdict statistics when tickerStats is provided', () => {
        render(<SeasonalityVerdictCard tickerStats={mockTickerStats as any} loading={false} />);

        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('Statistical Verdict')).toBeInTheDocument();
        expect(screen.getByText('APR')).toBeInTheDocument();
        expect(screen.getByText('SEP')).toBeInTheDocument();
        expect(screen.getByText(/Trend summary for COMI/i)).toBeInTheDocument();
    });

    it('renders empty ghost state when no stats are provided', () => {
        render(<SeasonalityVerdictCard tickerStats={null} loading={false} />);
        expect(screen.getByText(/Search a ticker to reveal its ghost/i)).toBeInTheDocument();
    });

    it('renders loading state when loading is true', () => {
        render(<SeasonalityVerdictCard tickerStats={null} loading={true} />);
        expect(screen.getByText(/Consulting the Casket/i)).toBeInTheDocument();
    });
});
