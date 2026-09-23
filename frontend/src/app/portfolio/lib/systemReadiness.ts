import { apiFetch, readJsonSafe } from '@/lib/api';

type BootStatusPayload = {
    system_ready?: boolean;
    pipeline_state?: string | null;
};

function sleep(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function isReady(payload: BootStatusPayload | null) {
    if (!payload) return false;
    if (payload.system_ready === true) return true;
    return String(payload.pipeline_state || '').trim().toUpperCase() === 'FRESH';
}

export async function waitForSystemReady(options?: { timeoutMs?: number; intervalMs?: number }) {
    const timeoutMs = options?.timeoutMs ?? 20000;
    const intervalMs = options?.intervalMs ?? 1000;
    const startedAt = Date.now();

    while (Date.now() - startedAt < timeoutMs) {
        try {
            const res = await apiFetch('/api/v1/system/boot-status', { cache: 'no-store' });
            const body = await readJsonSafe<BootStatusPayload>(res);
            if (res.ok && isReady(body)) {
                return true;
            }
        } catch {
            // Ignore transient network/bootstrap errors while waiting.
        }
        await sleep(intervalMs);
    }

    return false;
}
