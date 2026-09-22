import { fireEvent, render, screen } from '@testing-library/react';

import { SectorRrgPanel } from './SectorRrgPanel';

const rows = [
    {
        ticker: 'BANKS',
        Sector: 'Banks',
        Status: 'LEADING',
        x: 1.2,
        y: 2.8,
        trail: [{ x: 0.8, y: 2.1 }, { x: 1.2, y: 2.8 }],
    },
];

describe('SectorRrgPanel', () => {
    it('renders the chart surface and delegates fullscreen open', () => {
        const onOpenFullscreen = jest.fn();

        render(
            <SectorRrgPanel data={rows} onOpenFullscreen={onOpenFullscreen} />
        );

        expect(screen.getByText(/Click to Expand/i)).toBeInTheDocument();
        fireEvent.click(screen.getByTestId('sector-rrg-panel'));

        expect(onOpenFullscreen).toHaveBeenCalledTimes(1);
    });
});
