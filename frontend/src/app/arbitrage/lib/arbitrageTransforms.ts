/**
 * Pure transformation functions for the Arbitrage page.
 * Extracted from ArbitragePage for isolated testing.
 */

/**
 * Returns Tailwind class string for Z-Score value coloring.
 * Significant Z-Scores (|z| > 2) are highlighted in cyan.
 */
export const getZScoreClass = (zScore: number): string => {
    return Math.abs(zScore) > 2 ? 'text-cyan-400' : 'text-gray-300';
};

/**
 * Returns Tailwind class string for Confidence value coloring.
 * High confidence (> 75%) is highlighted in emerald, otherwise yellow.
 */
export const getConfidenceClass = (confidence: number): string => {
    return confidence > 75 ? 'text-emerald-500' : 'text-yellow-500';
};

/**
 * Returns Tailwind class string for Echo Type badge.
 * "Positive" is emerald-tinted, "Negative" is rose-tinted.
 */
export const getEchoTypeClass = (type: string): string => {
    return type === 'Positive'
        ? 'text-emerald-500 bg-emerald-950/20'
        : 'text-rose-500 bg-rose-950/20';
};

/**
 * Returns Tailwind class string for trade execution feedback message.
 */
export const getActionStatusClass = (type: 'success' | 'error'): string => {
    return type === 'success'
        ? 'bg-emerald-900/40 border-emerald-500/50 text-emerald-200'
        : 'bg-red-900/40 border-red-500/50 text-red-200';
};

/**
 * Filters mirror pairs by a search term matching Leader or Follower tickers (case-insensitive).
 */
export const filterMirrors = (mirrors: any[], filter: string): any[] => {
    if (!mirrors) return [];
    if (!filter) return mirrors;
    const lower = filter.toLowerCase();
    return mirrors.filter(
        (m) =>
            m.Leader?.toLowerCase()?.includes(lower) ||
            m.Follower?.toLowerCase()?.includes(lower)
    );
};
