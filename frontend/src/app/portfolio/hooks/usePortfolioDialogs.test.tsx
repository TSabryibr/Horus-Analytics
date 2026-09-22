import { renderHook, act } from '@testing-library/react';
import { usePortfolioDialogs } from './usePortfolioDialogs';

describe('usePortfolioDialogs', () => {
    const mockShowUiMessage = jest.fn();
    const mockSubmitClosePosition = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    const setup = (hoard: any = { positions: [] }) => {
        return renderHook(() => usePortfolioDialogs({
            hoard,
            showUiMessage: mockShowUiMessage,
            submitClosePosition: mockSubmitClosePosition,
        }));
    };

    describe('Genesis Arrays', () => {
        it('adds, updates, and removes holding rows', () => {
            const { result } = setup();

            act(() => {
                result.current.addGenesisHoldingRow();
                result.current.addGenesisHoldingRow();
            });

            expect(result.current.genesisData.holdings).toHaveLength(2);
            const firstId = result.current.genesisData.holdings[0].id;

            act(() => {
                result.current.updateGenesisHoldingRow(firstId, 'ticker', 'COMI');
            });

            expect(result.current.genesisData.holdings[0].ticker).toBe('COMI');

            act(() => {
                result.current.removeGenesisHoldingRow(firstId);
            });

            expect(result.current.genesisData.holdings).toHaveLength(1);
            expect(result.current.genesisData.holdings[0].ticker).toBe(''); // The second one
        });
    });

    describe('Close Position Logic', () => {
        const mockHoard = {
            positions: [
                { ticker: 'COMI', shares: 1000, current_price: 50 },
                { ticker: 'HRHO', shares: 0, current_price: 10 },
            ]
        };

        it('requests close position successfully', () => {
            const { result } = setup(mockHoard);

            act(() => {
                result.current.requestClosePosition('COMI');
            });

            expect(result.current.closeConfirmOpen).toBe(true);
            expect(result.current.pendingClosePosition?.ticker).toBe('COMI');
            expect(result.current.pendingCloseShares).toBe('1000');
            expect(result.current.pendingClosePrice).toBe('50.000'); // formatPrice adds .000
        });

        it('shows error if no sellable shares', () => {
            const { result } = setup(mockHoard);

            act(() => {
                result.current.requestClosePosition('HRHO');
            });

            expect(mockShowUiMessage).toHaveBeenCalledWith('error', 'Position HRHO has no sellable shares.');
            expect(result.current.closeConfirmOpen).toBe(false);
        });

        it('calculates quick close shares', () => {
            const { result } = setup(mockHoard);

            act(() => {
                result.current.requestClosePosition('COMI');
            });

            act(() => {
                result.current.setQuickCloseShares(50);
            });

            expect(result.current.pendingCloseShares).toBe('500');

            act(() => {
                result.current.setQuickCloseShares(100);
            });

            expect(result.current.pendingCloseShares).toBe('1000');
        });

        it('submits close position request properly', async () => {
            const { result } = setup(mockHoard);

            act(() => {
                result.current.requestClosePosition('COMI');
            });

            await act(async () => {
                await result.current.confirmClosePosition();
            });

            expect(mockSubmitClosePosition).toHaveBeenCalledWith(
                mockHoard.positions[0],
                1000,
                50
            );
            expect(result.current.closeConfirmOpen).toBe(false);
        });

        it('prevents submission of invalid shares', async () => {
            const { result } = setup(mockHoard);

            act(() => {
                result.current.requestClosePosition('COMI');
            });

            act(() => {
                result.current.setPendingCloseShares('2000'); // larger than max limit
            });

            await act(async () => {
                await result.current.confirmClosePosition();
            });

            expect(mockShowUiMessage).toHaveBeenCalledWith('error', 'Cannot sell more than 1000 shares for COMI.');
            expect(mockSubmitClosePosition).not.toHaveBeenCalled();
        });
    });
});
