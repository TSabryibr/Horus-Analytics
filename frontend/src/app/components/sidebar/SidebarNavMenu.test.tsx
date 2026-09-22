import { render, screen } from '@testing-library/react';

import { SidebarNavMenu } from './SidebarNavMenu';

describe('SidebarNavMenu', () => {
    it('renders anchor and grouped navigation labels when expanded', () => {
        render(
            <SidebarNavMenu
                isCollapsed={false}
                pathname="/oracle"
                t={(key) => key}
            />
        );

        expect(screen.getByText('Primary')).toBeInTheDocument();
        expect(screen.getByText('Intelligence')).toBeInTheDocument();
        expect(screen.getByText('Oversight')).toBeInTheDocument();
        expect(screen.getByText('System')).toBeInTheDocument();
        expect(screen.getByText('Command center')).toBeInTheDocument();
        expect(screen.getByText('Dispatch control')).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /nav\.dashboard/i })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /nav\.telegram/i })).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /nav\.oracle/i })).toHaveAttribute('href', '/oracle');
    });

    it('hides group labels when collapsed but keeps route links reachable', () => {
        render(
            <SidebarNavMenu
                isCollapsed
                pathname="/"
                t={(key) => key}
            />
        );

        expect(screen.queryByText('Primary')).not.toBeInTheDocument();
        expect(screen.queryByText('Intelligence')).not.toBeInTheDocument();
        expect(screen.getByRole('link', { name: /nav\.dashboard/i })).toHaveAttribute('title', 'nav.dashboard');
        expect(screen.getByRole('link', { name: /nav\.telegram/i })).toHaveAttribute('title', 'nav.telegram');
    });
});
