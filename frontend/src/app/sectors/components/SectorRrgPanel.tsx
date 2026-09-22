import { Maximize2 } from 'lucide-react';

import { SectorRrgRow } from '../lib/sectorTransforms';
import { RRGChart } from './RRGChart';

interface SectorRrgPanelProps {
    data: SectorRrgRow[];
    onOpenFullscreen: () => void;
}

export function SectorRrgPanel({ data, onOpenFullscreen }: SectorRrgPanelProps) {
    return (
        <div
            className="bg-slate-900/30 border border-white/5 rounded-2xl p-4 relative group cursor-pointer"
            data-testid="sector-rrg-panel"
            onClick={onOpenFullscreen}
        >
            <div className="absolute top-4 right-4 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="bg-slate-800/80 border border-white/10 rounded-lg px-2 py-1 flex items-center gap-1.5 text-[10px] text-slate-400 font-bold uppercase">
                    <Maximize2 size={12} /> Click to Expand
                </div>
            </div>
            <div className="h-[550px]">
                <RRGChart data={data} width={1200} height={550} />
            </div>
        </div>
    );
}
