export type SectorViewMode = 'sectors' | 'stocks';

export interface SectorTrailPoint {
    x: number;
    y: number;
}

export interface SectorRrgRow {
    ticker?: string;
    Sector: string;
    Status: 'LEADING' | 'WEAKENING' | 'IMPROVING' | 'LAGGING' | string;
    x: number;
    y: number;
    trail?: SectorTrailPoint[];
    Velocity?: number;
    TopDriver?: string;
}

export interface SectorRrgResponse {
    status?: string;
    data?: SectorRrgRow[];
}

export interface SectorQuadrantCounts {
    LEADING: number;
    IMPROVING: number;
    WEAKENING: number;
    LAGGING: number;
}

export const sectorsList = [
    'Banks',
    'Basic Resources',
    'Building Materials',
    'Contracting & Construction Engineering',
    'Educational Service',
    'Energy & Support Services',
    'Food, Beverages and Tobacco',
    'Healthcare and Pharmaceuticals',
    'IT , Media & Communication Services',
    'Industrial Goods and Services and Automobiles',
    'Non-bank financial services',
    'Paper & Packaging',
    'Real Estate',
    'Shipping & Transportation Services',
    'Textiles & Durables',
    'Trade & Distribution',
    'Travel & Leisure',
    'Utilities',
] as const;

export function sortSectorRows(rows: SectorRrgRow[]): SectorRrgRow[] {
    return [...rows].sort((a, b) => b.y - a.y);
}

export function countSectorQuadrants(rows: SectorRrgRow[]): SectorQuadrantCounts {
    return rows.reduce<SectorQuadrantCounts>(
        (counts, row) => {
            if (row.Status === 'LEADING') counts.LEADING += 1;
            else if (row.Status === 'IMPROVING') counts.IMPROVING += 1;
            else if (row.Status === 'WEAKENING') counts.WEAKENING += 1;
            else counts.LAGGING += 1;
            return counts;
        },
        { LEADING: 0, IMPROVING: 0, WEAKENING: 0, LAGGING: 0 },
    );
}

export function getSectorStatusColor(status: string): string {
    if (status === 'LEADING') return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
    if (status === 'WEAKENING') return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
    if (status === 'IMPROVING') return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
    return 'text-rose-400 bg-rose-400/10 border-rose-400/20';
}

export function buildSectorRrgUrl(
    apiBase: string,
    viewMode: SectorViewMode,
    selectedSector: string,
): string {
    let url = `${apiBase}/api/v1/rrg?view=${viewMode}&trail=10`;
    if (viewMode === 'stocks' && selectedSector) {
        url += `&sector=${encodeURIComponent(selectedSector)}`;
    }
    return url;
}
