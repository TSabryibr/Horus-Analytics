import { render, screen } from '@testing-library/react';

import RootLayout from './layout';

jest.mock('./globals.css', () => ({}));

jest.mock('./components/BootLayoutGate', () => {
    function MockBootLayoutGate({ children }: { children: React.ReactNode }) {
        return <div data-testid="boot-gate">{children}</div>;
    }

    return MockBootLayoutGate;
});

jest.mock('./context/GlobalDataContext', () => ({
    GlobalDataProvider: ({ children }: { children: React.ReactNode }) => (
        <div data-testid="global-provider">{children}</div>
    ),
}));

jest.mock('../context/LanguageContext', () => ({
    LanguageProvider: ({ children }: { children: React.ReactNode }) => (
        <div data-testid="language-provider">{children}</div>
    ),
}));

jest.mock('./components/MainLayoutWrapper', () => {
    function MockMainLayoutWrapper({ children }: { children: React.ReactNode }) {
        return <div data-testid="main-layout">{children}</div>;
    }

    return MockMainLayoutWrapper;
});

jest.mock('../components/PageTransition', () => {
    function MockPageTransition({ children }: { children: React.ReactNode }) {
        return <div data-testid="page-transition">{children}</div>;
    }

    return MockPageTransition;
});

describe('RootLayout startup gating order', () => {
    it('places the global data provider behind the startup boot gate', () => {
        const layout = RootLayout({
            children: <div>app-content</div>,
        });
        const body = (layout as React.ReactElement).props.children.props.children;

        render(
            body
        );

        const bootGate = screen.getByTestId('boot-gate');
        const globalProvider = screen.getByTestId('global-provider');

        expect(bootGate.contains(globalProvider)).toBe(true);
    });
});
