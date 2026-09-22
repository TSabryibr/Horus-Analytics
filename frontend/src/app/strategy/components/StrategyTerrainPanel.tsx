import { Shield, Zap } from 'lucide-react';
import clsx from 'clsx';

type StrategyTerrainPanelProps = {
    getRegimeColor: (regime: string) => string;
    proposal: {
        regime: string;
        regime_score: number;
        volatility: string;
        volatility_value: number;
    };
};

export function StrategyTerrainPanel({
    getRegimeColor,
    proposal,
}: StrategyTerrainPanelProps) {
    return (
        <>
            <div className="section-surface industrial-corner rounded-xl p-6">
                <h3 className="text-lg font-bold text-slate-100 flex items-center mb-4">
                    <Shield className="w-5 h-5 mr-2 text-indigo-400" />
                    The Terrain (Regime)
                </h3>
                <div className={clsx('p-4 rounded-lg border text-center', getRegimeColor(proposal.regime))}>
                    <div className="text-2xl font-bold">{proposal.regime}</div>
                    <div className="text-xs opacity-70 mt-1">Score: {proposal.regime_score}/10</div>
                </div>
            </div>

            <div className="section-surface industrial-corner rounded-xl p-6">
                <h3 className="text-lg font-bold text-slate-100 flex items-center mb-4">
                    <Zap className="w-5 h-5 mr-2 text-yellow-500" />
                    The Weather (Volatility)
                </h3>
                <div className="flex justify-between items-center bg-slate-950/60 p-4 rounded-lg border border-white/10">
                    <div>
                        <div className="text-sm text-slate-400">Status</div>
                        <div className="font-bold text-slate-200">{proposal.volatility}</div>
                    </div>
                    <div className="text-right">
                        <div className="text-sm text-slate-400">ATR %</div>
                        <div className="font-mono text-yellow-400">{proposal.volatility_value}%</div>
                    </div>
                </div>
            </div>
        </>
    );
}
