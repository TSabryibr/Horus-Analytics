'use client';

import { useEffect } from 'react';
import { ErrorState } from '@/components/ui/ErrorState';
import { useRouter } from 'next/navigation';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    const router = useRouter();

    useEffect(() => {
        console.error('Portfolio Error Captured:', error);
    }, [error]);

    return (
        <div className="p-8">
            <ErrorState
                title="Portfolio Inaccessible"
                message={error.message || "Failed to load portfolio telemetry. The secure link might be temporarily unstable."}
                retry={() => reset()}
                home={() => router.push('/')}
            />
        </div>
    );
}
