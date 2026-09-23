/**
 * Formats a Date object as HH:MM.
 */
export const formatClockHHMM = (date: Date): string => {
    return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
};

/**
 * Parses and formats a raw status timestamp string or Date object into HH:MM.
 * Handles space-separated and 'T' separated strings.
 */
export const formatStatusTimestamp = (value?: string | Date | null): string => {
    if (!value) return '--:--';
    if (value instanceof Date) {
        if (Number.isNaN(value.getTime())) return '--:--';
        return formatClockHHMM(value);
    }

    const raw = String(value).trim();
    if (!raw) return '--:--';

    // Fast-path for direct time matching
    const directTimeMatch = raw.match(/(?:T|\s)(\d{2}):(\d{2})/);
    if (directTimeMatch) {
        return `${directTimeMatch[1]}:${directTimeMatch[2]}`;
    }

    // Fallback Date object parsing
    const normalized = raw.includes('T')
        ? raw
        : raw.includes(' ')
            ? raw.replace(' ', 'T')
            : `${raw}T00:00:00`;
            
    const parsed = new Date(normalized);
    if (Number.isNaN(parsed.getTime())) {
        return '--:--';
    }
    return formatClockHHMM(parsed);
};
