import { AnalyticsItem } from '@/types';

export interface AnalyticsStatusResponse {
    status?: string;
    scan_id?: string | null;
    rows?: number;
    last_updated?: string | null;
    error?: string | null;
}

export interface AnalyticsColumnState {
    Ticker: boolean;
    Price: boolean;
    Score: boolean;
    Status: boolean;
    Trend: boolean;
    RSI: boolean;
    Target_1: boolean;
    Target_2: boolean;
    Risk_Reward: boolean;
    Stop_Loss: boolean;
    Volume: boolean;
    ATR: boolean;
}

export interface AnalyticsSortConfig {
    key: string;
    direction: 'asc' | 'desc';
}

export const defaultAnalyticsColumns: AnalyticsColumnState = {
    Ticker: true,
    Price: true,
    Score: true,
    Status: true,
    Trend: true,
    RSI: true,
    Target_1: true,
    Target_2: true,
    Risk_Reward: true,
    Stop_Loss: true,
    Volume: false,
    ATR: false,
};

export function toAnalyticsArray(payload: unknown): AnalyticsItem[] {
    if (Array.isArray(payload)) {
        return payload as AnalyticsItem[];
    }
    if (payload && typeof payload === 'object' && Array.isArray((payload as { data?: unknown }).data)) {
        return (payload as { data: AnalyticsItem[] }).data;
    }
    if (payload && typeof payload === 'object' && Array.isArray((payload as { rows?: unknown }).rows)) {
        return (payload as { rows: AnalyticsItem[] }).rows;
    }
    if (payload && typeof payload === 'object' && Array.isArray((payload as { results?: unknown }).results)) {
        return (payload as { results: AnalyticsItem[] }).results;
    }
    return [];
}

export function formatAnalyticsDate(dateStr: string): string {
    if (!dateStr || dateStr === 'Never' || dateStr === '-') return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
        });
    } catch {
        return dateStr;
    }
}

export function filterAnalyticsRows(
    rows: AnalyticsItem[],
    search: string,
    filterStatus: string,
    minScore: number,
): AnalyticsItem[] {
    return rows.filter((item) => {
        if (!item) return false;

        const ticker = item.Ticker || '';
        const matchesSearch = ticker.toUpperCase().includes(search.toUpperCase());

        if (search.length > 0) {
            return matchesSearch;
        }

        const matchesStatus = filterStatus === 'ALL' || (item.Status && item.Status.includes(filterStatus));
        const matchesScore = (item.Signal_Score || 0) >= minScore;
        return matchesStatus && matchesScore;
    });
}

export function toSortableNumber(value: string | number | boolean | null | undefined): number {
    if (typeof value === 'number') {
        return Number.isFinite(value) ? value : 0;
    }
    if (typeof value === 'string') {
        const parsed = parseFloat(value);
        return Number.isFinite(parsed) ? parsed : 0;
    }
    if (typeof value === 'boolean') {
        return value ? 1 : 0;
    }
    return 0;
}

export function sortAnalyticsRows(
    rows: AnalyticsItem[],
    sortConfig: AnalyticsSortConfig | null,
): AnalyticsItem[] {
    return [...rows].sort((a, b) => {
        if (!sortConfig) return 0;

        let valA = a[sortConfig.key as keyof AnalyticsItem];
        let valB = b[sortConfig.key as keyof AnalyticsItem];

        if (
            sortConfig.key === 'Risk_Reward' ||
            sortConfig.key === 'Target_2' ||
            sortConfig.key === 'Signal_Score' ||
            sortConfig.key === 'Price' ||
            sortConfig.key === 'RSI'
        ) {
            valA = toSortableNumber(valA);
            valB = toSortableNumber(valB);
        }

        const comparableA = valA ?? '';
        const comparableB = valB ?? '';

        if (comparableA < comparableB) return sortConfig.direction === 'asc' ? -1 : 1;
        if (comparableA > comparableB) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });
}
