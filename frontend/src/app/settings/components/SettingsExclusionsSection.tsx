'use client';

import React from 'react';
import { Shield } from 'lucide-react';

interface SettingsExclusionsSectionProps {
    excluded: string[];
    newExclusion: string;
    autocompleteOptions: string[];
    onInputChange: (value: string) => void;
    onAddExclusion: (tickerToAdd?: string) => void;
    onRemoveExclusion: (ticker: string) => void;
}

export function SettingsExclusionsSection({
    excluded,
    newExclusion,
    autocompleteOptions,
    onInputChange,
    onAddExclusion,
    onRemoveExclusion,
}: SettingsExclusionsSectionProps) {
    return (
        <div className="section-surface p-6 rounded-xl md:col-span-2">
            <div className="flex items-center mb-6">
                <div className="p-2 bg-red-500/20 rounded-lg mr-2">
                    <Shield className="h-5 w-5 text-red-400" />
                </div>
                <div>
                    <h2 className="text-xl font-bold">Blacklisted Tickers</h2>
                    <p className="text-xs text-gray-400">Permanently exclude these stocks from all scanners.</p>
                </div>
            </div>

            <div className="space-y-4">
                <div className="relative">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={newExclusion}
                            onChange={(e) => onInputChange(e.target.value.toUpperCase())}
                            onKeyDown={(e) => e.key === 'Enter' && onAddExclusion(newExclusion)}
                            placeholder="Search Ticker to Blacklist..."
                            className="control-input flex-1 focus:border-red-500"
                        />
                        {autocompleteOptions.length > 0 && (
                            <div className="absolute top-full left-0 w-full bg-[#1A1A2E] border border-white/10 rounded-b-lg z-50 max-h-40 overflow-y-auto">
                                {autocompleteOptions.map((ticker) => (
                                    <div
                                        key={ticker}
                                        onClick={() => {
                                            onAddExclusion(ticker);
                                        }}
                                        className="px-4 py-2 hover:bg-white/10 cursor-pointer text-sm text-gray-300 hover:text-white"
                                    >
                                        {ticker}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex flex-wrap gap-2">
                    {excluded.map((ticker) => (
                        <span key={ticker} className="flex items-center bg-red-500/20 text-red-300 px-3 py-1 rounded-full text-sm border border-red-500/30">
                            {ticker}
                            <button onClick={() => onRemoveExclusion(ticker)} className="ml-2 hover:text-white">
                                x
                            </button>
                        </span>
                    ))}
                    {excluded.length === 0 && <span className="text-gray-500 text-sm italic">No exclusions set.</span>}
                </div>
            </div>
        </div>
    );
}
