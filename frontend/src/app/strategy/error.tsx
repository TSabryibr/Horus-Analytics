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
        console.error('Strategy Error Captured:', error);
    }, [error]);

    return (
        <div className="p-8">
            <ErrorState
                title="Algorithm Fault"
                message={error.message || "The strategy execution engine encountered an internal validation error."}
                retry={() => reset()}
                home={() => router.push('/')}
            />
        </div>
    );
}
