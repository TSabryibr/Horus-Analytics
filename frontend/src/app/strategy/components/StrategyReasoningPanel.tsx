type StrategyReasoningPanelProps = {
    reasoning?: string;
};

export function StrategyReasoningPanel({ reasoning }: StrategyReasoningPanelProps) {
    return (
        <div className="section-surface-muted rounded-lg border border-white/10 p-4 italic text-slate-400 text-sm">
            &quot; {reasoning || 'No reasoning provided.'} &quot;
        </div>
    );
}
