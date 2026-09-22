import React from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';

import { PortfolioProvider, getPreferredPortfolioId, usePortfolioData } from './PortfolioContext';
import { apiFetch, isIgnorableNetworkError, readJsonSafe } from '@/lib/api';

jest.mock('@/lib/api', () => ({
    apiFetch: jest.fn(),
    isIgnorableNetworkError: jest.fn(() => false),
    readJsonSafe: jest.fn(),
}));

function PortfolioConsumer() {
    const { activePortfolioId, defaultPortfolioId, portfolios, refreshPortfolios, setDefaultSystemPortfolioId } = usePortfolioData();

    return (
        <div>
            <div data-testid="active-portfolio-id">{activePortfolioId}</div>
            <div data-testid="default-portfolio-id">{defaultPortfolioId}</div>
            <div data-testid="portfolio-count">{portfolios.length}</div>
            <button onClick={() => void refreshPortfolios()}>refresh</button>
            <button onClick={() => void setDefaultSystemPortfolioId(8)}>set-default</button>
        </div>
    );
}

describe('PortfolioContext', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        (isIgnorableNetworkError as jest.Mock).mockReturnValue(false);
    });

    it('prefers the persisted SYSTEM default before user fallbacks', () => {
        expect(getPreferredPortfolioId([
            { id: 2, name: 'My Portfolio', type: 'USER' },
            { id: 3, name: 'Other', type: 'USER' },
            { id: 4, name: 'Horus', type: 'USER' },
            { id: 8, name: 'Daily Simulation', type: 'SYSTEM' },
        ], 8)).toBe(8);
    });

    it('falls back to the first SYSTEM portfolio before user preferences', () => {
        expect(getPreferredPortfolioId([
            { id: 8, name: 'Daily Simulation', type: 'SYSTEM' },
            { id: 2, name: 'My Portfolio', type: 'USER' },
            { id: 3, name: 'Other', type: 'USER' },
        ])).toBe(8);
    });

    it('falls back to STRATEGY portfolios when no SYSTEM portfolios exist', () => {
        expect(getPreferredPortfolioId([
            { id: 12, name: 'Breakout Profile', type: 'STRATEGY' },
            { id: 2, name: 'My Portfolio', type: 'USER' },
        ])).toBe(12);
    });

    it('falls back to My Portfolio then any user portfolio when no SYSTEM portfolios exist', () => {
        expect(getPreferredPortfolioId([
            { id: 2, name: 'My Portfolio', type: 'USER' },
            { id: 3, name: 'Other', type: 'USER' },
        ])).toBe(2);

        expect(getPreferredPortfolioId([
            { id: 3, name: 'Other', type: 'USER' },
        ])).toBe(3);
    });

    it('auto-selects the persisted default SYSTEM portfolio on first refresh', async () => {
        (apiFetch as jest.Mock)
            .mockResolvedValueOnce({ ok: true, kind: 'portfolios' })
            .mockResolvedValueOnce({ ok: true, kind: 'default' });
        (readJsonSafe as jest.Mock).mockImplementation(async (response: { kind: string }) => {
            if (response.kind === 'portfolios') {
                return [
                    { id: 8, name: 'Daily Simulation', type: 'SYSTEM' },
                    { id: 2, name: 'My Portfolio', type: 'USER' },
                    { id: 7, name: 'Horus', type: 'USER' },
                ];
            }
            return {
                portfolio_id: 8,
                portfolio_name: 'Daily Simulation',
                portfolio_type: 'SYSTEM',
            };
        });

        render(
            <PortfolioProvider>
                <PortfolioConsumer />
            </PortfolioProvider>
        );

        await waitFor(() => {
            expect(screen.getByTestId('active-portfolio-id')).toHaveTextContent('8');
        });
        expect(screen.getByTestId('default-portfolio-id')).toHaveTextContent('8');
        expect(screen.getByTestId('portfolio-count')).toHaveTextContent('3');
    });

    it('does not overwrite an already-selected active portfolio', async () => {
        (apiFetch as jest.Mock)
            .mockResolvedValueOnce({ ok: true, kind: 'portfolios-initial' })
            .mockResolvedValueOnce({ ok: true, kind: 'default-initial' })
            .mockResolvedValueOnce({ ok: true, kind: 'portfolios-refresh' })
            .mockResolvedValueOnce({ ok: true, kind: 'default-refresh' });
        (readJsonSafe as jest.Mock)
            .mockResolvedValueOnce([
                { id: 8, name: 'Daily Simulation', type: 'SYSTEM' },
                { id: 7, name: 'Horus', type: 'USER' },
                { id: 2, name: 'My Portfolio', type: 'USER' },
            ])
            .mockResolvedValueOnce({
                portfolio_id: 8,
                portfolio_name: 'Daily Simulation',
                portfolio_type: 'SYSTEM',
            })
            .mockResolvedValueOnce([
                { id: 8, name: 'Daily Simulation', type: 'SYSTEM' },
                { id: 7, name: 'Horus', type: 'USER' },
                { id: 2, name: 'My Portfolio', type: 'USER' },
                { id: 9, name: 'Another', type: 'USER' },
            ])
            .mockResolvedValueOnce({
                portfolio_id: 8,
                portfolio_name: 'Daily Simulation',
                portfolio_type: 'SYSTEM',
            });

        render(
            <PortfolioProvider>
                <PortfolioConsumer />
            </PortfolioProvider>
        );

        await waitFor(() => {
            expect(screen.getByTestId('active-portfolio-id')).toHaveTextContent('8');
        });

        await act(async () => {
            screen.getByRole('button', { name: 'refresh' }).click();
        });

        expect(screen.getByTestId('active-portfolio-id')).toHaveTextContent('8');
        expect(screen.getByTestId('portfolio-count')).toHaveTextContent('4');
    });

    it('falls back to Horus when no SYSTEM portfolios exist', async () => {
        (apiFetch as jest.Mock)
            .mockResolvedValueOnce({ ok: true, kind: 'portfolios' })
            .mockResolvedValueOnce({ ok: true, kind: 'default' });
        (readJsonSafe as jest.Mock)
            .mockResolvedValueOnce([
                { id: 2, name: 'My Portfolio', type: 'USER' },
                { id: 7, name: 'Horus', type: 'USER' },
            ])
            .mockResolvedValueOnce({
                portfolio_id: null,
                portfolio_name: null,
                portfolio_type: null,
            });

        render(
            <PortfolioProvider>
                <PortfolioConsumer />
            </PortfolioProvider>
        );

        await waitFor(() => {
            expect(screen.getByTestId('active-portfolio-id')).toHaveTextContent('7');
        });
        expect(screen.getByTestId('default-portfolio-id')).toHaveTextContent('0');
    });

    it('updates the default portfolio id after a successful default assignment', async () => {
        (apiFetch as jest.Mock)
            .mockResolvedValueOnce({ ok: true, kind: 'portfolios' })
            .mockResolvedValueOnce({ ok: true, kind: 'default' })
            .mockResolvedValueOnce({ ok: true, kind: 'set-default' });
        (readJsonSafe as jest.Mock)
            .mockResolvedValueOnce([
                { id: 8, name: 'Daily Simulation', type: 'SYSTEM' },
                { id: 9, name: 'Intraday Simulation', type: 'SYSTEM' },
            ])
            .mockResolvedValueOnce({
                portfolio_id: 9,
                portfolio_name: 'Intraday Simulation',
                portfolio_type: 'SYSTEM',
            })
            .mockResolvedValueOnce({
                status: 'updated',
                portfolio_id: 8,
                portfolio_name: 'Daily Simulation',
                portfolio_type: 'SYSTEM',
            });

        render(
            <PortfolioProvider>
                <PortfolioConsumer />
            </PortfolioProvider>
        );

        await waitFor(() => {
            expect(screen.getByTestId('default-portfolio-id')).toHaveTextContent('9');
        });

        await act(async () => {
            screen.getByRole('button', { name: 'set-default' }).click();
        });

        await waitFor(() => {
            expect(screen.getByTestId('default-portfolio-id')).toHaveTextContent('8');
        });
    });

    it('stays quiet when portfolio bootstrap hits an ignorable offline error', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        (apiFetch as jest.Mock).mockRejectedValueOnce(new TypeError('Failed to fetch'));
        (isIgnorableNetworkError as jest.Mock).mockReturnValue(true);

        render(
            <PortfolioProvider>
                <PortfolioConsumer />
            </PortfolioProvider>
        );

        await waitFor(() => {
            expect(apiFetch).toHaveBeenCalled();
        });

        expect(consoleErrorSpy).not.toHaveBeenCalled();
        consoleErrorSpy.mockRestore();
    });
});
