import { render, screen } from '@testing-library/react';

import type { SectorViewMode } from '../lib/sectorTransforms';
import { SectorRankingsTable } from './SectorRankingsTable';

const rows = [
    {
        ticker: 'BANKS',
        Sector: 'Banks',
        Status: 'LEADING',
        x: 1.2,
        y: 2.8,
        trail: [{ x: 0.8, y: 2.1 }, { x: 1.2, y: 2.8 }],
    },
    {
        ticker: 'COMI',
        Sector: 'Banks',
        Status: 'IMPROVING',
        x: 0.7,
        y: 0.9,
        trail: [{ x: 0.2, y: 0.4 }, { x: 0.7, y: 0.9 }],
    },
];

describe('SectorRankingsTable', () => {
    it('renders counts and sector rows for sectors view', () => {
        render(
            <SectorRankingsTable
                dataCount={rows.length}
                quadrantCounts={{ LEADING: 1, IMPROVING: 1, WEAKENING: 0, LAGGING: 0 }}
                rows={rows}
                viewMode={'sectors' as SectorViewMode}
            />
        );

        expect(screen.getByText('Rankings (2)')).toBeInTheDocument();
        expect(screen.getByText('LEAD: 1')).toBeInTheDocument();
        expect(screen.getByText('+2.80%')).toBeInTheDocument();
        expect(screen.queryByText('Sector')).not.toBeInTheDocument();
    });

    it('renders the sector column in stocks view', () => {
        render(
            <SectorRankingsTable
                dataCount={1}
                quadrantCounts={{ LEADING: 0, IMPROVING: 1, WEAKENING: 0, LAGGING: 0 }}
                rows={[rows[1]]}
                viewMode={'stocks' as SectorViewMode}
            />
        );

        expect(screen.getByText('Sector')).toBeInTheDocument();
        expect(screen.getAllByText('Banks').length).toBeGreaterThan(0);
    });
});
