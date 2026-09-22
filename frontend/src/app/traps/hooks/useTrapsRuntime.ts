import { useTrapsData } from '../../context/GlobalDataContext';

export function useTrapsRuntime() {
    const { traps: rawTraps, trapsLoading, refreshTraps } = useTrapsData();
    
    // Normalize traps data to prevent null/undefined errors
    const traps = rawTraps || { bull_traps: [], bear_traps: [] };
    const bullTraps = traps.bull_traps || [];
    const bearTraps = traps.bear_traps || [];
    
    // Derived state
    const isLoading = trapsLoading;
    const hasAnyTraps = bullTraps.length > 0 || bearTraps.length > 0;

    return {
        bullTraps,
        bearTraps,
        isLoading,
        hasAnyTraps,
        onRefresh: refreshTraps,
    };
}
