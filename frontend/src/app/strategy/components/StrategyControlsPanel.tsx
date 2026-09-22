import { CheckCircle, RefreshCw, Settings } from 'lucide-react';
import clsx from 'clsx';

import { StrategyProposal } from '@/types/domain';
import { defaultManualParams } from '../lib/strategyTransforms';

type ManualParams = typeof defaultManualParams;
type ManualParamKey = keyof ManualParams;

type StrategyControlsPanelProps = {
    applying: boolean;
    manualMode: boolean;
    manualParams: ManualParams;
    onApply: () => void;
    onManualParamChange: (key: ManualParamKey, value: number) => void;
    proposal: Pick<StrategyProposal, 'changes'> | null;
};

export function StrategyControlsPanel({
    applying,
    manualMode,
    manualParams,
    onApply,
    onManualParamChange,
    proposal,
}: StrategyControlsPanelProps) {
    const hasChangedProposal = proposal?.changes?.some((change) => change.changed);

    return (
        <div className="section-surface industrial-corner rounded-xl p-6 flex flex-col">
            <h3 className="text-lg font-bold text-slate-100 flex items-center mb-6">
                <Settings className="w-5 h-5 mr-2 text-slate-400" />
                {manualMode ? 'Manual Overrides' : 'Proposed Laws (Parameters)'}
            </h3>

            {manualMode ? (
                <div className="flex-1 space-y-5">
                    {Object.entries(manualParams).map(([key, value]) => (
                        <div key={key} className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400 font-mono">{key.replace('_', ' ')}</span>
                                <span className="text-white font-bold">{value}</span>
                            </div>
                            <input
                                type="range"
                                min={key.includes('RSI') ? 20 : key.includes('PCT') ? 0.5 : 0.5}
                                max={key.includes('RSI') ? 100 : key.includes('PCT') ? 10 : 5}
                                step={key.includes('RSI') ? 1 : 0.1}
                                value={value}
                                onChange={(e) => onManualParamChange(key as ManualParamKey, parseFloat(e.target.value))}
                                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
                            />
                        </div>
                    ))}
                </div>
            ) : (
                <div className="flex-1 space-y-3">
                    {proposal?.changes?.map((change, idx) => (
                        <div
                            key={`${change.parameter}-${idx}`}
                            className="flex justify-between items-center p-3 rounded-lg border border-white/10 bg-slate-950/50"
                        >
                            <div className="text-sm font-medium text-slate-300">{change.parameter}</div>
                            <div className="flex items-center space-x-3 text-sm font-mono">
                                <div className="text-slate-500 decoration-slice line-through">{change.old_value}</div>
                                <div className="text-slate-600">{'->'}</div>
                                <div className={clsx('font-bold', change.changed ? 'text-emerald-400' : 'text-slate-400')}>
                                    {change.new_value}
                                </div>
                            </div>
                        </div>
                    ))}
                    {(!proposal?.changes || proposal.changes.length === 0) && (
                        <div className="text-center py-10 text-slate-500 italic">
                            No strategy changes proposed.
                        </div>
                    )}
                </div>
            )}

            <div className="mt-8">
                {manualMode ? (
                    <button
                        onClick={onApply}
                        disabled={applying}
                        className="w-full py-4 bg-amber-500 hover:bg-amber-400 text-black font-bold rounded-lg transition flex justify-center items-center disabled:opacity-50"
                    >
                        {applying ? (
                            <RefreshCw className="w-5 h-5 animate-spin mr-2" />
                        ) : (
                            <CheckCircle className="w-5 h-5 mr-2" />
                        )}
                        {applying ? 'Applying...' : 'Apply Manual Overrides'}
                    </button>
                ) : hasChangedProposal ? (
                    <button
                        onClick={onApply}
                        disabled={applying}
                        className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg transition flex justify-center items-center disabled:opacity-50"
                    >
                        {applying ? (
                            <RefreshCw className="w-5 h-5 animate-spin mr-2" />
                        ) : (
                            <CheckCircle className="w-5 h-5 mr-2" />
                        )}
                        {applying ? 'Adapting...' : 'Apply Strategy Changes'}
                    </button>
                ) : (
                    <button
                        disabled
                        className="w-full py-4 bg-slate-900/70 text-slate-500 font-bold rounded-lg cursor-not-allowed border border-white/10"
                    >
                        System is already optimized
                    </button>
                )}
            </div>
        </div>
    );
}
