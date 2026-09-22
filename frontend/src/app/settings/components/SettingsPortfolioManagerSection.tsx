'use client';

import React from 'react';
import { BriefcaseBusiness } from 'lucide-react';

import type { SettingsState } from '../hooks/useSettingsRuntime';

interface SettingsPortfolioManagerSectionProps {
    settings: SettingsState;
    onChange: (key: string, value: number | string | boolean) => void;
}

const FieldGroup = ({
    label,
    desc,
    children,
}: {
    label: string;
    desc: string;
    children: React.ReactNode;
}) => (
    <div className="mb-5">
        <label className="block text-sm font-medium text-gray-300 mb-1">{label}</label>
        <p className="text-xs text-gray-500 mb-2">{desc}</p>
        {children}
    </div>
);

export function SettingsPortfolioManagerSection({
    settings,
    onChange,
}: SettingsPortfolioManagerSectionProps) {
    return (
        <div className="section-surface p-6 rounded-xl">
            <div className="flex items-center mb-6">
                <BriefcaseBusiness className="h-5 w-5 text-cyan-300 mr-2" />
                <h2 className="text-xl font-bold">Portfolio Manager Controls</h2>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <FieldGroup label="Default Include Positions" desc="Default report size in the manager modal">
                    <input
                        type="number"
                        min={1}
                        max={100}
                        value={settings.PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS ?? ''}
                        onChange={(e) => onChange('PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                        className="control-input w-full focus:border-cyan-500"
                    />
                </FieldGroup>

                <FieldGroup label="Telegram Chunk Size" desc="Max characters per Telegram report chunk">
                    <input
                        type="number"
                        min={500}
                        max={4096}
                        value={settings.PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN ?? ''}
                        onChange={(e) => onChange('PORTFOLIO_MGMT_TELEGRAM_CHUNK_MAX_LEN', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                        className="control-input w-full focus:border-cyan-500"
                    />
                </FieldGroup>
            </div>

            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 mb-4">
                <div>
                    <span className="block text-sm font-medium">Default Refresh Prices</span>
                    <span className="text-xs text-gray-500">Refresh prices by default before generating manager reports</span>
                </div>
                <input
                    type="checkbox"
                    checked={Boolean(settings.PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES)}
                    onChange={(e) => onChange('PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES', e.target.checked)}
                    className="h-5 w-5 accent-cyan-500"
                />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <FieldGroup label="Action Preview Limit" desc="Rows shown in manager action panel">
                    <input
                        type="number"
                        min={1}
                        max={100}
                        value={settings.PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT ?? ''}
                        onChange={(e) => onChange('PORTFOLIO_MGMT_ACTION_ITEMS_PREVIEW_LIMIT', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                        className="control-input w-full focus:border-cyan-500"
                    />
                </FieldGroup>
                <FieldGroup label="Report Action Limit" desc="Action items included in Telegram report">
                    <input
                        type="number"
                        min={1}
                        max={100}
                        value={settings.PORTFOLIO_MGMT_REPORT_ACTION_ITEMS_LIMIT ?? ''}
                        onChange={(e) => onChange('PORTFOLIO_MGMT_REPORT_ACTION_ITEMS_LIMIT', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                        className="control-input w-full focus:border-cyan-500"
                    />
                </FieldGroup>
                <FieldGroup label="Risk Rec Limit" desc="Risk recommendations included in Telegram report">
                    <input
                        type="number"
                        min={1}
                        max={100}
                        value={settings.PORTFOLIO_MGMT_REPORT_RISK_RECOMMENDATIONS_LIMIT ?? ''}
                        onChange={(e) => onChange('PORTFOLIO_MGMT_REPORT_RISK_RECOMMENDATIONS_LIMIT', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                        className="control-input w-full focus:border-cyan-500"
                    />
                </FieldGroup>
                <FieldGroup label="TP2 % From TP1" desc="Percent extension used to derive TP2 from TP1">
                    <input
                        type="number"
                        step="0.1"
                        min={0}
                        value={settings.PORTFOLIO_MGMT_TP2_PCT ?? ''}
                        onChange={(e) => onChange('PORTFOLIO_MGMT_TP2_PCT', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-cyan-500"
                    />
                </FieldGroup>
                <FieldGroup label="Drawdown Trigger %" desc="Trigger reduce-risk review at this unrealized drawdown">
                    <input
                        type="number"
                        step="0.1"
                        min={0}
                        value={settings.PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT ?? ''}
                        onChange={(e) => onChange('PORTFOLIO_MGMT_REDUCE_RISK_DRAWDOWN_PCT', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-cyan-500"
                    />
                </FieldGroup>
                <FieldGroup label="TP1 Proximity Trigger %" desc="Trigger prepare-TP action when within this distance to TP1">
                    <input
                        type="number"
                        step="0.1"
                        min={0}
                        value={settings.PORTFOLIO_MGMT_PREPARE_TP_PROXIMITY_PCT ?? ''}
                        onChange={(e) => onChange('PORTFOLIO_MGMT_PREPARE_TP_PROXIMITY_PCT', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-cyan-500"
                    />
                </FieldGroup>
            </div>
        </div>
    );
}
