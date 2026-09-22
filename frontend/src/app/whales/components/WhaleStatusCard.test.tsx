import { render, screen } from '@testing-library/react';

import { WhaleStatusCard } from './WhaleStatusCard';

describe('WhaleStatusCard', () => {
    it('renders the sonar status summary with candidate and sector counts', () => {
        render(<WhaleStatusCard candidateCount={7} sectorCount={4} />);

        expect(screen.getByText('Sonar Range: Full Market')).toBeInTheDocument();
        expect(
            screen.getByText('Detected 7 stocks with significant volume/price divergence across 4 sectors.'),
        ).toBeInTheDocument();
    });
});
