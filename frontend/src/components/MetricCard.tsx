import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import clsx from 'clsx';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    trend?: number;
}

export const MetricCard = ({ title, value, icon: Icon, trend }: MetricCardProps) => (
    <div 
        role="region"
        aria-label={`${title} metric`}
        tabIndex={0}
        className="relative group p-6 bg-[#0A0D14] border border-white/10 industrial-corner scan-line overflow-hidden transition-all duration-500 hover:-translate-y-1 hover:border-primary/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:border-primary" 
        data-testid="metric-card"
    >
        {/* Background Industrial Pattern */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
            style={{ backgroundImage: 'radial-gradient(circle, currentColor 1px, transparent 1px)', backgroundSize: '16px 16px' }} />

        <div className="relative flex items-center justify-between mb-6">
            <div className="flex flex-col">
                <h3 className="meta-label text-slate-500 group-hover:text-primary/80 transition-colors tracking-[0.25em]">{title}</h3>
                <div className="h-0.5 w-8 bg-primary/20 mt-1 transition-all group-hover:w-12 group-hover:bg-primary/50" />
            </div>
            <div className="p-2.5 bg-white/5 rounded-xl border border-white/5 group-hover:bg-primary/10 group-hover:border-primary/20 transition-all">
                <Icon className="h-4 w-4 text-slate-400 group-hover:text-primary group-hover:scale-110 transition-all" />
            </div>
        </div>

        <div className="relative text-4xl font-heading font-bold text-white tracking-tighter tabular-nums drop-">
            {value}
        </div>

        {trend !== undefined && (
            <div className={clsx("relative flex items-center mt-4 text-[9px] font-bold uppercase tracking-[0.2em]", trend >= 0 ? "text-emerald-400" : "text-rose-400")}>
                <div className={clsx("p-0.5 rounded-sm mr-2", trend >= 0 ? "bg-emerald-500/10" : "bg-rose-500/10")}>
                    {trend >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                </div>
                <span>{Math.abs(trend)}% Velocity</span>
                <span className="ml-auto text-slate-600 font-mono tracking-normal">REF:STABLE</span>
            </div>
        )}
    </div>
);
