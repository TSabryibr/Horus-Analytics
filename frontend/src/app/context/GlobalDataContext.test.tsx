import React from 'react';
import { render, screen } from '@testing-library/react';

import { GlobalDataProvider } from './GlobalDataContext';

const mockUsePathname = jest.fn();

jest.mock('next/navigation', () => ({
    usePathname: () => mockUsePathname(),
}));

jest.mock('./PortfolioContext', () => ({
    PortfolioProvider: ({ children }: { children: React.ReactNode }) => (
        <div data-testid="portfolio-provider">{children}</div>
    ),
    usePortfolioData: jest.fn(() => ({
        activePortfolioId: 1,
        setActivePortfolioId: jest.fn(),
        portfolios: [],
        refreshPortfolios: jest.fn(),
    })),
}));

jest.mock('./DashboardContext', () => ({
    DashboardProvider: ({ children, enabled }: { children: React.ReactNode; enabled?: boolean }) => (
        <div data-testid="dashboard-provider" data-enabled={String(enabled)}>
            {children}
        </div>
    ),
    useDashboardData: jest.fn(() => ({
        dashboard: {
            metrics: null,
            curve: [],
            signals: [],
            health: null,
            dataSource: 'LIVE',
            loading: false,
            error: null,
            portfolioId: 1,
            lastSync: null,
        },
        dashboardLoading: false,
        dashboardUpdatedAt: null,
        refreshDashboard: jest.fn(),
    })),
}));

jest.mock('./NewsContext', () => ({
    NewsProvider: ({ children, enabled }: { children: React.ReactNode; enabled?: boolean }) => (
        <div data-testid="news-provider" data-enabled={String(enabled)}>
            {children}
        </div>
    ),
    useNewsData: jest.fn(() => ({
        news: [],
        newsSentiment: null,
        newsLoading: false,
        newsError: null,
        newsUpdatedAt: null,
        refreshNews: jest.fn(),
    })),
}));

jest.mock('./MarketContext', () => ({
    MarketProvider: ({
        children,
        enabled,
        scope,
    }: {
        children: React.ReactNode;
        enabled?: boolean;
        scope?: Record<string, boolean>;
    }) => (
        <div
            data-testid="market-provider"
            data-enabled={String(enabled)}
            data-scope={JSON.stringify(scope || {})}
        >
            {children}
        </div>
    ),
    useMarketData: jest.fn(() => ({
        sectors: [],
        whales: null,
        arbitrage: null,
        traps: null,
        strategy: null,
        oracle: null,
        loading: {
            sectors: false,
            whales: false,
            arbitrage: false,
            traps: false,
            strategy: false,
            oracle: false,
        },
        lastUpdated: {},
        refreshMarket: jest.fn(),
        refreshOracleNoCache: jest.fn(),
        refreshOracleWithProvider: jest.fn(),
    })),
}));

jest.mock('./LiveContext', () => ({
    LiveProvider: ({ children, enabled }: { children: React.ReactNode; enabled?: boolean }) => (
        <div data-testid="live-provider" data-enabled={String(enabled)}>
            {children}
        </div>
    ),
}));

jest.mock('./SignalDeskCoreContext', () => ({
    SignalDeskCoreProvider: ({ children, enabled }: { children: React.ReactNode; enabled?: boolean }) => (
        <div data-testid="signal-desk-core-provider" data-enabled={String(enabled)}>
            {children}
        </div>
    ),
    useSignalDeskCore: jest.fn(() => ({
        desk: null,
        deskLoading: false,
        deskError: null,
        refreshDesk: jest.fn(),
        setOperatingMode: jest.fn(),
        promoteCandidate: jest.fn(),
        runAutopilot: jest.fn(),
    })),
}));

jest.mock('./SignalLifecycleContext', () => ({
    SignalLifecycleProvider: ({ children, enabled }: { children: React.ReactNode; enabled?: boolean }) => (
        <div data-testid="signal-lifecycle-provider" data-enabled={String(enabled)}>
            {children}
        </div>
    ),
    useSignalLifecycle: jest.fn(() => ({
        lifecycleSummary: null,
        lifecycleRecords: [],
        lifecycleLoading: false,
        lifecycleError: null,
        refreshLifecycle: jest.fn(),
        overrideLifecycle: jest.fn(),
    })),
}));

jest.mock('./SignalFollowUpContext', () => ({
    SignalFollowUpProvider: ({ children, enabled }: { children: React.ReactNode; enabled?: boolean }) => (
        <div data-testid="signal-followup-provider" data-enabled={String(enabled)}>
            {children}
        </div>
    ),
    useSignalFollowUp: jest.fn(() => ({
        followUpSummary: null,
        followUpRecords: [],
        followUpLoading: false,
        followUpError: null,
        refreshFollowUps: jest.fn(),
        processFollowUps: jest.fn(),
        actOnFollowUp: jest.fn(),
    })),
}));

describe('GlobalDataProvider', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('enables only dashboard streams on the home route', () => {
        mockUsePathname.mockReturnValue('/');

        render(
            <GlobalDataProvider>
                <div>home child</div>
            </GlobalDataProvider>
        );

        expect(screen.getByTestId('portfolio-provider')).toBeInTheDocument();
        expect(screen.getByTestId('signal-desk-core-provider')).toHaveAttribute('data-enabled', 'true');
        expect(screen.getByTestId('dashboard-provider')).toHaveAttribute('data-enabled', 'true');
        expect(screen.getByTestId('news-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('market-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('live-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByText('home child')).toBeInTheDocument();
    });

    it('enables only market streams on the oracle route', () => {
        mockUsePathname.mockReturnValue('/oracle');

        render(
            <GlobalDataProvider>
                <div>oracle child</div>
            </GlobalDataProvider>
        );

        expect(screen.getByTestId('portfolio-provider')).toBeInTheDocument();
        expect(screen.getByTestId('signal-desk-core-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('dashboard-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('news-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('market-provider')).toHaveAttribute('data-enabled', 'true');
        expect(screen.getByTestId('market-provider')).toHaveAttribute(
            'data-scope',
            JSON.stringify({
                sectors: false,
                whales: false,
                arbitrage: false,
                traps: false,
                strategy: false,
                oracle: true,
            })
        );
        expect(screen.getByTestId('live-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByText('oracle child')).toBeInTheDocument();
    });

    it('enables only arbitrage streams on the arbitrage route', () => {
        mockUsePathname.mockReturnValue('/arbitrage');

        render(
            <GlobalDataProvider>
                <div>arbitrage child</div>
            </GlobalDataProvider>
        );

        expect(screen.getByTestId('market-provider')).toHaveAttribute('data-enabled', 'true');
        expect(screen.getByTestId('signal-desk-core-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('market-provider')).toHaveAttribute(
            'data-scope',
            JSON.stringify({
                sectors: false,
                whales: false,
                arbitrage: true,
                traps: false,
                strategy: false,
                oracle: false,
            })
        );
        expect(screen.getByText('arbitrage child')).toBeInTheDocument();
    });

    it('enables only live streams on the live route', () => {
        mockUsePathname.mockReturnValue('/live');

        render(
            <GlobalDataProvider>
                <div>live child</div>
            </GlobalDataProvider>
        );

        expect(screen.getByTestId('dashboard-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('signal-desk-core-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('news-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('market-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('live-provider')).toHaveAttribute('data-enabled', 'true');
        expect(screen.getByText('live child')).toBeInTheDocument();
    });

    it('enables only news streams on the news route', () => {
        mockUsePathname.mockReturnValue('/news');

        render(
            <GlobalDataProvider>
                <div>news child</div>
            </GlobalDataProvider>
        );

        expect(screen.getByTestId('dashboard-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('signal-desk-core-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('news-provider')).toHaveAttribute('data-enabled', 'true');
        expect(screen.getByTestId('market-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('live-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByText('news child')).toBeInTheDocument();
    });

    it('disables heavy streams on utility routes like settings', () => {
        mockUsePathname.mockReturnValue('/settings');

        render(
            <GlobalDataProvider>
                <div>settings child</div>
            </GlobalDataProvider>
        );

        expect(screen.getByTestId('dashboard-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('signal-desk-core-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('news-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('market-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByTestId('live-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByText('settings child')).toBeInTheDocument();
    });

    it('enables the shared signal desk on the telegram route', () => {
        mockUsePathname.mockReturnValue('/telegram');

        render(
            <GlobalDataProvider>
                <div>telegram child</div>
            </GlobalDataProvider>
        );

        expect(screen.getByTestId('signal-desk-core-provider')).toHaveAttribute('data-enabled', 'true');
        expect(screen.getByTestId('dashboard-provider')).toHaveAttribute('data-enabled', 'false');
        expect(screen.getByText('telegram child')).toBeInTheDocument();
    });
});
