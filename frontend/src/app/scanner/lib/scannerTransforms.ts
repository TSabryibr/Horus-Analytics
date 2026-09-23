import clsx from 'clsx';

export function truncateScannerPrice(val: number | string, decimals: number = 3): string {
    const n = Number(val);
    if (!Number.isFinite(n)) return '0.000';
    const factor = Math.pow(10, decimals);
    const truncated = Math.trunc(n * factor) / factor;
    return truncated.toFixed(decimals);
}

export function getScannerRegimeClass(regime: string | undefined): string {
    return clsx(
        'text-2xl heading-title',
        regime === 'BULLISH'
            ? 'text-emerald-400'
            : regime === 'BEARISH'
                ? 'text-rose-400'
                : 'text-amber-400',
    );
}

export function getScannerBreadthBarClass(breadth: number | undefined): string {
    return clsx(
        'h-1.5 rounded-full transition-all duration-[1500ms]',
        Number(breadth) > 50
            ? 'bg-primary  '
            : 'bg-rose-500',
    );
}

export function formatScannerRouteProfile(profile: string | null | undefined): string {
    if (!profile) return 'Unrouted';
    if (profile === 'EGX30_TREND_PROFILE') return 'EGX30 Trend';
    if (profile === 'EGX70_TACTICAL_PROFILE') return 'EGX70 Tactical';
    if (profile === 'ILLIQUID_NO_TRADE_PROFILE') return 'No Trade';
    return profile.replaceAll('_', ' ');
}

export function formatScannerSectorRs(value: number | null | undefined): string {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return 'Sector RS N/A';
    return `Sector RS ${numeric >= 0 ? '+' : ''}${numeric.toFixed(2)}`;
}

export function formatScannerVsaLabel(value: boolean | null | undefined): string {
    if (value === true) return 'VSA OK';
    if (value === false) return 'VSA Blocked';
    return 'VSA N/A';
}

export function formatScannerWhaleAlignment(value: string | null | undefined): string {
    const normalized = String(value || '').toUpperCase();
    if (normalized === 'SUPPORTIVE') return 'Whale Support';
    if (normalized === 'CONFLICT') return 'Whale Conflict';
    return 'Whale Neutral';
}

export function describeScannerWhaleAlignment(value: string | null | undefined): string {
    const normalized = String(value || '').toUpperCase();
    if (normalized === 'SUPPORTIVE') return 'Accumulation aligns with the long setup.';
    if (normalized === 'CONFLICT') return 'Distribution is pushing against the long setup.';
    return 'Whale flow is neutral for this setup.';
}

export function formatScannerTrapRiskBand(value: string | null | undefined): string {
    const normalized = String(value || '').toUpperCase();
    if (!normalized) return 'Trap N/A';
    return `Trap ${normalized.charAt(0)}${normalized.slice(1).toLowerCase()}`;
}

export function describeScannerTrapRiskBand(value: string | null | undefined): string {
    const normalized = String(value || '').toUpperCase();
    if (normalized === 'LOW') return 'Limited trap pressure under the current scoring mix.';
    if (normalized === 'MEDIUM') return 'Some trap pressure is present, but not yet stacked.';
    if (normalized === 'HIGH') return 'Elevated trap pressure suggests future review thresholds may trigger.';
    if (normalized === 'SEVERE') return 'Stacked risk from multiple pressure signals.';
    return 'Trap-risk scoring is not available for this setup.';
}

export function formatScannerEnforcementState(value: string | null | undefined): string {
    const normalized = String(value || '').toUpperCase();
    if (normalized === 'BLOCK_EXECUTION') return 'Blocked';
    if (normalized === 'WATCH_ONLY') return 'Watch Only';
    return 'Actionable';
}

export function describeScannerEnforcementState(value: string | null | undefined): string {
    const normalized = String(value || '').toUpperCase();
    if (normalized === 'BLOCK_EXECUTION') return 'Execution is blocked, but the row stays visible for operator review.';
    if (normalized === 'WATCH_ONLY') return 'This setup stays visible, but it is downgraded to watch-only.';
    return 'No whale/trap enforcement threshold is active for this setup.';
}

export function formatScannerEnforcementReason(value: string | null | undefined): string {
    const normalized = String(value || '').trim();
    if (!normalized) return 'no enforcement';
    return normalized.replaceAll('_', ' ');
}
