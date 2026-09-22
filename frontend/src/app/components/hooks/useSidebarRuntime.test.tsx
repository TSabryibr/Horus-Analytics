import { renderHook, act } from '@testing-library/react';
import { __resetSidebarStatusCacheForTests, useSidebarRuntime } from './useSidebarRuntime';
import { usePathname } from 'next/navigation';
import { useLanguage } from '@/context/LanguageContext';
import { useDashboardData, useDataSyncStatus, usePortfolioData } from '../../context/GlobalDataContext';
import { usePolling } from '@/hooks/usePolling';

// ── Mocks ────────────────────────────────────────────────────────────────────
jest.mock('next/navigation', () => ({
    usePathname: jest.fn(),
}));

jest.mock('@/context/LanguageContext', () => ({
    useLanguage: jest.fn(),
}));

jest.mock('../../context/GlobalDataContext', () => ({
    useDashboardData: jest.fn(),
    useDataSyncStatus: jest.fn(),
    usePortfolioData: jest.fn(),
}));

jest.mock('@/hooks/usePolling', () => ({
    usePolling: jest.fn(),
}));

describe('useSidebarRuntime', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorage.clear();
        __resetSidebarStatusCacheForTests();
        (global.fetch as unknown as jest.Mock) = jest.fn();

        (usePathname as jest.Mock).mockReturnValue('/scanner');
        (useLanguage as jest.Mock).mockReturnValue({
            t: (key: string) => key,
            language: 'en',
            setLanguage: jest.fn(),
            isRtl: false,
        });

        (useDataSyncStatus as jest.Mock).mockReturnValue({
            lastUpdated: { dashboard: '2026-03-19T00:00:00Z' },
            loading: { dashboard: false },
        });

        (usePortfolioData as jest.Mock).mockReturnValue({
            portfolios: [{ id: 1, name: 'Main', type: 'USER' }],
            activePortfolioId: 1,
            defaultPortfolioId: 0,
            setActivePortfolioId: jest.fn(),
            setDefaultSystemPortfolioId: jest.fn(),
        });

        (useDashboardData as jest.Mock).mockReturnValue({
            dashboard: { lastSync: '2026-03-19T00:00:00Z' },
        });
    });

    it('initializes with false collapsed state and reads from localStorage', () => {
        localStorage.setItem('sidebar-collapsed', 'true');
        const { result } = renderHook(() => useSidebarRuntime());
        
        // Note: The hook uses useEffect for hydration and localStorage read, 
        // so it initializes false on server render (initial frame), then true after mount.
        // Let's test the toggle function instead for core logic.
        expect(result.current.isCollapsed).toBe(true); 
    });

    it('toggles sidebar state and updates localStorage', () => {
        const { result } = renderHook(() => useSidebarRuntime());

        act(() => {
            result.current.toggleSidebar();
        });

        expect(result.current.isCollapsed).toBe(true);
        expect(localStorage.getItem('sidebar-collapsed')).toBe('true');
    });

    it('toggles language between en and ar', () => {
        const mockSetLanguage = jest.fn();
        (useLanguage as jest.Mock).mockReturnValue({
            t: (k: string) => k,
            language: 'en',
            setLanguage: mockSetLanguage,
        });

        const { result } = renderHook(() => useSidebarRuntime());

        act(() => {
            result.current.toggleLanguage();
        });

        expect(mockSetLanguage).toHaveBeenCalledWith('ar');
    });

    it('passes down contexts successfully', () => {
        const { result } = renderHook(() => useSidebarRuntime());

        expect(result.current.pathname).toBe('/scanner');
        expect(result.current.activePortfolioId).toBe(1);
        expect(result.current.language).toBe('en');
        // Initial sync display fallback
        expect(result.current.lastSyncDisplay).toBe('00:00'); 
    });

    it('reuses a fresh sidebar status cache across remounts instead of refetching immediately', async () => {
        let firstTask: (() => void | Promise<void>) | undefined;
        let secondTask: (() => void | Promise<void>) | undefined;

        (usePolling as jest.Mock)
            .mockImplementationOnce((task: () => void | Promise<void>) => {
                firstTask = task;
            })
            .mockImplementationOnce((task: () => void | Promise<void>) => {
                secondTask = task;
            });

        (global.fetch as jest.Mock).mockResolvedValue({
            ok: true,
            json: async () => ({
                history: { status: 'FRESH', ok: true, last_updated: '2026-03-19T00:00:00Z' },
                intraday: { status: 'LIVE', ok: true, last_bar: '2026-03-19T00:00:00Z' },
                source: { intraday_provider: 'METASTOCK_DAT' },
                evaluated_at: '2026-03-19T00:00:00Z',
            }),
        });

        const firstRender = renderHook(() => useSidebarRuntime());
        await act(async () => {
            await firstTask?.();
        });
        firstRender.unmount();

        const secondRender = renderHook(() => useSidebarRuntime());
        await act(async () => {
            await secondTask?.();
        });

        expect(global.fetch).toHaveBeenCalledTimes(1);
    });
});
