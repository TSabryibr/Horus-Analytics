'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { CalendarDays, Plus, RefreshCw, Trash2, Upload } from 'lucide-react';

type HolidayRecord = {
    id: number;
    date: string;
    description: string;
    created_at?: string | null;
};

interface SettingsHolidayCalendarSectionProps {
    apiBase: string;
    onMessage: (message: string) => void;
}

const currentYear = new Date().getFullYear();

const parseBulkHolidays = (raw: string, fallbackDescription: string) => {
    const rows = raw
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);

    return rows.map((line) => {
        const match = line.match(/^(\d{4}-\d{2}-\d{2})(?:[\s,;|-]+(.+))?$/);
        if (!match) {
            throw new Error(`Invalid holiday row: ${line}`);
        }
        return {
            date: match[1],
            description: (match[2] || fallbackDescription || 'EGX market holiday').trim(),
        };
    });
};

export function SettingsHolidayCalendarSection({
    apiBase,
    onMessage,
}: SettingsHolidayCalendarSectionProps) {
    const [holidays, setHolidays] = useState<HolidayRecord[]>([]);
    const [loading, setLoading] = useState(false);
    const [date, setDate] = useState('');
    const [description, setDescription] = useState('EGX market holiday');
    const [bulkText, setBulkText] = useState('');

    const upcoming = useMemo(
        () => holidays.filter((holiday) => holiday.date >= new Date().toISOString().slice(0, 10)).slice(0, 6),
        [holidays]
    );

    const loadHolidays = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${apiBase}/api/v1/system/holidays?start_date=${currentYear}-01-01&end_date=${currentYear + 1}-12-31`);
            if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
            const data = await res.json();
            setHolidays(Array.isArray(data?.holidays) ? data.holidays : []);
        } catch {
            onMessage('Could not load market holidays.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        void loadHolidays();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [apiBase]);

    const saveHoliday = async () => {
        if (!date) {
            onMessage('Choose a holiday date first.');
            return;
        }
        setLoading(true);
        try {
            const res = await fetch(`${apiBase}/api/v1/system/holidays`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date, description }),
            });
            if (!res.ok) throw new Error(await res.text());
            setDate('');
            onMessage('Market holiday saved.');
            await loadHolidays();
        } catch {
            onMessage('Could not save market holiday.');
        } finally {
            setLoading(false);
        }
    };

    const importBulk = async () => {
        let parsed: Array<{ date: string; description: string }>;
        try {
            parsed = parseBulkHolidays(bulkText, description);
        } catch (error) {
            onMessage(error instanceof Error ? error.message : 'Invalid holiday import.');
            return;
        }
        if (parsed.length === 0) {
            onMessage('Paste at least one holiday date.');
            return;
        }

        setLoading(true);
        try {
            const res = await fetch(`${apiBase}/api/v1/system/holidays`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ holidays: parsed }),
            });
            if (!res.ok) throw new Error(await res.text());
            setBulkText('');
            onMessage(`${parsed.length} market holiday${parsed.length === 1 ? '' : 's'} imported.`);
            await loadHolidays();
        } catch {
            onMessage('Could not import market holidays.');
        } finally {
            setLoading(false);
        }
    };

    const deleteHoliday = async (holidayDate: string) => {
        setLoading(true);
        try {
            const res = await fetch(`${apiBase}/api/v1/system/holidays/${holidayDate}`, { method: 'DELETE' });
            if (!res.ok) throw new Error(await res.text());
            onMessage('Market holiday removed.');
            await loadHolidays();
        } catch {
            onMessage('Could not remove market holiday.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="section-surface rounded-xl p-6 md:col-span-2">
            <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="flex items-center">
                    <div className="mr-2 rounded-lg bg-emerald-500/20 p-2">
                        <CalendarDays className="h-5 w-5 text-emerald-300" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold">Market Holidays</h2>
                        <p className="text-xs text-gray-400">Maintain EGX closure dates used by scanning, live mode, freshness, and trade monitoring.</p>
                    </div>
                </div>
                <button
                    type="button"
                    onClick={loadHolidays}
                    disabled={loading}
                    className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-white/[0.08] disabled:opacity-50"
                    title="Refresh holidays"
                >
                    <RefreshCw className="h-4 w-4" />
                    Refresh
                </button>
            </div>

            <div className="grid gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
                <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
                    <p className="mb-4 text-sm font-semibold text-emerald-200">Add single holiday</p>
                    <div className="grid gap-3 sm:grid-cols-[10rem_minmax(0,1fr)]">
                        <input
                            type="date"
                            value={date}
                            onChange={(event) => setDate(event.target.value)}
                            className="control-input w-full focus:border-emerald-500"
                        />
                        <input
                            type="text"
                            value={description}
                            onChange={(event) => setDescription(event.target.value)}
                            className="control-input w-full focus:border-emerald-500"
                            placeholder="Holiday description"
                        />
                    </div>
                    <button
                        type="button"
                        onClick={saveHoliday}
                        disabled={loading}
                        className="mt-4 inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
                    >
                        <Plus className="h-4 w-4" />
                        Save Holiday
                    </button>

                    <div className="mt-6 border-t border-white/10 pt-5">
                        <p className="mb-2 text-sm font-semibold text-emerald-200">Bulk import</p>
                        <textarea
                            value={bulkText}
                            onChange={(event) => setBulkText(event.target.value)}
                            className="control-input min-h-32 w-full resize-y focus:border-emerald-500"
                            placeholder={'2026-06-16 Eid holiday\n2026-07-23 Revolution Day'}
                        />
                        <button
                            type="button"
                            onClick={importBulk}
                            disabled={loading}
                            className="mt-3 inline-flex items-center justify-center gap-2 rounded-lg border border-emerald-400/30 bg-emerald-400/10 px-4 py-2 text-sm font-bold text-emerald-200 hover:bg-emerald-400/15 disabled:opacity-50"
                        >
                            <Upload className="h-4 w-4" />
                            Import Dates
                        </button>
                    </div>
                </div>

                <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
                    <div className="mb-4 flex items-center justify-between">
                        <p className="text-sm font-semibold text-emerald-200">Registered holidays</p>
                        <span className="rounded-full border border-white/10 px-2 py-1 font-mono text-xs text-slate-400">{holidays.length}</span>
                    </div>
                    <div className="max-h-80 space-y-2 overflow-y-auto pr-1">
                        {holidays.length === 0 ? (
                            <p className="rounded-lg border border-dashed border-white/10 p-4 text-sm text-slate-500">No holidays registered for this window.</p>
                        ) : holidays.map((holiday) => (
                            <div key={holiday.date} className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-slate-950/30 px-3 py-2">
                                <div className="min-w-0">
                                    <p className="font-mono text-sm text-white">{holiday.date}</p>
                                    <p className="truncate text-xs text-slate-500">{holiday.description || 'EGX market holiday'}</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => deleteHoliday(holiday.date)}
                                    disabled={loading}
                                    className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-red-400/20 text-red-300 hover:bg-red-400/10 disabled:opacity-50"
                                    title={`Remove ${holiday.date}`}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                    <div className="mt-5 border-t border-white/10 pt-4">
                        <p className="mb-3 text-xs font-black uppercase tracking-[0.22em] text-slate-500">Upcoming</p>
                        <div className="flex flex-wrap gap-2">
                            {upcoming.length === 0 ? (
                                <span className="text-xs text-slate-500">No upcoming registered closures.</span>
                            ) : upcoming.map((holiday) => (
                                <span key={`upcoming-${holiday.date}`} className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 font-mono text-xs text-emerald-200">
                                    {holiday.date}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
