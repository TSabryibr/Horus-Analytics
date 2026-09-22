import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { TrapCard } from './TrapCard';

describe('TrapCard', () => {
    it('renders bull trap details correctly', () => {
        render(
            <TrapCard 
                type="bull"
                ticker="COMI"
                date="2026-03-19"
                price="103.20"
                depth={2.4}
                details="Breakout failed"
            />
        );

        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('103.20')).toBeInTheDocument();
        expect(screen.getByText('-2.4% Fakeout')).toBeInTheDocument();
        expect(screen.getByText('Breakout failed')).toBeInTheDocument();
        expect(screen.getByText('COMI')).toHaveClass('group-hover:text-rose-400');
    });

    it('renders bear trap details correctly', () => {
        render(
            <TrapCard 
                type="bear"
                ticker="HRHO"
                date="2026-03-19"
                price="37.80"
                depth={1.9}
                details="Breakdown reversed"
            />
        );

        expect(screen.getByText('HRHO')).toBeInTheDocument();
        expect(screen.getByText('37.80')).toBeInTheDocument();
        expect(screen.getByText('+1.9% Rebound')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toHaveClass('group-hover:text-emerald-400');
    });
});
