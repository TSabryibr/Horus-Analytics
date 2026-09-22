import { fireEvent, render, screen } from '@testing-library/react';

import { WhaleCandidatesGrid } from './WhaleCandidatesGrid';

describe('WhaleCandidatesGrid', () => {
    it('renders candidate cards and dispatches ticker selection', () => {
        const onSelectTicker = jest.fn();

        render(
            <WhaleCandidatesGrid
                candidates={[
                    {
                        Ticker: 'COMI',
                        Sector: 'Banks',
                        Signal: 'ACCUMULATION',
                        Last_Price: 103.25,
                        Strength: 2.55,
                    },
                    {
                        Ticker: 'HRHO',
                        Sector: 'Industrials',
                        Signal: 'DISTRIBUTION',
                        Last_Price: 37.15,
                        Strength: 1.21,
                    },
                ]}
                isLoading={false}
                onSelectTicker={onSelectTicker}
                truncatePrice={(value) => Number(value).toFixed(3)}
            />,
        );

        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText(/HIGH CONVICTION/i)).toBeInTheDocument();
        expect(screen.getByText('Whales Buying')).toBeInTheDocument();
        expect(screen.getByText('Whales Selling')).toBeInTheDocument();

        fireEvent.click(screen.getByText('COMI'));
        expect(onSelectTicker).toHaveBeenCalledWith('COMI');
    });

    it('renders the loading state', () => {
        render(
            <WhaleCandidatesGrid
                candidates={[]}
                isLoading
                onSelectTicker={jest.fn()}
                truncatePrice={jest.fn()}
            />,
        );

        expect(screen.getByRole('status')).toBeInTheDocument();
    });
});
