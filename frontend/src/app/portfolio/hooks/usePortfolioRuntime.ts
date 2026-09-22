'use client';

import { useCallback, useEffect, useState } from 'react';
import { PortfolioHealth, Position } from '@/types';
import { apiFetch, readJsonSafe } from '@/lib/api';
import { waitForSystemReady } from '../lib/systemReadiness';

export interface HoardData {
    status: string;
    net_worth_egp: number;
    net_worth_usd: number;
    cash_egp: number;
    cash_usd: number;
    positions: Position[];
}

export interface PortfolioAnalysisReport {
    status: string;
    health_score: number;
    heat: number;
    recommendations: { type: string; severity: string; title: string; message: string }[];
    sector_breakdown: Record<string, number>;
}

export interface PortfolioReportTrade {
    ticker: string;
    entry_price: number;
    exit_price: number;
    exit_date: string;
    pnl: number;
    reason?: string;
}

export interface PortfolioReportMetrics {
    total_pnl: number;
    realized_pnl?: number;
    unrealized_pnl?: number;
    win_rate: number;
    profit_factor: number;
    total_trades: number;
}

export interface PortfolioReportCurvePoint {
    date: string;
    equity: number;
}

export interface PortfolioReportBundle {
    metrics: PortfolioReportMetrics;
    curve: PortfolioReportCurvePoint[];
    trades: PortfolioReportTrade[];
}

export type CurrencyMode = 'EGP' | 'USD';
export type FeeMode = 'GROSS' | 'NET';

type UiMessage = { type: 'error' | 'success'; text: string } | null;

export function usePortfolioRuntime({ activePortfolioId }: { activePortfolioId: number | null }) {
    const [hoard, setHoard] = useState<HoardData | null>(null);
    const [health, setHealth] = useState<PortfolioHealth | null>(null);
    const [analysis, setAnalysis] = useState<PortfolioAnalysisReport | null>(null);
    const [report, setReport] = useState<PortfolioReportBundle | null>(null);
    const [loading, setLoading] = useState(false);
    const [uiMessage, setUiMessage] = useState<UiMessage>(null);

    // FX & Fee Transparency State
    const [currencyMode, setCurrencyMode] = useState<CurrencyMode>('EGP');
    const [feeMode, setFeeMode] = useState<FeeMode>('GROSS');
    const [usdRate, setUsdRate] = useState<number>(50.0);

    const showUiMessage = useCallback((type: 'error' | 'success', text: string) => {
        setUiMessage({ type, text });
    }, []);

    const clearUiMessage = useCallback(() => {
        setUiMessage(null);
    }, []);

    const refreshData = useCallback(async () => {
        if (!activePortfolioId) {
            setHoard(null);
            setHealth(null);
            setAnalysis(null);
            setReport(null);
            setLoading(false);
            return;
        }

        setLoading(true);
        try {
            const ready = await waitForSystemReady();
            if (!ready) {
                setLoading(false);
                return;
            }

            const [hoardRes, healthRes, analysisRes, reportRes, rateRes] = await Promise.all([
                apiFetch(`/api/v1/portfolio?portfolio_id=${activePortfolioId}`),
                apiFetch('/api/v1/analytics/health'),
                apiFetch(`/api/v1/portfolio/analysis?portfolio_id=${activePortfolioId}`),
                apiFetch(`/api/v1/portfolio/report?portfolio_id=${activePortfolioId}`),
                apiFetch('/api/v1/market/rate'),
            ]);

            const hoardJson = await readJsonSafe<any>(hoardRes);
            setHoard(hoardJson.status === 'active' ? hoardJson : null);

            const healthJson = await readJsonSafe<any>(healthRes);
            setHealth(healthJson.status === 'success' ? healthJson : null);

            if (analysisRes.ok) {
                const analysisJson = await readJsonSafe<any>(analysisRes);
                setAnalysis(analysisJson);
            } else {
                setAnalysis(null);
            }

            if (reportRes.ok) {
                const reportJson = await readJsonSafe<PortfolioReportBundle | null>(reportRes);
                setReport(reportJson);
            } else {
                setReport(null);
            }

            if (rateRes.ok) {
                const rateJson = await readJsonSafe<{ rate?: number }>(rateRes);
                if (rateJson?.rate && rateJson.rate > 0) {
                    setUsdRate(rateJson.rate);
                }
            }
        } catch (error) {
            console.error('Fetch error:', error);
            setHoard(null);
            setHealth(null);
            setAnalysis(null);
            setReport(null);
        } finally {
            setLoading(false);
        }
    }, [activePortfolioId]);

    useEffect(() => {
        void refreshData();
    }, [refreshData]);

    // Gross calculations
    const floatingPnl = hoard?.positions ? hoard.positions.reduce((acc, pos) => acc + (pos.pnl || 0), 0) : 0;
    const settledPnl = report?.metrics?.realized_pnl ?? 0;

    // EGX friction: 0.15% entry + 0.15% current/exit = 0.30% round trip
    const floatingFees = hoard?.positions
        ? hoard.positions.reduce((acc, pos) => {
              const entryCost = (pos.entry_price || 0) * (pos.shares || 0);
              const exitValue = (pos.current_price || pos.entry_price || 0) * (pos.shares || 0);
              return acc + (entryCost * 0.0015 + exitValue * 0.0015);
          }, 0)
        : 0;

    const settledFees = report?.trades
        ? report.trades.reduce((acc, tr) => {
              const notional = (tr.entry_price || 0) * 100; // approximate trade size friction
              return acc + notional * 0.003;
          }, 0)
        : 0;

    const netFloatingPnl = floatingPnl - floatingFees;
    const netSettledPnl = settledPnl - settledFees;

    const effectiveFloatingPnl = feeMode === 'NET' ? netFloatingPnl : floatingPnl;
    const effectiveSettledPnl = feeMode === 'NET' ? netSettledPnl : settledPnl;

    const fxFactor = currencyMode === 'USD' ? 1 / (usdRate || 50.0) : 1.0;
    const displayFloatingPnl = effectiveFloatingPnl * fxFactor;
    const displaySettledPnl = effectiveSettledPnl * fxFactor;

    const netWorthEgp = hoard?.net_worth_egp ?? 0;
    const netWorthUsd = hoard?.net_worth_usd ?? (netWorthEgp / (usdRate || 50.0));
    const displayNetWorth = currencyMode === 'USD' ? netWorthUsd : netWorthEgp;

    const openPositionCount = hoard?.positions?.length ?? 0;
    const closedTradeCount = report?.metrics?.total_trades ?? 0;
    const winRate = report?.metrics?.win_rate ?? 0;

    return {
        hoard,
        health,
        analysis,
        report,
        floatingPnl,
        settledPnl,
        netFloatingPnl,
        netSettledPnl,
        displayFloatingPnl,
        displaySettledPnl,
        displayNetWorth,
        floatingFees,
        settledFees,
        currencyMode,
        setCurrencyMode,
        feeMode,
        setFeeMode,
        usdRate,
        openPositionCount,
        closedTradeCount,
        winRate,
        loading,
        uiMessage,
        showUiMessage,
        clearUiMessage,
        refreshData,
    };
}
