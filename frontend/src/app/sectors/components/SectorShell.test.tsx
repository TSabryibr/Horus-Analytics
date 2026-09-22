import { fireEvent, render, screen } from '@testing-library/react';

import type { SectorViewMode } from '../lib/sectorTransforms';
import { SectorShell } from './SectorShell';

describe('SectorShell', () => {
    it('renders the page chrome and delegates mode, sector, and refresh actions', () => {
        const setViewMode = jest.fn();
        const setSelectedSector = jest.fn();
        const onRefresh = jest.fn();

        render(
            <SectorShell
                loading={false}
                onRefresh={onRefresh}
                sectorsList={['Banks', 'Real Estate']}
                selectedSector=""
                setSelectedSector={setSelectedSector}
                setViewMode={setViewMode}
                viewMode={'stocks' as SectorViewMode}
                leadingCount={4}
                benchmark="EGX30"
            />
        );

        expect(screen.getByText('Sector Rotation (RRG)')).toBeInTheDocument();
        expect(screen.getByText('🟢 4 Leading')).toBeInTheDocument();
        expect(screen.getByText('EGX30')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Sectors' }));
        fireEvent.click(screen.getByRole('button', { name: 'Stocks' }));
        fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Banks' } });
        fireEvent.click(screen.getByRole('button', { name: /Refresh sector rotation/i }));

        expect(setViewMode).toHaveBeenCalledWith('sectors');
        expect(setViewMode).toHaveBeenCalledWith('stocks');
        expect(setSelectedSector).toHaveBeenCalledWith('Banks');
        expect(onRefresh).toHaveBeenCalledTimes(1);
    });
});
