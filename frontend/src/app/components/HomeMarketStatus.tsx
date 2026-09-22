import { useEffect, useMemo, useState } from 'react';
import useSWR from 'swr';
import clsx from 'clsx';

import { swrFetcher } from '@/lib/api';

export function HomeMarketStatus() {
    const { data: simData } = useSWR('/api/v1/simulate/status', swrFetcher, {
        refreshInterval: 10000,
        revalidateOnFocus: true,
    });

    const [now, setNow] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setNow(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    const time = useMemo(() => {
        if (simData?.active && simData?.date) {
            const simDate = new Date(simData.date);
            simDate.setHours(now.getHours(), now.getMinutes(), now.getSeconds());
            return simDate;
        }

        return now;
    }, [simData, now]);

    const simulationActive = Boolean(simData?.active);
    const hour = time.getHours();
    const minute = time.getMinutes();
    const day = time.getDay();

    const isWeekend = day === 5 || day === 6;
    const isWorkDay = !isWeekend;
    const isMarketHours = isWorkDay && (
        (hour > 10 || (hour === 10 && minute >= 0)) &&
        (hour < 14 || (hour === 14 && minute <= 30))
    );

    return (
        <div className="flex items-center space-x-6">
            <div className="text-right hidden md:block">
                <p className="text-[10px] text-slate-500 font-semibold tracking-[0.2em] uppercase">
                    {simulationActive ? 'Simulation Clock' : 'Telemetry Time'}
                </p>
                <p
                    className={clsx(
                        'text-sm font-medium font-mono tabular-nums',
                        simulationActive ? 'text-amber-400' : 'text-white/90',
                    )}
                    suppressHydrationWarning
                >
                    {simulationActive ? time.toLocaleDateString() : time.toLocaleTimeString()}
                </p>
            </div>
            <div
                className={clsx(
                    'flex items-center space-x-3 px-4 py-2 rounded-2xl border   transition-all duration-300',
                    isMarketHours ? 'bg-emerald-500/10 border-emerald-500/20    ' : 'bg-white/5 border-white/10',
                )}
            >
                <span className="relative flex h-2 w-2">
                    {isMarketHours && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />}
                    <span className={clsx('relative inline-flex rounded-full h-2 w-2', isMarketHours ? 'bg-emerald-500' : 'bg-slate-500')} />
                </span>
                <span className={clsx('text-[10px] font-bold tracking-widest uppercase', isMarketHours ? 'text-emerald-400' : 'text-slate-400')}>
                    {isMarketHours ? 'Market Active' : 'Market Standby'}
                </span>
            </div>
        </div>
    );
}
