import { render, screen, fireEvent } from '@testing-library/react';
import { ArbitrageShell } from './ArbitrageShell';

describe('ArbitrageShell', () => {
    const mockOnRefresh = jest.fn();
    const mockOnFilterChange = jest.fn();
    const mockOnUniverseChange = jest.fn();

    it('renders title and shared command header details', () => {
        render(
            <ArbitrageShell loading={false} filter="" universe="default" onUniverseChange={mockOnUniverseChange} onFilterChange={mockOnFilterChange} onRefresh={mockOnRefresh} activeCount={6} executionMode="⚡ SINGLE-LEG">
                <div>Content</div>
            </ArbitrageShell>
        );

        expect(screen.getByText('Pair Trading Scanner')).toBeInTheDocument();
        expect(screen.getByText('🟢 6 Pairs Active')).toBeInTheDocument();
        expect(screen.getByText('⚡ SINGLE-LEG')).toBeInTheDocument();
        expect(screen.getByText(/Lead-lag arbitrage/i)).toBeInTheDocument();
        expect(screen.getAllByText('EGX100').length).toBeGreaterThan(0);
    });

    it('renders children', () => {
        render(
            <ArbitrageShell loading={false} filter="" universe="default" onUniverseChange={mockOnUniverseChange} onFilterChange={mockOnFilterChange} onRefresh={mockOnRefresh}>
                <div data-testid="test-child">Child</div>
            </ArbitrageShell>
        );

        expect(screen.getByTestId('test-child')).toBeInTheDocument();
    });

    it('calls onRefresh when refresh button is clicked', () => {
        const { container } = render(
            <ArbitrageShell loading={false} filter="" universe="default" onUniverseChange={mockOnUniverseChange} onFilterChange={mockOnFilterChange} onRefresh={mockOnRefresh}>
                <div>Content</div>
            </ArbitrageShell>
        );

        const button = screen.getByRole('button', { name: /Refresh arbitrage data/i });
        fireEvent.click(button);
        expect(mockOnRefresh).toHaveBeenCalledTimes(1);
    });

    it('disables refresh button while loading', () => {
        const { container } = render(
            <ArbitrageShell loading={true} filter="" universe="default" onUniverseChange={mockOnUniverseChange} onFilterChange={mockOnFilterChange} onRefresh={mockOnRefresh}>
                <div>Content</div>
            </ArbitrageShell>
        );

        const button = screen.getByRole('button', { name: /Refresh arbitrage data/i });
        expect(button).toBeDisabled();
    });

    it('calls onFilterChange as user types in the filter input', () => {
        render(
            <ArbitrageShell loading={false} filter="" universe="default" onUniverseChange={mockOnUniverseChange} onFilterChange={mockOnFilterChange} onRefresh={mockOnRefresh}>
                <div>Content</div>
            </ArbitrageShell>
        );

        fireEvent.change(screen.getByPlaceholderText('Filter pairs...'), { target: { value: 'COMI' } });
        expect(mockOnFilterChange).toHaveBeenCalledWith('COMI');
    });

    it('renders universe controls and switches to extended mode', () => {
        render(
            <ArbitrageShell loading={false} filter="" universe="default" onUniverseChange={mockOnUniverseChange} onFilterChange={mockOnFilterChange} onRefresh={mockOnRefresh}>
                <div>Content</div>
            </ArbitrageShell>
        );

        expect(screen.getByRole('button', { name: 'EGX100' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Extended' })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Extended' }));
        expect(mockOnUniverseChange).toHaveBeenCalledWith('extended');
    });
});
