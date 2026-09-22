import clsx from 'clsx';

interface NewsSentimentPanelProps {
    score: number;
    regime: string;
    regimeClass: string;
    barColorClass: string;
    bullHits: number;
    bearHits: number;
}

export function NewsSentimentPanel({
    score,
    regime,
    regimeClass,
    barColorClass,
    bullHits,
    bearHits,
}: NewsSentimentPanelProps) {
    return (
        <div className="section-surface industrial-corner rounded-xl p-5">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <p className="text-xs uppercase tracking-widest text-slate-500">News Sentiment Analyzer</p>
                    <h2 className="text-lg font-semibold text-slate-100 mt-1">Greed vs Fear</h2>
                </div>
                <div className={clsx("px-3 py-1 rounded-full text-xs font-bold border", regimeClass)}>
                    {regime}
                </div>
            </div>

            <div className="mt-4">
                <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-slate-400">Sentiment Score</span>
                    <span className="font-bold text-white">{score.toFixed(1)} / 100</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                        className={clsx(
                            "h-2 transition-all duration-700",
                            barColorClass
                        )}
                        style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
                    />
                </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3">
                    <p className="text-xs uppercase tracking-widest text-emerald-300">Greed Hits</p>
                    <p className="text-xl font-bold text-emerald-200 mt-1">{bullHits}</p>
                </div>
                <div className="rounded-lg border border-rose-500/20 bg-rose-500/10 p-3">
                    <p className="text-xs uppercase tracking-widest text-rose-300">Fear Hits</p>
                    <p className="text-xl font-bold text-rose-200 mt-1">{bearHits}</p>
                </div>
            </div>
        </div>
    );
}
