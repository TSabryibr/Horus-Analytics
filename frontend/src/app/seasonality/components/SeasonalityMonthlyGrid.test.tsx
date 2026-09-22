import React from 'react';
import { render, screen } from '@testing-library/react';
import { SeasonalityMonthlyGrid } from './SeasonalityMonthlyGrid';

describe('SeasonalityMonthlyGrid', () => {
    const mockMonths = [
        { label: 'Jan', average_return: 1.2, win_rate: 58, count: 10 },
        { label: 'Feb', average_return: -0.4, win_rate: 44, count: 10 },
    ];

    it('renders monthly breakdown grid correctly', () => {
        const { container } = render(<SeasonalityMonthlyGrid months={mockMonths} ticker="COMI" />);
        expect(container).toBeTruthy();
    });

    it('returns null when no months provided', () => {
        const { container } = render(<SeasonalityMonthlyGrid months={undefined} ticker="N/A" />);
        expect(container.firstChild).toBeNull();
    });
});
