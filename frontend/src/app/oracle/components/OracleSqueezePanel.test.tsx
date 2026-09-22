import { render, screen } from '@testing-library/react';

import { OracleSqueezePanel } from './OracleSqueezePanel';

describe('OracleSqueezePanel', () => {
    it('renders squeeze candidates when the status is found', () => {
        render(
            <OracleSqueezePanel
                squeeze={{ status: 'found', count: 2 }}
                candidates={[
                    { Ticker: 'COMI', Sector: 'Banks', Price: 103.25, BandWidth: 0.0184 },
                    { Ticker: 'HRHO', Sector: 'Industrials', Price: 37.8, BandWidth: 0.0122 },
                ]}
            />
        );

        expect(screen.getByText('The Coil (Squeezes)')).toBeInTheDocument();
        expect(screen.getByText(/Found 2 stocks preparing for an explosive move\./)).toBeInTheDocument();
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
    });

    it('renders the expanded-market empty state when nothing is found', () => {
        render(<OracleSqueezePanel squeeze={{ status: 'none', count: 0 }} candidates={[]} />);

        expect(screen.getByText('Market is expanded.')).toBeInTheDocument();
        expect(screen.getByText('No volatility squeezes detected.')).toBeInTheDocument();
    });
});
