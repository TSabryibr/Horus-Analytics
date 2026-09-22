import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { PortfolioReplicateDialog } from './PortfolioReplicateDialog';
import { Position } from '@/types';

describe('PortfolioReplicateDialog', () => {
    const samplePositions: Position[] = [
        {
            ticker: 'COMI',
            shares: 100,
            entry_price: 50,
            current_price: 55,
            pnl: 500,
            pnl_pct: 10,
            status: 'OPEN',
            currency: 'EGP',
            sector: 'Banking',
        },
    ];

    it('renders dialog with source, target, position count, and semantics warning when open', () => {
        render(
            <PortfolioReplicateDialog
                open={true}
                loading={false}
                sourcePortfolioId={2}
                sourcePortfolioName="Alpha Fleet"
                targetPortfolioId={1}
                sourcePositions={samplePositions}
                onClose={jest.fn()}
                onConfirm={jest.fn()}
            />
        );

        expect(screen.getByRole('dialog', { name: /Confirm Fleet Replication/i })).toBeInTheDocument();
        expect(screen.getByText('Alpha Fleet')).toBeInTheDocument();
        expect(screen.getByText('Portfolio #1')).toBeInTheDocument();
        expect(screen.getByText('1 position(s)')).toBeInTheDocument();
        expect(screen.getByText(/Replacement Semantics Notice:/i)).toBeInTheDocument();
    });

    it('calls onClose when Cancel button is clicked', () => {
        const onCloseMock = jest.fn();
        render(
            <PortfolioReplicateDialog
                open={true}
                loading={false}
                sourcePortfolioId={2}
                targetPortfolioId={1}
                sourcePositions={samplePositions}
                onClose={onCloseMock}
                onConfirm={jest.fn()}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));
        expect(onCloseMock).toHaveBeenCalledTimes(1);
    });

    it('calls onConfirm when Confirm Replication button is clicked', () => {
        const onConfirmMock = jest.fn();
        render(
            <PortfolioReplicateDialog
                open={true}
                loading={false}
                sourcePortfolioId={2}
                targetPortfolioId={1}
                sourcePositions={samplePositions}
                onClose={jest.fn()}
                onConfirm={onConfirmMock}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /Confirm Replication/i }));
        expect(onConfirmMock).toHaveBeenCalledTimes(1);
    });

    it('disables buttons when loading is true', () => {
        render(
            <PortfolioReplicateDialog
                open={true}
                loading={true}
                sourcePortfolioId={2}
                targetPortfolioId={1}
                sourcePositions={samplePositions}
                onClose={jest.fn()}
                onConfirm={jest.fn()}
            />
        );

        expect(screen.getByRole('button', { name: /Cancel/i })).toBeDisabled();
        expect(screen.getByRole('button', { name: /Replicating.../i })).toBeDisabled();
    });
});
