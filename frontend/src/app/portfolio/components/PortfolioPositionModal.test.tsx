import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { Position } from '@/types';
import { PortfolioPositionModal } from './PortfolioPositionModal';

describe('PortfolioPositionModal', () => {
    it('renders add mode and wires field changes', () => {
        const onClose = jest.fn();
        const onSubmit = jest.fn((event: React.FormEvent) => event.preventDefault());
        const onFieldChange = jest.fn();

        render(
            <PortfolioPositionModal
                mode="add"
                actionLoading={false}
                formData={{
                    ticker: 'COMI',
                    shares: '100',
                    price: '103.2',
                    sl: '',
                    tp: '',
                    tp2: '',
                    date: '',
                }}
                onClose={onClose}
                onSubmit={onSubmit}
                onFieldChange={onFieldChange}
            />
        );

        expect(screen.getByRole('dialog', { name: /Add position/i })).toBeInTheDocument();
        fireEvent.change(screen.getByPlaceholderText('e.g. COMI'), { target: { value: 'HRHO' } });
        fireEvent.change(screen.getByPlaceholderText('100'), { target: { value: '200' } });
        fireEvent.change(screen.getByPlaceholderText('0.0000'), { target: { value: '88.5' } });
        fireEvent.click(screen.getByRole('button', { name: /Authorize Entry/i }));
        fireEvent.click(screen.getByRole('button', { name: /Close/i }));

        expect(onFieldChange).toHaveBeenCalledWith('ticker', 'HRHO');
        expect(onFieldChange).toHaveBeenCalledWith('shares', '200');
        expect(onFieldChange).toHaveBeenCalledWith('price', '88.5');
        expect(onSubmit).toHaveBeenCalled();
        expect(onClose).toHaveBeenCalled();
    });

    it('renders update mode for an existing position', () => {
        const position = { ticker: 'COMI' } as Position;

        render(
            <PortfolioPositionModal
                mode="update"
                actionLoading={false}
                position={position}
                formData={{
                    ticker: '',
                    shares: '',
                    price: '',
                    sl: '90',
                    tp: '120',
                    tp2: '130',
                    date: '',
                }}
                onClose={jest.fn()}
                onSubmit={jest.fn((event: React.FormEvent) => event.preventDefault())}
                onFieldChange={jest.fn()}
            />
        );

        expect(screen.getByRole('dialog', { name: /Update position/i })).toBeInTheDocument();
        expect(screen.getByText(/Recalibrate COMI/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Apply Risk Patch/i })).toBeInTheDocument();
        expect(screen.queryByPlaceholderText('e.g. COMI')).not.toBeInTheDocument();
    });
});
