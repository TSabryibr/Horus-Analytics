'use client';

import { useNewsRuntime } from './hooks/useNewsRuntime';
import {
    getBifrostRegimeClass,
    getBifrostBarColor,
} from './lib/newsTransforms';
import { NewsShell } from './components/NewsShell';
import { NewsSentimentPanel } from './components/NewsSentimentPanel';
import { NewsCard } from './components/NewsCard';

export default function NewsClient() {
    const {
        news,
        newsLoading,
        onRefresh,
        bifrostScore,
        bifrostRegime,
        bifrostBull,
        bifrostBear,
    } = useNewsRuntime();

    const isLoading = newsLoading;

    return (
        <NewsShell
            loading={isLoading}
            onRefresh={onRefresh}
            bifrostRegime={bifrostRegime}
            articleCount={news.length}
        >
            {/* Bifrost Sentiment Panel */}
            <NewsSentimentPanel
                score={bifrostScore}
                regime={bifrostRegime}
                regimeClass={getBifrostRegimeClass(bifrostRegime)}
                barColorClass={getBifrostBarColor(bifrostScore)}
                bullHits={bifrostBull}
                bearHits={bifrostBear}
            />

            {/* News Grid */}
            {isLoading && news.length === 0 ? (
                <div className="flex-1 flex justify-center items-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
                </div>
            ) : news.length === 0 ? (
                <div className="section-surface-muted industrial-corner rounded-3xl border border-white/10 p-12 text-center my-6">
                    <p className="text-base font-bold text-slate-200">No Market Headlines Ingested</p>
                    <p className="text-xs text-slate-400 mt-2">Bifrost engine is monitoring signal wires. Click refresh to query new headlines.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {news.map((item, idx) => (
                        <NewsCard
                            key={idx}
                            source={item.source || item.Source || 'Unknown'}
                            title={item.title || item.Headline || 'No Headline'}
                            summary={item.summary || ''}
                            link={item.link || item.URL || '#'}
                            tickers={item.tickers || []}
                            gossipScore={item.gossip_score || 0}
                        />
                    ))}
                </div>
            )}
        </NewsShell>
    );
}
