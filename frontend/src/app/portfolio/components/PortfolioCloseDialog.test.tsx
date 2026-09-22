import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { Position } from '@/types';
import { PortfolioCloseDialog } from './PortfolioCloseDialog';

describe('PortfolioCloseDialog', () => {
    const position = {
        ticker: 'COMI',
        shares: 100,
        current_price: 99.5,
        entry_price: 90,
        pnl: 950,
        pnl_pct: 10.56,
        status: 'OPEN',
    } as Position;

    it('renders the close dialog and wires confirmation controls', () => {
        const onCancel = jest.fn();
        const onConfirm = jest.fn();
        const onPriceChange = jest.fn();
        const onSharesChange = jest.fn();
        const onPercentClick = jest.fn();

        render(
            <PortfolioCloseDialog
                position={position}
                sharesValue="100"
                priceValue="101.25"
                maxShares={100}
                loading={false}
                onCancel={onCancel}
                onConfirm={onConfirm}
                onPriceChange={onPriceChange}
                onSharesChange={onSharesChange}
                onPercentClick={onPercentClick}
            />
        );

        expect(screen.getByRole('dialog', { name: /Close COMI/i })).toBeInTheDocument();
        expect(screen.getByText(/Current shares: 100/i)).toBeInTheDocument();

        fireEvent.change(screen.getByLabelText('Selling Price'), { target: { value: '102.5' } });
        fireEvent.change(screen.getByLabelText('Shares to Sell'), { target: { value: '50' } });
        fireEvent.click(screen.getByRole('button', { name: '50%' }));
        fireEvent.click(screen.getByRole('button', { name: /Keep Position/i }));
        fireEvent.click(screen.getByRole('button', { name: /Sell Shares/i }));

        expect(onPriceChange).toHaveBeenCalledWith('102.5');
        expect(onSharesChange).toHaveBeenCalledWith('50');
        expect(onPercentClick).toHaveBeenCalledWith(50);
        expect(onCancel).toHaveBeenCalled();
        expect(onConfirm).toHaveBeenCalled();
    });
});
