import { useMemo, useState } from 'react';

interface UseSettingsExclusionsArgs {
    excluded: string[];
    setExcluded: React.Dispatch<React.SetStateAction<string[]>>;
    allTickers: string[];
}

export function useSettingsExclusions({
    excluded,
    setExcluded,
    allTickers,
}: UseSettingsExclusionsArgs) {
    const [newExclusion, setNewExclusion] = useState('');

    const addExclusion = (tickerToAdd?: string) => {
        const normalized = String(tickerToAdd ?? newExclusion).trim().toUpperCase();
        if (!normalized || excluded.includes(normalized)) {
            return;
        }
        setExcluded([...excluded, normalized]);
        setNewExclusion('');
    };

    const removeExclusion = (ticker: string) => {
        setExcluded(excluded.filter((value) => value !== ticker));
    };

    const autocompleteOptions = useMemo(() => {
        if (newExclusion.length === 0 || allTickers.includes(newExclusion)) {
            return [];
        }
        return allTickers
            .filter((ticker) => ticker.includes(newExclusion) && !excluded.includes(ticker))
            .slice(0, 10);
    }, [allTickers, excluded, newExclusion]);

    return {
        newExclusion,
        setNewExclusion,
        addExclusion,
        removeExclusion,
        autocompleteOptions,
    };
}
