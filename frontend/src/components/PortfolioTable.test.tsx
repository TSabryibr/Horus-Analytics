import { render, screen, fireEvent } from '@testing-library/react';
import { PortfolioTable } from './PortfolioTable';
import { Position, PortfolioHealth } from '../types';
import '@testing-library/jest-dom';

const mockPositions: Position[] = [
    { id: 1, ticker: 'BTC', currency: 'USD', shares: 1.5, entry_price: 30000, current_price: 35000, pnl_pct: 16.67, pnl: 7500, risk_status: 'LOW', status: 'OPEN' },
    { id: 2, ticker: 'ETH', currency: 'USD', shares: 10, entry_price: 2000, current_price: 1800, pnl_pct: -10.0, pnl: -2000, risk_status: 'HIGH', status: 'OPEN' },
];

const mockHealth: PortfolioHealth = {
    status: 'HEALTHY',
    diagnoses: []
};

describe('PortfolioTable', () => {
    const mockEdit = jest.fn();
    const mockClose = jest.fn();

    beforeEach(() => {
        mockEdit.mockClear();
        mockClose.mockClear();
    });

    it('renders positions correctly', () => {
        render(<PortfolioTable positions={mockPositions} health={mockHealth} onEdit={mockEdit} onClose={mockClose} />);
        expect(screen.getByText('BTC')).toBeInTheDocument();
        expect(screen.getByText('ETH')).toBeInTheDocument();
        expect(screen.getByText('1.5')).toBeInTheDocument(); // shares
        expect(screen.getByText('Sell 1.5')).toBeInTheDocument();
    });

    it('calls onEdit when edit button click', () => {
        render(<PortfolioTable positions={mockPositions} health={mockHealth} onEdit={mockEdit} onClose={mockClose} />);
        const editBtns = screen.getAllByTitle("Update Risk");
        fireEvent.click(editBtns[0]);
        expect(mockEdit).toHaveBeenCalledWith(mockPositions[0]);
    });

    it('calls onClose when delete button click', () => {
        render(<PortfolioTable positions={mockPositions} health={mockHealth} onEdit={mockEdit} onClose={mockClose} />);
        const closeBtns = screen.getAllByTitle("Close Position");
        fireEvent.click(closeBtns[0]);
        expect(mockClose).toHaveBeenCalledWith(mockPositions[0].ticker);
    });
});
