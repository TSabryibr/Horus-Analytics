'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, HelpCircle, BookOpen, Shield, Zap, Target, Waves } from 'lucide-react';

type TerminalManualProps = {
    isOpen: boolean;
    onClose: () => void;
};

export function TerminalManual({ isOpen, onClose }: TerminalManualProps) {
    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[200] flex items-center justify-center p-6 sm:p-12">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                    />
                    
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-2xl bg-[#0A0D14] border border-white/10 p-8 shadow-2xl overflow-hidden max-h-[80vh] overflow-y-auto custom-scrollbar"
                    >
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/50 via-primary to-primary/50" />
                        
                        <div className="flex items-center justify-between mb-8">
                            <div className="flex items-center gap-3">
                                <BookOpen className="text-primary h-5 w-5" />
                                <h2 className="text-xl font-heading font-black tracking-tighter text-white uppercase italic">
                                    Operational_Manual // V0.4
                                </h2>
                            </div>
                            <button 
                                onClick={onClose}
                                className="text-slate-500 hover:text-white transition-colors"
                            >
                                <X size={20} />
                            </button>
                        </div>

                        <div className="grid gap-10">
                            <ManualSection 
                                icon={Shield}
                                title="CORE_TELEMETRY"
                                items={[
                                    { label: "MTRX_SCORE", text: "Confluence indicator (0-5). Measures agreement between momentum and volume logic." },
                                    { label: "EQUITY_VARIANCE", text: "Measures the volatility of the winning percentage over time." }
                                ]}
                            />

                            <ManualSection 
                                icon={Zap}
                                title="SIGNAL_INDICATORS"
                                items={[
                                    { label: "ALPHA_MULTIPLIER", text: "The system's profit factor. A value > 1 indicates a net profitable strategy." },
                                    { label: "PRECISION_RATE", text: "Trailing accuracy of the current ML model's directional signals." }
                                ]}
                            />

                            <ManualSection 
                                icon={Target}
                                title="PREDATORY_ALGORITHMS"
                                items={[
                                    { label: "TRAP_DETECTION", text: "Identifies liquidity grabs where retail participants are likely to be liquidated." },
                                    { label: "WHALE_TRACKING", text: "Monitors institutional block trades and significant wallet movements." }
                                ]}
                            />
                        </div>

                        <div className="mt-12 pt-6 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                            <span>HORUS_ANALYTICS // SYSTEM_MANUAL</span>
                            <span className="opacity-50 italic">Property of Arch_Node</span>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}

function ManualSection({ icon: Icon, title, items }: { icon: any, title: string, items: { label: string, text: string }[] }) {
    return (
        <div className="space-y-4">
            <div className="flex items-center gap-3 pb-2 border-b border-white/5">
                <Icon className="text-slate-500 h-4 w-4" />
                <h3 className="text-xs font-black text-slate-400 tracking-[0.3em] uppercase">{title}</h3>
            </div>
            <div className="grid gap-4">
                {items.map((item, i) => (
                    <div key={i} className="group">
                        <span className="block text-[10px] font-black text-primary tracking-widest uppercase mb-1">{item.label}</span>
                        <p className="text-[12px] text-slate-400 leading-relaxed font-sans">{item.text}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
