import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import ArbitragePage from './page';

const refreshArbitrage = jest.fn();
const setUniverse = jest.fn();
const setFilter = jest.fn();
const onExecute = jest.fn();

function mockRuntime(overrides: Record<string, any> = {}) {
    return {
        isLoading: false,
        universe: 'default',
        setUniverse,
        filter: '',
        setFilter,
        filteredMirrors: [
            { Leader: 'COMI', Follower: 'HRHO', Lag: 2, Confidence: 81.2, Type: 'Positive' },
            { Leader: 'ETEL', Follower: 'FWRY', Lag: 1, Confidence: 71.4, Type: 'Negative' },
        ],
        executing: {},
        actionStatus: null,
        onRefresh: refreshArbitrage,
        onExecute,
        ...overrides,
    };
}

let runtimeValue = mockRuntime();

jest.mock('./hooks/useArbitrageRuntime', () => ({
    useArbitrageRuntime: () => runtimeValue,
}));

describe('ArbitragePage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        runtimeValue = mockRuntime();
    });

    it('renders mirror pairs with leader, follower, lag, and confidence', () => {
        render(<ArbitragePage />);

        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
        expect(screen.getByText('ETEL')).toBeInTheDocument();
        expect(screen.getByText('FWRY')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText('81.2%')).toBeInTheDocument();
        expect(screen.getByText('71.4%')).toBeInTheDocument();
    });

    it('shows type badge for each mirror (Positive Echo / Negative Echo)', () => {
        render(<ArbitragePage />);

        expect(screen.getByText('Positive Echo')).toBeInTheDocument();
        expect(screen.getByText('Negative Echo')).toBeInTheDocument();
    });

    it('filters mirror pairs case-insensitively by ticker', () => {
        render(<ArbitragePage />);

        fireEvent.change(screen.getByPlaceholderText('Filter pairs...'), { target: { value: 'fWRy' } });

        expect(setFilter).toHaveBeenCalledWith('fWRy');
    });

    it('shows empty message when no mirrors exist', () => {
        runtimeValue = mockRuntime({ filteredMirrors: [] });
        render(<ArbitragePage />);

        expect(screen.getByText('No echoing pairs found in the current mirror scan.')).toBeInTheDocument();
    });

    it('shows empty message when filter matches nothing', () => {
        runtimeValue = mockRuntime({ filter: 'ZZZZZ', filteredMirrors: [] });
        render(<ArbitragePage />);

        expect(screen.getByText('No echoing pairs found in the current mirror scan.')).toBeInTheDocument();
    });

    it('calls refreshArbitrage when header button is clicked', () => {
        render(<ArbitragePage />);

        fireEvent.click(screen.getAllByRole('button')[2]);
        expect(refreshArbitrage).toHaveBeenCalledTimes(1);
    });
});
