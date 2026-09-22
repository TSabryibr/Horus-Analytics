"use client";

import { useState, useEffect, useCallback } from "react";
import useSWR from "swr";
import { apiFetch, readJsonSafe, swrFetcher } from "@/lib/api";

const ORACLE_SCOPE_ALIASES: Record<string, string> = {
  EGX30: "EGX30",
  EGX70: "EGX70",
  EGX100: "EGX100",
  ALL: "ALL",
  UNIVERSE: "ALL",
  UNIVERS: "ALL",
};

export function normalizeOracleAssetChoice(value: string) {
  const normalized = String(value || "").trim().toUpperCase();
  if (!normalized) {
    return "";
  }
  return ORACLE_SCOPE_ALIASES[normalized] || normalized;
}

export function useAssetIntelligence() {
  const [selectedTicker, setSelectedTicker] = useState<string>("");
  const [historicalReportId, setHistoricalReportId] = useState<number | null>(null);

  // 1. Get Default Ticker
  const { data: defaultData } = useSWR("/api/v1/ai/asset-reports/default", swrFetcher);

  useEffect(() => {
    if (defaultData?.ticker && !selectedTicker) {
      setSelectedTicker(normalizeOracleAssetChoice(defaultData.ticker));
    }
  }, [defaultData, selectedTicker]);

  // 2. Get Asset History
  const { data: history = [], isLoading: historyLoading, mutate: mutateHistory } = useSWR(
    selectedTicker ? `/api/v1/ai/asset-reports/history?ticker=${selectedTicker}` : null,
    swrFetcher
  );

  // 3. Get Asset Report (Live or Historical)
  const reportUrl = historicalReportId 
    ? `/api/v1/ai/asset-report/${historicalReportId}` 
    : (selectedTicker ? `/api/v1/ai/asset-report?ticker=${selectedTicker}` : null);
    
  const { data: report, isLoading: reportLoading, error: reportError, mutate: mutateReport } = useSWR(reportUrl, swrFetcher);

  const refreshReport = useCallback(async () => {
    if (!selectedTicker) {
      return;
    }

    setHistoricalReportId(null);
    const response = await apiFetch(`/api/v1/ai/asset-report?ticker=${selectedTicker}&force_refresh=true`);
    const nextReport = await readJsonSafe(response);
    await mutateReport(
      nextReport,
      { revalidate: false }
    );
    void mutateHistory();
  }, [selectedTicker, mutateReport, mutateHistory]);

  const selectHistoryReport = useCallback((id: number | null) => {
    setHistoricalReportId(id);
  }, []);

  return {
    selectedTicker,
    setSelectedTicker: (t: string) => {
      setSelectedTicker(normalizeOracleAssetChoice(t));
      setHistoricalReportId(null);
    },
    report,
    reportLoading,
    reportError,
    refreshReport,
    history,
    historyLoading,
    selectedReportId: historicalReportId,
    selectHistoryReport,
  };
}
