'use client';

import { useState } from 'react';
import { AlertTriangle, Filter, Play, RefreshCw, Volume2, VolumeX } from 'lucide-react';
import { cn } from '@/lib/utils';
import { PineProfileDetailsDialog } from '@/app/components/PineProfileDetailsDialog';
import { IndustrialButton } from '../../components/custom/IndustrialButton';
import type { ScannerStrategyProfile } from '../hooks/useScannerRuntime';

type ScannerControlsProps = {
    index: string;
    isIntraday: boolean;
    loading: boolean;
    progress: string;
    scannerProfiles: ScannerStrategyProfile[];
    selectedProfile: ScannerStrategyProfile | null;
    selectedProfileId: string;
    setIndex: (value: string) => void;
    setIsIntraday: (value: boolean) => void;
    setSelectedProfileId: (value: string) => void;
    onRunScan: () => void;
    isMuted?: boolean;
    onToggleMute?: () => void;
};

function formatAuditStamp(value?: string | null) {
    if (!value) {
        return 'Pending';
    }

    return value.replace('T', ' ').slice(0, 16);
}

function formatMetric(value?: number | string) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
        return 'N/A';
    }

    return numeric.toFixed(1);
}

function getPromotionMarginLines(profile: ScannerStrategyProfile | null) {
    const actuals = profile?.promotion_summary?.actuals;
    const thresholds = profile?.promotion_summary?.thresholds;

    if (!actuals || !thresholds) {
        return [];
    }

    const lines: string[] = [];
    const compatibilityActual = Number(actuals.compatibility_score);
    const compatibilityThreshold = Number(thresholds.compatibility_score);
    const combinedActual = Number(actuals.combined_score);
    const combinedThreshold = Number(thresholds.combined_score);
    const drawdownActual = Number(actuals.max_drawdown);
    const drawdownThreshold = Number(thresholds.max_drawdown);

    if (Number.isFinite(compatibilityActual) && Number.isFinite(compatibilityThreshold) && compatibilityActual - compatibilityThreshold <= 5) {
        lines.push(`Compatibility margin: ${formatMetric(compatibilityActual)} vs ready floor ${formatMetric(compatibilityThreshold)}`);
    }

    if (Number.isFinite(combinedActual) && Number.isFinite(combinedThreshold) && combinedActual - combinedThreshold <= 5) {
        lines.push(`Combined score margin: ${formatMetric(combinedActual)} vs ready floor ${formatMetric(combinedThreshold)}`);
    }

    if (Number.isFinite(drawdownActual) && Number.isFinite(drawdownThreshold) && drawdownThreshold - drawdownActual <= 5) {
        lines.push(`Drawdown headroom: ${formatMetric(drawdownActual)}% vs ${formatMetric(drawdownThreshold)}% max`);
    }

    return lines;
}

function getProfileFamilyLabel(sourceType?: string) {
    const normalized = String(sourceType || '').trim().toUpperCase();
    if (normalized === 'PRICE_ACTION') {
        return 'Price-action';
    }
    if (normalized === 'PINE_LOGIC_IMPORT') {
        return 'Imported logic';
    }
    return 'Pine';
}

export function ScannerControls({
    index,
    isIntraday,
    loading,
    progress,
    scannerProfiles,
    selectedProfile,
    selectedProfileId,
    setIndex,
    setIsIntraday,
    setSelectedProfileId,
    onRunScan,
    isMuted = false,
    onToggleMute
}: ScannerControlsProps) {
    const [detailsOpen, setDetailsOpen] = useState(false);
    const profileMarket = selectedProfile?.market || index;
    const isProfileSelected = Boolean(selectedProfileId);
    const savedProfileLabel = selectedProfile ? `${selectedProfile.market} / ${selectedProfile.timeframe || '1D'}` : `${index} / 1D`;
    const promotionMarginLines = getPromotionMarginLines(selectedProfile);
    const hasPromotionWarning = promotionMarginLines.length > 0;
    const lastActivation = selectedProfile?.activation_history?.[0];
    const profileFamilyLabel = getProfileFamilyLabel(selectedProfile?.source_type);
    const detailsPrimaryHref = selectedProfile?.profile_id
        ? (String(selectedProfile.source_type || '').toUpperCase() === 'PRICE_ACTION'
            ? `/strategy?mode=PRICE_ACTION&profileId=${selectedProfile.profile_id}`
            : `/optimization?mode=PINE_LAB&profileId=${selectedProfile.profile_id}`)
        : null;
    const detailsPrimaryLabel = String(selectedProfile?.source_type || '').toUpperCase() === 'PRICE_ACTION'
        ? 'Open in Strategy Lab'
        : 'Open in Pine Lab';

    return (
        <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3 bg-slate-950 industrial-border border p-3 rounded-none">
                <div className="flex min-w-[200px] flex-col gap-1">
                    <span className="mb-1 ml-1 text-[9px] font-black uppercase tracking-widest text-slate-600">Strategy Profile</span>
                    <div className="group relative">
                        <select
                            aria-label="Scanner Strategy"
                            value={selectedProfileId}
                            onChange={(e) => setSelectedProfileId(e.target.value)}
                            className="w-full cursor-pointer border border-white/10 bg-white/[0.03] py-2 pl-3 pr-8 text-[11px] font-bold uppercase tracking-tight text-white outline-none transition focus:border-primary/50"
                        >
                            <option value="">[ DEFAULT CORE ]</option>
                            {scannerProfiles.map((p) => (
                                <option key={p.profile_id} value={String(p.profile_id)}>{p.profile_name}</option>
                            ))}
                        </select>
                        <Filter className="pointer-events-none absolute right-2.5 top-1/2 size-3 -translate-y-1/2 text-slate-500 transition-colors group-hover:text-primary" />
                    </div>
                </div>

                <div className="flex min-w-[140px] flex-col gap-1">
                    <span className="mb-1 ml-1 text-[9px] font-black uppercase tracking-widest text-slate-600">Market Scope</span>
                    <div className="group relative">
                        <select
                            aria-label="Market Universe"
                            value={profileMarket}
                            disabled={isProfileSelected}
                            onChange={(e) => setIndex(e.target.value)}
                            className="w-full cursor-pointer border border-white/10 bg-white/[0.03] py-2 pl-3 pr-8 text-[11px] font-bold uppercase tracking-tight text-white outline-none transition focus:border-primary/50 disabled:opacity-40"
                        >
                            <option value="EGX30">EGX 30</option>
                            <option value="EGX70">EGX 70</option>
                            <option value="EGX100">EGX 100</option>
                            <option value="ALL">UNIVERSE</option>
                        </select>
                        <Filter className="pointer-events-none absolute right-2.5 top-1/2 size-3 -translate-y-1/2 text-slate-500 transition-colors group-hover:text-primary" />
                    </div>
                </div>

                <div className="flex flex-col gap-1">
                    <span className="mb-1 ml-1 text-[9px] font-black uppercase tracking-widest text-slate-600">Scan Mode & Horizon</span>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setIsIntraday(!isIntraday)}
                            disabled={isProfileSelected}
                            className={cn(
                                'flex items-center gap-2 px-3.5 py-1.5 border text-[11px] font-black uppercase tracking-widest transition-all rounded-sm',
                                isIntraday
                                    ? 'bg-cyan-500/10 border-cyan-400/40 text-cyan-200 shadow-[0_0_12px_rgba(34,211,238,0.2)]'
                                    : 'bg-amber-500/10 border-amber-400/40 text-amber-200 shadow-[0_0_12px_rgba(251,191,36,0.15)]',
                                isProfileSelected && 'opacity-60 cursor-not-allowed'
                            )}
                        >
                            <span className={cn(
                                'size-2 rounded-full animate-pulse',
                                isIntraday ? 'bg-cyan-400' : 'bg-amber-400'
                            )} />
                            <span>
                                {isProfileSelected
                                    ? savedProfileLabel
                                    : isIntraday
                                        ? '⚡ LIVE INTRADAY PULSE'
                                        : '📅 EOD DAILY CLOSE'}
                            </span>
                        </button>
                        <span className="hidden sm:inline-block text-[9px] font-mono tracking-wider text-slate-400 border border-white/5 bg-black/40 px-2 py-1">
                            {isIntraday ? 'Stream: Live Parquet' : 'Stream: EOD Database'}
                        </span>
                    </div>
                </div>

                <div className="flex flex-col gap-1">
                    <span className="mb-1 ml-1 text-[9px] font-black uppercase tracking-widest text-slate-600">Audio</span>
                    <button
                        onClick={onToggleMute}
                        className={cn(
                            'size-9 flex items-center justify-center border transition-all',
                            isMuted
                                ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20',
                        )}
                        title={isMuted ? 'Unmute Alerts' : 'Mute Alerts'}
                    >
                        {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
                    </button>
                </div>

                <div className="ml-auto flex flex-col gap-1">
                    <span className="mb-1 text-[9px] font-black uppercase tracking-widest text-transparent">.</span>
                    <IndustrialButton
                        variant="primary"
                        disabled={loading}
                        onClick={onRunScan}
                        className="min-w-[180px] h-9"
                    >
                        {loading ? (
                            <div className="flex items-center gap-2">
                                <RefreshCw className="size-3 animate-spin" />
                                <span className="text-[10px] tracking-widest">{progress || 'Scanning...'}</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-2">
                                <Play className="size-3 fill-current" />
                                <span>Initialize Scan</span>
                            </div>
                        )}
                    </IndustrialButton>
                </div>
            </div>

            {selectedProfile ? (
                <div className="section-surface-muted industrial-corner space-y-4 rounded-[1.15rem] border border-white/10 p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                        <div className="space-y-2">
                            <div className="flex flex-wrap items-center gap-2">
                                <span className="text-[10px] font-black uppercase tracking-[0.24em] text-slate-400">Profile Audit</span>
                                {selectedProfile.is_active ? (
                                    <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-emerald-300">
                                        Active Default
                                    </span>
                                ) : null}
                                <span className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-slate-300">
                                    Saved {savedProfileLabel}
                                </span>
                            </div>
                            <div>
                                <p className="text-sm font-black uppercase tracking-[0.16em] text-white">{selectedProfile.profile_name}</p>
                                <p className="mt-1 text-xs text-slate-400">
                                    {profileFamilyLabel} scanner profile with persisted market, timeframe, and audit telemetry.
                                </p>
                            </div>
                        </div>

                        <IndustrialButton
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setDetailsOpen(true)}
                            className="self-start"
                        >
                            View Full Profile
                        </IndustrialButton>
                    </div>

                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                        <div className="rounded-[1rem] border border-white/8 bg-black/20 px-3 py-3 text-xs text-slate-300">
                            Created: {formatAuditStamp(selectedProfile.created_at)}
                        </div>
                        <div className="rounded-[1rem] border border-white/8 bg-black/20 px-3 py-3 text-xs text-slate-300">
                            Ready: {formatAuditStamp(selectedProfile.ready_at)}
                        </div>
                        <div className="rounded-[1rem] border border-white/8 bg-black/20 px-3 py-3 text-xs text-slate-300">
                            Activated: {formatAuditStamp(selectedProfile.activated_at)}
                        </div>
                        <div className="rounded-[1rem] border border-white/8 bg-black/20 px-3 py-3 text-xs text-slate-300">
                            Activations: {Number(selectedProfile.activation_count ?? 0)}
                        </div>
                    </div>

                    {lastActivation?.previous_active_profile_name ? (
                        <p className="text-xs text-slate-400">
                            Last activation replaced {lastActivation.previous_active_profile_name}
                        </p>
                    ) : null}

                    {hasPromotionWarning ? (
                        <div className="rounded-[1rem] border border-amber-500/20 bg-amber-500/10 p-4">
                            <div className="flex items-start gap-3">
                                <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-300" />
                                <div className="space-y-2">
                                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-amber-200">Promotion Margin Warning</p>
                                    <p className="text-xs text-amber-100/90">
                                        Selected {profileFamilyLabel.toLowerCase()} scanner profile is close to one or more promotion thresholds.
                                    </p>
                                    <div className="space-y-1 text-xs text-amber-100/90">
                                        {promotionMarginLines.map((line) => (
                                            <p key={line}>{line}</p>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : null}
                </div>
            ) : null}

            <PineProfileDetailsDialog
                isOpen={detailsOpen}
                profile={selectedProfile}
                onClose={() => setDetailsOpen(false)}
                primaryHref={detailsPrimaryHref}
                primaryLabel={detailsPrimaryLabel}
            />
        </div>
    );
}
