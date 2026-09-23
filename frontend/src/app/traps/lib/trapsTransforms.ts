/**
 * Pure transformation functions for the Traps page.
 */

/**
 * Formats the fakeout depth percentage with a sign and % symbol.
 * Bull traps are negative (price fell back), Bear traps are positive (price rebounded).
 */
export function formatFakeoutDepth(depth: number, type: 'bull' | 'bear'): string {
    const sign = type === 'bull' ? '-' : '+';
    return `${sign}${depth.toFixed(1)}% ${type === 'bull' ? 'Fakeout' : 'Rebound'}`;
}

/**
 * Returns the CSS classes for a trap card based on its type.
 */
export function getTrapCardClasses(type: 'bull' | 'bear'): string {
    if (type === 'bull') {
        return 'border-rose-900/50 hover:border-rose-500';
    }
    return 'border-emerald-900/50 hover:border-emerald-500';
}

/**
 * Returns the CSS classes for the trap ticker based on its type.
 */
export function getTickerClasses(type: 'bull' | 'bear'): string {
    if (type === 'bull') {
        return 'group-hover:text-rose-400';
    }
    return 'group-hover:text-emerald-400';
}

/**
 * Returns the CSS classes for the detail box based on its type.
 */
export function getDetailBoxClasses(type: 'bull' | 'bear'): string {
    if (type === 'bull') {
        return 'bg-rose-950/20 text-rose-300 border-rose-900/50';
    }
    return 'bg-emerald-950/20 text-emerald-300 border-emerald-900/50';
}
