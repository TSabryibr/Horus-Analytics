const DEFAULT_API_ORIGIN = 'http://localhost:8100';

function isLoopbackHost(hostname: string) {
    return ['localhost', '127.0.0.1', '::1', '[::1]'].includes(hostname);
}

export function resolveApiOrigin(configuredOrigin?: string, currentOrigin?: string) {
    const normalizedConfigured = configuredOrigin?.trim();
    const normalizedCurrent = currentOrigin?.trim();

    if (normalizedConfigured) {
        try {
            const configuredUrl = new URL(normalizedConfigured);
            if (normalizedCurrent) {
                try {
                    const currentUrl = new URL(normalizedCurrent);
                    const sameLoopbackAlias = isLoopbackHost(configuredUrl.hostname)
                        && isLoopbackHost(currentUrl.hostname)
                        && configuredUrl.protocol === currentUrl.protocol
                        && configuredUrl.port === currentUrl.port;

                    if (sameLoopbackAlias) {
                        return currentUrl.origin;
                    }
                } catch {
                    return configuredUrl.origin;
                }
            }
            return configuredUrl.origin;
        } catch {
            return normalizedConfigured;
        }
    }

    if (normalizedCurrent) {
        try {
            const currentUrl = new URL(normalizedCurrent);
            const isLoopback = isLoopbackHost(currentUrl.hostname);
            const isFrontendDevPort = ['3000', '3100'].includes(currentUrl.port);

            if (isLoopback && isFrontendDevPort) {
                return DEFAULT_API_ORIGIN;
            }

            return currentUrl.origin;
        } catch {
            return normalizedCurrent;
        }
    }

    return DEFAULT_API_ORIGIN;
}

export function getBaseUrl() {
    const currentOrigin = typeof window !== 'undefined' ? window.location.origin : undefined;
    return resolveApiOrigin(process.env.NEXT_PUBLIC_API_URL, currentOrigin);
}

export function getWsBase() {
    return getBaseUrl().replace(/^http/, 'ws');
}

export function apiUrl(endpoint: string) {
    if (endpoint.startsWith('http')) return endpoint;

    // Normalize endpoint: ensure it starts with / then strip /api/v1 or /api if present
    let path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    path = path.replace(/^\/api\/v1\//, '/').replace(/^\/api\/v1$/, '/').replace(/^\/api\//, '/').replace(/^\/api$/, '/');

    // Ensure final path starts with /
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${getApiBase()}${cleanPath}`;
}

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
    const url = apiUrl(endpoint);
    const apiKey = process.env.NEXT_PUBLIC_API_KEY || '';
    const isFormDataBody = typeof FormData !== 'undefined' && options.body instanceof FormData;
    const finalHeaders = new Headers(options.headers || {});
    finalHeaders.set('x-api-key', apiKey);

    if (!isFormDataBody && !finalHeaders.has('Content-Type')) {
        finalHeaders.set('Content-Type', 'application/json');
    }

    return fetch(url, {
        ...options,
        headers: finalHeaders
    });
}

export function getApiBase() {
    return `${getBaseUrl()}/api/v1`;
}

export function isIgnorableNetworkError(error: unknown) {
    if (!error) return false;
    if (typeof DOMException !== 'undefined' && error instanceof DOMException) {
        return error.name === 'AbortError';
    }
    if (error instanceof TypeError) {
        const message = error.message.toLowerCase();
        return message.includes('failed to fetch') || message.includes('networkerror');
    }
    if (error instanceof Error) {
        const message = error.message.toLowerCase();
        if (message.includes('404 not found')) {
            return true;
        }
        return error.name === 'AbortError';
    }
    return false;
}

export async function readJsonSafe<T>(response: Response): Promise<T> {
    try {
        if (typeof response.text !== 'function' && typeof response.json === 'function') {
            return await response.json() as T;
        }
        const text = await response.text();
        if (!text) return {} as T;
        return JSON.parse(text) as T;
    } catch {
        return {} as T;
    }
}

export function pickApiMessage(data: any, fallback: string = 'Unknown error') {
    if (!data) return fallback;
    if (typeof data === 'string') return data;
    if (data.detail) return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    if (data.message) return typeof data.message === 'string' ? data.message : JSON.stringify(data.message);
    if (data.error) return typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
    return fallback;
}

export const swrFetcher = async (url: string) => {
    const res = await apiFetch(url);
    const json = await readJsonSafe<any>(res);
    if (!res.ok) {
        throw new Error(pickApiMessage(json, `Failed to fetch: ${res.statusText}`));
    }
    return json;
};
