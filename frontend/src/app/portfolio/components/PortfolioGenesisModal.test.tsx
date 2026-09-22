import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';

import { PortfolioGenesisModal } from './PortfolioGenesisModal';

describe('PortfolioGenesisModal', () => {
    it('renders genesis form and wires reserve and holding actions', () => {
        const onClose = jest.fn();
        const onSubmit = jest.fn((event: React.FormEvent) => event.preventDefault());
        const onFieldChange = jest.fn();
        const onAddHolding = jest.fn();
        const onRemoveHolding = jest.fn();
        const onUpdateHolding = jest.fn();

        render(
            <PortfolioGenesisModal
                actionLoading={false}
                genesisData={{
                    egp_balance: '1000',
                    usd_balance: '100',
                    holdings: [{ id: 1, ticker: 'COMI', shares: '100', price: '90' }],
                }}
                onClose={onClose}
                onSubmit={onSubmit}
                onFieldChange={onFieldChange}
                onAddHolding={onAddHolding}
                onRemoveHolding={onRemoveHolding}
                onUpdateHolding={onUpdateHolding}
            />
        );

        expect(screen.getByRole('dialog', { name: /Treasury genesis/i })).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: 'Treasury Genesis' })).toBeInTheDocument();

        const egpSection = screen.getByText('EGP Balance').parentElement;
        const usdSection = screen.getByText('USD Balance').parentElement;

        expect(egpSection).not.toBeNull();
        expect(usdSection).not.toBeNull();

        fireEvent.change(within(egpSection as HTMLElement).getByDisplayValue('1000'), { target: { value: '1500' } });
        fireEvent.change(within(usdSection as HTMLElement).getByDisplayValue('100'), { target: { value: '250' } });
        fireEvent.change(screen.getByDisplayValue('COMI'), { target: { value: 'HRHO' } });
        fireEvent.change(screen.getByDisplayValue('90'), { target: { value: '95' } });
        fireEvent.click(screen.getByRole('button', { name: /Add Ticker/i }));
        fireEvent.click(screen.getByRole('button', { name: /Authorize Treasury Genesis/i }));
        fireEvent.click(screen.getByRole('button', { name: /Close/i }));
        fireEvent.click(screen.getByRole('button', { name: /Remove holding COMI/i }));

        expect(onFieldChange).toHaveBeenCalledWith('egp_balance', '1500');
        expect(onFieldChange).toHaveBeenCalledWith('usd_balance', '250');
        expect(onUpdateHolding).toHaveBeenCalledWith(1, 'ticker', 'HRHO');
        expect(onUpdateHolding).toHaveBeenCalledWith(1, 'price', '95');
        expect(onAddHolding).toHaveBeenCalled();
        expect(onSubmit).toHaveBeenCalled();
        expect(onClose).toHaveBeenCalled();
        expect(onRemoveHolding).toHaveBeenCalledWith(1);
    });

    it('renders the empty holding hint when no holdings exist', () => {
        render(
            <PortfolioGenesisModal
                actionLoading={false}
                genesisData={{
                    egp_balance: '',
                    usd_balance: '',
                    holdings: [],
                }}
                onClose={jest.fn()}
                onSubmit={jest.fn((event: React.FormEvent) => event.preventDefault())}
                onFieldChange={jest.fn()}
                onAddHolding={jest.fn()}
                onRemoveHolding={jest.fn()}
                onUpdateHolding={jest.fn()}
            />
        );

        expect(screen.getByText(/No holdings added. You can start with just cash./i)).toBeInTheDocument();
    });
});
