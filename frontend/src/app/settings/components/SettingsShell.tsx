'use client';

import React, { useState, useEffect } from 'react';
import clsx from 'clsx';

import { SettingsCommandDeckHeader } from './SettingsCommandDeckHeader';
import { SettingsDiffModal } from './SettingsDiffModal';
import { SettingsState, SignalDeskPolicyState } from '../hooks/useSettingsRuntime';

interface SettingsShellProps {
    loading: boolean;
    message: string;
    saving: boolean;
    hasChanges: boolean;
    onSave: () => void | Promise<void>;
    settings?: SettingsState;
    originalSettings?: SettingsState;
    excluded?: string[];
    originalExcluded?: string[];
    signalDeskPolicy?: SignalDeskPolicyState;
    originalSignalDeskPolicy?: SignalDeskPolicyState;
    children: React.ReactNode;
}

export function SettingsShell({
    loading,
    message,
    saving,
    hasChanges,
    onSave,
    settings,
    originalSettings,
    excluded,
    originalExcluded,
    signalDeskPolicy,
    originalSignalDeskPolicy,
    children,
}: SettingsShellProps) {
    const [isDiffModalOpen, setIsDiffModalOpen] = useState(false);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
                e.preventDefault();
                if (hasChanges && !saving) {
                    setIsDiffModalOpen(true);
                }
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [hasChanges, saving]);

    if (loading) {
        return <div className="page-shell page-shell-wide text-white">Loading configuration...</div>;
    }

    return (
        <div className="page-shell page-shell-wide text-white">
            <div className="mx-auto flex max-w-[96rem] flex-col gap-8">
                <SettingsCommandDeckHeader
                    saving={saving}
                    hasChanges={hasChanges}
                    message={message}
                    settings={settings}
                    onSave={() => setIsDiffModalOpen(true)}
                />

                {message ? (
                    <div
                        className={clsx(
                            'rounded-[1.25rem] border px-4 py-3 text-sm',
                            /failed|error/i.test(message)
                                ? 'border-orange-500/30 bg-orange-500/10 text-orange-100'
                                : 'border-cyan-500/20 bg-cyan-500/10 text-cyan-50'
                        )}
                    >
                        {message}
                    </div>
                ) : null}

                {children}
            </div>

            <SettingsDiffModal
                isOpen={isDiffModalOpen}
                onClose={() => setIsDiffModalOpen(false)}
                onConfirm={onSave}
                saving={saving}
                settings={settings}
                originalSettings={originalSettings}
                excluded={excluded}
                originalExcluded={originalExcluded}
                signalDeskPolicy={signalDeskPolicy}
                originalSignalDeskPolicy={originalSignalDeskPolicy}
            />
        </div>
    );
}
