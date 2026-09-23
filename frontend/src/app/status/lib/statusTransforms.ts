export function resolveSourceEngine(provider?: string | null) {
    const providerLabels: Record<string, string> = {
        METASTOCK_DAT: 'MetaStock DAT',
        CSV: 'MetaStock CSV',
        MUBASHER_DB: 'Mubasher DB',
        DIRECTFN: 'DirectFN Feed',
    };

    const normalizedProvider = String(provider || '').toUpperCase();
    return providerLabels[normalizedProvider] || normalizedProvider || 'Unknown';
}

export function resolveDriftValue(ageMins?: number | null) {
    return typeof ageMins === 'number' ? `${ageMins} Minutes` : 'N/A';
}

export function resolveHistorySymbolCount(history?: {
    kpis?: { symbol_count?: number | null } | null;
    file_count?: number | null;
} | null) {
    return history?.kpis?.symbol_count ?? history?.file_count ?? 0;
}

export function resolveHistoryAgeHours(lastUpdated?: string | null, now?: Date | null) {
    if (!lastUpdated) {
        return 0;
    }

    const parsed = new Date(`${lastUpdated}T00:00:00`);
    if (Number.isNaN(parsed.getTime())) {
        return 0;
    }

    const effectiveNow = now ?? new Date();

    return Math.max(0, Math.round((effectiveNow.getTime() - parsed.getTime()) / (1000 * 60 * 60)));
}
