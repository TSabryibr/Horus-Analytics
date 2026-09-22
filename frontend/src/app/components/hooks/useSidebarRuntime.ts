import { useState, useCallback, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { useLanguage } from '@/context/LanguageContext';
import { useDashboardData, useDataSyncStatus, usePortfolioData } from '../../context/GlobalDataContext';
import { usePolling } from '@/hooks/usePolling';
import { getBaseUrl } from '@/lib/api';
import { resolveRuntimeSurfaceState } from '../../lib/runtimeStatus';
import { PROVIDER_LABELS } from '../config/navigation';
import { formatStatusTimestamp } from '../lib/sidebarTransforms';

const SIDEBAR_STATUS_CACHE_TTL_MS = 15_000;

let sidebarStatusCache:
    | {
        data: any;
        fetchedAt: number;
    }
    | null = null;

export interface SidebarRuntimeState {
    isCollapsed: boolean;
    hydrated: boolean;
    pathname: string;
    t: (key: string) => string;
    language: string;
    isRtl: boolean;
    portfolios: any[];
    activePortfolioId: number;
    defaultPortfolioId: number;
    toggleSidebar: () => void;
    setActivePortfolioId: (portfolioId: number) => void;
    setDefaultSystemPortfolioId: (portfolioId: number) => Promise<boolean>;
    deletePortfolio: (portfolioId: number) => Promise<boolean>;
    toggleLanguage: () => void;
    startSimulation: () => Promise<void>;
    backendSourceLabel: string;
    feedModeLabel: string | null;
    lastSyncDisplay: string;
    systemStatus: {
        code: string;
        label: string;
        dotClass: string;
        textClass: string;
    };
}

export function __resetSidebarStatusCacheForTests() {
    sidebarStatusCache = null;
}

export function useSidebarRuntime() {
    const pathname = usePathname();
    const { t, language, setLanguage, isRtl } = useLanguage();
    
    // Global Contexts
    const { lastUpdated, loading } = useDataSyncStatus();
    const { activePortfolioId, defaultPortfolioId, setActivePortfolioId, setDefaultSystemPortfolioId, portfolios, deletePortfolio } = usePortfolioData();
    const { dashboard } = useDashboardData();

    // Local State
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [hydrated, setHydrated] = useState(false);
    const [dataStatus, setDataStatus] = useState<any>(null);

    // Initial Hydration
    useEffect(() => {
        setHydrated(true);
        if (typeof window === 'undefined') return;
        setIsCollapsed(localStorage.getItem('sidebar-collapsed') === 'true');
    }, []);

    // Polling Backend Status
    const fetchDataStatus = useCallback(async () => {
        try {
            const now = Date.now();
            if (sidebarStatusCache && now - sidebarStatusCache.fetchedAt < SIDEBAR_STATUS_CACHE_TTL_MS) {
                setDataStatus(sidebarStatusCache.data);
                return;
            }

            const apiBase = getBaseUrl();
            const res = await fetch(`${apiBase}/api/v1/data/status`, { cache: 'no-store' });
            if (!res.ok) return;
            const data = await res.json();
            sidebarStatusCache = {
                data,
                fetchedAt: now,
            };
            setDataStatus(data);
        } catch {
            // Ignore transient polling failures.
        }
    }, []);

    usePolling(fetchDataStatus, { intervalMs: 30_000, runImmediately: true, pauseWhenHidden: true });

    // Actions
    const toggleSidebar = () => {
        const newState = !isCollapsed;
        setIsCollapsed(newState);
        if (typeof window !== 'undefined') {
            localStorage.setItem('sidebar-collapsed', String(newState));
            window.dispatchEvent(new Event('sidebar-toggle'));
        }
    };

    const toggleLanguage = () => {
        setLanguage(language === 'en' ? 'ar' : 'en');
    };

    const startSimulation = async () => {
        const date = new Date().toISOString().split('T')[0];
        const apiBase = getBaseUrl();
        try {
            const res = await fetch(`${apiBase}/api/v1/simulate/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date })
            });
            if (res.ok && typeof window !== 'undefined') {
                window.sessionStorage.removeItem('horus.dashboard.cache.v1');
                window.location.reload();
            }
        } catch (e) {
            console.error("Failed to start simulation:", e);
        }
    };

    // Derived Status
    const isSyncing = Object.values(loading).some(Boolean);
    const backendKnown = Boolean(dataStatus);
    const activeIntradayProvider = String(dataStatus?.source?.intraday_provider || '').toUpperCase();
    const backendSourceLabel = PROVIDER_LABELS[activeIntradayProvider] || activeIntradayProvider || 'Detecting';
    const intradaySourceDecision = String(dataStatus?.source?.intraday_decision?.reason || '').toLowerCase();
    const intradayStatus = String(dataStatus?.intraday?.status || '').toUpperCase();
    const feedModeLabel =
        intradayStatus === 'LIVE' && intradaySourceDecision === 'upstream_intraday_stale'
            ? 'Realtime live, archive stale'
            : null;
    
    const backendLastSync = formatStatusTimestamp(
        dataStatus?.intraday?.last_bar || dataStatus?.history?.last_updated || dataStatus?.evaluated_at
    );
    const fallbackLastSync = formatStatusTimestamp((dashboard.lastSync || lastUpdated.dashboard) as Date | string | null);
    const lastSyncDisplay = backendLastSync !== '--:--' ? backendLastSync : fallbackLastSync;

    const systemStatus = resolveRuntimeSurfaceState({
        isSyncing,
        backendKnown,
        historyStatus: dataStatus?.history?.status,
        intradayStatus: dataStatus?.intraday?.status,
        historyOk: dataStatus?.history?.ok,
        intradayOk: dataStatus?.intraday?.ok,
    });

    return {
        // Core State
        isCollapsed,
        hydrated,
        pathname,
        
        // Translation
        t,
        language,
        isRtl,
        
        // Context Data
        portfolios,
        activePortfolioId,
        defaultPortfolioId,
        
        // Actions
        toggleSidebar,
        setActivePortfolioId,
        setDefaultSystemPortfolioId,
        deletePortfolio,
        toggleLanguage,
        startSimulation,
        
        // Derived Status View Data
        backendSourceLabel,
        feedModeLabel,
        lastSyncDisplay,
        systemStatus
    } satisfies SidebarRuntimeState;
}
