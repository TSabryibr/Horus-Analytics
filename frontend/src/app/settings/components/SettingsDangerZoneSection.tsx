'use client';

import { AlertTriangle, RefreshCw } from 'lucide-react';

interface SettingsDangerZoneSectionProps {
    saving: boolean;
    operationLoading: boolean;
    onHardReset: () => void | Promise<void>;
}

export function SettingsDangerZoneSection({
    saving,
    operationLoading,
    onHardReset,
}: SettingsDangerZoneSectionProps) {
    const busy = saving || operationLoading;

    return (
        <div className="section-surface rounded-[1.75rem] border border-orange-500/30 p-6">
            <div className="flex items-center gap-3">
                <div className="rounded-xl bg-orange-500/15 p-2">
                    <AlertTriangle className="h-5 w-5 text-orange-300" />
                </div>
                <div>
                    <h3 className="text-xl font-bold text-orange-100">Hard reset corridor</h3>
                    <p className="text-xs uppercase tracking-[0.24em] text-orange-300/70">Irreversible system operation</p>
                </div>
            </div>

            <div className="mt-5 flex flex-col gap-5 rounded-[1.25rem] border border-orange-500/20 bg-orange-500/[0.06] p-5 xl:flex-row xl:items-center xl:justify-between">
                <div className="max-w-3xl">
                    <p className="text-sm leading-7 text-slate-300">
                        This action destroys the local <code className="rounded bg-black/30 px-1 py-0.5 text-xs">horus.db</code> store plus cached market data files. Use it only when you intend to rebuild the stack from zero.
                    </p>
                </div>
                <button
                    type="button"
                    onClick={() => {
                        void onHardReset();
                    }}
                    disabled={busy}
                    className="action-primary rounded-xl !bg-orange-500 px-5 py-3 text-xs font-black uppercase tracking-[0.24em] !text-slate-950 hover:!bg-orange-400 disabled:opacity-50"
                >
                    {busy ? <RefreshCw className="mr-2 inline h-4 w-4 animate-spin" /> : <AlertTriangle className="mr-2 inline h-4 w-4" />}
                    Hard Reset Data
                </button>
            </div>
        </div>
    );
}
