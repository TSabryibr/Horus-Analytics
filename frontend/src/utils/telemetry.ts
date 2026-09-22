export function formatTimeSince(date: Date | number | string | null | undefined): string {
    if (!date) return '--';
    const d = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
    if (isNaN(d.getTime())) return '--';
    const seconds = Math.floor((Date.now() - d.getTime()) / 1000);
    if (seconds < 0) return '0s ago';
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
}

export function isStale(date: Date | number | string | null | undefined, thresholdMs = 5 * 60 * 1000): boolean {
    if (!date) return true;
    const d = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
    if (isNaN(d.getTime())) return true;
    return Date.now() - d.getTime() > thresholdMs;
}

export function getStreamStatus(
    wsConnected?: boolean | null,
    loading?: boolean
): { label: string; value: string; tone: 'success' | 'danger' | 'warning' | 'muted' } {
    if (wsConnected === true) {
        return { label: 'Stream', value: '⚡ WS LIVE', tone: 'success' };
    }
    if (wsConnected === false) {
        return { label: 'Stream', value: '🔌 DISCONNECTED', tone: 'danger' };
    }
    if (loading) {
        return { label: 'Stream', value: '⏳ POLLING', tone: 'warning' };
    }
    return { label: 'Stream', value: '❓ UNKNOWN', tone: 'muted' };
}

export function getPollingStatus(
    loading: boolean,
    unavailable: boolean
): { label: string; value: string; tone: 'success' | 'danger' | 'warning' } {
    if (loading) {
        return { label: 'Transport', value: '⏳ POLLING', tone: 'warning' };
    }
    if (unavailable) {
        return { label: 'Transport', value: '🔌 API UNAVAILABLE', tone: 'danger' };
    }
    return { label: 'Transport', value: '🔄 HTTP POLL', tone: 'success' };
}
