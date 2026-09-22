import { render, screen } from '@testing-library/react';

import { WhaleSectorSummary } from './WhaleSectorSummary';

describe('WhaleSectorSummary', () => {
    it('renders the top sector summary grid with accumulation and distribution counts', () => {
        render(
            <WhaleSectorSummary
                sectors={[
                    { name: 'Banks', count: 3, accumulation: 2, distribution: 1 },
                    { name: 'Industrials', count: 2, accumulation: 1, distribution: 1 },
                ]}
            />,
        );

        expect(screen.getByText('Banks')).toBeInTheDocument();
        expect(screen.getByText('Industrials')).toBeInTheDocument();
        expect(screen.getByText('▲2')).toBeInTheDocument();
        expect(screen.getAllByText('▼1').length).toBeGreaterThanOrEqual(1);
    });

    it('renders nothing when no sectors are available', () => {
        const { container } = render(<WhaleSectorSummary sectors={[]} />);

        expect(container.firstChild).toBeNull();
    });
});
