import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { SeasonalityLeadersTable } from './SeasonalityLeadersTable';

describe('SeasonalityLeadersTable', () => {
    const mockProps = {
        performers: [
            { ticker: 'COMI', avg_return: 3.2, win_rate: 64, best_month: 'APR' },
        ],
        loading: false,
        currentMonthLabel: 'Mar',
        onTickerClick: jest.fn(),
    };

    it('renders header and performers list', () => {
        render(<SeasonalityLeadersTable {...mockProps} />);

        expect(screen.getByText('Mar Historical Leaders (Top 10)')).toBeInTheDocument();
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('+3.2%')).toBeInTheDocument();
        expect(screen.getByText('64%')).toBeInTheDocument();
    });

    it('triggers ticker click', () => {
        render(<SeasonalityLeadersTable {...mockProps} />);
        const row = screen.getByText('COMI').closest('tr');
        if (row) fireEvent.click(row);
        expect(mockProps.onTickerClick).toHaveBeenCalledWith('COMI');
    });

    it('renders loading skeletons when loading', () => {
        const { container } = render(<SeasonalityLeadersTable {...mockProps} performers={undefined} loading={true} />);
        expect(container.querySelectorAll('tbody tr')).toHaveLength(5);
    });
});
