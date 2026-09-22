import { render, screen } from '@testing-library/react';

import { StrategyTerrainPanel } from './StrategyTerrainPanel';

describe('StrategyTerrainPanel', () => {
    it('renders regime and volatility details', () => {
        render(
            <StrategyTerrainPanel
                getRegimeColor={() => 'border-emerald-500 text-emerald-300'}
                proposal={{
                    regime: 'BULLISH',
                    regime_score: 8.4,
                    volatility: 'ELEVATED',
                    volatility_value: 2.1,
                }}
            />,
        );

        expect(screen.getByText('The Terrain (Regime)')).toBeInTheDocument();
        expect(screen.getByText('BULLISH')).toBeInTheDocument();
        expect(screen.getByText('Score: 8.4/10')).toBeInTheDocument();
        expect(screen.getByText('The Weather (Volatility)')).toBeInTheDocument();
        expect(screen.getByText('ELEVATED')).toBeInTheDocument();
        expect(screen.getByText('2.1%')).toBeInTheDocument();
    });
});
