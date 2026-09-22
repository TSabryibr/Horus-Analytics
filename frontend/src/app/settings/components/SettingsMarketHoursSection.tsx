'use client';

import React from 'react';
import clsx from 'clsx';
import { Clock } from 'lucide-react';

import type { SettingsState } from '../hooks/useSettingsRuntime';

interface SettingsMarketHoursSectionProps {
    settings: SettingsState;
    onChange: (key: string, value: string | number | boolean) => void;
}

const FieldGroup = ({
    label,
    desc,
    id,
    children,
}: {
    label: string;
    desc: string;
    id?: string;
    children: React.ReactNode;
}) => (
    <div className="mb-6">
        <label htmlFor={id} className="block text-sm font-medium text-gray-300 mb-1">{label}</label>
        <p className="text-xs text-gray-500 mb-2">{desc}</p>
        {children}
    </div>
);

export function SettingsMarketHoursSection({
    settings,
    onChange,
}: SettingsMarketHoursSectionProps) {
    return (
        <div className="section-surface p-6 rounded-xl md:col-span-2">
            <div className="flex items-center mb-6">
                <div className="p-2 bg-amber-500/20 rounded-lg mr-2">
                    <Clock className="h-5 w-5 text-amber-400" />
                </div>
                <div>
                    <h2 className="text-xl font-bold">Market Hours</h2>
                    <p className="text-xs text-gray-400">Configure EGX trading session times. Scan schedules automatically adjust.</p>
                </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 mb-6">
                <div>
                    <span className="block text-sm font-medium">Ramadan Mode</span>
                    <span className="text-xs text-gray-500">Enable shortened Ramadan session hours</span>
                </div>
                <input
                    type="checkbox"
                    checked={Boolean(settings.RAMADAN_MODE)}
                    onChange={(e) => onChange('RAMADAN_MODE', e.target.checked)}
                    className="h-5 w-5 accent-amber-500"
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className={clsx('p-4 rounded-lg border', !settings.RAMADAN_MODE ? 'bg-amber-500/5 border-amber-500/20' : 'bg-white/5 border-white/10 opacity-60')}>
                    <h3 className="text-sm font-semibold text-amber-300 mb-4">Normal Session</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <FieldGroup label="Open (HHMM)" desc="e.g. 1000 = 10:00">
                            <input
                                type="text"
                                maxLength={4}
                                value={settings.MARKET_START_HHMM_NORMAL || ''}
                                onChange={(e) => onChange('MARKET_START_HHMM_NORMAL', e.target.value.replace(/\D/g, '').slice(0, 4))}
                                className="control-input w-full focus:border-amber-500 font-mono text-center"
                                placeholder="1000"
                            />
                        </FieldGroup>
                        <FieldGroup label="Close (HHMM)" desc="e.g. 1430 = 14:30">
                            <input
                                type="text"
                                maxLength={4}
                                value={settings.MARKET_END_HHMM_NORMAL || ''}
                                onChange={(e) => onChange('MARKET_END_HHMM_NORMAL', e.target.value.replace(/\D/g, '').slice(0, 4))}
                                className="control-input w-full focus:border-amber-500 font-mono text-center"
                                placeholder="1430"
                            />
                        </FieldGroup>
                    </div>
                </div>

                <div className={clsx('p-4 rounded-lg border', settings.RAMADAN_MODE ? 'bg-amber-500/5 border-amber-500/20' : 'bg-white/5 border-white/10 opacity-60')}>
                    <h3 className="text-sm font-semibold text-amber-300 mb-4">Ramadan Session</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <FieldGroup label="Open (HHMM)" desc="e.g. 1000 = 10:00">
                            <input
                                type="text"
                                maxLength={4}
                                value={settings.MARKET_START_HHMM_RAMADAN || ''}
                                onChange={(e) => onChange('MARKET_START_HHMM_RAMADAN', e.target.value.replace(/\D/g, '').slice(0, 4))}
                                className="control-input w-full focus:border-amber-500 font-mono text-center"
                                placeholder="1000"
                            />
                        </FieldGroup>
                        <FieldGroup label="Close (HHMM)" desc="e.g. 1330 = 13:30">
                            <input
                                type="text"
                                maxLength={4}
                                value={settings.MARKET_END_HHMM_RAMADAN || ''}
                                onChange={(e) => onChange('MARKET_END_HHMM_RAMADAN', e.target.value.replace(/\D/g, '').slice(0, 4))}
                                className="control-input w-full focus:border-amber-500 font-mono text-center"
                                placeholder="1330"
                            />
                        </FieldGroup>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6 pt-6 border-t border-white/5">
                <FieldGroup id="pre-close-offset" label="Pre-Close Offset (min)" desc="Runs X min before close">
                    <input
                        id="pre-close-offset"
                        type="number"
                        value={settings.PRE_CLOSE_OFFSET_MINS ?? ''}
                        onChange={(e) => onChange('PRE_CLOSE_OFFSET_MINS', e.target.value === '' ? '' : parseInt(e.target.value))}
                        className="control-input w-full focus:border-amber-500"
                    />
                </FieldGroup>
                <FieldGroup id="daily-signal-offset" label="Daily Signal Offset (min)" desc="Runs X min after close">
                    <input
                        id="daily-signal-offset"
                        type="number"
                        value={settings.DAILY_SIGNAL_OFFSET_MINS ?? ''}
                        onChange={(e) => onChange('DAILY_SIGNAL_OFFSET_MINS', e.target.value === '' ? '' : parseInt(e.target.value))}
                        className="control-input w-full focus:border-amber-500"
                    />
                </FieldGroup>
                <FieldGroup id="intraday-interval" label="Intraday Interval (min)" desc="Frequency of intraday scans">
                    <input
                        id="intraday-interval"
                        type="number"
                        value={settings.INTRADAY_INTERVAL_MINS ?? ''}
                        onChange={(e) => onChange('INTRADAY_INTERVAL_MINS', e.target.value === '' ? '' : parseInt(e.target.value))}
                        className="control-input w-full focus:border-amber-500"
                    />
                </FieldGroup>
            </div>

            <p className="text-xs text-gray-500 mt-4">
                <strong>Pre-Close</strong> signal runs {settings.PRE_CLOSE_OFFSET_MINS || 20} min before close · <strong>Daily Signal</strong> runs {settings.DAILY_SIGNAL_OFFSET_MINS || 30} min after close · <strong>Intraday</strong> checks every {settings.INTRADAY_INTERVAL_MINS || 5} min during session
            </p>
        </div>
    );
}
