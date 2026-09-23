type BootstrapSnapshot<T> = {
    value: T;
    timestamp: number;
};

type BootstrapEntry<T> = {
    promise: Promise<T> | null;
    snapshot: BootstrapSnapshot<T> | null;
};

const DEFAULT_BOOTSTRAP_TTL_MS = 2_000;

type BootstrapRunner<T> = ((key: string, loader: () => Promise<T>) => Promise<T>) & {
    reset: () => void;
};

export function createBootstrapRequest<T>(ttlMs = DEFAULT_BOOTSTRAP_TTL_MS): BootstrapRunner<T> {
    const cache = new Map<string, BootstrapEntry<T>>();

    const runBootstrapRequest = (async (key: string, loader: () => Promise<T>): Promise<T> => {
        const now = Date.now();
        const existing = cache.get(key);

        if (existing?.promise) {
            return existing.promise;
        }

        if (existing?.snapshot && now - existing.snapshot.timestamp < ttlMs) {
            return existing.snapshot.value;
        }

        const promise = loader()
            .then((value) => {
                cache.set(key, {
                    promise: null,
                    snapshot: {
                        value,
                        timestamp: Date.now(),
                    },
                });
                return value;
            })
            .catch((error) => {
                cache.delete(key);
                throw error;
            });

        cache.set(key, {
            promise,
            snapshot: existing?.snapshot ?? null,
        });

        return promise;
    }) as BootstrapRunner<T>;

    runBootstrapRequest.reset = () => {
        cache.clear();
    };

    return runBootstrapRequest;
}
