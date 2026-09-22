import { fireEvent, render, screen } from '@testing-library/react';

import { defaultAnalyticsColumns } from '../lib/analyticsTransforms';
import { AnalyticsFilters } from './AnalyticsFilters';

describe('AnalyticsFilters', () => {
    it('renders filter controls and delegates search and slider changes', () => {
        const setSearch = jest.fn();
        const setMinScore = jest.fn();
        const setFilterStatus = jest.fn();
        const setShowColMenu = jest.fn();
        const toggleColumn = jest.fn();

        render(
            <AnalyticsFilters
                columns={defaultAnalyticsColumns}
                filterStatus="ALL"
                minScore={3}
                search=""
                setFilterStatus={setFilterStatus}
                setMinScore={setMinScore}
                setSearch={setSearch}
                setShowColMenu={setShowColMenu}
                showColMenu
                toggleColumn={toggleColumn}
            />
        );

        fireEvent.change(screen.getByPlaceholderText('Search Ticker...'), { target: { value: 'COMI' } });
        fireEvent.change(screen.getByRole('combobox'), { target: { value: 'BUY' } });
        fireEvent.change(screen.getByRole('slider'), { target: { value: '7' } });
        fireEvent.click(screen.getByRole('button', { name: /Columns/i }));
        fireEvent.click(screen.getByLabelText(/Volume/i));

        expect(setSearch).toHaveBeenCalledWith('COMI');
        expect(setFilterStatus).toHaveBeenCalledWith('BUY');
        expect(setMinScore).toHaveBeenCalledWith(7);
        expect(setShowColMenu).toHaveBeenCalledWith(false);
        expect(toggleColumn).toHaveBeenCalledWith('Volume');
    });

    it('disables score and status filters while search is active', () => {
        render(
            <AnalyticsFilters
                columns={defaultAnalyticsColumns}
                filterStatus="ALL"
                minScore={8}
                search="HRHO"
                setFilterStatus={jest.fn()}
                setMinScore={jest.fn()}
                setSearch={jest.fn()}
                setShowColMenu={jest.fn()}
                showColMenu={false}
                toggleColumn={jest.fn()}
            />
        );

        expect(screen.getByRole('combobox')).toBeDisabled();
        expect(screen.getByRole('slider')).toBeDisabled();
    });
});
