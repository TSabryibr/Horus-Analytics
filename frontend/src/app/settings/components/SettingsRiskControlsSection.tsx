'use client';

import React from 'react';
import { Shield } from 'lucide-react';

import type { SettingsState } from '../hooks/useSettingsRuntime';

interface SettingsRiskControlsSectionProps {
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
    <div className="mb-6">
        <label className="block text-sm font-medium text-gray-300 mb-1">{label}</label>
        <p className="text-xs text-gray-500 mb-2">{desc}</p>
        {children}
    </div>
);

export function SettingsRiskControlsSection({
    settings,
    onChange,
}: SettingsRiskControlsSectionProps) {
    const executionTag = !settings.AUTO_TRADE_ENABLED
        ? 'AUTO_OFF'
        : !settings.SIGNAL_AUTO_EXECUTION_ENABLED
            ? 'SIGNAL_EXEC_OFF'
        : settings.LIVE_ARM_GUARD_ENABLED
            ? 'MANUAL_ARM'
            : 'AUTO_ENTRY';
    const executionDetail = executionTag === 'SIGNAL_EXEC_OFF'
        ? 'Execution monitor will skip signal entries until Signal Auto Execution is enabled.'
        : executionTag === 'AUTO_OFF'
            ? 'Automated entries and exits are disabled.'
            : executionTag === 'MANUAL_ARM'
                ? 'Live entries require a daily manual arm before execution.'
                : 'Valid signals can route through risk gates automatically.';

    return (
        <div className="section-surface p-6 rounded-xl">
            <div className="flex items-center mb-6">
                <Shield className="h-5 w-5 text-red-400 mr-2" />
                <h2 className="text-xl font-bold">Risk Controls</h2>
            </div>

            <div className="mb-6 rounded-xl border border-cyan-500/20 bg-cyan-500/[0.06] p-4">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <div>
                        <p className="meta-label text-slate-500">Live Execution Gate</p>
                        <p className="mt-1 text-sm text-slate-300">Current policy: <span className="font-mono text-cyan-100">{executionTag}</span></p>
                        <p className="mt-1 text-xs leading-5 text-slate-500">{executionDetail}</p>
                    </div>
                    <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 font-mono text-[10px] font-black uppercase tracking-[0.2em] text-cyan-100">
                        {executionTag}
                    </span>
                </div>

                <div className="grid gap-3 md:grid-cols-3">
                    <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                        <div>
                            <span className="block text-sm font-medium">Auto Trading</span>
                            <span className="text-xs text-gray-500">Enable automated entries and exits</span>
                        </div>
                        <input
                            type="checkbox"
                            checked={Boolean(settings.AUTO_TRADE_ENABLED)}
                            onChange={(e) => onChange('AUTO_TRADE_ENABLED', e.target.checked)}
                            className="h-5 w-5 accent-red-500"
                        />
                    </div>

                    <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                        <div>
                            <span className="block text-sm font-medium">Signal Auto Execution</span>
                            <span className="text-xs text-gray-500">Allow scheduled signal runs to open live entries after risk gates pass</span>
                        </div>
                        <input
                            type="checkbox"
                            checked={Boolean(settings.SIGNAL_AUTO_EXECUTION_ENABLED)}
                            onChange={(e) => onChange('SIGNAL_AUTO_EXECUTION_ENABLED', e.target.checked)}
                            className="h-5 w-5 accent-orange-500"
                        />
                    </div>

                    <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                        <div>
                            <span className="block text-sm font-medium">Require Daily Manual Arm</span>
                            <span className="text-xs text-gray-500">Pause live entries until execution is manually armed for the day</span>
                        </div>
                        <input
                            type="checkbox"
                            checked={Boolean(settings.LIVE_ARM_GUARD_ENABLED)}
                            onChange={(e) => onChange('LIVE_ARM_GUARD_ENABLED', e.target.checked)}
                            className="h-5 w-5 accent-red-500"
                        />
                    </div>
                </div>
            </div>

            <FieldGroup label="Stop Loss %" desc="Fixed percentage stop loss">
                <input
                    type="number"
                    step="0.1"
                    value={settings.SL_PCT ?? ''}
                    onChange={(e) => onChange('SL_PCT', e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="control-input w-full focus:border-red-500"
                />
            </FieldGroup>

            <FieldGroup label="Slippage %" desc="Simulated execution cost per trade">
                <input
                    type="number"
                    step="0.1"
                    value={settings.SLIPPAGE_PCT ?? ''}
                    onChange={(e) => onChange('SLIPPAGE_PCT', e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="control-input w-full focus:border-yellow-500"
                />
            </FieldGroup>

            <FieldGroup label="Commission %" desc="Per-side commission model">
                <input
                    type="number"
                    step="0.01"
                    value={settings.COMMISSION_PCT ?? ''}
                    onChange={(e) => onChange('COMMISSION_PCT', e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="control-input w-full focus:border-yellow-500"
                />
            </FieldGroup>

            <FieldGroup label="Take Profit %" desc="Target 1 percentage">
                <input
                    type="number"
                    step="0.1"
                    value={settings.TP1_PCT ?? ''}
                    onChange={(e) => onChange('TP1_PCT', e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="control-input w-full focus:border-green-500"
                />
            </FieldGroup>

            <FieldGroup label="Min Turnover (EGP)" desc="Filter out low liquidity stocks">
                <input
                    type="number"
                    step="100000"
                    value={settings.MIN_TURNOVER ?? ''}
                    onChange={(e) => onChange('MIN_TURNOVER', e.target.value === '' ? '' : parseInt(e.target.value))}
                    className="control-input w-full focus:border-purple-500"
                />
            </FieldGroup>

            <div className="grid grid-cols-2 gap-4">
                <FieldGroup label="Max Positions" desc="Global position limit">
                    <input
                        type="number"
                        value={settings.MAX_POSITIONS ?? ''}
                        onChange={(e) => onChange('MAX_POSITIONS', e.target.value === '' ? '' : parseInt(e.target.value))}
                        className="control-input w-full focus:border-red-500"
                    />
                </FieldGroup>
                <FieldGroup label="Risk %" desc="Risk per trade">
                    <input
                        type="number"
                        step="0.1"
                        value={settings.RISK_PER_TRADE ?? ''}
                        onChange={(e) => onChange('RISK_PER_TRADE', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-red-500"
                    />
                </FieldGroup>
            </div>

            <FieldGroup label="Min Risk/Reward" desc="Block setups below this reward-to-risk floor">
                <input
                    type="number"
                    step="0.1"
                    value={settings.MIN_RISK_REWARD ?? ''}
                    onChange={(e) => onChange('MIN_RISK_REWARD', e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="control-input w-full focus:border-red-500"
                />
            </FieldGroup>

            <div className="grid grid-cols-3 gap-4">
                <FieldGroup label="Max Daily Trades" desc="Entry velocity cap per portfolio/day">
                    <input
                        type="number"
                        min={1}
                        value={settings.MAX_DAILY_TRADES ?? ''}
                        onChange={(e) => onChange('MAX_DAILY_TRADES', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                        className="control-input w-full focus:border-orange-500"
                    />
                </FieldGroup>
                <FieldGroup label="Max Portfolio Heat %" desc="Block new entries when risk exposure is too high">
                    <input
                        type="number"
                        step="0.1"
                        value={settings.MAX_PORTFOLIO_HEAT ?? ''}
                        onChange={(e) => onChange('MAX_PORTFOLIO_HEAT', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-orange-500"
                    />
                </FieldGroup>
                <FieldGroup label="Pending Gap Cap %" desc="Skip next-open entries when gap exceeds this level">
                    <input
                        type="number"
                        step="0.1"
                        value={settings.PENDING_ENTRY_MAX_GAP_PCT ?? ''}
                        onChange={(e) => onChange('PENDING_ENTRY_MAX_GAP_PCT', e.target.value === '' ? '' : parseFloat(e.target.value))}
                        className="control-input w-full focus:border-orange-500"
                    />
                </FieldGroup>
            </div>

            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 mb-4">
                <div>
                    <span className="block text-sm font-medium">Use ATR Exits</span>
                    <span className="text-xs text-gray-500">Dynamic SL/TP based on volatility</span>
                </div>
                <input
                    type="checkbox"
                    checked={Boolean(settings.USE_ATR_EXITS)}
                    onChange={(e) => onChange('USE_ATR_EXITS', e.target.checked)}
                    className="h-5 w-5 accent-purple-500"
                />
            </div>

            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 mb-4">
                <div>
                    <span className="block text-sm font-medium">Heat Protection</span>
                    <span className="text-xs text-gray-500">Block new entries when portfolio heat exceeds the limit</span>
                </div>
                <input
                    type="checkbox"
                    checked={Boolean(settings.HEAT_PROTECTION_ENABLED)}
                    onChange={(e) => onChange('HEAT_PROTECTION_ENABLED', e.target.checked)}
                    className="h-5 w-5 accent-orange-500"
                />
            </div>

            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 mb-4">
                <div>
                    <span className="block text-sm font-medium">Trailing Stop</span>
                    <span className="text-xs text-gray-500">Move stop-loss with favorable price action</span>
                </div>
                <input
                    type="checkbox"
                    checked={Boolean(settings.TRAILING_STOP_ENABLED)}
                    onChange={(e) => onChange('TRAILING_STOP_ENABLED', e.target.checked)}
                    className="h-5 w-5 accent-cyan-500"
                />
            </div>

            {settings.TRAILING_STOP_ENABLED && (
                <div className="grid grid-cols-2 gap-4 p-3 bg-cyan-500/5 rounded-lg border border-cyan-500/10 mb-4">
                    <FieldGroup label="Trailing Type" desc="Trailing model">
                        <select
                            value={String(settings.TRAILING_STOP_TYPE || 'FIXED')}
                            onChange={(e) => onChange('TRAILING_STOP_TYPE', e.target.value)}
                            className="control-input w-full focus:border-cyan-500"
                        >
                            <option value="FIXED">FIXED</option>
                            <option value="PERCENT">PERCENT</option>
                            <option value="ATR">ATR</option>
                        </select>
                    </FieldGroup>
                    <FieldGroup label="Trailing Value" desc="Percent or ATR multiplier by selected type">
                        <input
                            type="number"
                            step="0.1"
                            value={settings.TRAILING_STOP_VALUE ?? ''}
                            onChange={(e) => onChange('TRAILING_STOP_VALUE', e.target.value === '' ? '' : parseFloat(e.target.value))}
                            className="control-input w-full focus:border-cyan-500"
                        />
                    </FieldGroup>
                </div>
            )}

            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 mb-4">
                <div>
                    <span className="block text-sm font-medium">Regime Filter</span>
                    <span className="text-xs text-gray-500">Apply macro-regime gating to new entries</span>
                </div>
                <input
                    type="checkbox"
                    checked={Boolean(settings.REGIME_FILTER_ENABLED)}
                    onChange={(e) => onChange('REGIME_FILTER_ENABLED', e.target.checked)}
                    className="h-5 w-5 accent-emerald-500"
                />
            </div>

            {settings.REGIME_FILTER_ENABLED && (
                <FieldGroup label="Regime Mode" desc="Override or auto-detect regime stance">
                    <select
                        value={String(settings.REGIME_MODE || 'AUTO')}
                        onChange={(e) => onChange('REGIME_MODE', e.target.value)}
                        className="control-input w-full focus:border-emerald-500"
                    >
                        <option value="AUTO">AUTO</option>
                        <option value="BULLISH">BULLISH</option>
                        <option value="CAUTIOUS">CAUTIOUS</option>
                        <option value="BEARISH">BEARISH</option>
                    </select>
                </FieldGroup>
            )}

            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 mb-4">
                <div>
                    <span className="block text-sm font-medium">Sector Limit</span>
                    <span className="text-xs text-gray-500">Restrict concentration in any single sector</span>
                </div>
                <input
                    type="checkbox"
                    checked={Boolean(settings.SECTOR_LIMIT_ENABLED)}
                    onChange={(e) => onChange('SECTOR_LIMIT_ENABLED', e.target.checked)}
                    className="h-5 w-5 accent-violet-500"
                />
            </div>

            {settings.SECTOR_LIMIT_ENABLED && (
                <FieldGroup label="Max Per Sector" desc="Maximum open positions per sector">
                    <input
                        type="number"
                        min={1}
                        value={settings.MAX_PER_SECTOR ?? ''}
                        onChange={(e) => onChange('MAX_PER_SECTOR', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                        className="control-input w-full focus:border-violet-500"
                    />
                </FieldGroup>
            )}

            {settings.USE_ATR_EXITS && (
                <div className="grid grid-cols-2 gap-4 p-3 bg-purple-500/5 rounded-lg border border-purple-500/10">
                    <FieldGroup label="ATR TP Mult." desc="Target multiplier">
                        <input
                            type="number"
                            step="0.1"
                            value={settings.ATR_TP_MULTIPLIER ?? ''}
                            onChange={(e) => onChange('ATR_TP_MULTIPLIER', e.target.value === '' ? '' : parseFloat(e.target.value))}
                            className="control-input w-full focus:border-purple-500"
                        />
                    </FieldGroup>
                    <FieldGroup label="ATR SL Mult." desc="Stop multiplier">
                        <input
                            type="number"
                            step="0.1"
                            value={settings.ATR_SL_MULTIPLIER ?? ''}
                            onChange={(e) => onChange('ATR_SL_MULTIPLIER', e.target.value === '' ? '' : parseFloat(e.target.value))}
                            className="control-input w-full focus:border-purple-500"
                        />
                    </FieldGroup>
                </div>
            )}
        </div>
    );
}
