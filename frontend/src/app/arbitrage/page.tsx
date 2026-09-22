'use client';

import { Zap, Search } from 'lucide-react';
import { useArbitrageRuntime } from './hooks/useArbitrageRuntime';
import { ArbitrageShell } from './components/ArbitrageShell';
import { ArbitrageMirrorCard } from './components/ArbitrageMirrorCard';

export default function ArbitragePage() {
    const {
        isLoading,
        universe,
        setUniverse,
        filter,
        setFilter,
        filteredMirrors,
        executing,
        actionStatus,
        onRefresh,
        onExecute,
    } = useArbitrageRuntime();

    return (
        <ArbitrageShell
            loading={isLoading}
            universe={universe}
            onUniverseChange={setUniverse}
            filter={filter}
            onFilterChange={setFilter}
            onRefresh={onRefresh}
            activeCount={filteredMirrors.length}
            executionMode="⚡ SINGLE-LEG"
        >
            {/* Explanation Alert */}
            <div className="bg-emerald-950/10 border border-emerald-500/20 rounded-xl p-4 flex items-start space-x-4">
                <Zap className="w-6 h-6 text-emerald-400 mt-1 shrink-0" />
                <div>
                    <div className="text-sm font-bold text-emerald-300">Lead-Lag Impulse Edge (Unhedged Single-Leg)</div>
                    <div className="text-xs text-slate-400 leading-relaxed mt-0.5">
                        These pairs display statistical &quot;Echoes&quot;. When the <span className="font-semibold text-emerald-400">Leader</span> moves, the <span className="font-semibold text-slate-200">Follower</span> historically repeats the move with a specific time delay (<span className="font-semibold text-slate-200">Lag</span>).
                        Orders execute as unhedged single-leg trades on the Follower asset with automated <span className="font-semibold text-emerald-400">ATR Stop-Loss (-1.5%)</span> and <span className="font-semibold text-emerald-400">Take-Profit (+2.5%)</span> brackets via T212 API.
                    </div>
                </div>
            </div>

            {/* Loading Spinner */}
            {isLoading && (
                <div className="flex-1 flex justify-center items-center">
                    <div className="w-10 h-10 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin" />
                </div>
            )}

            {/* Mirrors Grid */}
            {!isLoading && filteredMirrors.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredMirrors.map((m: any, idx: number) => (
                        <ArbitrageMirrorCard
                            key={idx}
                            mirror={m}
                            idx={idx}
                            isExecuting={!!executing[idx]}
                            actionStatus={actionStatus}
                            onExecute={onExecute}
                        />
                    ))}
                </div>
            )}

            {/* Empty State */}
            {!isLoading && filteredMirrors.length === 0 && (
                <div className="flex-1 flex flex-col justify-center items-center text-gray-600">
                    <Search className="w-12 h-12 mb-2 opacity-20" />
                    <p>No echoing pairs found in the current mirror scan.</p>
                </div>
            )}
        </ArbitrageShell>
    );
}
