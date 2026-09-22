'use client';

import Link from 'next/link';
import { SearchX, ArrowLeft } from 'lucide-react';

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[70vh] text-center p-4">
            <div className="p-6 bg-slate-800/50 rounded-full mb-6 border border-slate-700/50 text-slate-400">
                <SearchX size={64} />
            </div>

            <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">Route Not Found</h2>

            <p className="text-slate-400 max-w-md mb-8 leading-relaxed">
                The requested endpoint does not exist. Verify the URL or return to the command center.
            </p>

            <Link
                href="/"
                className="flex items-center gap-2 px-6 py-3 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 rounded-lg transition-all font-medium group"
            >
                <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
                Return to Dashboard
            </Link>
        </div>
    );
}
