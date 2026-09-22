'use client';

import { useEffect } from 'react';
import './globals.css';

export default function GlobalError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error('Global Error Captured:', error);
    }, [error]);

    return (
        <html lang="en">
            <body className="font-sans bg-[#0F1115] text-white overflow-hidden flex items-center justify-center h-screen">
                <div className="text-center p-8">
                    <h1 className="text-4xl font-bold text-red-500 mb-4">SYSTEM FAILURE</h1>
                    <p className="text-slate-400 mb-8 max-w-md mx-auto">
                        The Horus Terminal encountered an unrecoverable error. The kernel must be restarted.
                    </p>
                    <button
                        onClick={() => reset()}
                        className="px-8 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold tracking-wide transition-colors"
                    >
                        REBOOT SYSTEM
                    </button>
                    <div className="mt-8 text-xs text-slate-400 font-mono">
                        ERR_CODE: {error.digest || 'UNKNOWN'}
                    </div>
                </div>
            </body>
        </html>
    );
}
