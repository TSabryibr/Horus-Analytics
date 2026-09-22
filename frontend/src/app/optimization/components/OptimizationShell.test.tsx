import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { OptimizationShell } from './OptimizationShell';

describe('OptimizationShell', () => {
    it('renders the header, mode switcher, message banner, and children', () => {
        const onSelectMode = jest.fn();

        const now = new Date();
        render(
            <OptimizationShell
                mode="SIMULATOR"
                onSelectMode={onSelectMode}
                uiMessage={{ type: 'error', text: 'Optimizer is unavailable.' }}
                wsConnected={true}
                lastUpdated={now}
            >
                <div data-testid="optimization-shell-children" />
            </OptimizationShell>
        );

        expect(screen.getByRole('heading', { name: /Strategy Lab/i })).toBeInTheDocument();
        expect(screen.getByText('Lab Environment')).toBeInTheDocument();
        expect(screen.getByText('⚡ WS LIVE')).toBeInTheDocument();
        expect(screen.getByText('0s ago')).toBeInTheDocument();
        expect(screen.getByText('SIMULATOR')).toBeInTheDocument();
        expect(screen.getByRole('group', { name: /Strategy Lab mode/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Backtester/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /AI Optimizer/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Pine Lab/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Backtester/i })).toHaveAttribute('aria-pressed', 'true');
        expect(screen.getByRole('button', { name: /AI Optimizer/i })).toHaveAttribute('aria-pressed', 'false');
        expect(screen.getByText('Optimizer is unavailable.')).toBeInTheDocument();
        expect(screen.getByTestId('optimization-shell-children')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /AI Optimizer/i }));

        expect(onSelectMode).toHaveBeenCalledWith('OPTIMIZER');

        fireEvent.click(screen.getByRole('button', { name: /Pine Lab/i }));

        expect(onSelectMode).toHaveBeenCalledWith('PINE_LAB');
    });
});
