'use client';

import React, { createContext, useContext, ReactNode, useMemo } from 'react';
import useSWR from 'swr';
import { swrFetcher } from '@/lib/api';
import { NewsItem, BifrostSentiment } from '@/types';
import { extractSyncTimestamp } from './syncTimestamps';

type NewsContextValue = {
    news: NewsItem[];
    newsSentiment: BifrostSentiment | null;
    newsLoading: boolean;
    newsError: any;
    newsUpdatedAt: string | null;
    refreshNews: () => void;
};

const NewsDataContext = createContext<NewsContextValue | undefined>(undefined);

export function NewsProvider({ children, initialData, enabled = true }: { children: ReactNode, initialData?: any, enabled?: boolean }) {
    const { data, error, isLoading, isValidating, mutate } = useSWR(enabled ? '/api/v1/news' : null, swrFetcher, {
        refreshInterval: 300000, // 5 minutes
        revalidateOnFocus: false,
        fallbackData: enabled ? initialData : undefined
    });

    const value = useMemo(() => {
        let news: NewsItem[] = [];
        let newsSentiment: BifrostSentiment | null = null;

        if (Array.isArray(data)) {
            news = data;
        } else if (data?.status === 'success') {
            news = Array.isArray(data.data) ? data.data : [];
            newsSentiment = data.bifrost ?? null;
        }

        return {
            news,
            newsSentiment,
            newsLoading: enabled && (isLoading || isValidating),
            newsError: enabled ? error : null,
            newsUpdatedAt: extractSyncTimestamp(data),
            refreshNews: () => {
                if (!enabled) {
                    return;
                }
                void mutate();
            }
        };
    }, [data, enabled, error, isLoading, isValidating, mutate]);

    return (
        <NewsDataContext.Provider value={value}>
            {children}
        </NewsDataContext.Provider>
    );
}

export function useNewsData() {
    const context = useContext(NewsDataContext);
    if (context === undefined) {
        throw new Error('useNewsData must be used within a NewsProvider');
    }
    return context;
}
