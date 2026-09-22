import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { SettingsDataSourcesSection } from './SettingsDataSourcesSection';

describe('SettingsDataSourcesSection', () => {
    it('renders provider controls and wires provider changes', () => {
        const onChange = jest.fn();

        render(
            <SettingsDataSourcesSection
                settings={{
                    LOCAL_HISTORY_PROVIDER: 'CSV',
                    LOCAL_INTRADAY_PROVIDER: 'CSV',
                    METASTOCK_DAT_INTRADAY_AVAILABLE: false,
                    METASTOCK_INTRADAY_AVAILABLE: true,
                    METASTOCK_DAT_INTRADAY_FOLDER: '',
                    METASTOCK_INTRADAY_FOLDER: 'C:\\csv',
                }}
                onChange={onChange}
            />
        );

        const selects = screen.getAllByRole('combobox');
        fireEvent.change(selects[0], { target: { value: 'AUTO' } });
        fireEvent.change(selects[1], { target: { value: 'CSV' } });

        expect(onChange).toHaveBeenCalledWith('LOCAL_HISTORY_PROVIDER', 'AUTO');
        expect(onChange).toHaveBeenCalledWith('LOCAL_INTRADAY_PROVIDER', 'CSV');
        expect(screen.getByText(/Intraday DAT path: not configured/i)).toBeInTheDocument();
        expect(screen.getByText(/Intraday CSV path: C:\\csv/i)).toBeInTheDocument();
    });

    it('defaults provider controls to Mubasher DB when no setting is loaded', () => {
        render(
            <SettingsDataSourcesSection
                settings={{}}
                onChange={jest.fn()}
            />
        );

        const selects = screen.getAllByRole('combobox') as HTMLSelectElement[];
        expect(selects[0].value).toBe('MUBASHER_DB');
        expect(selects[1].value).toBe('MUBASHER_DB');
    });

    it('renders Mubasher stream readiness and wires tick controls', () => {
        const onChange = jest.fn();

        render(
            <SettingsDataSourcesSection
                settings={{
                    LOCAL_HISTORY_PROVIDER: 'MUBASHER_DB',
                    LOCAL_INTRADAY_PROVIDER: 'MUBASHER_DB',
                    LOCAL_TICKS_PROVIDER: 'MUBASHER_DB',
                    TICK_SYNC_ENABLED: true,
                    MUBASHER_HISTORY_DB_AVAILABLE: true,
                    MUBASHER_HISTORY_DB_PATH: 'C:\\mubasher\\History\\CASE\\history.db',
                    MUBASHER_INTRADAY_DB_AVAILABLE: true,
                    MUBASHER_INTRADAY_DB_PATH: 'C:\\mubasher\\Intraday\\CASE\\INTRADAY_MASTER.db',
                    MUBASHER_HISTORICAL_TRADE_AVAILABLE: true,
                    MUBASHER_HISTORICAL_TRADE_FOLDER: 'C:\\mubasher\\HistoricalTrade\\CASE',
                    MUBASHER_HISTORICAL_TRADE_DB_COUNT: 4,
                    MUBASHER_HISTORICAL_TRADE_LATEST_DATE: '20260601',
                }}
                onChange={onChange}
            />
        );

        expect(screen.getByText('Mubasher History DB')).toBeInTheDocument();
        expect(screen.getByText('Mubasher Intraday DB')).toBeInTheDocument();
        expect(screen.getByText('HistoricalTrade Ticks')).toBeInTheDocument();
        expect(screen.getByText(/Latest: 20260601/i)).toBeInTheDocument();
        expect(screen.getByText(/DB files: 4/i)).toBeInTheDocument();

        const selects = screen.getAllByRole('combobox');
        fireEvent.change(selects[2], { target: { value: 'AUTO' } });
        fireEvent.click(screen.getByRole('checkbox', { name: /sync historicaltrade ticks/i }));

        expect(onChange).toHaveBeenCalledWith('LOCAL_TICKS_PROVIDER', 'AUTO');
        expect(onChange).toHaveBeenCalledWith('TICK_SYNC_ENABLED', false);
    });
});
