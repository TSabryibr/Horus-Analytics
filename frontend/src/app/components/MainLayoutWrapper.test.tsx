import React from 'react';
import { renderToString } from 'react-dom/server.node';

import MainLayoutWrapper from './MainLayoutWrapper';
import { useSidebarRuntime } from './hooks/useSidebarRuntime';

const mockSidebarRuntime = {
    isCollapsed: false,
    hydrated: true,
    pathname: '/status',
    t: (value: string) => value,
    language: 'en',
    isRtl: false,
    toggleLanguage: jest.fn(),
    portfolios: [{ id: 1, name: 'Main', type: 'USER' }],
    activePortfolioId: 1,
    toggleSidebar: jest.fn(),
    setActivePortfolioId: jest.fn(),
    startSimulation: jest.fn(),
    backendSourceLabel: 'Metastock',
    lastSyncDisplay: '00:00',
    systemStatus: {
        code: 'FRESH',
        label: 'All Systems Go',
        dotClass: 'bg-emerald-400',
        textClass: 'text-emerald-300',
    },
};

jest.mock('./hooks/useSidebarRuntime', () => ({
    useSidebarRuntime: jest.fn(),
}));

jest.mock('./Sidebar', () => ({
    __esModule: true,
    default: ({ runtime }: { runtime?: unknown }) => (
        <div data-testid="sidebar" data-runtime={runtime ? 'provided' : 'missing'}>
            Sidebar
        </div>
    ),
}));

jest.mock('./SimulationBanner', () => ({
    __esModule: true,
    default: () => <div data-testid="simulation-banner">Simulation Banner</div>,
}));

jest.mock('next/image', () => {
    function MockNextImage({ alt, priority: _priority, ...props }: { alt: string; priority?: boolean }) {
        return <img alt={alt} {...props} />;
    }
    return MockNextImage;
});

jest.mock('next/link', () => {
    function MockNextLink({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) {
        return (
            <a href={href} {...props}>{children}</a>
        );
    }
    return MockNextLink;
});

describe('MainLayoutWrapper', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        window.localStorage.clear();
        (useSidebarRuntime as jest.Mock).mockReturnValue(mockSidebarRuntime);
    });

    it('renders the real shell during the server render instead of a mount-gated placeholder', () => {
        const html = renderToString(
            <MainLayoutWrapper>
                <div>Child Content</div>
            </MainLayoutWrapper>
        );

        expect(html).toContain('Child Content');
        expect(html).toContain('Simulation Banner');
        expect(html).toContain('Horus');
        expect(html).toContain('Encrypted Data Link Active');
    });

    it('hydrates the shared navbar runtime once for the shell frame', () => {
        const html = renderToString(
            <MainLayoutWrapper>
                <div>Child Content</div>
            </MainLayoutWrapper>
        );

        expect(useSidebarRuntime).toHaveBeenCalledTimes(1);
        expect(html).toContain('Toggle language');
    });

    it('does not render the legacy sidebar in the live layout shell', () => {
        const html = renderToString(
            <MainLayoutWrapper>
                <div>Child Content</div>
            </MainLayoutWrapper>
        );

        expect(html).not.toContain('data-testid="sidebar"');
    });
});
