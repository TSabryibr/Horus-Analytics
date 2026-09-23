export const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/**
 * Returns the current month label (e.g., 'Mar')
 */
export function getCurrentMonthLabel(): string {
    return MONTH_NAMES[new Date().getMonth()];
}

/**
 * Formats return percentage with sign prefix
 */
export function formatReturn(value: number): string {
    const prefix = value > 0 ? '+' : '';
    return `${prefix}${value}%`;
}
