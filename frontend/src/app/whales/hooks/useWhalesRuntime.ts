import { useState } from 'react';

import { useWhalesData } from '../../context/GlobalDataContext';

import {
    aggregateWhaleSectors,
    filterWhaleCandidates,
    truncateWhalePrice,
} from '../lib/whaleTransforms';

export function useWhalesRuntime() {
    const { whales, whalesLoading, refreshWhales } = useWhalesData();
    const [filter, setFilter] = useState('');

    const filteredWhales = filterWhaleCandidates(whales?.candidates, filter);
    const sortedSectors = aggregateWhaleSectors(whales?.candidates);

    return {
        whales,
        isLoading: whalesLoading,
        refreshWhales,
        filter,
        setFilter,
        filteredWhales,
        sortedSectors,
        truncatePrice: truncateWhalePrice,
    };
}
