import { render, screen } from '@testing-library/react';
import { SignalCard } from './SignalCard';
import '@testing-library/jest-dom';

describe('SignalCard', () => {
    const mockProps = {
        ticker: 'TEST',
        signal_type: 'BUY',
        price: 150.1234,
        score: 5,
        date: '2025-01-30T10:00:00'
    };

    it('renders ticker symbol', () => {
        render(<SignalCard {...mockProps} />);
        // Ticker appears in the icon circle (sliced) and the main text
        expect(screen.getByText('TEST')).toBeInTheDocument();
    });

    it('renders correct signal type', () => {
        render(<SignalCard {...mockProps} />);
        // 'BUY' appears in the signal type span
        expect(screen.getAllByText('BUY').length).toBeGreaterThan(0);
    });

    it('renders price with 3 decimal formatting', () => {
        render(<SignalCard {...mockProps} />);
        expect(screen.getByText('150.123')).toBeInTheDocument();
    });

    it('renders score', () => {
        render(<SignalCard {...mockProps} />);
        expect(screen.getByText('MTRX_5/5')).toBeInTheDocument();
    });

    it('renders date safely', () => {
        render(<SignalCard {...mockProps} />);
        // Date formatting might vary by locale, but let's check basic presence
        const dateElement = screen.getByText(/30 JAN|Jan 30|Jan\. 30/i);
        expect(dateElement).toBeInTheDocument();
    });
});
