"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { OracleShell } from "./components/OracleShell";
import { OracleAiReportPanel } from "./components/OracleAiReportPanel";
import { ReportHistoryBrowser } from "./components/tac-briefing/ReportHistoryBrowser";
import { SupportResistanceRadar } from "./components/tac-briefing/SupportResistanceRadar";
import { SentimentTimeline } from "./components/tac-briefing/SentimentTimeline";
import { normalizeOracleAssetChoice, useAssetIntelligence } from "./hooks/useAssetIntelligence";
import { Globe, Search, ShieldAlert } from "lucide-react";
import { CommandToolbar } from "@/app/components/custom/CommandToolbar";
import { IndustrialButton } from "@/app/components/custom/IndustrialButton";
import { IndustrialCard } from "@/app/components/custom/IndustrialCard";
import { IndustrialInput } from "@/app/components/custom/IndustrialInput";
import { useSignalDeskData } from "../context/GlobalDataContext";

// New Panel Imports
import { OracleMacroPanel } from "./components/OracleMacroPanel";
import { OracleSqueezePanel } from "./components/OracleSqueezePanel";
import { getSignalColor } from "./lib/oracleTransforms";
import type { OracleIndex } from "./hooks/useOracleRuntime";
import useSWR from "swr";
import { apiFetch, readJsonSafe } from "@/lib/api";

const ORACLE_SCOPE_OPTIONS = [
  { value: "EGX30", label: "EGX30" },
  { value: "EGX70", label: "EGX70" },
  { value: "EGX100", label: "EGX100" },
  { value: "ALL", label: "UNIVERSE" },
] as const;

function getOracleAssetLabel(value: string) {
  return ORACLE_SCOPE_OPTIONS.find((option) => option.value === value)?.label || value;
}

const postFetcher = async (key: [string, any]) => {
  const [endpoint, body] = key;
  const res = await apiFetch(endpoint, {
    method: "POST",
    body: JSON.stringify(body),
  });
  const payload = await readJsonSafe<any>(res);
  if (!res.ok) {
    throw new Error(payload?.detail || "Failed to fetch predictions.");
  }
  return payload.data;
};

function buildRadarModel(report: any) {
  const snapshot = report?.snapshot;
  const scope = snapshot?.scope;
  const scopeLevels = snapshot?.scope_levels;
  const leadTicker = snapshot?.lead_ticker || snapshot?.lead_ticker_levels?.ticker || null;
  const leadLevels = snapshot?.lead_ticker_levels;

  if (scope && scopeLevels) {
    const currentPrice = Number(leadLevels?.entry ?? snapshot?.recommendation?.entry ?? 0);
    const supports = Array.isArray(scopeLevels?.supports)
      ? scopeLevels.supports.map((level: any) => ({
          price: Number(level.price ?? 0),
          strength: Number(level.strength ?? 0.4),
          type: "SUPPORT" as const,
          label: level.label,
          members: Number(level.members ?? 0),
        }))
      : [];
    const resistances = Array.isArray(scopeLevels?.resistances)
      ? scopeLevels.resistances.map((level: any) => ({
          price: Number(level.price ?? 0),
          strength: Number(level.strength ?? 0.4),
          type: "RESISTANCE" as const,
          label: level.label,
          members: Number(level.members ?? 0),
        }))
      : [];

    return {
      ready: currentPrice > 0 && (supports.length > 0 || resistances.length > 0),
      mode: "scope" as const,
      currentPrice,
      leadTicker,
      levels: [...supports, ...resistances],
      emptyMessage: "Tactical levels are still calibrating for this asset scope...",
    };
  }

  const recommendation = snapshot?.recommendation;
  const currentPrice = Number(recommendation?.entry ?? 0);
  const target = Number(recommendation?.target ?? 0);
  const stop = Number(recommendation?.stop ?? 0);
  const priceLevels = snapshot?.price_levels;
  const priceCurrent = Number(priceLevels?.current_price ?? 0);
  const priceSupports = Array.isArray(priceLevels?.supports)
    ? priceLevels.supports.map((level: any) => ({
        price: Number(level.price ?? 0),
        strength: Number(level.strength ?? 0.4),
        type: "SUPPORT" as const,
        label: level.label,
        members: Number(level.members ?? 0),
      }))
    : [];
  const priceResistances = Array.isArray(priceLevels?.resistances)
    ? priceLevels.resistances.map((level: any) => ({
        price: Number(level.price ?? 0),
        strength: Number(level.strength ?? 0.4),
        type: "RESISTANCE" as const,
        label: level.label,
        members: Number(level.members ?? 0),
      }))
    : [];

  if (priceCurrent > 0 && (priceSupports.length > 0 || priceResistances.length > 0)) {
    return {
      ready: true,
      mode: "single" as const,
      currentPrice: priceCurrent,
      leadTicker: snapshot?.ticker || null,
      levels: [...priceSupports, ...priceResistances],
      emptyMessage: `No ${snapshot?.ticker || "asset"} price-history support/resistance levels are available yet.`,
    };
  }

  return {
    ready: currentPrice > 0 && target > 0 && stop > 0,
    mode: "single" as const,
    currentPrice,
    leadTicker: snapshot?.recommendation?.ticker || null,
    levels: [
      { price: target, strength: 0.8, type: "RESISTANCE" as const },
      { price: stop, strength: 0.9, type: "SUPPORT" as const },
    ],
    emptyMessage: `No ${snapshot?.ticker || "asset"} support/resistance levels are available yet.`,
  };
}

function OracleContent() {
  const searchParams = useSearchParams();
  const {
    selectedTicker,
    setSelectedTicker,
    report,
    reportLoading,
    reportError,
    refreshReport,
    history,
    historyLoading,
    selectedReportId,
    selectHistoryReport,
  } = useAssetIntelligence();

  const { promoteCandidate } = useSignalDeskData();

  const [searchInput, setSearchInput] = useState("");
  const [activeTab, setActiveTab] = useState<"asset" | "macro" | "squeeze">("asset");
  const [macroIndex, setMacroIndex] = useState<OracleIndex>("EGX30");
  const [promoteStatus, setPromoteStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Live SWR fetching for prediction tab sub-views
  const { data: macroData } = useSWR(
    activeTab === "macro" ? ["/api/v1/prediction", { mode: "MACRO", index: macroIndex }] : null,
    postFetcher
  );

  const { data: squeezeData } = useSWR(
    activeTab === "squeeze" ? ["/api/v1/prediction", { mode: "SQUEEZE" }] : null,
    postFetcher
  );

  const selectedTickerLabel = getOracleAssetLabel(selectedTicker);
  const selectedScopeValue = ORACLE_SCOPE_OPTIONS.some((option) => option.value === selectedTicker) ? selectedTicker : "CUSTOM";
  const radarModel = buildRadarModel(report);
  const verdict = report?.verdict || "NEUTRAL";
  const confidence = Number(report?.confidence || 0);
  const queryTicker = searchParams.get("ticker");
  const queryAsset = searchParams.get("asset");

  useEffect(() => {
    const normalizedQueryAsset = normalizeOracleAssetChoice(queryAsset || "");
    const normalizedQueryTicker = normalizeOracleAssetChoice(queryTicker || "");
    if (normalizedQueryAsset) {
      setSelectedTicker(normalizedQueryAsset);
      return;
    }
    if (normalizedQueryTicker) {
      setSelectedTicker(normalizedQueryTicker);
    }
  }, [queryAsset, queryTicker, setSelectedTicker]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setSelectedTicker(searchInput.trim().toUpperCase());
      setSearchInput("");
    }
  };

  const recommendation = report?.snapshot?.recommendation;
  const handlePromote = async (lane: "INTRADAY" | "SWING" | "POSITION") => {
    if (!recommendation?.entry || !recommendation?.stop || !recommendation?.target || !selectedTicker) {
      return;
    }

    setPromoteStatus(null);
    const success = await promoteCandidate({
      lane,
      ticker: selectedTicker,
      side: verdict === "BEARISH" ? "SELL" : "BUY",
      entry_price: Number(recommendation.entry),
      stop_loss: Number(recommendation.stop),
      target_price: Number(recommendation.target),
      confidence: Number(confidence || 0),
      score: Number(confidence || 0) / 10,
      horizon_days: lane === "INTRADAY" ? 1 : lane === "SWING" ? 5 : 20,
      source_module: "ORACLE",
      rationale: {
        verdict,
        short_term: report?.analysis?.short_term,
        tactical_edge: report?.analysis?.tactical_edge,
        risk_profile: report?.analysis?.risk_profile,
      },
    });

    if (success) {
      setPromoteStatus({
        type: "success",
        message: `// PROMOTE_SUCCESS::TICKER[${selectedTicker}] -> DESK[${lane}]`,
      });
      setTimeout(() => setPromoteStatus(null), 5000);
    } else {
      setPromoteStatus({
        type: "error",
        message: `// PROMOTE_ERROR::FAILED TO ROUTE [${selectedTicker}] TO SIGNAL DESK.`,
      });
    }
  };

  return (
    <OracleShell
      isLoading={reportLoading && !report}
      onRefresh={refreshReport}
      selectedTicker={selectedTicker}
      selectedTickerLabel={selectedTickerLabel}
      isHistorical={!!selectedReportId}
      forecastTimestamp={report?.generated_at ? String(report.generated_at).replace("T", " ").slice(0, 16) : undefined}
    >
      <CommandToolbar
        label="Deep Intelligence Command"
        description="Query a ticker, load fresh tactical synthesis, and switch between live and archived briefings without leaving the command lane."
        trailing={
          <IndustrialButton type="submit" form="oracle-search-form">
            Analyze
          </IndustrialButton>
        }
      >
        <div className="min-w-[11rem]">
          <label className="mb-2 block text-[9px] uppercase tracking-[0.28em] text-slate-500" htmlFor="oracle-asset-scope">
            Oracle Asset Scope
          </label>
          <select
            id="oracle-asset-scope"
            aria-label="Oracle Asset Scope"
            value={selectedScopeValue}
            onChange={(e) => {
              if (e.target.value !== "CUSTOM") {
                setSelectedTicker(e.target.value);
              }
            }}
            className="w-full rounded-[1rem] border border-white/10 bg-black/25 px-3 py-3 text-[11px] font-black uppercase tracking-[0.18em] text-slate-200 outline-none transition hover:border-white/20 focus:border-cyan-400/40"
          >
            {selectedScopeValue === "CUSTOM" ? (
              <option value="CUSTOM" className="bg-slate-950 text-slate-200">
                {selectedTickerLabel}
              </option>
            ) : null}
            {ORACLE_SCOPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value} className="bg-slate-950 text-slate-200">
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <form id="oracle-search-form" onSubmit={handleSearch} className="flex min-w-0 flex-1">
          <IndustrialInput
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="ENTER TICKER FOR DEEP INTELLIGENCE (E.G. CIIC, MFOT)..."
            shellClassName="min-w-0 flex-1 rounded-[1.1rem]"
            className="uppercase tracking-[0.22em]"
            leadingSlot={<Search size={18} />}
            trailingSlot={
              <kbd className="hidden rounded-[0.8rem] border border-white/10 bg-black/20 px-2 py-1 text-[10px] text-slate-500 sm:inline-flex">
                CMD + K
              </kbd>
            }
          />
        </form>
      </CommandToolbar>

      {/* SWR Error Recovery Card */}
      {reportError && (
        <div className="mb-6 rounded-[1.25rem] border border-rose-500/30 bg-rose-500/10 p-4 font-mono text-xs text-rose-200 shadow-[0_0_20px_rgba(244,63,94,0.08)]">
          <div className="flex items-center gap-3">
            <ShieldAlert className="h-5 w-5 text-rose-400 shrink-0" />
            <div>
              <p className="font-bold uppercase tracking-wider">Oracle Report Fetch Failure</p>
              <p className="text-[11px] opacity-80 mt-0.5">
                {String(reportError?.message || "Failed to load fresh AI forecast data. Click Refresh Intel to retry.")}
              </p>
            </div>
            <IndustrialButton variant="ghost" size="sm" onClick={refreshReport} className="ml-auto text-xs">
              Retry
            </IndustrialButton>
          </div>
        </div>
      )}

      {/* Executive Forecast Banner */}
      {report && !reportLoading && (
        <div className="mb-6 rounded-[1.25rem] border border-cyan-500/30 bg-[linear-gradient(135deg,rgba(15,23,42,0.95),rgba(30,41,59,0.95))] p-4 shadow-[0_0_25px_rgba(34,211,238,0.1)]">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className={`px-3 py-1 text-xs font-black uppercase tracking-widest rounded-full border ${
                verdict === "BULLISH"
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300 shadow-[0_0_10px_rgba(16,185,129,0.15)]"
                  : verdict === "BEARISH"
                  ? "bg-rose-500/10 border-rose-500/30 text-rose-300 shadow-[0_0_10px_rgba(244,63,94,0.15)]"
                  : "bg-amber-500/10 border-amber-500/30 text-amber-300"
              }`}>
                {verdict === "BULLISH" ? "🟢 BULLISH BIAS" : verdict === "BEARISH" ? "🔴 BEARISH BIAS" : "🟡 NEUTRAL STANCE"}
              </span>
              <span className="font-mono text-xs text-slate-300 border border-white/10 bg-black/30 px-2.5 py-1 rounded-sm">
                Confidence: <strong className="text-cyan-300">{Number(confidence).toFixed(0)}%</strong>
              </span>
              {report?.analysis?.tactical_edge ? (
                <span className="hidden md:inline-block font-mono text-[11px] text-slate-400 truncate max-w-md">
                  Edge: <span className="text-slate-200">{report.analysis.tactical_edge}</span>
                </span>
              ) : null}
            </div>

            <div className="flex flex-wrap items-center gap-4 font-mono text-xs">
              <div>
                <span className="text-slate-500 uppercase tracking-widest text-[9px]">Entry: </span>
                <span className="text-white font-bold">{recommendation?.entry ? Number(recommendation.entry).toFixed(2) : "N/A"}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase tracking-widest text-[9px]">Stop Loss: </span>
                <span className="text-rose-400 font-bold">{recommendation?.stop ? Number(recommendation.stop).toFixed(2) : "N/A"}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase tracking-widest text-[9px]">Target 1: </span>
                <span className="text-emerald-400 font-bold">{recommendation?.target ? Number(recommendation.target).toFixed(2) : "N/A"}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="mb-6 flex border-b border-white/10 pb-px">
        {(["asset", "macro", "squeeze"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => {
              setActiveTab(tab);
              setPromoteStatus(null);
            }}
            className={`border-b-2 px-6 py-3 font-mono text-[11px] font-bold uppercase tracking-[0.18em] transition-all ${
              activeTab === tab
                ? "border-cyan-500 text-cyan-400"
                : "border-transparent text-slate-500 hover:text-slate-300"
            }`}
          >
            {tab === "asset"
              ? "Asset Intel"
              : tab === "macro"
              ? "Market Canary"
              : "Volatility Coil"}
          </button>
        ))}
      </div>

      {/* Promotion success/error notification */}
      {promoteStatus && (
        <div
          className={`mb-6 rounded-[1rem] border p-4 font-mono text-xs flex justify-between items-center transition-all ${
            promoteStatus.type === "success"
              ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.05)]"
              : "bg-rose-500/10 border-rose-500/30 text-rose-400 shadow-[0_0_15px_rgba(244,63,94,0.05)]"
          }`}
        >
          <span>{promoteStatus.message}</span>
          <button
            onClick={() => setPromoteStatus(null)}
            className="text-[10px] uppercase underline tracking-wider opacity-60 hover:opacity-100"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Tab Content Rendering */}
      {activeTab === "asset" && (
        <div className="flex min-h-[800px] flex-col gap-6 xl:flex-row">
          {/* Left Side: Intelligence Briefing */}
          <div className="flex-1 space-y-6">
            <OracleAiReportPanel
              title={`${selectedTickerLabel} Intelligence Briefing`}
              report={report}
              isLoading={reportLoading}
              onRefresh={refreshReport}
              isHistorical={!!selectedReportId}
              onPromote={handlePromote}
            />

            {/* Sub-Intelligence Grid */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <IndustrialCard
                tone="secondary"
                title="S/R Overlap Radar"
                subtitle="Signal geometry and tactical proximity map"
                headerSlot={<Globe size={14} className="text-cyan-400" />}
                className="rounded-[1.4rem]"
              >
                {radarModel.ready ? (
                  <SupportResistanceRadar
                    currentPrice={radarModel.currentPrice}
                    levels={radarModel.levels}
                    mode={radarModel.mode}
                    leadTicker={radarModel.leadTicker}
                  />
                ) : (
                  <div className="section-surface-muted flex h-48 items-center justify-center rounded-[1.1rem] border border-dashed border-white/10 text-sm text-slate-500">
                    {radarModel.emptyMessage}
                  </div>
                )}
              </IndustrialCard>

              <IndustrialCard
                tone="secondary"
                title="Sentiment Narrative"
                subtitle="Aggregate index and narrative impact sweep"
                headerSlot={<ShieldAlert size={14} className="text-amber-400" />}
                className="rounded-[1.4rem]"
              >
                <SentimentTimeline
                  score={report?.snapshot?.sentiment?.score || 50}
                  regime={report?.snapshot?.sentiment?.regime || "NEUTRAL"}
                  hits={report?.snapshot?.scope_news_mentions || report?.snapshot?.news_mentions || []}
                  leadHits={report?.snapshot?.lead_ticker_news_mentions || []}
                  mode={report?.snapshot?.scope ? "scope" : "single"}
                  leadTicker={report?.snapshot?.lead_ticker || null}
                  ticker={report?.snapshot?.ticker || selectedTicker}
                />
              </IndustrialCard>
            </div>
          </div>

          {/* Right Side: Archives & Telemetry */}
          <div className="w-full space-y-6 xl:sticky xl:top-[var(--chrome-sticky-offset)] xl:w-[21rem] xl:self-start">
            <div className="flex-1">
              <ReportHistoryBrowser
                history={history}
                selectedId={selectedReportId}
                onSelect={selectHistoryReport}
                isLoading={historyLoading}
              />
            </div>

            {/* Tactical Status */}
            <IndustrialCard
              tone="rail"
              title="Tactical Status"
              subtitle="Rail telemetry node"
              className="rounded-[1.3rem] font-mono"
            >
              <div className="space-y-3 text-[10px] uppercase leading-relaxed text-slate-400">
                <div className="flex items-center justify-between border-b border-white/6 pb-2">
                  <span>Station</span>
                  <span className="text-cyan-300">{selectedTicker ? `TAC-${selectedTicker.substring(0, 4)}` : "AWAITING"}</span>
                </div>
                <div className="flex items-center justify-between border-b border-white/6 pb-2">
                  <span>Uptime</span>
                  <span className="tabular-nums text-slate-200">{report ? "ACTIVE" : "--:--:--"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Status</span>
                  <span className={report ? "text-emerald-300" : "text-amber-300"}>{report ? "Online" : "Standby"}</span>
                </div>
              </div>
            </IndustrialCard>
          </div>
        </div>
      )}

      {activeTab === "macro" && (
        <div className="grid grid-cols-1 gap-6">
          <OracleMacroPanel
            activeIndex={macroIndex}
            setActiveIndex={setMacroIndex}
            macro={macroData}
            macroSignalColor={getSignalColor(macroData?.signal || "")}
          />
        </div>
      )}

      {activeTab === "squeeze" && (
        <div className="grid grid-cols-1 gap-6">
          <OracleSqueezePanel
            squeeze={squeezeData}
            candidates={squeezeData?.candidates || []}
          />
        </div>
      )}
    </OracleShell>
  );
}

export default function OraclePage() {
  return (
    <React.Suspense fallback={null}>
      <OracleContent />
    </React.Suspense>
  );
}
