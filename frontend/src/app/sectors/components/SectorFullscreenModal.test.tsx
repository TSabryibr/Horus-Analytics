import { fireEvent, render, screen } from '@testing-library/react';

import { SectorFullscreenModal } from './SectorFullscreenModal';

describe('SectorFullscreenModal', () => {
    it('renders fullscreen chrome and delegates close actions', () => {
        const onClose = jest.fn();

        render(
            <SectorFullscreenModal isOpen onClose={onClose}>
                <div>rrg-body</div>
            </SectorFullscreenModal>
        );

        expect(screen.getByText('Alfheim RRG - Fullscreen')).toBeInTheDocument();
        expect(screen.getByText('rrg-body')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Close fullscreen RRG/i }));
        expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('does not render when closed and closes on backdrop click', () => {
        const onClose = jest.fn();
        const { rerender } = render(
            <SectorFullscreenModal isOpen={false} onClose={onClose}>
                <div>rrg-body</div>
            </SectorFullscreenModal>
        );

        expect(screen.queryByText('Alfheim RRG - Fullscreen')).not.toBeInTheDocument();

        rerender(
            <SectorFullscreenModal isOpen onClose={onClose}>
                <div>rrg-body</div>
            </SectorFullscreenModal>
        );

        fireEvent.click(screen.getByTestId('sector-fullscreen-backdrop'));
        expect(onClose).toHaveBeenCalledTimes(1);
    });
});
