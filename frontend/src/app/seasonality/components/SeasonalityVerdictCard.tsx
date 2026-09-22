import { Calendar, Info, TrendingDown } from 'lucide-react';

interface VerdictStats {
    ticker: string;
    verdict: {
        best_month: string;
        worst_month: string;
        summary: string;
    };
}

interface SeasonalityVerdictCardProps {
    tickerStats: VerdictStats | null;
    loading: boolean;
}

export function SeasonalityVerdictCard({ tickerStats, loading }: SeasonalityVerdictCardProps) {
    return (
        <div className="section-surface industrial-corner rounded-xl p-6 flex flex-col justify-center items-center text-center relative overflow-hidden">
            {tickerStats ? (
                <>
                    <div className="absolute top-0 right-0 p-4 opacity-5">
                        <Calendar className="w-24 h-24 text-rose-500" />
                    </div>
                    <h2 className="text-4xl font-bold text-white mb-1">{tickerStats.ticker}</h2>
                    <p className="text-xs text-slate-500 mb-6 uppercase tracking-widest">Statistical Verdict</p>

                    <div className="w-full space-y-4">
                        <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-lg p-3">
                            <div className="text-[10px] text-emerald-500 font-bold uppercase mb-1">Optimal Exit Month</div>
                            <div className="text-xl font-bold text-emerald-400">{tickerStats.verdict.best_month}</div>
                        </div>
                        <div className="bg-rose-950/20 border border-rose-500/20 rounded-lg p-3">
                            <div className="text-[10px] text-rose-500 font-bold uppercase mb-1">Danger Zone Month</div>
                            <div className="text-xl font-bold text-rose-400">{tickerStats.verdict.worst_month}</div>
                        </div>
                    </div>

                    <div className="mt-8 flex items-start space-x-2 text-left">
                        <Info className="w-4 h-4 text-slate-600 mt-1 shrink-0" />
                        <p className="text-[11px] text-slate-400 italic">
                            {tickerStats.verdict.summary}. Patterns calculated from multiple years of historical candle data.
                        </p>
                    </div>
                </>
            ) : (
                <div className="text-slate-600">
                    <TrendingDown className="w-12 h-12 mb-4 mx-auto opacity-20" />
                    {loading ? "Consulting the Casket..." : "Search a ticker to reveal its ghost."}
                </div>
            )}
        </div>
    );
}
