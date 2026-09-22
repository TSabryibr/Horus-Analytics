import { fireEvent, render, screen } from '@testing-library/react';

import { AuditLifecyclePanel } from './AuditLifecyclePanel';

describe('AuditLifecyclePanel', () => {
    it('renders lifecycle rows and dispatches override actions', () => {
        const onOverride = jest.fn();

        render(
            <AuditLifecyclePanel
                loading={false}
                summary={{ active_count: 3, ambiguous_count: 1 }}
                rows={[
                    { id: 1, ticker: 'COMI', state: 'AMBIGUOUS', lane: 'swing', source_module: 'SCANNER', published_at: '2026-04-22T10:00:00' },
                    { id: 2, ticker: 'HRHO', state: 'OPEN', lane: 'intraday', source_module: 'ORACLE', published_at: '2026-04-22T11:00:00' },
                ]}
                onOverride={onOverride}
            />
        );

        expect(screen.getByText('Lifecycle Review Ledger')).toBeInTheDocument();
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Resolve Open/i }));
        expect(onOverride).toHaveBeenCalledWith(1, expect.objectContaining({ action: 'RECLASSIFY', target_state: 'OPEN' }));

        fireEvent.click(screen.getByRole('button', { name: /Mark TP1/i }));
        expect(onOverride).toHaveBeenCalledWith(2, expect.objectContaining({ action: 'MARK_TP1' }));
    });
});
