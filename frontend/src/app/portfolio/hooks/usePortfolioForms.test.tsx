import { renderHook, act } from '@testing-library/react';
import { usePortfolioForms } from './usePortfolioForms';

describe('usePortfolioForms', () => {
    const mockSubmitAddPosition = jest.fn();
    const mockSubmitUpdatePosition = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    const setup = () => {
        return renderHook(() => usePortfolioForms({
            submitAddPosition: mockSubmitAddPosition,
            submitUpdatePosition: mockSubmitUpdatePosition,
        }));
    };

    it('initializes with default state', () => {
        const { result } = setup();

        expect(result.current.isAddModalOpen).toBe(false);
        expect(result.current.isUpdateModalOpen).toBe(false);
        expect(result.current.selectedPosition).toBeNull();
        expect(result.current.formData.ticker).toBe('');
    });

    it('handles form field changes', () => {
        const { result } = setup();

        act(() => {
            result.current.handleFormFieldChange('ticker', 'COMI');
            result.current.handleFormFieldChange('shares', '100');
        });

        expect(result.current.formData.ticker).toBe('COMI');
        expect(result.current.formData.shares).toBe('100');
    });

    it('calls submitAddPosition and clears form on success', async () => {
        mockSubmitAddPosition.mockImplementation(async (data, options) => {
            options.closeModal();
            options.resetForm();
        });

        const { result } = setup();

        act(() => {
            result.current.setIsAddModalOpen(true);
            result.current.handleFormFieldChange('ticker', 'COMI');
        });

        expect(result.current.isAddModalOpen).toBe(true);

        const fakeEvent = { preventDefault: jest.fn() } as unknown as React.FormEvent;

        await act(async () => {
            await result.current.handleAddPosition(fakeEvent);
        });

        expect(fakeEvent.preventDefault).toHaveBeenCalled();
        expect(mockSubmitAddPosition).toHaveBeenCalledWith(
            expect.objectContaining({ ticker: 'COMI' }),
            expect.any(Object)
        );

        expect(result.current.isAddModalOpen).toBe(false);
        expect(result.current.formData.ticker).toBe('');
    });

    it('calls submitUpdatePosition and resets tracking state on success', async () => {
        mockSubmitUpdatePosition.mockImplementation(async (pos, data, options) => {
            options.onComplete();
        });

        const { result } = setup();
        const mockPos = { ticker: 'HRHO', current_price: 15 } as any;

        act(() => {
            result.current.setIsUpdateModalOpen(true);
            result.current.setSelectedPosition(mockPos);
        });

        expect(result.current.selectedPosition).toBe(mockPos);

        const fakeEvent = { preventDefault: jest.fn() } as unknown as React.FormEvent;

        await act(async () => {
            await result.current.handleUpdatePosition(fakeEvent);
        });

        expect(mockSubmitUpdatePosition).toHaveBeenCalledWith(
            mockPos,
            expect.any(Object),
            expect.any(Object)
        );

        expect(result.current.isUpdateModalOpen).toBe(false);
        expect(result.current.selectedPosition).toBeNull();
    });
});
