import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import { TrapsShell } from './TrapsShell';

describe('TrapsShell', () => {
    const mockOnRefresh = jest.fn();

    it('renders with header and children', () => {
        render(
            <TrapsShell
                loading={false}
                onRefresh={mockOnRefresh}
                dominantBias="🔴 BULL TRAPS DOMINANT (5/8)"
                maxDepth={6.8}
                trapCount={8}
            >
                <div data-testid="child">Test Child</div>
            </TrapsShell>
        );

        expect(screen.getByText('Bull Trap Detector')).toBeInTheDocument();
        expect(screen.getByText('🔴 BULL TRAPS DOMINANT (5/8)')).toBeInTheDocument();
        expect(screen.getByText('6.8% SEVERE')).toBeInTheDocument();
        expect(screen.getByText('8 Staged')).toBeInTheDocument();
        expect(screen.getByText(/False breakout and breakdown detection/i)).toBeInTheDocument();
        expect(screen.getByTestId('child')).toBeInTheDocument();
    });

    it('calls onRefresh when button is clicked', () => {
        const { container } = render(
            <TrapsShell loading={false} onRefresh={mockOnRefresh}>
                <div>Content</div>
            </TrapsShell>
        );

        fireEvent.click(screen.getByRole('button', { name: /Refresh trap detection/i }));
        expect(mockOnRefresh).toHaveBeenCalledTimes(1);
    });

    it('disables refresh button during loading and shows spinning icon', () => {
        const { container } = render(
            <TrapsShell loading={true} onRefresh={mockOnRefresh}>
                <div>Content</div>
            </TrapsShell>
        );

        const button = screen.getByRole('button', { name: /Refresh trap detection/i });
        expect(button).toBeDisabled();
        expect(container.querySelector('.animate-spin')).toBeInTheDocument();
    });
});
