import { fireEvent, render, screen } from '@testing-library/react';

import { WhalesShell } from './WhalesShell';

describe('WhalesShell', () => {
    it('renders shell chrome and dispatches filter and refresh actions', () => {
        const onFilterChange = jest.fn();
        const onRefresh = jest.fn();

        render(
            <WhalesShell
                filter="co"
                isLoading={false}
                onFilterChange={onFilterChange}
                onRefresh={onRefresh}
                netFlowBias="🟢 Accumulation Lead (+5)"
                leadSector="Banking"
                candidateCount={12}
            >
                <div>whales-body</div>
            </WhalesShell>,
        );

        expect(screen.getByText('Institutional Flow Tracker')).toBeInTheDocument();
        expect(screen.getByText('🟢 Accumulation Lead (+5)')).toBeInTheDocument();
        expect(screen.getByText('Banking')).toBeInTheDocument();
        expect(screen.getByText('12 Candidates')).toBeInTheDocument();
        expect(screen.getByText('whales-body')).toBeInTheDocument();

        fireEvent.change(screen.getByPlaceholderText('Filter by ticker or sector...'), {
            target: { value: 'bank' },
        });
        fireEvent.click(screen.getByRole('button', { name: /Refresh whale data/i }));

        expect(onFilterChange).toHaveBeenCalledWith('bank');
        expect(onRefresh).toHaveBeenCalledTimes(1);
    });

    it('disables refresh while loading', () => {
        render(
            <WhalesShell
                filter=""
                isLoading
                onFilterChange={jest.fn()}
                onRefresh={jest.fn()}
            >
                <div>whales-body</div>
            </WhalesShell>,
        );

        expect(screen.getByRole('button', { name: /Refresh whale data/i })).toBeDisabled();
    });
});
