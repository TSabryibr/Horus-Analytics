import { fireEvent, render, screen } from '@testing-library/react';

import { HomeArchivesModal } from './HomeArchivesModal';

describe('HomeArchivesModal', () => {
    it('renders grouped archive entries and closes through the close action', () => {
        const onClose = jest.fn();

        render(
            <HomeArchivesModal
                archivesByDate={{
                    '2026-03-18': [
                        { ticker: 'COMI', signal_type: 'BUY', price: 101, score: 8 },
                    ],
                }}
                isOpen
                onClose={onClose}
            />
        );

        expect(screen.getByText('Matrix Archive Logs')).toBeInTheDocument();
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('CONF: 80%')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Close archive modal/i }));
        expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('renders the empty archive state when no entries exist', () => {
        render(
            <HomeArchivesModal
                archivesByDate={{}}
                isOpen
                onClose={jest.fn()}
            />
        );

        expect(screen.getByText('Log Data Corrupted or Empty')).toBeInTheDocument();
    });
});
