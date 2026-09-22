import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';

import { SettingsPortfolioManagerSection } from './SettingsPortfolioManagerSection';

describe('SettingsPortfolioManagerSection', () => {
    it('renders portfolio manager controls and emits updates', () => {
        const onChange = jest.fn();

        render(
            <SettingsPortfolioManagerSection
                settings={{
                    PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS: 15,
                    PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES: true,
                    PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT: 15,
                    PORTFOLIO_MGMT_REPORT_ACTION_ITEMS_LIMIT: 10,
                    PORTFOLIO_MGMT_REPORT_RISK_RECOMMENDATIONS_LIMIT: 8,
                    PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT: 3,
                    PORTFOLIO_MGMT_PREPARE_TP_PROXIMITY_PCT: 1,
                    PORTFOLIO_MGMT_TP2_PCT: 4,
                    PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN: 3500,
                }}
                onChange={onChange}
            />
        );

        fireEvent.change(screen.getAllByDisplayValue('15')[0], { target: { value: '20' } });
        fireEvent.change(screen.getByDisplayValue('3500'), { target: { value: '3000' } });

        const refreshContainer = screen.getByText('Default Refresh Prices').closest('.flex.items-center.justify-between');
        if (!refreshContainer) {
            throw new Error('Refresh toggle container missing');
        }
        fireEvent.click(within(refreshContainer).getByRole('checkbox'));

        expect(onChange).toHaveBeenCalledWith('PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS', 20);
        expect(onChange).toHaveBeenCalledWith('PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN', 3000);
        expect(onChange).toHaveBeenCalledWith('PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES', false);
    });
});
