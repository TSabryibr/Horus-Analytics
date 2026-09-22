'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';

type InfoTooltipProps = {
    children: React.ReactNode;
    content: string;
    className?: string;
};

export function InfoTooltip({ children, content, className }: InfoTooltipProps) {
    const [isVisible, setIsVisible] = useState(false);

    return (
        <div 
            className={clsx("relative inline-block", className)}
            onMouseEnter={() => setIsVisible(true)}
            onMouseLeave={() => setIsVisible(false)}
            onFocus={() => setIsVisible(true)}
            onBlur={() => setIsVisible(false)}
        >
            {children}
            <AnimatePresence>
                {isVisible && (
                    <motion.div
                        initial={{ opacity: 0, y: 5, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 5, scale: 0.95 }}
                        transition={{ duration: 0.15, ease: "easeOut" }}
                        className="absolute z-[100] bottom-full left-1/2 -translate-x-1/2 mb-3 w-48 p-3 bg-slate-950 border border-primary/40 text-white shadow-2xl pointer-events-none"
                    >
                        <div className="relative text-[10px] font-mono leading-relaxed tracking-wider uppercase">
                            <div className="absolute top-0 left-0 w-1.5 h-1.5 border-t border-l border-primary/60" />
                            <div className="absolute top-0 right-0 w-1.5 h-1.5 border-t border-r border-primary/60" />
                            <div className="absolute bottom-0 left-0 w-1.5 h-1.5 border-b border-l border-primary/60" />
                            <div className="absolute bottom-0 right-0 w-1.5 h-1.5 border-b border-r border-primary/60" />
                            {content}
                        </div>
                        <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px] border-t-primary/40" />
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
