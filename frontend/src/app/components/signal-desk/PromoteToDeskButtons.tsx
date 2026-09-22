'use client';

type SignalDeskLaneKey = 'INTRADAY' | 'SWING' | 'POSITION';

interface PromoteToDeskButtonsProps {
    compact?: boolean;
    onPromote: (lane: SignalDeskLaneKey) => void | Promise<unknown>;
}

const LANE_BUTTONS: Array<{ lane: SignalDeskLaneKey; label: string; className: string }> = [
    { lane: 'INTRADAY', label: 'Intraday', className: 'border-amber-400/20 text-amber-200 hover:border-amber-300/40 hover:bg-amber-500/10' },
    { lane: 'SWING', label: 'Swing', className: 'border-cyan-400/20 text-cyan-200 hover:border-cyan-300/40 hover:bg-cyan-500/10' },
    { lane: 'POSITION', label: 'Position', className: 'border-emerald-400/20 text-emerald-200 hover:border-emerald-300/40 hover:bg-emerald-500/10' },
];

export function PromoteToDeskButtons({ compact = false, onPromote }: PromoteToDeskButtonsProps) {
    return (
        <div className={compact ? 'flex flex-wrap gap-1.5' : 'flex flex-wrap gap-2'}>
            {LANE_BUTTONS.map((button) => (
                <button
                    key={button.lane}
                    type="button"
                    onClick={() => void onPromote(button.lane)}
                    className={`rounded-full border px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.18em] transition ${button.className}`}
                >
                    {button.label}
                </button>
            ))}
        </div>
    );
}

export type { SignalDeskLaneKey };
