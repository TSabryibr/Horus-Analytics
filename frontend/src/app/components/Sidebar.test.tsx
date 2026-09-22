import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import Sidebar from './Sidebar';
import { __resetSidebarStatusCacheForTests } from './hooks/useSidebarRuntime';

const mockUsePathname = jest.fn();
const mockUseDataSyncStatus = jest.fn();
const mockUsePortfolioData = jest.fn();
const mockUseDashboardData = jest.fn();

jest.mock('next/navigation', () => ({
    usePathname: () => mockUsePathname(),
}));

jest.mock('next/link', () => {
    function MockNextLink({ children, href, prefetch, ...rest }: { children: React.ReactNode; href: string; prefetch?: boolean }) {
        return <a href={href} data-prefetch={String(prefetch)} {...rest}>{children}</a>;
    }
    return MockNextLink;
});

jest.mock('next/image', () => {
    function MockNextImage({ alt, ...props }: { alt: string }) {
        return <img alt={alt} {...props} />;
    }
    return MockNextImage;
});

jest.mock('../context/GlobalDataContext', () => ({
    useDataSyncStatus: () => mockUseDataSyncStatus(),
    usePortfolioData: () => mockUsePortfolioData(),
    useDashboardData: () => mockUseDashboardData(),
}));

jest.mock('@/context/LanguageContext', () => ({
    useLanguage: () => ({
        t: (k: string) => k,
        language: 'en',
        setLanguage: jest.fn(),
        isRtl: false
    })
}));

const now = new Date();
const recent = new Date(now.getTime() - 30_000);
const stale = new Date(now.getTime() - 10 * 60_000);

function baseSyncState() {
    return {
        loading: {
            news: false,
            sectors: false,
            whales: false,
            arbitrage: false,
            traps: false,
            strategy: false,
            oracle: false,
            dashboard: false,
        },
        lastUpdated: {
            news: recent,
            sectors: recent,
            whales: recent,
            arbitrage: recent,
            traps: recent,
            strategy: recent,
            oracle: recent,
            dashboard: recent,
        },
    };
}

function setupSidebar({
    sync = baseSyncState(),
    dataSource = 'LIVE',
    backendStatus,
}: {
    sync?: ReturnType<typeof baseSyncState>;
    dataSource?: 'LIVE' | 'FALLBACK' | 'LOADING';
    backendStatus?: Record<string, unknown>;
} = {}) {
    (global.fetch as unknown as jest.Mock) = jest.fn(async () => ({
        ok: true,
        json: async () =>
            backendStatus ?? {
                history: { status: 'FRESH', ok: true, last_updated: recent.toISOString() },
                intraday: { status: 'LIVE', ok: true, last_bar: recent.toISOString() },
                source: { intraday_provider: 'METASTOCK_DAT' },
                evaluated_at: recent.toISOString(),
            },
    }));

    mockUsePathname.mockReturnValue('/status');
    mockUseDataSyncStatus.mockReturnValue(sync);
    mockUsePortfolioData.mockReturnValue({
        activePortfolioId: 1,
        setActivePortfolioId: jest.fn(),
        portfolios: [{ id: 1, name: 'My Portfolio', type: 'USER' }],
        refreshPortfolios: jest.fn(),
    });
    mockUseDashboardData.mockReturnValue({
        dashboard: {
            metrics: null,
            curve: [],
            signals: [],
            health: null,
            dataSource,
            loading: false,
            error: null,
            portfolioId: 1,
            lastSync: recent,
        },
    });
    render(<Sidebar />);
}

describe('Sidebar system status', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        __resetSidebarStatusCacheForTests();
    });

    it('shows syncing state when any domain is loading', async () => {
        const sync = baseSyncState();
        sync.loading.news = true;
        setupSidebar({ sync, dataSource: 'LIVE' });

        await waitFor(() => {
            expect(screen.getByText('Syncing Data...')).toBeInTheDocument();
            expect(screen.getByText('LINK_STATUS')).toBeInTheDocument();
        });
    });

    it('shows stale state when critical timestamps are old', async () => {
        const sync = baseSyncState();
        sync.lastUpdated.strategy = stale;
        sync.lastUpdated.whales = stale;
        sync.lastUpdated.oracle = stale;
        sync.lastUpdated.dashboard = stale;
        setupSidebar({
            sync,
            dataSource: 'FALLBACK',
            backendStatus: {
                history: { status: 'STALE', ok: false, last_updated: stale.toISOString() },
                intraday: { status: 'STALE', ok: false, last_bar: stale.toISOString() },
                source: { intraday_provider: 'DIRECTFN' },
                evaluated_at: stale.toISOString(),
            },
        });

        await waitFor(() => {
            expect(screen.getByText('Data Latency')).toBeInTheDocument();
            expect(screen.getByText('DirectFN Feed')).toBeInTheDocument();
        });
    });

    it('shows fresh state when data is recent and not loading', async () => {
        setupSidebar({
            sync: baseSyncState(),
            dataSource: 'LOADING',
            backendStatus: {
                history: { status: 'FRESH', ok: true, last_updated: recent.toISOString() },
                intraday: { status: 'LIVE', ok: true, last_bar: recent.toISOString() },
                source: { intraday_provider: 'MUBASHER_DB' },
                evaluated_at: recent.toISOString(),
            },
        });

        await waitFor(() => {
            expect(screen.getByText('All Systems Go')).toBeInTheDocument();
            expect(screen.getByText('Mubasher DB')).toBeInTheDocument();
        });
    });

    it('shows when realtime data is live while the Mubasher archive is stale', async () => {
        setupSidebar({
            backendStatus: {
                history: { status: 'FRESH', ok: true, last_updated: recent.toISOString() },
                intraday: { status: 'LIVE', ok: true, last_bar: recent.toISOString() },
                source: {
                    intraday_provider: 'MUBASHER_DB',
                    intraday_decision: {
                        reason: 'upstream_intraday_stale',
                    },
                },
                evaluated_at: recent.toISOString(),
            },
        });

        await waitFor(() => {
            expect(screen.getByText('Realtime live, archive stale')).toBeInTheDocument();
        });
    });

    it('disables route prefetching on sidebar navigation links', async () => {
        setupSidebar();

        await waitFor(() => {
            const links = screen.getAllByRole('link');
            expect(links.length).toBeGreaterThan(5);
            expect(links.every((link) => link.getAttribute('data-prefetch') === 'false')).toBe(true);
        });
    });
});
