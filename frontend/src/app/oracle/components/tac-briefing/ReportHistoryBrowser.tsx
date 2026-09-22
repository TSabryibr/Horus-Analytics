"use client";

import React from "react";
import { motion } from "framer-motion";
import { ChevronRight, Clock, Zap } from "lucide-react";

interface ReportHistoryItem {
  id: number;
  ticker: string;
  generated_at: string;
  confidence_score: number;
  source_module: string;
}

interface ReportHistoryBrowserProps {
  history: ReportHistoryItem[];
  selectedId: number | null;
  onSelect: (id: number | null) => void;
  isLoading: boolean;
}

export const ReportHistoryBrowser: React.FC<ReportHistoryBrowserProps> = ({
  history,
  selectedId,
  onSelect,
  isLoading,
}) => {
  const archivalNodeCount = history.length;

  return (
    <div className="section-surface industrial-corner flex h-full flex-col overflow-hidden rounded-[1.35rem] font-mono text-[11px]">
      <div className="flex items-center justify-between border-b border-white/6 bg-white/[0.03] p-3">
        <div className="flex items-center gap-2 text-slate-400">
          <Clock size={14} className="text-cyan-500" />
          <span className="text-[10px] font-black uppercase tracking-[0.24em]">Tactical Archives</span>
        </div>
        {isLoading ? <Zap size={12} className="animate-pulse text-cyan-500" /> : null}
      </div>

      <div className="custom-scrollbar flex-1 overflow-y-auto">
        <button
          onClick={() => onSelect(null)}
          className={`w-full flex items-center justify-between border-b border-white/6 p-4 transition-colors ${
            selectedId === null
              ? "bg-cyan-500/10 text-cyan-300 shadow-[inset_2px_0_0_#22d3ee]"
              : "text-slate-500 hover:bg-white/[0.04]"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`rounded-[0.85rem] border border-white/8 bg-black/20 p-1.5 ${
                selectedId === null ? "text-cyan-400" : "text-slate-600"
              }`}
            >
              <Zap size={14} />
            </div>
            <div className="text-left">
              <div className="font-bold uppercase tracking-tight">Live Synthesis</div>
              <div className="text-[9px] opacity-60">Real-time tactical snapshot</div>
            </div>
          </div>
          {selectedId === null ? <ChevronRight size={14} /> : null}
        </button>

        {history.length === 0 && !isLoading ? (
          <div className="p-8 text-center italic text-slate-700">No archived intelligence...</div>
        ) : (
          history.map((item, index) => {
            const date = new Date(item.generated_at);
            const isSelected = selectedId === item.id;

            return (
              <motion.button
                key={item.id}
                initial={{ opacity: 0, x: -5 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => onSelect(item.id)}
                className={`w-full flex items-center justify-between border-b border-white/6 p-4 transition-colors ${
                  isSelected
                    ? "bg-white/[0.06] text-white shadow-[inset_2px_0_0_#475569]"
                    : "text-slate-400 hover:bg-white/[0.04]"
                }`}
              >
                <div className="space-y-1 text-left">
                  <div className="flex items-center gap-2">
                    <span className="font-bold">{date.toLocaleDateString()}</span>
                    <span className="rounded border border-white/8 bg-black/20 px-1.5 py-0.5 text-[9px] uppercase text-slate-500">
                      {item.source_module}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} | CONF:{" "}
                    {item.confidence_score.toFixed(0)}%
                  </div>
                </div>
                {isSelected ? <ChevronRight size={14} className="text-slate-500" /> : null}
              </motion.button>
            );
          })
        )}
      </div>

      <div className="flex justify-between border-t border-white/6 bg-black/20 px-3 py-2 text-[9px] uppercase text-slate-600">
        <span>Nodes: {archivalNodeCount} Archival</span>
        <span>Secure Stream</span>
      </div>
    </div>
  );
};
