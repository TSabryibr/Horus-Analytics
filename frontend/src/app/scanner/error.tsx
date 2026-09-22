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
        console.error('Sub-route Error Captured:', error);
    }, [error]);

    return (
        <div className="p-8">
            <ErrorState
                title="Viewport Error"
                message={error.message || "An unexpected error occurred in this module."}
                retry={() => reset()}
                home={() => router.push('/')}
            />
        </div>
    );
}
