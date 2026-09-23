/**
 * Pure transformation functions for the News component.
 * Logic extracted from NewsClient.tsx to allow for isolated testing.
 */

/**
 * Returns Tailwind class string for news item sentiment badges based on gossip score.
 */
export const getSentimentColor = (score: number): string => {
    if (score > 1) return 'text-green-500 border-green-500/30 bg-green-500/10';
    if (score < -1) return 'text-red-500 border-red-500/30 bg-red-500/10';
    return 'text-gray-400 border-gray-500/30 bg-gray-500/10';
};

/**
 * Returns Tailwind class string for Bifrost regime badges.
 */
export const getBifrostRegimeClass = (regime: string): string => {
    if (regime === "EUXUBERANT GREED") return "text-amber-300 border-amber-500/30 bg-amber-500/10";
    if (regime === "BLOOD PARALYSIS") return "text-rose-300 border-rose-500/30 bg-rose-500/10";
    return "text-slate-300 border-slate-500/30 bg-slate-500/10";
};

/**
 * Returns Tailwind class string for the Bifrost sentiment progress bar color.
 */
export const getBifrostBarColor = (score: number): string => {
    if (score >= 70) return "bg-amber-400";
    if (score <= 30) return "bg-rose-400";
    return "bg-slate-400";
};

/**
 * Formats a sentiment score with a sign prefix if positive.
 * e.g., 3 -> "+3", -2 -> "-2", 0 -> "0"
 */
export const formatSentimentScore = (score: number): string => {
    return (score > 0 ? '+' : '') + score;
};
