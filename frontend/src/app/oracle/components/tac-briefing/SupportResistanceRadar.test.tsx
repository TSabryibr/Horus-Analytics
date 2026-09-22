import { render, screen } from '@testing-library/react';

import { SupportResistanceRadar } from './SupportResistanceRadar';

describe('SupportResistanceRadar', () => {
    it('renders the hybrid scope legend and lead ticker label', () => {
        render(
            <SupportResistanceRadar
                currentPrice={82.5}
                mode="scope"
                leadTicker="COMI"
                levels={[
                    { price: 79.1, strength: 0.82, type: 'SUPPORT', members: 3 },
                    { price: 88.6, strength: 0.77, type: 'RESISTANCE', members: 4 },
                ]}
            />
        );

        expect(screen.getByText('BASKET SUPPORT')).toBeInTheDocument();
        expect(screen.getByText('BASKET RESISTANCE')).toBeInTheDocument();
        expect(screen.getByText('LEAD COMI')).toBeInTheDocument();
        expect(screen.getByText('S/R Radar v2.0')).toBeInTheDocument();
        expect(screen.getByText('Current')).toBeInTheDocument();
        expect(screen.getAllByText('82.50').length).toBeGreaterThan(0);
        expect(screen.getAllByText('79.10').length).toBeGreaterThan(0);
        expect(screen.getAllByText('88.60').length).toBeGreaterThan(0);
    });
});
