export type SimulationProfileSummary = {
    id: number;
    profile_name: string;
    source_type: string;
    profile_state?: string | null;
    market?: string | null;
    timeframe?: string | null;
};

type RawSimulationProfileSummary = Partial<SimulationProfileSummary> & {
    profile_id?: number | string | null;
};

export function normalizeSimulationProfiles(rawProfiles: unknown): SimulationProfileSummary[] {
    if (!Array.isArray(rawProfiles)) {
        return [];
    }

    return rawProfiles
        .map((rawProfile): SimulationProfileSummary | null => {
            if (!rawProfile || typeof rawProfile !== 'object') {
                return null;
            }

            const candidate = rawProfile as RawSimulationProfileSummary;
            const normalizedId = Number(candidate.id ?? candidate.profile_id);
            if (!Number.isFinite(normalizedId)) {
                return null;
            }

            return {
                id: normalizedId,
                profile_name: String(candidate.profile_name || ''),
                source_type: String(candidate.source_type || ''),
                profile_state: candidate.profile_state ?? null,
                market: candidate.market ?? null,
                timeframe: candidate.timeframe ?? null,
            };
        })
        .filter((profile): profile is SimulationProfileSummary => profile !== null);
}
