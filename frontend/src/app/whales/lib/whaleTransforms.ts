import { WhaleCandidate } from '../../../types';

export interface SectorSummary {
    name: string;
    count: number;
    accumulation: number;
    distribution: number;
}

export const truncateWhalePrice = (val: number | undefined, decimals: number = 3): string => {
    if (val === undefined || !Number.isFinite(val)) {
        return '0.000';
    }

    const factor = Math.pow(10, decimals);
    const truncated = Math.trunc(val * factor) / factor;
    return truncated.toFixed(decimals);
};

export const filterWhaleCandidates = (
    candidates: WhaleCandidate[] | undefined,
    filter: string,
) => {
    const normalizedFilter = filter.toLowerCase();

    return candidates?.filter(
        (candidate) =>
            candidate.Ticker?.toLowerCase()?.includes(normalizedFilter) ||
            candidate.Sector?.toLowerCase()?.includes(normalizedFilter),
    ) || [];
};

export const aggregateWhaleSectors = (candidates: WhaleCandidate[] | undefined): SectorSummary[] => {
    const sectorStats = candidates?.reduce((acc: Record<string, SectorSummary>, current: WhaleCandidate) => {
        const sector = current.Sector || 'Other';

        if (!acc[sector]) {
            acc[sector] = { name: sector, count: 0, accumulation: 0, distribution: 0 };
        }

        acc[sector].count++;

        if (current.Signal === 'ACCUMULATION') {
            acc[sector].accumulation++;
        } else {
            acc[sector].distribution++;
        }

        return acc;
    }, {} as Record<string, SectorSummary>);

    return Object.values(sectorStats || {}).sort((a, b) => b.count - a.count);
};
