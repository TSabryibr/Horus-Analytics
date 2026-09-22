'use client';

import type { ReactNode } from 'react';

import clsx from 'clsx';
import { RefreshCw, ShieldAlert, Zap } from 'lucide-react';

type AccentColor = 'red' | 'orange' | 'cyan';

type SimulationControlsProps = {
    children: ReactNode;
    onSimulate: () => void | Promise<void>;
    loading: boolean;
    accentColor: AccentColor;
};

export function SimulationControls({ children, onSimulate, loading, accentColor }: SimulationControlsProps) {
    const btnCls = {
        red: 'bg-red-500 hover:bg-red-400  ',
        orange: 'bg-orange-500 hover:bg-orange-400  ',
        cyan: 'bg-cyan-500 hover:bg-cyan-400  ',
    }[accentColor];

    return (
        <div className="group relative">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-red-500/20 to-orange-500/20 rounded-3xl blur opacity-20 transition duration-1000 group-hover:opacity-40" />
            <div className="relative bg-white/[0.02] border border-white/10 rounded-3xl p-8 flex flex-col md:flex-row items-end gap-8">
                {children}
                <button
                    onClick={onSimulate}
                    disabled={loading}
                    className={clsx(
                        'w-full md:w-auto px-10 py-5 text-white font-black tracking-widest rounded-2xl transition-all active:scale-95 disabled:opacity-30 disabled:pointer-events-none uppercase text-xs flex items-center justify-center gap-3',
                        btnCls
                    )}
                >
                    {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5 fill-current" />}
                    EXECUTE_ANALYSIS
                </button>
            </div>
        </div>
    );
}

type MetricBoxProps = {
    label: string;
    value: string;
    color: 'red' | 'orange' | 'cyan' | 'yellow' | 'slate';
    tooltip?: string;
};

export function MetricBox({ label, value, color, tooltip }: MetricBoxProps) {
    const colorMap = {
        red: 'text-red-400 border-red-500/20 bg-red-500/5',
        orange: 'text-orange-400 border-orange-500/20 bg-orange-500/5',
        cyan: 'text-cyan-400 border-cyan-500/20 bg-cyan-500/5',
        yellow: 'text-yellow-400 border-yellow-500/20 bg-yellow-500/5',
        slate: 'text-slate-300 border-white/10 bg-white/5',
    }[color];

    return (
        <div 
            title={tooltip}
            className={clsx('relative overflow-hidden rounded-2xl border p-6 transition-all hover:border-white/20', colorMap)}
        >
            <div className="absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 bg-current opacity-[0.03] rotate-45" />
            <span className="block text-[10px] font-black uppercase tracking-[0.2em] opacity-60 mb-2">{label}</span>
            <span className="text-2xl font-black font-mono tracking-tighter">{value}</span>
        </div>
    );
}

type GlassCardProps = {
    title: string;
    icon: ReactNode;
    children: ReactNode;
};

export function GlassCard({ title, icon, children }: GlassCardProps) {
    return (
        <div className="bg-white/[0.02] border border-white/5 rounded-3xl p-8 overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-50" />
            <div className="flex items-center gap-3 mb-8">
                <div className="p-2.5 bg-white/5 rounded-xl border border-white/10">{icon}</div>
                <h3 className="text-lg font-black tracking-tight text-slate-100 uppercase">{title}</h3>
            </div>
            {children}
        </div>
    );
}

export function ErrorDisplay({ error }: { error: string }) {
    return (
        <div className="mt-8 bg-red-900/10 border border-red-500/20 rounded-2xl p-5 flex items-center gap-4 text-red-400">
            <div className="p-2 bg-red-500/10 rounded-lg">
                <ShieldAlert className="w-5 h-5" />
            </div>
            <span className="text-sm font-bold tracking-tight">{error}</span>
        </div>
    );
}

type DistributionRowProps = {
    label: string;
    value: number;
    color: 'red' | 'orange' | 'rose';
};

export function DistributionRow({ label, value, color }: DistributionRowProps) {
    const barColor = {
        red: 'bg-red-500/50',
        orange: 'bg-orange-500/50',
        rose: 'bg-rose-500/50',
    }[color];

    return (
        <div>
            <div className="flex justify-between items-center mb-2">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{label}</span>
                <span className="text-xs font-mono font-bold text-slate-200">{value.toFixed(1)}%</span>
            </div>
            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div className={clsx('h-full transition-all duration-1000', barColor)} style={{ width: `${value}%` }} />
            </div>
        </div>
    );
}
