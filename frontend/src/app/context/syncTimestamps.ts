'use client';

const TIMESTAMP_KEYS = ['updated_at', 'generated_at', 'created_at', 'evaluated_at', 'last_sync'] as const;

export type SyncTimestampMap = Record<string, string | null>;

export function extractSyncTimestamp(value: unknown): string | null {
    if (!value) {
        return null;
    }
    if (typeof value === 'string') {
        return value.trim().length > 0 ? value : null;
    }
    if (Array.isArray(value)) {
        return null;
    }
    if (typeof value !== 'object') {
        return null;
    }

    const record = value as Record<string, unknown>;
    for (const key of TIMESTAMP_KEYS) {
        const candidate = record[key];
        if (typeof candidate === 'string' && candidate.trim().length > 0) {
            return candidate;
        }
    }

    if (record.data && typeof record.data === 'object') {
        return extractSyncTimestamp(record.data);
    }

    return null;
}
