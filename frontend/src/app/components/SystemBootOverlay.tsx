"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Image from 'next/image';
import {
    Activity,
    ArrowRight,
    Database,
    RadioTower,
    RefreshCw,
    Send,
    ShieldCheck,
    Siren,
    TriangleAlert,
    Waypoints,
} from 'lucide-react';
import { usePathname } from 'next/navigation';
import { getApiBase } from '@/lib/api';

import {
    OPEN_SYSTEM_BOOT_EVENT,
    SYSTEM_BOOT_SESSION_KEY,
    type BootCheck,
    type BootMode,
    type FullSystemStatusPayload,
    resolveBootConsoleModel,
} from './systemBootModel';

const CHECK_ICON_BY_KEY = {
    api: RadioTower,
    database: Database,
    market: Activity,
    scanner: Waypoints,
    scheduler: ShieldCheck,
    telegram: Send,
} as const;

function formatLogLine(message: string) {
    const stamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    return `[${stamp}] ${message}`;
}

type TerminalLogTone = 'ready' | 'warning' | 'offline' | 'pending' | 'info';

interface TerminalLogEntry {
    id: string;
    time: string;
    source: string;
    message: string;
    tone: TerminalLogTone;
    status: string;
}

function classifyTerminalLog(message: string): TerminalLogTone {
    const normalized = message.toLowerCase();

    if (/(failed|unavailable|offline|unreachable|timed out|withheld|cannot reach)/.test(normalized)) {
        return 'offline';
    }

    if (/(degraded|delayed|warning|retry|retriggered|stale)/.test(normalized)) {
        return 'warning';
    }

    if (/(confirmed|operational|ready|authorized|sampled successfully|aligned)/.test(normalized)) {
        return 'ready';
    }

    if (/(pending|launching|running|detected|requested)/.test(normalized)) {
        return 'pending';
    }

    return 'info';
}

function resolveTerminalSource(message: string) {
    const sourceMatch = message.match(/^([A-Z][A-Z\s]+?)\s+(confirmed|degraded|unavailable|pending):/);

    if (sourceMatch?.[1]) {
        return sourceMatch[1].trim();
    }

    if (/health surface/i.test(message)) return 'HEALTH SURFACE';
    if (/manual/i.test(message)) return 'OPERATOR';
    if (/cold start|boot|console/i.test(message)) return 'BOOT';
    if (/readiness/i.test(message)) return 'READINESS';

    return 'SYSTEM';
}

function parseTerminalLogLine(log: string, index: number): TerminalLogEntry {
    const match = log.match(/^\[([^\]]+)\]\s*(.*)$/);
    const time = match?.[1] || '--:--:--';
    const message = match?.[2] || log;
    const tone = classifyTerminalLog(message);
    const statusByTone: Record<TerminalLogTone, string> = {
        ready: 'OK',
        warning: 'WARN',
        offline: 'FAULT',
        pending: 'WAIT',
        info: 'INFO',
    };

    return {
        id: `${index}-${log}`,
        time,
        source: resolveTerminalSource(message),
        message,
        tone,
        status: statusByTone[tone],
    };
}

function getTerminalToneClasses(tone: TerminalLogTone) {
    const classes: Record<TerminalLogTone, { rail: string; badge: string; text: string }> = {
        ready: {
            rail: 'bg-cyan-300/70',
            badge: 'border-cyan-300/20 bg-cyan-300/[0.08] text-cyan-100',
            text: 'text-cyan-100',
        },
        warning: {
            rail: 'bg-amber-300/75',
            badge: 'border-amber-300/24 bg-amber-300/[0.08] text-amber-100',
            text: 'text-amber-100',
        },
        offline: {
            rail: 'bg-orange-300/80',
            badge: 'border-orange-300/24 bg-orange-300/[0.08] text-orange-100',
            text: 'text-orange-100',
        },
        pending: {
            rail: 'bg-slate-400/65',
            badge: 'border-white/10 bg-white/[0.04] text-slate-200',
            text: 'text-slate-200',
        },
        info: {
            rail: 'bg-blue-300/55',
            badge: 'border-blue-300/18 bg-blue-300/[0.06] text-blue-100',
            text: 'text-blue-100',
        },
    };

    return classes[tone];
}

function describeCheckTransition(check: BootCheck) {
    const prefix = `${check.shortLabel.toUpperCase()}`;

    if (check.state === 'ready') {
        return `${prefix} confirmed: ${check.detail}.`;
    }

    if (check.state === 'warning') {
        return `${prefix} degraded: ${check.detail}.`;
    }

    if (check.state === 'offline') {
        return `${prefix} unavailable: ${check.detail}.`;
    }

    return `${prefix} pending: ${check.detail}.`;
}

interface SystemBootOverlayProps {
    onStartupResolved?: () => void;
}

export default function SystemBootOverlay({ onStartupResolved }: SystemBootOverlayProps) {
    const pathname = usePathname();
    const apiBase = getApiBase();
    const [isVisible, setIsVisible] = useState(false);
    const [bootMode, setBootMode] = useState<BootMode>('startup');
    const [payload, setPayload] = useState<FullSystemStatusPayload | null>(null);
    const [fetchError, setFetchError] = useState<string | null>(null);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);
    const [startedAt, setStartedAt] = useState(() => Date.now());
    const [readyAt, setReadyAt] = useState<number | null>(null);
    const [visualProgress, setVisualProgress] = useState(12);
    const lastCheckSignatureRef = useRef<string>('');
    const requestInFlightRef = useRef(false);
    const retryCountRef = useRef(0);

    const model = useMemo(() => resolveBootConsoleModel(payload, fetchError), [payload, fetchError]);
    const terminalEntries = useMemo(() => logs.map(parseTerminalLogLine), [logs]);
    const terminalSummary = useMemo(() => ({
        ok: terminalEntries.filter((entry) => entry.tone === 'ready').length,
        warn: terminalEntries.filter((entry) => entry.tone === 'warning').length,
        fault: terminalEntries.filter((entry) => entry.tone === 'offline').length,
    }), [terminalEntries]);

    const appendLog = useCallback((line: string) => {
        setLogs((previous) => {
            const next = [...previous, formatLogLine(line)];
            return next.slice(-8);
        });
    }, []);

    const closeOverlay = useCallback(() => {
        if (typeof window !== 'undefined') {
            window.sessionStorage.setItem(SYSTEM_BOOT_SESSION_KEY, 'true');
        }
        onStartupResolved?.();
        setIsVisible(false);
    }, [onStartupResolved]);

    const copyDiagnostics = useCallback(() => {
        if (!payload) return;
        const diagData = JSON.stringify(payload, null, 2);
        void navigator.clipboard.writeText(diagData);
        appendLog('System diagnostics copied to clipboard.');
    }, [payload, appendLog]);

    const fetchStatus = useCallback(async (reason: 'poll' | 'retry' | 'manual-open' | 'startup-open' = 'poll') => {
        if (requestInFlightRef.current) {
            return;
        }

        requestInFlightRef.current = true;
        setIsRefreshing(true);
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 8000);

        try {
            const response = await fetch(`${apiBase}/system/boot-status`, {
                cache: 'no-store',
                signal: controller.signal,
            });

            if (!response.ok) {
                throw new Error(`Status surface returned ${response.status}`);
            }

            const nextPayload = await response.json() as FullSystemStatusPayload;
            setPayload(nextPayload);
            setFetchError(null);
            retryCountRef.current = 0;

            if (reason !== 'poll') {
                appendLog(reason === 'retry' ? 'Readiness checks retriggered.' : 'Health surface sampled successfully.');
            }
        } catch (error) {
            const message = error instanceof DOMException && error.name === 'AbortError'
                ? 'Initial health sample timed out'
                : error instanceof Error
                    ? error.message
                    : 'Unable to reach backend health surface';

            if ((reason === 'startup-open' || reason === 'retry') && retryCountRef.current < 3) {
                retryCountRef.current += 1;
                appendLog(`Health sample failed (${message}). Auto-retrying (${retryCountRef.current}/3)...`);
                window.setTimeout(() => {
                    requestInFlightRef.current = false;
                    void fetchStatus(reason);
                }, 1200 * retryCountRef.current);
            } else {
                setFetchError(message);
                appendLog(`Health surface request failed: ${message}.`);
            }
        } finally {
            window.clearTimeout(timeout);
            requestInFlightRef.current = false;
            setIsRefreshing(false);
        }
    }, [apiBase, appendLog]);

    useEffect(() => {
        if (pathname !== '/') {
            setIsVisible(false);
            return;
        }

        if (typeof window === 'undefined') {
            return;
        }

        const sessionBooted = window.sessionStorage.getItem(SYSTEM_BOOT_SESSION_KEY);
        if (sessionBooted) {
            setIsVisible(false);
            return;
        }

        setBootMode('startup');
        setStartedAt(Date.now());
        setPayload(null);
        setFetchError(null);
        setLogs([formatLogLine('Cold start detected. Launching operational readiness console.')]);
        setReadyAt(null);
        setVisualProgress(12);
        setIsVisible(true);
        void fetchStatus('startup-open');
    }, [fetchStatus, pathname]);

    useEffect(() => {
        const shouldPollStartup = bootMode === 'startup' && model.consoleState === 'BOOTING';
        const shouldPollManualInspection = bootMode === 'manual-inspection';

        if (pathname !== '/' || !isVisible || (!shouldPollStartup && !shouldPollManualInspection)) {
            return;
        }

        const interval = window.setInterval(() => {
            void fetchStatus('poll');
        }, 4000);

        return () => window.clearInterval(interval);
    }, [bootMode, fetchStatus, isVisible, model.consoleState, pathname]);

    useEffect(() => {
        if (typeof window === 'undefined') {
            return;
        }

        const handleManualOpen = () => {
            if (pathname !== '/') {
                return;
            }

            setBootMode('manual-inspection');
            setStartedAt(Date.now());
            setFetchError(null);
            setLogs([formatLogLine('Manual boot console inspection requested.')]);
            setIsVisible(true);
            void fetchStatus('manual-open');
        };

        window.addEventListener(OPEN_SYSTEM_BOOT_EVENT, handleManualOpen);
        return () => window.removeEventListener(OPEN_SYSTEM_BOOT_EVENT, handleManualOpen);
    }, [fetchStatus, pathname]);

    useEffect(() => {
        if (model.consoleState === 'READY' && payload) {
            setReadyAt((previous) => previous ?? Date.now());
            return;
        }

        setReadyAt(null);
    }, [model.consoleState, payload]);

    useEffect(() => {
        if (!isVisible) {
            return;
        }

        if (payload || fetchError || model.consoleState !== 'BOOTING') {
            setVisualProgress(model.progress);
            return;
        }

        setVisualProgress((current) => Math.max(current, model.progress));

        const interval = window.setInterval(() => {
            setVisualProgress((current) => {
                if (current >= 68) {
                    return current;
                }

                if (current < 24) {
                    return current + 4;
                }

                if (current < 40) {
                    return current + 3;
                }

                if (current < 56) {
                    return current + 2;
                }

                return current + 1;
            });
        }, 420);

        return () => window.clearInterval(interval);
    }, [fetchError, isVisible, model.consoleState, model.progress, payload]);

    useEffect(() => {
        if (!isVisible) {
            return;
        }

        const signature = JSON.stringify({
            state: model.consoleState,
            summary: model.summary,
            checks: model.checks.map((check) => `${check.key}:${check.state}:${check.detail}`),
        });

        if (signature === lastCheckSignatureRef.current) {
            return;
        }

        lastCheckSignatureRef.current = signature;

        const notableChecks = model.checks.filter((check) => check.state !== 'pending');
        const nextLines = [
            `${model.headline}.`,
            ...notableChecks.slice(0, 3).map(describeCheckTransition),
        ];

        setLogs((previous) => {
            const merged = [...previous, ...nextLines.map(formatLogLine)];
            return merged.slice(-8);
        });
    }, [isVisible, model]);

    useEffect(() => {
        if (!isVisible || bootMode !== 'startup' || model.consoleState !== 'READY' || readyAt === null) {
            return;
        }

        const minimumStartupDisplayMs = 2400;
        const resolvedStateHoldMs = 1200;
        const startupRemaining = Math.max(0, minimumStartupDisplayMs - (Date.now() - startedAt));
        const readyHoldRemaining = Math.max(0, resolvedStateHoldMs - (Date.now() - readyAt));
        const remaining = Math.max(startupRemaining, readyHoldRemaining);

        const timer = window.setTimeout(() => {
            closeOverlay();
        }, remaining);

        return () => window.clearTimeout(timer);
    }, [bootMode, closeOverlay, isVisible, model.consoleState, readyAt, startedAt]);

    if (pathname !== '/' || !isVisible) {
        return null;
    }

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                className="fixed inset-0 z-[9999] overflow-x-hidden overflow-y-auto bg-[radial-gradient(circle_at_top,rgba(25,74,112,0.28),transparent_32%),radial-gradient(circle_at_50%_40%,rgba(7,38,58,0.22),transparent_44%),linear-gradient(180deg,#020612_0%,#030816_48%,#02050d_100%)] text-white"
            >
                <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(86,131,167,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(86,131,167,0.06)_1px,transparent_1px)] bg-[size:72px_72px] opacity-30" />
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(1,3,10,0.42)_62%,rgba(1,3,10,0.86)_100%)]" />

                <div className="relative z-10 flex min-h-screen flex-col px-4 py-4 sm:px-6 sm:py-5 lg:px-10 lg:py-6">
                    <header className="flex flex-col gap-4 border border-white/8 bg-[#040a16]/80 px-5 py-4 text-[11px] uppercase tracking-[0.3em] text-slate-400 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
                        <div className="flex flex-wrap items-center gap-3">
                            <span className="font-heading text-[0.7rem] font-bold tracking-[0.38em] text-cyan-200/90">Operational Boot Console</span>
                            <span className="h-3 w-px bg-white/10" />
                            <span className={model.consoleState === 'READY' ? 'text-cyan-200' : model.consoleState === 'DEGRADED' ? 'text-amber-300' : model.consoleState === 'OFFLINE' ? 'text-orange-300' : 'text-slate-300'}>
                                {model.consoleState}
                            </span>
                            <span className="h-3 w-px bg-white/10" />
                            <span>{bootMode === 'manual-inspection' ? 'Manual Inspection' : 'Session Launch'}</span>
                        </div>
                        <div className="flex flex-wrap items-center gap-3 text-[10px]">
                            <span>{model.marketLabel}</span>
                            <span className="h-3 w-px bg-white/10" />
                            <span>Health Sample {model.timestampLabel}</span>
                        </div>
                    </header>

                    <main className="mx-auto flex w-full max-w-7xl flex-1 items-start py-5 lg:py-6">
                        <div className="grid w-full gap-8 lg:grid-cols-[minmax(0,1.2fr)_minmax(22rem,0.9fr)]">
                            <section className="flex flex-col gap-8">
                                <div className="max-w-3xl">
                            <div className="mb-5 flex items-center gap-3 text-[10px] uppercase tracking-[0.36em] text-cyan-200/70">
                                <span className="inline-block h-2 w-2 rounded-full bg-cyan-300/80" />
                                Horus Analytics Command Layer
                            </div>
                                    <div className="grid gap-6 lg:grid-cols-[auto_minmax(0,1fr)_14rem] lg:items-end">
                                        <div className="relative flex h-24 w-24 items-center justify-center border border-cyan-300/12 bg-[#06101c]/65 p-3 backdrop-blur-sm">
                                            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(46,196,255,0.12),transparent_70%)]" />
                                            <Image
                                                src="/android-chrome-192x192.png"
                                                alt="Horus Logo"
                                                width={74}
                                                height={76}
                                                className="relative h-auto w-full object-contain opacity-95"
                                            />
                                        </div>
                                        <div>
                                            <h1 className="font-heading text-4xl font-black uppercase tracking-[0.16em] text-white sm:text-5xl">
                                                {model.headline}
                                            </h1>
                                            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300/80 sm:text-base">
                                                {model.summary}
                                            </p>
                                        </div>
                                        <div className="justify-self-start border border-cyan-300/12 bg-[#07101d]/70 px-5 py-4 backdrop-blur-sm lg:justify-self-end">
                                            <div className="text-[10px] uppercase tracking-[0.34em] text-slate-500">Launch Progress</div>
                                            <div className="mt-2 font-heading text-5xl font-black text-cyan-100">{visualProgress}%</div>
                                        </div>
                                    </div>
                                </div>

                                <div className="border border-white/8 bg-[#040a16]/76 p-5 backdrop-blur-sm">
                                    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                                        <div>
                                            <div className="text-[10px] uppercase tracking-[0.35em] text-slate-500">Trading Operations Stack</div>
                                            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-[#0a1421]">
                                                <motion.div
                                                    className={model.consoleState === 'DEGRADED' ? 'h-full bg-[linear-gradient(90deg,#2ec4ff_0%,#f1b35f_100%)]' : model.consoleState === 'OFFLINE' ? 'h-full bg-[linear-gradient(90deg,#f08d57_0%,#ffbd8c_100%)]' : 'h-full bg-[linear-gradient(90deg,#2ec4ff_0%,#83d4f2_100%)]'}
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${visualProgress}%` }}
                                                    transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
                                                />
                                            </div>
                                        </div>
                                        <div className="text-[10px] uppercase tracking-[0.35em] text-slate-500">
                                            {model.entryMode === 'ready' ? 'Full entry authorized' : model.entryMode === 'degraded' ? 'Degraded entry authorized' : 'Entry withheld pending retry'}
                                        </div>
                                    </div>

                                    <div className="mt-6 grid gap-3">
                                        {model.checks.map((check) => {
                                            const Icon = CHECK_ICON_BY_KEY[check.key as keyof typeof CHECK_ICON_BY_KEY] || Activity;
                                            const toneClass = check.state === 'ready'
                                                ? 'border-cyan-300/18 bg-cyan-400/[0.06] text-cyan-100'
                                                : check.state === 'warning'
                                                    ? 'border-amber-300/18 bg-amber-300/[0.06] text-amber-100'
                                                    : check.state === 'offline'
                                                        ? 'border-orange-300/18 bg-orange-300/[0.06] text-orange-100'
                                                        : 'border-white/8 bg-white/[0.02] text-slate-100';
                                            const badgeClass = check.state === 'ready'
                                                ? 'text-cyan-200'
                                                : check.state === 'warning'
                                                    ? 'text-amber-200'
                                                    : check.state === 'offline'
                                                        ? 'text-orange-200'
                                                        : 'text-slate-400';

                                            return (
                                                <div key={check.key} className={`grid gap-3 border px-4 py-3 sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-center ${toneClass}`}>
                                                    <div className="flex h-10 w-10 items-center justify-center border border-current/20 bg-black/10">
                                                        <Icon className="h-4 w-4" />
                                                    </div>
                                                    <div className="min-w-0">
                                                        <div className="text-[11px] font-semibold uppercase tracking-[0.28em]">{check.label}</div>
                                                        <div className="mt-1 text-sm text-current/80">{check.detail}</div>
                                                    </div>
                                                    <div className={`text-[10px] font-bold uppercase tracking-[0.32em] ${badgeClass}`}>
                                                        {check.state}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                <div className="flex flex-wrap items-center gap-3">
                                    {model.entryMode !== 'blocked' && (
                                        <button
                                            type="button"
                                            onClick={closeOverlay}
                                            className="group inline-flex items-center gap-3 border border-cyan-300/20 bg-cyan-300/[0.08] px-6 py-3 text-[11px] font-black uppercase tracking-[0.28em] text-cyan-50 transition hover:bg-cyan-300/[0.14]"
                                        >
                                            {model.entryMode === 'ready' ? 'Enter System' : 'Enter Degraded'}
                                            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                                        </button>
                                    )}

                                    <button
                                        type="button"
                                        onClick={() => void fetchStatus('retry')}
                                        className="inline-flex items-center gap-3 border border-white/10 bg-white/[0.04] px-5 py-3 text-[11px] font-black uppercase tracking-[0.28em] text-slate-200 transition hover:bg-white/[0.08]"
                                    >
                                        <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                                        Retry Checks
                                    </button>

                                    <button
                                        type="button"
                                        onClick={copyDiagnostics}
                                        className="inline-flex items-center gap-2 border border-white/10 bg-white/[0.04] px-5 py-3 text-[11px] font-black uppercase tracking-[0.28em] text-slate-200 transition hover:bg-white/[0.08]"
                                    >
                                        Copy Diagnostics
                                    </button>

                                    <a
                                        href="/status"
                                        className="inline-flex items-center gap-3 border border-white/8 px-5 py-3 text-[11px] font-black uppercase tracking-[0.28em] text-slate-300 transition hover:border-cyan-300/20 hover:text-white"
                                    >
                                        Open Full Status
                                    </a>
                                </div>
                            </section>

                            <section className="grid gap-6 self-stretch">
                                <div className="border border-white/8 bg-[#040a16]/82 p-5 backdrop-blur-sm">
                                    <div className="flex items-center justify-between gap-3">
                                        <div>
                                            <div className="text-[10px] uppercase tracking-[0.35em] text-slate-500">Operational Summary</div>
                                            <div className="mt-2 text-lg font-semibold text-white">Readiness Grid</div>
                                        </div>
                                        <div className="text-[10px] uppercase tracking-[0.3em] text-slate-500">{model.timestampLabel}</div>
                                    </div>
                                    <div className="mt-5 grid grid-cols-2 gap-3">
                                        {model.metrics.map((metric) => (
                                            <div key={metric.label} className="border border-white/6 bg-white/[0.02] px-4 py-3">
                                                <div className="text-[10px] uppercase tracking-[0.3em] text-slate-500">{metric.label}</div>
                                                <div className={`mt-2 text-base font-semibold ${metric.tone === 'support' ? 'text-cyan-100' : metric.tone === 'warning' ? 'text-amber-200' : 'text-slate-100'}`}>
                                                    {metric.value}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="flex min-h-[16rem] flex-col border border-white/8 bg-[#040a16]/82 p-5 backdrop-blur-sm lg:min-h-[18rem]">
                                    <div className="border-b border-white/6 pb-4">
                                        <div className="flex items-center justify-between gap-3">
                                            <div className="flex items-center gap-3">
                                                <div className="flex gap-2">
                                                    <span className="h-2.5 w-2.5 rounded-full bg-[#b25c5a]" />
                                                    <span className="h-2.5 w-2.5 rounded-full bg-[#d2a15a]" />
                                                    <span className="h-2.5 w-2.5 rounded-full bg-[#4bb7c9]" />
                                                </div>
                                                <div>
                                                    <div className="text-[10px] uppercase tracking-[0.35em] text-slate-400">Terminal Log</div>
                                                    <div className="mt-1 text-[10px] uppercase tracking-[0.22em] text-slate-600">{terminalEntries.length} retained entries</div>
                                                </div>
                                            </div>
                                            <div className="text-[10px] uppercase tracking-[0.28em] text-slate-500">
                                                {isRefreshing ? 'Sampling' : 'Stable'}
                                            </div>
                                        </div>

                                        <div className="mt-4 grid grid-cols-3 overflow-hidden border border-white/6 bg-slate-950/30">
                                            <div className="border-r border-white/6 px-3 py-2">
                                                <div className="text-[8px] font-black uppercase tracking-[0.22em] text-slate-600">OK</div>
                                                <div className="mt-1 font-mono text-sm font-black text-cyan-100">{terminalSummary.ok}</div>
                                            </div>
                                            <div className="border-r border-white/6 px-3 py-2">
                                                <div className="text-[8px] font-black uppercase tracking-[0.22em] text-slate-600">Warn</div>
                                                <div className="mt-1 font-mono text-sm font-black text-amber-100">{terminalSummary.warn}</div>
                                            </div>
                                            <div className="px-3 py-2">
                                                <div className="text-[8px] font-black uppercase tracking-[0.22em] text-slate-600">Fault</div>
                                                <div className="mt-1 font-mono text-sm font-black text-orange-100">{terminalSummary.fault}</div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-4 flex-1 space-y-2 overflow-auto pr-1 font-mono text-[12px]">
                                        {terminalEntries.map((entry) => {
                                            const toneClasses = getTerminalToneClasses(entry.tone);

                                            return (
                                                <div
                                                    key={entry.id}
                                                    className="grid gap-2 border border-white/6 bg-white/[0.018] px-3 py-3 sm:grid-cols-[4.8rem_4.6rem_minmax(5.5rem,0.7fr)_minmax(0,1fr)] sm:items-start"
                                                >
                                                    <div className="flex items-center gap-2 text-slate-500">
                                                        <span className={`h-8 w-1 flex-none rounded-full ${toneClasses.rail}`} />
                                                        <time className="text-[10px] uppercase tracking-[0.14em]">{entry.time}</time>
                                                    </div>
                                                    <span className={`w-fit border px-2 py-1 text-[9px] font-black uppercase tracking-[0.16em] ${toneClasses.badge}`}>
                                                        {entry.status}
                                                    </span>
                                                    <span className="truncate text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                                                        {entry.source}
                                                    </span>
                                                    <span className={`leading-5 ${toneClasses.text}`}>
                                                        {entry.message}
                                                    </span>
                                                </div>
                                            );
                                        })}
                                    </div>

                                    <div className="mt-4 border-t border-white/6 pt-4">
                                        <div className="flex items-start gap-3">
                                            {model.consoleState === 'DEGRADED' || model.consoleState === 'OFFLINE' ? (
                                                <TriangleAlert className="mt-0.5 h-4 w-4 flex-none text-amber-300" />
                                            ) : (
                                                <Siren className="mt-0.5 h-4 w-4 flex-none text-cyan-200" />
                                            )}
                                            <div>
                                                <div className="text-[10px] uppercase tracking-[0.32em] text-slate-500">Primary Issue</div>
                                                <div className="mt-2 text-sm leading-6 text-slate-200">
                                                    {model.primaryIssue || 'No blocking issues detected. Entry authorization aligned.'}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>
                        </div>
                    </main>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
