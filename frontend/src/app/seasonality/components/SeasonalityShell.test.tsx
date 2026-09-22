import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { SeasonalityShell } from './SeasonalityShell';

describe('SeasonalityShell', () => {
    const mockProps = {
        searchTicker: 'COMI',
        onSearchChange: jest.fn(),
        onSearch: jest.fn(),
        onRefresh: jest.fn(),
        loading: false,
        children: <div />,
    };

    it('renders header and children', () => {
        render(
            <SeasonalityShell {...mockProps} currentMonthLabel="July" activeBias="78% Bullish">
                <div data-testid="child">Content</div>
            </SeasonalityShell>
        );

        expect(screen.getByText('Seasonal Pattern Analysis')).toBeInTheDocument();
        expect(screen.getByText('📅 JULY CYCLE')).toBeInTheDocument();
        expect(screen.getByText('78% Bullish')).toBeInTheDocument();
        expect(screen.getByTestId('child')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Search specific ticker...')).toHaveValue('COMI');
    });

    it('triggers search change and submit', () => {
        render(<SeasonalityShell {...mockProps}>Content</SeasonalityShell>);
        const input = screen.getByPlaceholderText('Search specific ticker...');

        fireEvent.change(input, { target: { value: 'HRHO' } });
        expect(mockProps.onSearchChange).toHaveBeenCalledWith('HRHO');

        fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
        expect(mockProps.onSearch).toHaveBeenCalled();
    });

    it('triggers refresh', () => {
        render(<SeasonalityShell {...mockProps}>Content</SeasonalityShell>);
        const refreshBtn = screen.getByRole('button', { name: /Refresh seasonality data/i });
        fireEvent.click(refreshBtn);
        expect(mockProps.onRefresh).toHaveBeenCalled();
    });
});
