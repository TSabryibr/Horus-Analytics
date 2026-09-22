import { useCallback, useEffect, useMemo, useState } from 'react';
import { getBaseUrl, isIgnorableNetworkError } from '@/lib/api';

import {
    buildSectorRrgUrl,
    countSectorQuadrants,
    SectorQuadrantCounts,
    SectorRrgResponse,
    SectorRrgRow,
    sectorsList,
    SectorViewMode,
    sortSectorRows,
} from '../lib/sectorTransforms';

export function useSectorRuntime() {
    const [viewMode, setViewMode] = useState<SectorViewMode>('sectors');
    const [data, setData] = useState<SectorRrgRow[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedSector, setSelectedSector] = useState('');

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const apiBase = getBaseUrl();
            const url = buildSectorRrgUrl(apiBase, viewMode, selectedSector);
            const res = await fetch(url);
            const json = await res.json() as SectorRrgResponse;
            if (json.status === 'success') {
                setData(Array.isArray(json.data) ? json.data : []);
            }
        } catch (error) {
            if (!isIgnorableNetworkError(error)) {
                console.error(error);
            }
        } finally {
            setLoading(false);
        }
    }, [selectedSector, viewMode]);

    useEffect(() => {
        void fetchData();
    }, [fetchData]);

    const sortedData = useMemo(() => sortSectorRows(data), [data]);
    const quadrantCounts: SectorQuadrantCounts = useMemo(() => countSectorQuadrants(data), [data]);

    return {
        data,
        fetchData,
        loading,
        quadrantCounts,
        sectorsList,
        selectedSector,
        setSelectedSector,
        setViewMode,
        sortedData,
        viewMode,
    };
}
