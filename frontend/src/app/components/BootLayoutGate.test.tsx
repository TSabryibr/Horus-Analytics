import { fireEvent, render, screen } from '@testing-library/react';

import BootLayoutGate from './BootLayoutGate';
import { SYSTEM_BOOT_SESSION_KEY } from './systemBootModel';

const mockUsePathname = jest.fn();

jest.mock('next/navigation', () => ({
    usePathname: () => mockUsePathname(),
}));

jest.mock('./SystemBootOverlay', () => {
    function MockSystemBootOverlay({ onStartupResolved }: { onStartupResolved?: () => void }) {
        return (
            <button type="button" onClick={onStartupResolved}>
                resolve boot
            </button>
        );
    }

    return MockSystemBootOverlay;
});

describe('BootLayoutGate', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        window.sessionStorage.clear();
        mockUsePathname.mockReturnValue('/');
    });

    it('keeps the app shell deferred on first home launch until startup boot resolves', () => {
        render(
            <BootLayoutGate>
                <div>app-content</div>
            </BootLayoutGate>
        );

        expect(screen.getByRole('button', { name: /resolve boot/i })).toBeInTheDocument();
        expect(screen.queryByText('app-content')).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /resolve boot/i }));

        expect(screen.getByText('app-content')).toBeInTheDocument();
    });

    it('renders the app shell immediately when the startup session is already cleared', () => {
        window.sessionStorage.setItem(SYSTEM_BOOT_SESSION_KEY, 'true');

        render(
            <BootLayoutGate>
                <div>app-content</div>
            </BootLayoutGate>
        );

        expect(screen.getByText('app-content')).toBeInTheDocument();
    });

    it('renders the app shell immediately away from the home route', () => {
        mockUsePathname.mockReturnValue('/status');

        render(
            <BootLayoutGate>
                <div>app-content</div>
            </BootLayoutGate>
        );

        expect(screen.getByText('app-content')).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /resolve boot/i })).not.toBeInTheDocument();
    });
});
