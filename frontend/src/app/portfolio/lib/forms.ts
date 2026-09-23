export function toNumber(value: unknown): number {
    if (typeof value === 'number') return value;
    if (!value) return 0;
    const normalized = typeof value === 'string' ? value.replace(/,/g, '') : value;
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : 0;
}

export function truncatePrice(value: unknown, decimals: number = 3): string {
    const parsed = toNumber(value);
    if (!Number.isFinite(parsed)) return '0.000';
    const factor = Math.pow(10, decimals);
    const truncated = Math.trunc(parsed * factor) / factor;
    return truncated.toFixed(decimals);
}

export function formatPrice(value: unknown): string {
    return truncatePrice(value, 3);
}
