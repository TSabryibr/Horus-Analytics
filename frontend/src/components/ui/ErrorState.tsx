import React from 'react';
import { AlertOctagon, RefreshCw, Home } from 'lucide-react';
import { motion } from 'framer-motion';

interface ErrorStateProps {
    title?: string;
    message?: string;
    retry?: () => void;
    home?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
    title = "System Malfunction",
    message = "An unexpected error occurred in this sector.",
    retry,
    home
}) => {
    return (
        <div className="flex flex-col items-center justify-center min-h-[50vh] p-8 text-center">
            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="p-6 rounded-2xl bg-red-500/10 border border-red-500/20 max-w-md w-full"
            >
                <div className="flex justify-center mb-4">
                    <div className="p-4 rounded-full bg-red-500/20 text-red-400">
                        <AlertOctagon size={48} />
                    </div>
                </div>

                <h2 className="text-xl font-bold text-red-200 mb-2 font-mono tracking-tight">
                    {title}
                </h2>

                <p className="text-slate-400 mb-8 leading-relaxed">
                    {message}
                </p>

                <div className="flex gap-4 justify-center">
                    {retry && (
                        <button
                            onClick={retry}
                            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-200 border border-red-500/30 transition-all font-medium text-sm"
                        >
                            <RefreshCw size={16} />
                            Reinitialize
                        </button>
                    )}

                    {home && (
                        <button
                            onClick={home}
                            className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all font-medium text-sm"
                        >
                            <Home size={16} />
                            Dashboard
                        </button>
                    )}
                </div>
            </motion.div>
        </div>
    );
};
