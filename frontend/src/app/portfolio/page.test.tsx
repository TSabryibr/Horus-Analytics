import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import PortfolioPage from './page';

jest.mock('../context/GlobalDataContext', () => ({
    usePortfolioData: () => ({
        activePortfolioId: 1,
    }),
    useTrapsData: () => ({
        traps: { bull_traps: [], bear_traps: [] },
        trapsLoading: false,
        refreshTraps: jest.fn(),
    }),
}));

jest.mock('@/components/PortfolioTable', () => ({
    PortfolioTable: ({ onClose }: { onClose: (ticker: string) => void }) => (
        <div data-testid="mock-portfolio-table">
            <button type="button" onClick={() => onClose('COMI')}>
                Mock Close COMI
            </button>
        </div>
    ),
}));

jest.mock('./components/PortfolioReportSection', () => ({
    __esModule: true,
    default: () => <div data-testid="mock-portfolio-report-section" />,
}));

describe('PortfolioPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        Object.defineProperty(window, 'open', {
            writable: true,
            value: jest.fn(),
        });
    });

    it('renders initialized treasury view when active hoard is returned', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/boot-status')) {
                return { ok: true, json: async () => ({ system_ready: true }) } as Response;
            }
            if (url.includes('/api/v1/portfolio?portfolio_id=1')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'active',
                        net_worth_egp: 1500000,
                        net_worth_usd: 10000,
                        cash_egp: 250000,
                        cash_usd: 1200,
                        positions: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/analytics/health')) {
                return { ok: true, json: async () => ({ status: 'success', score: 80 }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/analysis?portfolio_id=1')) {
                return { ok: true, json: async () => ({ status: 'success', recommendations: [], sector_breakdown: {}, heat: 1, health_score: 90 }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/report?portfolio_id=1')) {
                return { ok: true, json: async () => ({ metrics: { total_pnl: 300, win_rate: 50, profit_factor: 1.2, total_trades: 3 }, curve: [], trades: [] }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<PortfolioPage />);

        await waitFor(() => {
            expect(screen.getByRole('heading', { name: /Portfolio Manager/i })).toBeInTheDocument();
            expect(screen.getByTestId('mock-portfolio-table')).toBeInTheDocument();
            expect(screen.getByTestId('mock-portfolio-report-section')).toBeInTheDocument();
        });
    });

    it('renders treasury initialization state when hoard is not active', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/boot-status')) {
                return { ok: true, json: async () => ({ system_ready: true }) } as Response;
            }
            if (url.includes('/api/v1/portfolio?portfolio_id=1')) {
                return { ok: true, json: async () => ({ status: 'inactive' }) } as Response;
            }
            if (url.includes('/api/v1/analytics/health')) {
                return { ok: true, json: async () => ({ status: 'success' }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/analysis?portfolio_id=1')) {
                return { ok: true, json: async () => ({ status: 'success', recommendations: [], sector_breakdown: {}, heat: 1, health_score: 90 }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/report?portfolio_id=1')) {
                return { ok: true, json: async () => ({ metrics: { total_pnl: 0, win_rate: 0, profit_factor: 0, total_trades: 0 }, curve: [], trades: [] }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<PortfolioPage />);

        await waitFor(() => {
            expect(screen.getByText('Initialize Treasury')).toBeInTheDocument();
        });
    });

    it('opens CSV export endpoint from toolbar action', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL) => {
            const url = String(input);
            if (url.includes('/api/v1/system/boot-status')) {
                return { ok: true, json: async () => ({ system_ready: true }) } as Response;
            }
            if (url.includes('/api/v1/portfolio?portfolio_id=1')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'active',
                        net_worth_egp: 1500000,
                        net_worth_usd: 10000,
                        cash_egp: 250000,
                        cash_usd: 1200,
                        positions: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/analytics/health')) {
                return { ok: true, json: async () => ({ status: 'success', score: 80 }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/analysis?portfolio_id=1')) {
                return { ok: true, json: async () => ({ status: 'success', recommendations: [], sector_breakdown: {}, heat: 1, health_score: 90 }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/report?portfolio_id=1')) {
                return { ok: true, json: async () => ({ metrics: { total_pnl: 300, win_rate: 50, profit_factor: 1.2, total_trades: 3 }, curve: [], trades: [] }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<PortfolioPage />);

        const exportButton = await screen.findByRole('button', { name: /Export CSV/i });
        fireEvent.click(exportButton);

        expect(window.open).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/portfolio/export?portfolio_id=1'),
            '_blank'
        );
    });

    it('imports CSV backup and calls the import endpoint', async () => {
        Object.defineProperty(window, 'confirm', {
            writable: true,
            value: jest.fn(() => true),
        });

        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/system/boot-status')) {
                return { ok: true, json: async () => ({ system_ready: true }) } as Response;
            }
            if (url.includes('/api/v1/portfolio?portfolio_id=1')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'active',
                        net_worth_egp: 1500000,
                        net_worth_usd: 10000,
                        cash_egp: 250000,
                        cash_usd: 1200,
                        positions: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/analytics/health')) {
                return { ok: true, json: async () => ({ status: 'success', score: 80 }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/analysis?portfolio_id=1')) {
                return { ok: true, json: async () => ({ status: 'success', recommendations: [], sector_breakdown: {}, heat: 1, health_score: 90 }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/report?portfolio_id=1')) {
                return { ok: true, json: async () => ({ metrics: { total_pnl: 300, win_rate: 50, profit_factor: 1.2, total_trades: 3 }, curve: [], trades: [] }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/import') && init?.method === 'POST') {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'success',
                        imported: { profile: 1, positions: 2, trades: 3, snapshots: 4 },
                    }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<PortfolioPage />);
        await screen.findByRole('button', { name: /Import File/i });

        const fileInput = screen.getByTestId('csv-import-input') as HTMLInputElement;
        expect(fileInput).toBeInTheDocument();

        const file = new File(['record_type,schema_version\nPROFILE,1\n'], 'backup.csv', { type: 'text/csv' });
        fireEvent.change(fileInput, { target: { files: [file] } });

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/portfolio/import?portfolio_id=1&replace_existing=true'),
                expect.objectContaining({ method: 'POST' })
            );
        });
    });

    it('shows WFA gate error when add position is blocked', async () => {
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/system/boot-status')) {
                return { ok: true, json: async () => ({ system_ready: true }) } as Response;
            }
            if (url.includes('/api/v1/portfolio?portfolio_id=1')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'active',
                        net_worth_egp: 1500000,
                        net_worth_usd: 10000,
                        cash_egp: 250000,
                        cash_usd: 1200,
                        positions: [],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/analytics/health')) {
                return { ok: true, json: async () => ({ status: 'success', score: 80 }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/analysis?portfolio_id=1')) {
                return { ok: true, json: async () => ({ status: 'success', recommendations: [], sector_breakdown: {}, heat: 1, health_score: 90 }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/report?portfolio_id=1')) {
                return { ok: true, json: async () => ({ metrics: { total_pnl: 300, win_rate: 50, profit_factor: 1.2, total_trades: 3 }, curve: [], trades: [] }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/add') && init?.method === 'POST') {
                return {
                    ok: false,
                    status: 403,
                    json: async () => ({ detail: 'Ticker blocked by WFA' }),
                } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<PortfolioPage />);

        fireEvent.click(await screen.findByRole('button', { name: /Add Position/i }));
        fireEvent.change(screen.getByPlaceholderText('e.g. COMI'), { target: { value: 'COMI' } });
        fireEvent.change(screen.getByPlaceholderText('100'), { target: { value: '100' } });
        fireEvent.change(screen.getByPlaceholderText('0.0000'), { target: { value: '103.2' } });
        fireEvent.click(screen.getByRole('button', { name: /Authorize Entry/i }));

        await waitFor(() => {
            expect(screen.getByText(/Blocked by WFA gate: Ticker blocked by WFA/i)).toBeInTheDocument();
        });
    });

    it('supports partial close with quantity and percentage shortcut buttons', async () => {
        const closePayloads: any[] = [];
        global.fetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
            const url = String(input);
            if (url.includes('/api/v1/system/boot-status')) {
                return { ok: true, json: async () => ({ system_ready: true }) } as Response;
            }
            if (url.includes('/api/v1/portfolio?portfolio_id=1')) {
                return {
                    ok: true,
                    json: async () => ({
                        status: 'active',
                        net_worth_egp: 1000000,
                        net_worth_usd: 0,
                        cash_egp: 100000,
                        cash_usd: 0,
                        positions: [
                            {
                                ticker: 'COMI',
                                shares: 100,
                                current_price: 99.5,
                                entry_price: 90,
                                pnl: 950,
                                pnl_pct: 10.56,
                                status: 'OPEN',
                            },
                        ],
                    }),
                } as Response;
            }
            if (url.includes('/api/v1/analytics/health')) {
                return { ok: true, json: async () => ({ status: 'success', score: 80 }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/analysis?portfolio_id=1')) {
                return {
                    ok: true,
                    json: async () => ({ status: 'success', recommendations: [], sector_breakdown: {}, heat: 1, health_score: 90 }),
                } as Response;
            }
            if (url.includes('/api/v1/portfolio/report?portfolio_id=1')) {
                return { ok: true, json: async () => ({ metrics: { total_pnl: 300, win_rate: 50, profit_factor: 1.2, total_trades: 3 }, curve: [], trades: [] }) } as Response;
            }
            if (url.includes('/api/v1/portfolio/close') && init?.method === 'POST') {
                closePayloads.push(JSON.parse(String(init.body || '{}')));
                return { ok: true, json: async () => ({ status: 'success', action: 'partial_sell' }) } as Response;
            }
            return { ok: true, json: async () => ({}) } as Response;
        }) as jest.Mock;

        render(<PortfolioPage />);

        fireEvent.click(await screen.findByRole('button', { name: /Mock Close COMI/i }));
        expect(await screen.findByRole('dialog', { name: /Close COMI/i })).toBeInTheDocument();

        fireEvent.change(screen.getByLabelText('Selling Price'), { target: { value: '101.25' } });
        fireEvent.click(screen.getByRole('button', { name: '50%' }));
        fireEvent.click(screen.getByRole('button', { name: /Sell Shares/i }));

        await waitFor(() => {
            expect(closePayloads.length).toBeGreaterThan(0);
        });
        expect(closePayloads[0]).toEqual(expect.objectContaining({
            ticker: 'COMI',
            shares: 50,
            price: 101.25,
            portfolio_id: 1,
        }));
    });
});
