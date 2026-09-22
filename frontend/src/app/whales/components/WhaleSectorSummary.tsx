'use client';

import { SectorSummary } from '../lib/whaleTransforms';

interface WhaleSectorSummaryProps {
    sectors: SectorSummary[];
}

export function WhaleSectorSummary({ sectors }: WhaleSectorSummaryProps) {
    if (sectors.length === 0) {
        return null;
    }

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {sectors.slice(0, 6).map((sector) => (
                <div key={sector.name} className="section-surface-muted rounded-lg p-3">
                    <div className="text-[10px] text-slate-500 uppercase font-bold truncate mb-1">{sector.name}</div>
                    <div className="flex items-center justify-between">
                        <span className="text-lg font-bold text-white">{sector.count}</span>
                        <div className="flex items-center gap-1">
                            <span className="text-[10px] text-emerald-500">▲{sector.accumulation}</span>
                            <span className="text-[10px] text-rose-500">▼{sector.distribution}</span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
