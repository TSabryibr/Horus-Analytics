import { render, screen } from '@testing-library/react';

import { StrategyReasoningPanel } from './StrategyReasoningPanel';

describe('StrategyReasoningPanel', () => {
    it('renders provided reasoning', () => {
        render(<StrategyReasoningPanel reasoning="Momentum and breadth are aligned." />);

        expect(screen.getByText(/Momentum and breadth are aligned\./)).toBeInTheDocument();
    });

    it('falls back when reasoning is empty', () => {
        render(<StrategyReasoningPanel reasoning="" />);

        expect(screen.getByText(/No reasoning provided\./)).toBeInTheDocument();
    });
});
