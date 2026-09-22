'use client';

import React from 'react';
import clsx from 'clsx';

import type { OllamaResult } from '../hooks/useSettingsActions';
import type { SettingsState } from '../hooks/useSettingsRuntime';

interface SettingsAiProvidersSectionProps {
    settings: SettingsState;
    ollamaSaving: boolean;
    ollamaTesting: boolean;
    ollamaResult: OllamaResult | null;
    onChange: (key: string, value: string) => void;
    onSaveOllamaSettings: () => void | Promise<void>;
    onTestOllamaSettings: () => void | Promise<void>;
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

export function SettingsAiProvidersSection({
    settings,
    ollamaSaving,
    ollamaTesting,
    ollamaResult,
    onChange,
    onSaveOllamaSettings,
    onTestOllamaSettings,
}: SettingsAiProvidersSectionProps) {
    return (
        <div className="grid grid-cols-1 gap-6 mt-6">
            <FieldGroup label="Ollama (Local LLM)" desc="Used for local AI report generation">
                <div className="space-y-2">
                    <label className="block text-xs font-semibold text-slate-300" htmlFor="pine-import-translation-provider">
                        Pine Logic Import Translator
                    </label>
                    <select
                        id="pine-import-translation-provider"
                        aria-label="Pine Logic Import Translator"
                        value={String(settings.PINE_IMPORT_TRANSLATION_PROVIDER || 'LOCAL').toUpperCase()}
                        onChange={(e) => onChange('PINE_IMPORT_TRANSLATION_PROVIDER', e.target.value)}
                        className="control-input w-full focus:border-blue-500 text-sm"
                    >
                        <option value="LOCAL">Local deterministic draft</option>
                        <option value="OLLAMA">Ollama-assisted translation</option>
                    </select>
                    <p className="text-xs text-gray-500">
                        Deterministic local draft is still the default. Switch to Ollama only when you want AI-assisted Pine logic mapping during import preview.
                    </p>
                    <input
                        type="text"
                        value={settings.OLLAMA_BASE_URL || ''}
                        onChange={(e) => onChange('OLLAMA_BASE_URL', e.target.value)}
                        className="control-input w-full focus:border-blue-500 font-mono text-sm"
                        placeholder="http://127.0.0.1:11434"
                    />
                    <input
                        type="text"
                        value={settings.AI_REPORT_OLLAMA_MODEL || ''}
                        onChange={(e) => onChange('AI_REPORT_OLLAMA_MODEL', e.target.value)}
                        className="control-input w-full focus:border-blue-500 font-mono text-sm"
                        placeholder="qwen3-coder:30b"
                    />
                    <input
                        type="password"
                        value={settings.OLLAMA_API_KEY || ''}
                        onChange={(e) => onChange('OLLAMA_API_KEY', e.target.value)}
                        className="control-input w-full focus:border-blue-500 font-mono text-sm"
                        placeholder="Optional bearer token"
                    />
                    {settings.OLLAMA_API_KEY_CONFIGURED ? (
                        <p className="font-mono text-[10px] font-black uppercase tracking-[0.18em] text-cyan-300">
                            Configured: {settings.OLLAMA_API_KEY_PREVIEW || '[set]'}
                        </p>
                    ) : null}
                    <div className="flex items-center gap-2">
                        <button
                            type="button"
                            onClick={() => {
                                void onSaveOllamaSettings();
                            }}
                            disabled={ollamaSaving || ollamaTesting}
                            className="action-secondary px-3 py-2 text-xs whitespace-nowrap"
                        >
                            {ollamaSaving ? 'Saving...' : 'Save'}
                        </button>
                        <button
                            type="button"
                            onClick={() => {
                                void onTestOllamaSettings();
                            }}
                            disabled={ollamaSaving || ollamaTesting}
                            className="action-primary !bg-blue-600 hover:!bg-blue-500 px-3 py-2 text-xs whitespace-nowrap"
                        >
                            {ollamaTesting ? 'Testing...' : 'Test'}
                        </button>
                    </div>
                    {ollamaResult && (
                        <p aria-live="polite" className={clsx('text-xs mt-2', ollamaResult.ok ? 'text-emerald-400' : 'text-red-400')}>
                            {ollamaResult.message}
                        </p>
                    )}
                </div>
            </FieldGroup>
        </div>
    );
}
