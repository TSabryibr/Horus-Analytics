"use client";

import React from "react";
import { AlertTriangle, History, RefreshCw, ShieldCheck, Zap } from "lucide-react";
import { IndustrialButton } from "@/app/components/custom/IndustrialButton";
import { IndustrialCard } from "@/app/components/custom/IndustrialCard";

interface OracleAiReportPanelProps {
  title: string;
  report: any;
  isLoading: boolean;
  onRefresh: () => void;
  isHistorical: boolean;
  onPromote: (lane: "INTRADAY" | "SWING" | "POSITION") => void | Promise<unknown>;
}

export const OracleAiReportPanel: React.FC<OracleAiReportPanelProps> = ({
  title,
  report,
  isLoading,
  onRefresh,
  isHistorical,
  onPromote,
}) => {
  const verdict = report?.verdict || "NEUTRAL";
  const confidence = report?.confidence || 0;
  const recommendation = report?.snapshot?.recommendation;
  const hasUsablePrice = (value: unknown) => Number.isFinite(Number(value)) && Number(value) > 0;
  const canPromote =
    hasUsablePrice(recommendation?.entry) &&
    hasUsablePrice(recommendation?.stop) &&
    hasUsablePrice(recommendation?.target);

  const getVerdictColor = (value: string) => {
    if (value === "BULLISH") {
      return "border-cyan-500/50 bg-cyan-500/10 text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.2)]";
    }
    if (value === "BEARISH") {
      return "border-rose-500/50 bg-rose-500/10 text-rose-400 shadow-[0_0_15px_rgba(244,63,94,0.2)]";
    }
    return "border-amber-500/50 bg-amber-500/10 text-amber-400 shadow-[0_0_15px_rgba(251,191,36,0.2)]";
  };

  // Safe accessors with fallbacks
  const analysisShortTerm = report?.analysis?.short_term || "Awaiting data…";
  const analysisTacticalEdge = report?.analysis?.tactical_edge || "Awaiting data…";
  const analysisRiskProfile = report?.analysis?.risk_profile || "Awaiting data…";

  const technicalContext = report?.snapshot?.technical_context;
  const isBullTrap = technicalContext?.is_bull_trap ?? false;
  const isBearTrap = technicalContext?.is_bear_trap ?? false;
  const trapLabel = isBullTrap ? "Bull Trap Risk" : isBearTrap ? "Bear Trap Flag" : "Trap Clear";
  const trapDotClass = isBullTrap || isBearTrap
    ? "bg-rose-500 shadow-[0_0_5px_rgba(244,63,94,1)]"
    : "bg-emerald-400 shadow-[0_0_5px_rgba(52,211,153,0.75)]";

  const whaleFlow = report?.snapshot?.whale_flow;
  const hasWhaleFlow = Array.isArray(whaleFlow) && whaleFlow.length > 0;

  const arbitrage = report?.snapshot?.arbitrage;
  const arbitrageCorrelation = arbitrage?.correlation;

  const generatedAt = report?.generated_at
    ? new Date(report.generated_at).toLocaleTimeString()
    : "N/A";

  return (
    <IndustrialCard
      tone="primary"
      title={`// Intelligence Stream::${title.replace(/\s+/g, "_").toUpperCase()}`}
      subtitle={isLoading ? "Synchronizing tactical snapshot" : "Primary intelligence briefing lane"}
      className="overflow-hidden rounded-[1.6rem] font-mono selection:bg-cyan-500/30"
      contentClassName="p-0"
      headerSlot={
        <div className="flex items-center gap-2">
          {isHistorical ? (
            <div className="command-chip command-chip-warning rounded-[999px]">
              <History size={10} />
              <span>Archived Briefing</span>
            </div>
          ) : null}
          <IndustrialButton
            type="button"
            variant="secondary"
            size="sm"
            onClick={onRefresh}
            disabled={isLoading}
          >
            <RefreshCw size={12} className={isLoading ? "animate-spin" : ""} />
            {isLoading ? "Synchronizing" : "Refresh Intel"}
          </IndustrialButton>
        </div>
      }
    >
      <div className="space-y-8 p-5 sm:p-6">
        {!report && isLoading ? (
          <div className="flex h-64 flex-col items-center justify-center space-y-4 opacity-50">
            <Zap size={24} className="animate-pulse text-cyan-500" />
            <div className="text-[10px] uppercase tracking-widest text-slate-500">
              Retrieving Tactical Snapshot...
            </div>
          </div>
        ) : !report ? (
          <div className="flex h-64 flex-col items-center justify-center space-y-4 opacity-50">
            <AlertTriangle size={24} className="text-rose-500" />
            <div className="text-[10px] uppercase tracking-widest text-slate-500">
              Zero data found for ticker. Select a valid asset.
            </div>
          </div>
        ) : (
          <>
            <div className="section-surface-muted industrial-corner rounded-[1.25rem] p-4 sm:p-5">
              <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
                <div className="space-y-1">
                  <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                    Asset Consensus
                  </div>
                  <div className={`rounded-lg border-2 px-6 py-2 text-2xl font-black transition-all ${getVerdictColor(verdict)}`}>
                    {verdict}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-xs">
                  <div>
                    <div className="text-[9px] font-bold uppercase text-slate-600">Confidence</div>
                    <div className="text-xl font-black text-slate-200">{confidence.toFixed(0)}%</div>
                  </div>
                  <div>
                    <div className="text-[9px] font-bold uppercase text-slate-600">Generated At</div>
                    <div className="text-sm font-bold text-slate-400">
                      {generatedAt}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div className="section-surface-muted industrial-corner rounded-[1.2rem] p-4 space-y-3">
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase text-cyan-400">
                  <ShieldCheck size={14} />
                  Short-Term Trajectory
                </div>
                <p className="text-xs italic leading-relaxed text-slate-400">
                  &quot;{analysisShortTerm}&quot;
                </p>
              </div>

              <div className="section-surface-muted industrial-corner rounded-[1.2rem] p-4 space-y-3">
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase text-amber-400">
                  <Zap size={14} />
                  Tactical Advantage
                </div>
                <p className="text-xs italic leading-relaxed text-slate-400">
                  &quot;{analysisTacticalEdge}&quot;
                </p>
              </div>

              <div className="industrial-corner rounded-[1.2rem] border border-rose-500/20 bg-rose-500/[0.06] p-4 space-y-3">
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase text-rose-400">
                  <AlertTriangle size={14} />
                  Systemic Risks
                </div>
                <p className="text-xs italic leading-relaxed text-slate-400">
                  &quot;{analysisRiskProfile}&quot;
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 rounded-[1.2rem] border border-white/6 bg-black/25 p-4 md:grid-cols-3">
              <div className="space-y-1">
                <div className="text-[9px] font-bold uppercase text-slate-600">S/R Status</div>
                <div className="flex items-center gap-2">
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${trapDotClass}`}
                  />
                  <span className="text-[10px] font-black uppercase text-slate-400">{trapLabel}</span>
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-[9px] font-bold uppercase text-slate-600">Whale Velocity</div>
                <div className="text-[10px] font-bold text-slate-200">
                  {hasWhaleFlow ? (
                    <span className="uppercase text-cyan-400">Active Accumulation</span>
                  ) : (
                    <span className="uppercase text-slate-500">Neutral Pressure</span>
                  )}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-[9px] font-bold uppercase text-slate-600">Mirrored Delta</div>
                <div className="text-[10px] font-bold text-slate-200">
                  {arbitrage && arbitrageCorrelation != null ? (
                    <span className="tabular-nums text-amber-400">
                      {(arbitrageCorrelation * 100).toFixed(1)}% LINKED
                    </span>
                  ) : (
                    <span className="italic uppercase text-slate-700">UNLINKED</span>
                  )}
                </div>
              </div>
            </div>

            <div className="section-surface-muted industrial-corner rounded-[1.2rem] p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.24em] text-slate-500">
                    Desk Promotion
                  </div>
                  <p className="mt-1 text-xs text-slate-400">
                    {canPromote
                      ? "Push this intelligence brief directly into the intraday, swing, or position lane."
                      : "No actionable levels are attached to this brief yet."}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <IndustrialButton type="button" variant="secondary" size="sm" disabled={!canPromote} onClick={() => void onPromote("INTRADAY")}>
                    Promote to Intraday Lane
                  </IndustrialButton>
                  <IndustrialButton type="button" variant="secondary" size="sm" disabled={!canPromote} onClick={() => void onPromote("SWING")}>
                    Promote to Swing Lane
                  </IndustrialButton>
                  <IndustrialButton type="button" variant="secondary" size="sm" disabled={!canPromote} onClick={() => void onPromote("POSITION")}>
                    Promote to Position Lane
                  </IndustrialButton>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="flex items-center justify-between border-t border-white/6 bg-black/20 px-4 py-2 opacity-40">
        <div className="text-[8px] uppercase tracking-tighter text-slate-500">
          SYSTEM_AUTH::ENCRYPTED_DEEP_LINK
        </div>
        <div className="text-[8px] uppercase tracking-tighter text-slate-500">
          HORUS_ANALYTICS_II_ORACLE
        </div>
      </div>
    </IndustrialCard>
  );
};
