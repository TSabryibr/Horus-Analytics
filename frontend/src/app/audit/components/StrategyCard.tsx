import { memo } from 'react';
import { Target, TrendingUp, TrendingDown } from 'lucide-react';
import { LineChart, Line } from 'recharts';
import clsx from 'clsx';
import { Strategy } from '@/types/domain';
import { MeasuredChartFrame } from '@/app/components/charts/MeasuredChartFrame';

interface StrategyCardProps {
    strat: Strategy;
    colors: string[];
    idx: number;
}

export const StrategyCard = memo(({ strat, colors, idx }: StrategyCardProps) => {
    return (
        <div className="bg-slate-900/30 border border-white/5 hover:border-blue-500/30 rounded-[2rem] p-8 relative group transition-all hover:translate-y-[-4px] overflow-hidden">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-xs font-black text-slate-500 uppercase tracking-widest">{strat.name}</h3>
                    <p className="text-[10px] text-slate-400 font-bold uppercase">{strat.count} Prophecies</p>
                </div>
                <div className={clsx(
                    "p-2 rounded-xl",
                    (strat.expected_value || 0) > 0 ? "bg-emerald-500/10" : "bg-rose-500/10"
                )}>
                    <Target size={16} className={(strat.expected_value || 0) > 0 ? "text-emerald-500" : "text-rose-500"} />
                </div>
            </div>

            <div className="space-y-4 mb-8">
                <div className="flex items-end justify-between">
                    <div className="text-4xl font-black text-white tracking-tighter">{strat.win_rate}%</div>
                    <div className="flex flex-col items-end">
                        <div className="text-[9px] font-black text-slate-400 uppercase">EV / Sig</div>
                        <div className={clsx("text-lg font-black", (strat.expected_value || 0) > 0 ? "text-emerald-400" : "text-rose-400")}>
                            {(strat.expected_value || 0) > 0 ? '+' : ''}{strat.expected_value || 0}%
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
                    <div>
                        <div className="text-[9px] font-black text-slate-400 uppercase mb-0.5 whitespace-nowrap">Max Drawdown</div>
                        <div className="text-xs font-bold text-rose-500">-{strat.max_drawdown}%</div>
                    </div>
                    <div>
                        <div className="text-[9px] font-black text-slate-400 uppercase mb-0.5 whitespace-nowrap">Conv. Rate</div>
                        <div className="text-xs font-bold text-blue-400">{strat.conversion_rate}%</div>
                    </div>
                </div>
            </div>

            {/* Mini Sparkline */}
            <MeasuredChartFrame className="h-16 w-full -mx-2" fallbackHeight={64}>
                {({ width, height }) => (
                    <LineChart
                        width={width}
                        height={height}
                        data={strat.equity_curve?.map((item, i) => ({ val: item.value, i }))}
                    >
                        <Line
                            type="monotone"
                            dataKey="val"
                            stroke={colors[idx % colors.length]}
                            strokeWidth={2}
                            dot={false}
                        />
                    </LineChart>
                )}
            </MeasuredChartFrame>
        </div>
    );
});

StrategyCard.displayName = 'StrategyCard';
