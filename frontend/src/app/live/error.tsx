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
        console.error('Live Mon Error Captured:', error);
    }, [error]);

    return (
        <div className="p-8">
            <ErrorState
                title="Live Feed Interrupted"
                message={error.message || "The real-time telemetry stream was disconnected. Re-syncing recommended."}
                retry={() => reset()}
                home={() => router.push('/')}
            />
        </div>
    );
}
