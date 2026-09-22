'use client';

import { useEffect } from 'react';
import { ErrorState } from '../components/ui/ErrorState';
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
        // Here you would typically log to a service (Sentry, etc)
        console.error('Run-time Error Captured:', error);
    }, [error]);

    return (
        <ErrorState
            title="Critical Layout Error"
            message={error.message || "The application encountered a critical failure in this viewport."}
            retry={() => reset()}
            home={() => router.push('/')}
        />
    );
}
