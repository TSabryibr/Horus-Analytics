import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { PortfolioRebalanceModal } from './PortfolioRebalanceModal';

describe('PortfolioRebalanceModal', () => {
    beforeEach(() => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/portfolio/rebalance')) {
                return {
                    ok: true,
                    json: async () => [
                        {
                            ticker: 'COMI',
                            currency: 'EGP',
                            is_usd: false,
                            action: 'TRIM',
                            current_pct: 35.0,
                            target_pct: 25.0,
                            drift_pct: 10.0,
                            current_shares: 1000,
                            target_shares: 700,
                            shares_delta: 300,
                            delta_value_native: -25500,
                            delta_value_egp: -25500,
                            current_price: 85.0,
                            current_price_egp: 85.0,
                            usd_rate: 50.0,
                            reason: 'Overweight (10.0% drift)',
                            model: 'EQUAL_WEIGHT',
                        },
                        {
                            ticker: 'EAST',
                            currency: 'EGP',
                            is_usd: false,
                            action: 'ADD',
                            current_pct: 15.0,
                            target_pct: 25.0,
                            drift_pct: -10.0,
                            current_shares: 500,
                            target_shares: 800,
                            shares_delta: 300,
                            delta_value_native: 9000,
                            delta_value_egp: 9000,
                            current_price: 30.0,
                            current_price_egp: 30.0,
                            usd_rate: 50.0,
                            reason: 'Underweight (10.0% drift)',
                            model: 'EQUAL_WEIGHT',
                        },
                        {
                            ticker: 'GTEX',
                            currency: 'USD',
                            is_usd: true,
                            action: 'ADD',
                            current_pct: 5.0,
                            target_pct: 25.0,
                            drift_pct: -20.0,
                            current_shares: 50000,
                            target_shares: 120000,
                            shares_delta: 70000,
                            delta_value_native: 3500,
                            delta_value_egp: 175000,
                            current_price: 0.05,
                            current_price_egp: 2.50,
                            usd_rate: 50.0,
                            reason: 'Underweight (20.0% drift)',
                            model: 'EQUAL_WEIGHT',
                        },
                    ],
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;
    });

    it('renders multi-currency recommendations, segments USD vs EGP cash flows, and requires admin confirmation', async () => {
        const onApply = jest.fn();
        const onClose = jest.fn();

        render(
            <PortfolioRebalanceModal
                isOpen={true}
                onClose={onClose}
                activePortfolioId={1}
                onApplyRebalance={onApply}
            />
        );

        expect(screen.getByText(/Institutional Rebalancing Desk/i)).toBeInTheDocument();
        expect((await screen.findAllByText('COMI')).length).toBeGreaterThan(0);
        expect(screen.getAllByText('EAST').length).toBeGreaterThan(0);
        expect(screen.getAllByText('GTEX').length).toBeGreaterThan(0);

        // Click "Review Execution Instructions" to advance to the staging execution report
        const reviewBtn = screen.getByRole('button', { name: /Review Execution Instructions/i });
        fireEvent.click(reviewBtn);

        // Verify Staging Report elements
        expect(screen.getByText(/Rebalance Execution Report & Staging Ticket/i)).toBeInTheDocument();
        expect(screen.getByText(/Phase 1: Sell Orders/i)).toBeInTheDocument();
        expect(screen.getByText(/Phase 2: Buy Orders/i)).toBeInTheDocument();
        expect(screen.getByText(/EGX Multi-Currency Notice/i)).toBeInTheDocument();

        // Check for segmented EGP and USD cash flow cards
        expect(screen.getByText(/🇪🇬 EGP Cash Generated/i)).toBeInTheDocument();
        expect(screen.getByText(/🇺🇸 USD Cash Required/i)).toBeInTheDocument();

        // The confirm button should be disabled before acknowledging the checkbox
        const confirmBtn = screen.getByRole('button', { name: /Confirm & Execute Rebalance/i });
        expect(confirmBtn).toBeDisabled();

        // Check the acknowledgment checkbox
        const ackCheckbox = screen.getByLabelText(/Admin Confirmation/i);
        fireEvent.click(ackCheckbox);
        expect(ackCheckbox).toBeChecked();
        expect(confirmBtn).not.toBeDisabled();

        // Click confirm
        fireEvent.click(confirmBtn);
        expect(onApply).toHaveBeenCalledWith('EQUAL_WEIGHT', expect.any(Object));
    });
});
