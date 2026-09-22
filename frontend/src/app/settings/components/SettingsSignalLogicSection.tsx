'use client';

import React from 'react';
import { Activity } from 'lucide-react';

import type { SettingsState } from '../hooks/useSettingsRuntime';

interface SettingsSignalLogicSectionProps {
    settings: SettingsState;
    onChange: (key: string, value: number | string) => void;
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

export function SettingsSignalLogicSection({
    settings,
    onChange,
}: SettingsSignalLogicSectionProps) {
    return (
        <div className="section-surface p-6 rounded-xl">
            <div className="flex items-center mb-6">
                <Activity className="h-5 w-5 text-blue-400 mr-2" />
                <h2 className="text-xl font-bold">Signal Logic</h2>
            </div>

            <FieldGroup id="signal-lookback" label="Signal Lookback" desc="Breakout resistance lookback window in trading days">
                <input
                    id="signal-lookback"
                    type="number"
                    value={settings.LOOKBACK ?? ''}
                    onChange={(e) => onChange('LOOKBACK', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                    className="control-input w-full focus:border-blue-500"
                />
            </FieldGroup>

            <FieldGroup label="RSI Thresholds (Min / Max)" desc="Relative Strength Index entry zone (30-100)">
                <div className="flex space-x-4">
                    <input
                        type="number"
                        value={settings.RSI_MIN ?? ''}
                        onChange={(e) => onChange('RSI_MIN', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-blue-500"
                    />
                    <input
                        type="number"
                        value={settings.RSI_MAX ?? ''}
                        onChange={(e) => onChange('RSI_MAX', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-blue-500"
                    />
                </div>
            </FieldGroup>

            <FieldGroup label="Momentum %" desc="Minimum daily change required to trigger">
                <input
                    type="number"
                    step="0.1"
                    value={settings.MOMENTUM ?? ''}
                    onChange={(e) => onChange('MOMENTUM', e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="control-input w-full focus:border-blue-500"
                />
            </FieldGroup>

            <FieldGroup label="Volume Spike (> Avg)" desc="Multiplier of 20-day Average Volume (e.g. 1.5x)">
                <input
                    type="number"
                    step="0.1"
                    value={settings.VOL_SPIKE ?? ''}
                    onChange={(e) => onChange('VOL_SPIKE', e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="control-input w-full focus:border-blue-500"
                />
            </FieldGroup>

            <div className="grid grid-cols-2 gap-4">
                <FieldGroup label="Min Signal Score" desc="Drop recommendations below this score">
                    <input
                        type="number"
                        step="0.1"
                        min={0}
                        max={10}
                        value={settings.MIN_SIGNAL_SCORE ?? ''}
                        onChange={(e) => onChange('MIN_SIGNAL_SCORE', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-blue-500"
                    />
                </FieldGroup>
                <FieldGroup label="Min Confidence %" desc="Drop recommendations below this confidence level">
                    <input
                        type="number"
                        step="0.1"
                        min={0}
                        max={100}
                        value={settings.MIN_SIGNAL_CONFIDENCE ?? ''}
                        onChange={(e) => onChange('MIN_SIGNAL_CONFIDENCE', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-blue-500"
                    />
                </FieldGroup>
            </div>

            <div className="grid grid-cols-3 gap-4">
                <FieldGroup label="Trickster RSI Max" desc="Oversold cap for mean-reversion setup">
                    <input
                        type="number"
                        step="0.1"
                        value={settings.TRICKSTER_RSI_MAX ?? ''}
                        onChange={(e) => onChange('TRICKSTER_RSI_MAX', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-blue-500"
                    />
                </FieldGroup>
                <FieldGroup label="Trickster Rel Vol Min" desc="Minimum relative volume for Trickster">
                    <input
                        type="number"
                        step="0.1"
                        value={settings.TRICKSTER_REL_VOL_MIN ?? ''}
                        onChange={(e) => onChange('TRICKSTER_REL_VOL_MIN', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-blue-500"
                    />
                </FieldGroup>
                <FieldGroup label="Trickster Stretch ATR" desc="Required EMA stretch in ATR units">
                    <input
                        type="number"
                        step="0.1"
                        value={settings.TRICKSTER_STRETCH_ATR ?? ''}
                        onChange={(e) => onChange('TRICKSTER_STRETCH_ATR', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-blue-500"
                    />
                </FieldGroup>
            </div>
        </div>
    );
}
