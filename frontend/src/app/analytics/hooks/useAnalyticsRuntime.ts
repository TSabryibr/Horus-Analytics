import { useEffect, useMemo, useState } from 'react';

import { apiFetch, isIgnorableNetworkError, readJsonSafe } from '@/lib/api';
import { AnalyticsItem } from '@/types';

import {
    AnalyticsColumnState,
    AnalyticsSortConfig,
    AnalyticsStatusResponse,
    defaultAnalyticsColumns,
    filterAnalyticsRows,
    formatAnalyticsDate,
    sortAnalyticsRows,
    toAnalyticsArray,
} from '../lib/analyticsTransforms';

export function useAnalyticsRuntime() {
    const [data, setData] = useState<AnalyticsItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [status, setStatus] = useState('IDLE');
    const [lastUpdated, setLastUpdated] = useState('-');
    const [search, setSearch] = useState('');
    const [filterStatus, setFilterStatus] = useState('ALL');
    const [minScore, setMinScore] = useState(0);
    const [sortConfig, setSortConfig] = useState<AnalyticsSortConfig | null>(null);
    const [columns, setColumns] = useState<AnalyticsColumnState>(defaultAnalyticsColumns);
    const [showColMenu, setShowColMenu] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await apiFetch('/api/v1/analytics', { cache: 'no-store' });
            const json = await readJsonSafe<unknown>(res);
            const rows = toAnalyticsArray(json);
            setData(rows);

            if (json && typeof json === 'object') {
                const obj = json as AnalyticsStatusResponse;
                setStatus(obj.status || 'IDLE');
                setLastUpdated(obj.last_updated || 'Never');
            } else {
                setStatus('IDLE');
                setLastUpdated('Never');
            }
        } catch (error) {
            if (!isIgnorableNetworkError(error)) {
                console.error('Analytics Fetch Error:', error);
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const filteredData = useMemo(
        () => filterAnalyticsRows(data, search, filterStatus, minScore),
        [data, search, filterStatus, minScore],
    );

    const sortedData = useMemo(
        () => sortAnalyticsRows(filteredData, sortConfig),
        [filteredData, sortConfig],
    );

    const requestSort = (key: string) => {
        let direction: 'asc' | 'desc' = 'asc';
        if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const toggleColumn = (key: string) => {
        setColumns((prev) => ({ ...prev, [key]: !prev[key as keyof AnalyticsColumnState] }));
    };

    return {
        columns,
        data,
        fetchData,
        filterStatus,
        filteredData,
        formattedLastUpdated: formatAnalyticsDate(lastUpdated),
        lastUpdated,
        loading,
        minScore,
        requestSort,
        search,
        setColumns,
        setFilterStatus,
        setLastUpdated,
        setLoading,
        setMinScore,
        setSearch,
        setShowColMenu,
        setStatus,
        showColMenu,
        sortConfig,
        sortedData,
        status,
        toggleColumn,
    };
}
