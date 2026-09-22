import { ExternalLink, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import clsx from 'clsx';
import { getSentimentColor, formatSentimentScore } from '../lib/newsTransforms';

interface NewsCardProps {
    source: string;
    title: string;
    summary: string;
    link: string;
    tickers: string[];
    gossipScore: number;
}

export function NewsCard({
    source,
    title,
    summary,
    link,
    tickers,
    gossipScore,
}: NewsCardProps) {
    const getSentimentIcon = (score: number) => {
        if (score > 1) return <TrendingUp className="w-4 h-4 mr-2" />;
        if (score < -1) return <TrendingDown className="w-4 h-4 mr-2" />;
        return <Minus className="w-4 h-4 mr-2" />;
    };

    return (
        <div className="section-surface industrial-corner rounded-xl p-5 hover:border-emerald-500/35 transition-all group flex flex-col">
            {/* Header: Source & Sentiment */}
            <div className="flex justify-between items-start mb-4">
                <span className="text-xs font-mono text-slate-500 bg-slate-950/70 px-2 py-1 rounded">
                    {source}
                </span>
                <div className={clsx("flex items-center px-2 py-1 rounded-full text-xs font-bold border", getSentimentColor(gossipScore))}>
                    {getSentimentIcon(gossipScore)}
                    Score: {formatSentimentScore(gossipScore)}
                </div>
            </div>

            {/* Title */}
            <h3 className="text-lg font-semibold text-slate-100 mb-3 leading-snug group-hover:text-emerald-400 transition-colors">
                {title}
            </h3>

            {/* Summary */}
            <p className="text-sm text-slate-400 mb-4 flex-1 line-clamp-4">
                {summary}
            </p>

            {/* Footer: Tickers & Link */}
            <div className="mt-auto pt-4 border-t border-white/10 flex justify-between items-center">
                <div className="flex flex-wrap gap-2">
                    {tickers && tickers.length > 0 ? (
                        tickers.map((t) => (
                            <span key={t} className="text-xs bg-blue-900/30 text-blue-400 px-2 py-1 rounded">
                                {t}
                            </span>
                        ))
                    ) : (
                        <span className="text-xs text-slate-600">Market Wide</span>
                    )}
                </div>
                <a
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1 text-slate-400 hover:text-white transition"
                >
                    <ExternalLink className="w-4 h-4" />
                </a>
            </div>
        </div>
    );
}
