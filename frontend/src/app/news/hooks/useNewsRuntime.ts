/**
 * Custom hook to manage the News feed runtime state and pre-compute Bifrost sentiment values.
 * Logic extracted from NewsClient.tsx to allow for better testability.
 */

import { useNewsData } from '../../context/GlobalDataContext';

export function useNewsRuntime() {
    // Preserve the mock path for existing tests by calling useNewsData internally
    const { news, newsSentiment, newsLoading, refreshNews } = useNewsData();

    // Normalizing raw sentiment scores into typed, default-safe values
    const bifrostScore = Number(newsSentiment?.score ?? 50);
    const bifrostRegime = newsSentiment?.regime ?? "BORING MORTALS";
    const bifrostBull = Number(newsSentiment?.bull_count ?? 0);
    const bifrostBear = Number(newsSentiment?.bear_count ?? 0);

    return {
        news,
        newsLoading,
        onRefresh: refreshNews,
        bifrostScore,
        bifrostRegime,
        bifrostBull,
        bifrostBear,
    };
}
