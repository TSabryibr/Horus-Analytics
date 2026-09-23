export const normalizeReportLine = (value: string) => value.trim().replace(/\s+/g, ' ').toLowerCase();

export const dedupeReportLines = (items: string[] = []) => {
    const seen = new Set<string>();
    return items
        .map((item) => String(item || '').trim())
        .filter((line) => {
            if (!line) return false;
            const key = normalizeReportLine(line);
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
};

export const truncatePrice = (val: number | undefined | null, decimals: number = 3): string => {
    const n = Number(val);
    if (!Number.isFinite(n)) return '0.000';
    const factor = Math.pow(10, decimals);
    const truncated = Math.trunc(n * factor) / factor;
    return truncated.toFixed(decimals);
};

export const getSignalColor = (signal: string) => {
    if (!signal) return 'text-gray-400';
    if (signal.includes('BEARISH')) return 'text-red-500';
    if (signal.includes('BULLISH')) return 'text-emerald-500';
    if (signal.includes('HEALTHY UPTREND')) return 'text-blue-400';
    if (signal.includes('HEALTHY DOWNTREND')) return 'text-orange-500';
    return 'text-gray-400';
};
