import { render, screen, fireEvent } from '@testing-library/react';
import { NewsShell } from './NewsShell';

describe('NewsShell', () => {
    const mockOnRefresh = jest.fn();

    it('renders title, subtitle, status items and children', () => {
        render(
            <NewsShell loading={false} onRefresh={mockOnRefresh} bifrostRegime="BULLISH" articleCount={12}>
                <div data-testid="child">Child Content</div>
            </NewsShell>
        );

        expect(screen.getByText('Market News Feed')).toBeInTheDocument();
        expect(screen.getByText('BULLISH REGIME')).toBeInTheDocument();
        expect(screen.getByText('12 Ingested')).toBeInTheDocument();
        expect(screen.getByText(/Newsflow monitoring/i)).toBeInTheDocument();
        expect(screen.getByTestId('child')).toBeInTheDocument();
    });

    it('handles refresh click', () => {
        const { container } = render(
            <NewsShell loading={false} onRefresh={mockOnRefresh}>
                <div>Content</div>
            </NewsShell>
        );

        fireEvent.click(screen.getByRole('button', { name: /Refresh news feed/i }));
        expect(mockOnRefresh).toHaveBeenCalled();
    });

    it('shows spinning icon and disables button when loading', () => {
        const { container } = render(
            <NewsShell loading={true} onRefresh={mockOnRefresh}>
                <div>Content</div>
            </NewsShell>
        );

        const button = screen.getByRole('button', { name: /Refresh news feed/i });
        expect(button).toBeDisabled();
        const icon = container.querySelector('.animate-spin');
        expect(icon).toBeInTheDocument();
    });
});
