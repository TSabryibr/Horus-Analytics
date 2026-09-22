'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode, useMemo, useCallback } from 'react';
import { apiFetch, isIgnorableNetworkError, readJsonSafe } from '@/lib/api';

export type PortfolioSummary = { id: number; name: string; type: string };
export type DefaultPortfolioSummary = { portfolio_id: number | null; portfolio_name: string | null; portfolio_type: string | null };

export function getPreferredPortfolioId(portfolios: PortfolioSummary[], defaultSystemPortfolioId?: number | null): number {
    const persistedDefaultSystem = portfolios.find((p) => p.id === defaultSystemPortfolioId && p.type === 'SYSTEM');
    if (persistedDefaultSystem) {
        return persistedDefaultSystem.id;
    }

    const firstSystem = portfolios.find((p) => p.type === 'SYSTEM');
    if (firstSystem) {
        return firstSystem.id;
    }
    const firstStrategy = portfolios.find((p) => p.type === 'STRATEGY');
    if (firstStrategy) {
        return firstStrategy.id;
    }

    const userPreferred =
        portfolios.find((p) => p.type === 'USER' && p.name === 'Horus') ||
        portfolios.find((p) => p.type === 'USER' && p.name === 'My Portfolio') ||
        portfolios.find((p) => p.type === 'USER') ||
        portfolios[0];

    return userPreferred?.id ?? 0;
}

type PortfolioContextValue = {
    activePortfolioId: number;
    defaultPortfolioId: number;
    setActivePortfolioId: (id: number) => void;
    setDefaultSystemPortfolioId: (id: number) => Promise<boolean>;
    portfolios: PortfolioSummary[];
    refreshPortfolios: () => Promise<void>;
    deletePortfolio: (id: number) => Promise<boolean>;
};

const PortfolioDataContext = createContext<PortfolioContextValue | undefined>(undefined);

export function PortfolioProvider({ children }: { children: ReactNode }) {
    const [activePortfolioId, setActivePortfolioId] = useState<number>(0);
    const [defaultPortfolioId, setDefaultPortfolioId] = useState<number>(0);
    const [portfolios, setPortfolios] = useState<PortfolioSummary[]>([]);

    const refreshPortfolios = useCallback(async () => {
        try {
            const [portfoliosResponse, defaultResponse] = await Promise.all([
                apiFetch('/api/v1/portfolios'),
                apiFetch('/api/v1/portfolios/default'),
            ]);
            if (!portfoliosResponse.ok) return;

            const portfolioData = await readJsonSafe<any>(portfoliosResponse);
            if (!Array.isArray(portfolioData)) return;
            setPortfolios(portfolioData);

            let resolvedDefaultPortfolioId = 0;
            if (defaultResponse.ok) {
                const defaultData = await readJsonSafe<DefaultPortfolioSummary>(defaultResponse);
                resolvedDefaultPortfolioId = Number(defaultData?.portfolio_id || 0);
            }
            setDefaultPortfolioId(resolvedDefaultPortfolioId);

            const preferredPortfolioId = getPreferredPortfolioId(portfolioData, resolvedDefaultPortfolioId);

            setActivePortfolioId((currentPortfolioId) => (
                currentPortfolioId === 0 && preferredPortfolioId > 0
                    ? preferredPortfolioId
                    : currentPortfolioId
            ));
        } catch (e) {
            if (isIgnorableNetworkError(e)) {
                return;
            }
            console.error('Failed to fetch portfolios', e);
        }
    }, []);

    const setDefaultSystemPortfolioId = useCallback(async (portfolioId: number) => {
        try {
            const response = await apiFetch('/api/v1/portfolios/default', {
                method: 'POST',
                body: JSON.stringify({ portfolio_id: portfolioId }),
            });
            if (!response.ok) return false;

            const data = await readJsonSafe<DefaultPortfolioSummary>(response);
            setDefaultPortfolioId(Number(data?.portfolio_id || 0));
            return true;
        } catch (e) {
            if (isIgnorableNetworkError(e)) {
                return false;
            }
            console.error('Failed to set default portfolio', e);
            return false;
        }
    }, []);

    const deletePortfolio = useCallback(async (portfolioId: number) => {
        try {
            const response = await apiFetch(`/api/v1/portfolios/${portfolioId}`, {
                method: 'DELETE',
            });
            if (!response.ok) return false;
            await refreshPortfolios();
            return true;
        } catch (e) {
            if (isIgnorableNetworkError(e)) {
                return false;
            }
            console.error('Failed to delete portfolio', e);
            return false;
        }
    }, [refreshPortfolios]);

    useEffect(() => {
        refreshPortfolios();
    }, [refreshPortfolios]);

    const value = useMemo(() => ({
        activePortfolioId,
        defaultPortfolioId,
        setActivePortfolioId,
        setDefaultSystemPortfolioId,
        portfolios,
        refreshPortfolios,
        deletePortfolio
    }), [activePortfolioId, defaultPortfolioId, portfolios, refreshPortfolios, setDefaultSystemPortfolioId, deletePortfolio]);

    return (
        <PortfolioDataContext.Provider value={value}>
            {children}
        </PortfolioDataContext.Provider>
    );
}

export function usePortfolioData() {
    const context = useContext(PortfolioDataContext);
    if (context === undefined) {
        throw new Error('usePortfolioData must be used within a PortfolioProvider');
    }
    return context;
}
