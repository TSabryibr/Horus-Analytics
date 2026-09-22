'use client';

import clsx from 'clsx';
import { RefreshCw, X } from 'lucide-react';

type ConfigForm = {
    auto_intraday: boolean;
    auto_daily: boolean;
    auto_horus_eye: boolean;
    auto_ai_daily_report: boolean;
    auto_weekly_report: boolean;
    auto_monthly_report: boolean;
};

type TelegramConfigModalProps = {
    isOpen: boolean;
    sending: boolean;
    configForm: ConfigForm;
    setConfigForm: (next: ConfigForm) => void;
    onClose: () => void;
    onSubmit: (event: React.FormEvent) => void | Promise<void>;
};

function ToggleRow({
    label,
    checked,
    onChange,
}: {
    label: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
}) {
    return (
        <label className="group flex cursor-pointer items-center justify-between rounded-xl border border-white/5 bg-black/20 p-3 transition-colors hover:border-white/10">
            <span className="text-xs font-bold text-slate-300 group-hover:text-white">{label}</span>
            <div
                className={clsx(
                    'relative flex h-5 w-10 items-center rounded-full p-1 transition-colors duration-200 ease-in-out',
                    checked ? 'bg-emerald-500' : 'bg-slate-700'
                )}
            >
                <div
                    className={clsx(
                        'absolute h-3 w-3 rounded-full bg-white transition-transform duration-200 ease-in-out',
                        checked ? 'translate-x-5' : 'translate-x-0'
                    )}
                />
            </div>
            <input
                type="checkbox"
                className="hidden"
                checked={checked}
                onChange={(event) => onChange(event.target.checked)}
            />
        </label>
    );
}

export function TelegramConfigModal({
    isOpen,
    sending,
    configForm,
    setConfigForm,
    onClose,
    onSubmit,
}: TelegramConfigModalProps) {
    if (!isOpen) {
        return null;
    }

    return (
        <div
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4"
            role="dialog"
            aria-modal="true"
            aria-label="Telegram configuration"
        >
            <div className="section-surface w-full max-w-md animate-in zoom-in-95 overflow-hidden rounded-[2rem] duration-200">
                <div className="flex items-center justify-between border-b border-white/5 bg-gradient-to-r from-blue-500/10 to-transparent p-8">
                    <div>
                        <h3 className="text-xl font-black uppercase tracking-tighter text-blue-400">Secure Uplink</h3>
                        <p className="font-mono text-xs text-gray-500">TELEGRAM_GATEWAY v4.0</p>
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        className="text-gray-500 transition hover:text-white"
                        aria-label="Close telegram configuration"
                    >
                        <X size={20} />
                    </button>
                </div>
                <form onSubmit={onSubmit} className="space-y-6 p-8">
                    <div className="space-y-4">
                        <div className="space-y-4">
                            <p className="text-[10px] font-black uppercase tracking-widest text-gray-500">Automation Toggles</p>

                            <ToggleRow
                                label="Broadcast Intraday Scans"
                                checked={configForm.auto_intraday}
                                onChange={(checked) => setConfigForm({ ...configForm, auto_intraday: checked })}
                            />
                            <ToggleRow
                                label="Broadcast Daily Close"
                                checked={configForm.auto_daily}
                                onChange={(checked) => setConfigForm({ ...configForm, auto_daily: checked })}
                            />
                            <ToggleRow
                                label="Horus Eye High Conviction (Score 8+)"
                                checked={configForm.auto_horus_eye}
                                onChange={(checked) => setConfigForm({ ...configForm, auto_horus_eye: checked })}
                            />
                            <ToggleRow
                                label="AI Daily Report Dispatch"
                                checked={configForm.auto_ai_daily_report}
                                onChange={(checked) => setConfigForm({ ...configForm, auto_ai_daily_report: checked })}
                            />
                            <ToggleRow
                                label="Weekly Analysis Report Dispatch"
                                checked={configForm.auto_weekly_report}
                                onChange={(checked) => setConfigForm({ ...configForm, auto_weekly_report: checked })}
                            />
                            <ToggleRow
                                label="Monthly Analysis Report Dispatch"
                                checked={configForm.auto_monthly_report}
                                onChange={(checked) => setConfigForm({ ...configForm, auto_monthly_report: checked })}
                            />
                        </div>
                    </div>
                    <button
                        type="submit"
                        disabled={sending}
                        className="action-primary w-full !bg-blue-600 py-4 hover:!bg-blue-500 disabled:opacity-50"
                    >
                        {sending ? <RefreshCw className="mx-auto animate-spin" /> : 'Establish Connection'}
                    </button>
                </form>
            </div>
        </div>
    );
}
