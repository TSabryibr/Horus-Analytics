import { act, renderHook, waitFor } from '@testing-library/react';

import { Position } from '@/types';
import { usePortfolioActions } from './usePortfolioActions';

describe('usePortfolioActions', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        Object.defineProperty(window, 'open', {
            writable: true,
            value: jest.fn(),
        });
        Object.defineProperty(window, 'confirm', {
            writable: true,
            value: jest.fn(() => true),
        });
    });

    it('submits add-position successfully and triggers refresh plus success mapping', async () => {
        const refreshData = jest.fn(async () => undefined);
        const showUiMessage = jest.fn();
        const clearUiMessage = jest.fn();

        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/portfolio/add')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'success' }),
                } as Response;
            }
            throw new Error(`Unexpected fetch: ${url}`);
        }) as jest.Mock;

        const { result } = renderHook(() =>
            usePortfolioActions({
                activePortfolioId: 7,
                refreshData,
                showUiMessage,
                clearUiMessage,
                importFileInputRef: { current: null },
            })
        );

        const closeModal = jest.fn();
        const resetForm = jest.fn();

        await act(async () => {
            await result.current.handleAddPosition({
                ticker: 'comi',
                shares: '100',
                price: '103.2',
                sl: '',
                tp: '120',
                tp2: '',
                date: '',
            }, { closeModal, resetForm });
        });

        await waitFor(() => {
            expect(closeModal).toHaveBeenCalled();
            expect(resetForm).toHaveBeenCalled();
            expect(refreshData).toHaveBeenCalled();
            expect(showUiMessage).toHaveBeenCalledWith('success', 'Position COMI added.');
        });
    });

    it('maps WFA block failures on add-position', async () => {
        const showUiMessage = jest.fn();

        global.fetch = jest.fn(async () => ({
            ok: false,
            status: 403,
            json: async () => ({ detail: 'Ticker blocked by WFA' }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() =>
            usePortfolioActions({
                activePortfolioId: 7,
                refreshData: jest.fn(async () => undefined),
                showUiMessage,
                clearUiMessage: jest.fn(),
                importFileInputRef: { current: null },
            })
        );

        await act(async () => {
            await result.current.handleAddPosition({
                ticker: 'COMI',
                shares: '100',
                price: '103.2',
                sl: '',
                tp: '',
                tp2: '',
                date: '',
            }, { closeModal: jest.fn(), resetForm: jest.fn() });
        });

        await waitFor(() => {
            expect(showUiMessage).toHaveBeenCalledWith('error', 'Blocked by WFA gate: Ticker blocked by WFA');
        });
    });

    it('consolidates duplicate genesis holdings before submitting', async () => {
        const refreshData = jest.fn(async () => undefined);
        const showUiMessage = jest.fn();
        const closeModal = jest.fn();
        const clearUiMessage = jest.fn();
        let submittedBody: any = null;

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/portfolio/genesis') && init?.method === 'POST') {
                submittedBody = JSON.parse(String(init.body));
                return {
                    ok: true,
                    json: async () => ({ status: 'success', errors: [] }),
                } as Response;
            }
            throw new Error(`Unexpected fetch: ${url}`);
        }) as jest.Mock;

        const { result } = renderHook(() =>
            usePortfolioActions({
                activePortfolioId: 7,
                refreshData,
                showUiMessage,
                clearUiMessage,
                importFileInputRef: { current: null },
            })
        );

        await act(async () => {
            await result.current.handleGenesis({
                egp_balance: '0',
                usd_balance: '0',
                holdings: [
                    { id: 1, ticker: 'tycn', shares: '6470', price: '15.3' },
                    { id: 2, ticker: 'TYCN', shares: '1230', price: '14.25' },
                    { id: 3, ticker: 'GTEX', shares: '240000', price: '0.0381' },
                ],
            }, { closeModal });
        });

        expect(submittedBody.holdings).toEqual([
            { ticker: 'TYCN', shares: 7700, price: (6470 * 15.3 + 1230 * 14.25) / 7700 },
            { ticker: 'GTEX', shares: 240000, price: 0.0381 },
        ]);
        expect(closeModal).toHaveBeenCalled();
        expect(refreshData).toHaveBeenCalled();
    });

    it('imports CSV backup and refreshes runtime data', async () => {
        const refreshData = jest.fn(async () => undefined);
        const showUiMessage = jest.fn();

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/portfolio/import?portfolio_id=7&replace_existing=true') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        imported: { profile: 1, positions: 2, trades: 3, snapshots: 4 },
                    }),
                } as Response;
            }
            throw new Error(`Unexpected fetch: ${url}`);
        }) as jest.Mock;

        const fileInput = { current: { click: jest.fn() } } as unknown as React.RefObject<HTMLInputElement>;
        const { result } = renderHook(() =>
            usePortfolioActions({
                activePortfolioId: 7,
                refreshData,
                showUiMessage,
                clearUiMessage: jest.fn(),
                importFileInputRef: fileInput,
            })
        );

        const file = new File(['csv'], 'backup.csv', { type: 'text/csv' });
        const event = {
            target: {
                files: [file],
                value: 'backup.csv',
            },
        } as unknown as React.ChangeEvent<HTMLInputElement>;

        await act(async () => {
            await result.current.handleImportCsv(event);
        });

        await waitFor(() => {
            expect(refreshData).toHaveBeenCalled();
            expect(showUiMessage).toHaveBeenCalledWith(
                'success',
                'Import complete: profile 1, positions 2, trades 3, snapshots 4.'
            );
            expect(event.target.value).toBe('');
        });
    });

    it('opens export endpoint for the active portfolio', () => {
        const { result } = renderHook(() =>
            usePortfolioActions({
                activePortfolioId: 7,
                refreshData: jest.fn(async () => undefined),
                showUiMessage: jest.fn(),
                clearUiMessage: jest.fn(),
                importFileInputRef: { current: null },
            })
        );

        result.current.handleExport();

        expect(window.open).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/portfolio/export?portfolio_id=7'),
            '_blank'
        );
    });

    it('updates a position and emits success mapping', async () => {
        const refreshData = jest.fn(async () => undefined);
        const showUiMessage = jest.fn();
        const position = { ticker: 'COMI' } as Position;

        global.fetch = jest.fn(async () => ({
            ok: true,
            json: async () => ({ status: 'success' }),
        }) as Response) as jest.Mock;

        const { result } = renderHook(() =>
            usePortfolioActions({
                activePortfolioId: 7,
                refreshData,
                showUiMessage,
                clearUiMessage: jest.fn(),
                importFileInputRef: { current: null },
            })
        );

        const onComplete = jest.fn();

        await act(async () => {
            await result.current.handleUpdatePosition(
                position,
                { sl: '90', tp: '120', tp2: '130' },
                { onComplete }
            );
        });

        await waitFor(() => {
            expect(onComplete).toHaveBeenCalled();
            expect(refreshData).toHaveBeenCalled();
            expect(showUiMessage).toHaveBeenCalledWith('success', 'Position COMI updated.');
        });
    });

    it('closes part of a position and maps the partial-close success message', async () => {
        const refreshData = jest.fn(async () => undefined);
        const showUiMessage = jest.fn();
        const position = {
            ticker: 'COMI',
            shares: 100,
            current_price: 99.5,
        } as Position;

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/portfolio/close') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({ status: 'success', action: 'partial_sell' }),
                } as Response;
            }
            throw new Error(`Unexpected fetch: ${url}`);
        }) as jest.Mock;

        const { result } = renderHook(() =>
            usePortfolioActions({
                activePortfolioId: 7,
                refreshData,
                showUiMessage,
                clearUiMessage: jest.fn(),
                importFileInputRef: { current: null },
            })
        );

        await act(async () => {
            await result.current.handleClosePosition(position, 50, 101.25);
        });

        await waitFor(() => {
            expect(refreshData).toHaveBeenCalled();
            expect(showUiMessage).toHaveBeenCalledWith('success', 'Sold 50/100 shares of COMI.');
        });
    });
});
