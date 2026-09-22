'use client';

import { useState } from 'react';
import { Calendar, Clock, X } from 'lucide-react';
import clsx from 'clsx';
import { usePolling } from '@/hooks/usePolling';
import { getBaseUrl, isIgnorableNetworkError } from '@/lib/api';

export default function SimulationBanner() {
    const [status, setStatus] = useState<{ active: boolean; date: string | null }>({ active: false, date: null });
    const [loading, setLoading] = useState(true);
    const [isTransitioning, setIsTransitioning] = useState(false);

    const apiBase = getBaseUrl();

    const fetchStatus = async () => {
        try {
            const res = await fetch(`${apiBase}/api/v1/simulate/status`);
            const data = await res.json();
            setStatus(data);
        } catch (e) {
            if (isIgnorableNetworkError(e)) {
                return;
            }
            console.error("Simulation Status Error:", e);
        } finally {
            setLoading(false);
        }
    };

    usePolling(fetchStatus, { intervalMs: 10_000, runImmediately: true, pauseWhenHidden: true });

    const stopSimulation = async () => {
        setIsTransitioning(true);
        try {
            const res = await fetch(`${apiBase}/api/v1/simulate/stop`, { method: 'POST' });
            if (res.ok) {
                setStatus({ active: false, date: null });
                if (typeof window !== 'undefined') {
                    window.sessionStorage.removeItem('horus.dashboard.cache.v1');
                }
                window.location.reload(); // Reload to refresh all data in all tabs
            }
        } catch (e) {
            if (isIgnorableNetworkError(e)) {
                return;
            }
            console.error("Stop Simulation Error:", e);
        } finally {
            setIsTransitioning(false);
        }
    };

    const changeDate = async (newDate: string) => {
        setIsTransitioning(true);
        try {
            const res = await fetch(`${apiBase}/api/v1/simulate/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date: newDate })
            });
            if (res.ok) {
                setStatus({ active: true, date: newDate });
                if (typeof window !== 'undefined') {
                    window.sessionStorage.removeItem('horus.dashboard.cache.v1');
                }
                window.location.reload(); // Reload to refresh all data
            }
        } catch (e) {
            if (isIgnorableNetworkError(e)) {
                return;
            }
            console.error("Change Simulation Date Error:", e);
        } finally {
            setIsTransitioning(false);
        }
    };

    if (loading || !status.active) return null;

    return (
        <div
            className={clsx(
                "sticky top-[var(--chrome-nav-height)] z-[105] w-full border-b border-amber-400/20 bg-slate-950/[0.78] px-4 py-2.5 backdrop-blur-xl transition-all duration-300 sm:px-6",
                isTransitioning && "pointer-events-none opacity-50"
            )}
        >
            <div className="mx-auto flex w-full max-w-[1700px] items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <div className="rounded-xl border border-amber-400/25 bg-amber-500/10 p-2.5 shadow-[0_10px_30px_rgba(245,158,11,0.12)]">
                        <Clock className="h-4 w-4 text-amber-500" />
                    </div>
                    <div>
                        <span className="text-[10px] font-black uppercase tracking-[0.32em] text-amber-300">Time Travel Active</span>
                        <p className="text-sm font-medium text-white">
                            Viewing market state as of <span className="font-bold text-amber-300">{status.date}</span>
                        </p>
                    </div>
                </div>

                <div className="flex flex-wrap items-center justify-end gap-3">
                    <div className="group relative">
                        <input
                            type="date"
                            value={status.date || ''}
                            onChange={(e) => changeDate(e.target.value)}
                            className="cursor-pointer rounded-xl border border-amber-400/20 bg-slate-900/70 px-4 py-2 text-xs font-black tracking-[0.2em] text-amber-100 outline-none transition focus:border-amber-400/50"
                        />
                        <Calendar className="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-amber-500/50 transition-colors group-hover:text-amber-400" />
                    </div>

                    <button
                        onClick={stopSimulation}
                        className="flex items-center gap-2 rounded-xl border border-amber-400/30 bg-amber-500 px-4 py-2 text-[10px] font-black uppercase tracking-[0.22em] text-slate-950 transition-transform hover:scale-[1.02] hover:bg-amber-400 active:scale-95"
                    >
                        <X className="h-3 w-3 stroke-[3]" />
                        Exit Simulation
                    </button>
                </div>
            </div>
        </div>
    );
}
