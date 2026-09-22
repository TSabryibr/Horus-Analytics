"use client";

import React from "react";
import { motion } from "framer-motion";

interface SentimentHit {
  title: string;
  score?: number;
  gossip_score?: number;
  sentiment_score?: number;
  source?: string;
}

interface SentimentTimelineProps {
  score: number; // 0-100
  regime: string;
  hits: SentimentHit[];
  leadHits?: SentimentHit[];
  mode?: "single" | "scope";
  leadTicker?: string | null;
  ticker?: string | null;
}

export const SentimentTimeline: React.FC<SentimentTimelineProps> = ({
  score,
  regime,
  hits,
  leadHits = [],
  mode = "single",
  leadTicker = null,
  ticker = null,
}) => {
  const assetLabel = String(ticker || leadTicker || "asset").trim().toUpperCase();
  const normalizedRegime = (() => {
    const label = String(regime || '').trim().toUpperCase();
    return !label || label === 'BORING MORTALS' ? 'NEUTRAL' : label;
  })();

  const getRegimeColor = (s: number) => {
    if (s >= 70) return "text-cyan-400";
    if (s <= 30) return "text-rose-400";
    return "text-amber-400";
  };

  const getGaugeColor = (s: number) => {
    if (s >= 70) return "bg-cyan-500";
    if (s <= 30) return "bg-rose-500";
    return "bg-amber-500";
  };

  const renderHit = (hit: SentimentHit, i: number, keyPrefix: string) => {
    const hitScore = Number(hit.score ?? hit.gossip_score ?? hit.sentiment_score ?? 0);
    const hitSource = String(hit.source || 'MARKET WIDE').trim() || 'MARKET WIDE';
    return (
      <motion.div
        key={`${keyPrefix}-${hit.title}-${i}`}
        initial={{ x: -10, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: i * 0.05 }}
        className="group flex items-start gap-3 p-2 bg-slate-900/30 border-l-2 border-slate-700 hover:border-cyan-500 hover:bg-slate-800/50 transition-all cursor-default"
      >
        <div className={`mt-1 h-2 w-2 rounded-full shrink-0 ${hitScore >= 0 ? 'bg-cyan-500 shadow-[0_0_5px_cyan]' : 'bg-rose-500 shadow-[0_0_5px_rose]'}`} />
        <div className="flex-1 space-y-1">
          <div className="text-slate-300 leading-tight group-hover:text-white transition-colors">
            {hit.title}
          </div>
          <div className="flex justify-between text-[9px]">
            <span className="text-slate-500 uppercase">{hitSource}</span>
            <span className={hitScore >= 0 ? 'text-cyan-500' : 'text-rose-500'}>
              SCORE: {hitScore > 0 ? '+' : ''}{hitScore}
            </span>
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="w-full space-y-4 font-mono text-[11px]">
      {/* Header Info */}
      <div className="flex justify-between items-end border-b border-slate-800 pb-2">
        <div className="space-y-1">
          <div className="text-slate-500 uppercase tracking-tighter">Sentiment Regime</div>
          <div className={`text-lg font-bold uppercase ${getRegimeColor(score)}`}>
            {normalizedRegime}
          </div>
        </div>
        <div className="text-right">
          <div className="text-slate-500">
            {mode === "scope" ? "AGGREGATE INDEX" : `${assetLabel} NEWS INDEX`}
          </div>
          <div className="text-2xl font-black">{score.toFixed(1)}%</div>
        </div>
      </div>

      {/* Main Gauge */}
      <div className="relative h-6 bg-slate-900 border border-slate-800 rounded shadow-inner overflow-hidden">
        {/* Zebra Stripes BG */}
        <div className="absolute inset-0 opacity-10 bg-[repeating-linear-gradient(45deg,transparent,transparent_10px,#475569_10px,#475569_20px)]" />
        
        {/* Fill */}
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          className={`h-full relative z-10 ${getGaugeColor(score)} shadow-[0_0_15px_rgba(34,211,238,0.3)]`}
        >
          <div className="absolute inset-0 bg-white/20 animate-pulse" />
        </motion.div>

        {/* Center line */}
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-700 z-20" />
      </div>

      {/* Markers/Hits */}
      <div className="space-y-3 max-h-56 overflow-y-auto pr-2 custom-scrollbar">
        {mode === "scope" ? (
          <>
            <div className="space-y-2">
              <div className="text-[9px] uppercase tracking-[0.24em] text-slate-500">Scope Narrative</div>
              {hits.length === 0 ? (
                <div className="text-slate-600 italic">No significant basket narrative hits detected...</div>
              ) : (
                hits.map((hit, i) => renderHit(hit, i, "scope"))
              )}
            </div>
            {leadHits.length > 0 ? (
              <div className="space-y-2 border-t border-white/6 pt-3">
                <div className="text-[9px] uppercase tracking-[0.24em] text-amber-300">
                  Lead Ticker Focus {leadTicker ? `:: ${leadTicker}` : ""}
                </div>
                {leadHits.map((hit, i) => renderHit(hit, i, "lead"))}
              </div>
            ) : null}
          </>
        ) : hits.length === 0 ? (
          <div className="text-slate-600 italic">No {assetLabel}-specific narrative hits detected.</div>
        ) : (
          hits.map((hit, i) => renderHit(hit, i, "single"))
        )}
      </div>

      {/* Zone Indicators */}
      <div className="flex justify-between text-[9px] text-slate-600 uppercase pt-2">
        <span>[ PANIC ]</span>
        <span>[ SKEPTICISM ]</span>
        <span>[ HOPE ]</span>
        <span>[ EUPHORIA ]</span>
      </div>
    </div>
  );
};
