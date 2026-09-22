'use client';

import type { ReactNode } from 'react';

import { clsx } from 'clsx';
import { AlertTriangle, Cpu } from 'lucide-react';
import { CommandHeader } from '@/app/components/custom/CommandHeader';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';

import { formatTimeSince, getStreamStatus, isStale } from '@/utils/telemetry';

export type OptimizationMode = 'OPTIMIZER' | 'SIMULATOR' | 'PINE_LAB';

type UiMessage = {
    type: 'error' | 'success';
    text: string;
} | null;

type OptimizationShellProps = {
    mode: OptimizationMode;
    onSelectMode: (mode: OptimizationMode) => void;
    uiMessage: UiMessage;
    children: ReactNode;
    wsConnected?: boolean;
    lastUpdated?: Date | null;
};

export function OptimizationShell({ mode, onSelectMode, uiMessage, children, wsConnected, lastUpdated = null }: OptimizationShellProps) {
    const streamInfo = getStreamStatus(wsConnected);
    const syncTime = formatTimeSince(lastUpdated);
    const syncStale = isStale(lastUpdated);

    return (
        <div className="page-shell page-shell-wide text-white">
            {uiMessage && (
                <div
                    className={clsx(
                        'mb-6 flex items-center gap-2 rounded-xl border px-4 py-3 text-sm',
                        uiMessage.type === 'error'
                            ? 'border-rose-500/40 bg-rose-500/10 text-rose-300'
                            : 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                    )}
                >
                    <AlertTriangle className="h-4 w-4" />
                    <span>{uiMessage.text}</span>
                </div>
            )}

            <CommandHeader
                eyebrow="Lab Environment"
                title="Strategy Lab"
                description="Parametric synthesis, optimization telemetry, and Pine strategy research inside one controlled command surface."
                icon={<Cpu className="h-8 w-8" />}
                statusItems={[
                    streamInfo,
                    { label: 'Sync', value: syncTime, tone: syncStale ? 'warning' : 'muted' },
                    { label: 'Mode', value: mode, tone: 'primary' },
                    { label: 'Auth', value: 'Ready', tone: 'muted' },
                ]}
                actions={
                    <div
                        role="group"
                        aria-label="Strategy Lab mode"
                        className="grid w-full grid-cols-1 gap-2 min-[380px]:grid-cols-2 sm:grid-cols-3 lg:min-w-[24rem]"
                    >
                        <IndustrialButton
                            type="button"
                            variant={mode === 'SIMULATOR' ? 'primary' : 'secondary'}
                            className="w-full min-w-0 px-3"
                            onClick={() => onSelectMode('SIMULATOR')}
                            aria-pressed={mode === 'SIMULATOR'}
                        >
                            Backtester
                        </IndustrialButton>
                        <IndustrialButton
                            type="button"
                            variant={mode === 'OPTIMIZER' ? 'primary' : 'secondary'}
                            className="w-full min-w-0 px-3"
                            onClick={() => onSelectMode('OPTIMIZER')}
                            aria-pressed={mode === 'OPTIMIZER'}
                        >
                            AI Optimizer
                        </IndustrialButton>
                        <IndustrialButton
                            type="button"
                            variant={mode === 'PINE_LAB' ? 'primary' : 'secondary'}
                            className="w-full min-w-0 px-3"
                            onClick={() => onSelectMode('PINE_LAB')}
                            aria-pressed={mode === 'PINE_LAB'}
                        >
                            Pine Lab
                        </IndustrialButton>
                    </div>
                }
            />

            {children}
        </div>
    );
}
