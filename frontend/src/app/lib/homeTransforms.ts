type ArchiveSignalWithDate = {
    date?: string;
};

export type HomeArchiveEntry = {
    ticker: string;
    signal_type: string;
    price: number;
    score: number;
    date?: string;
};

export function groupRecentSignalsByDate<T extends ArchiveSignalWithDate>(
    signals: T[] | undefined,
    now: Date = new Date(),
): Record<string, T[]> {
    if (!signals || !Array.isArray(signals)) {
        return {};
    }

    const cutoff = new Date(now);
    cutoff.setDate(cutoff.getDate() - 30);

    return signals.reduce<Record<string, T[]>>((grouped, signal) => {
        const dateKey = signal.date?.split('T')[0] || signal.date;
        if (!dateKey) {
            return grouped;
        }

        if (new Date(dateKey) < cutoff) {
            return grouped;
        }

        if (!grouped[dateKey]) {
            grouped[dateKey] = [];
        }

        grouped[dateKey].push(signal);
        return grouped;
    }, {});
}
