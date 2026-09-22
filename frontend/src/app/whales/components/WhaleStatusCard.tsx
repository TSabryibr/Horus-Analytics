'use client';

import { Compass } from 'lucide-react';

interface WhaleStatusCardProps {
    candidateCount: number;
    sectorCount: number;
}

export function WhaleStatusCard({ candidateCount, sectorCount }: WhaleStatusCardProps) {
    return (
        <div className="bg-cyan-950/10 border border-cyan-500/20 rounded-xl p-4 flex items-center space-x-4">
            <Compass className="w-6 h-6 text-cyan-400" />
            <div>
                <div className="text-sm font-bold text-cyan-300">Sonar Range: Full Market</div>
                <div className="text-xs text-gray-500">
                    Detected {candidateCount} stocks with significant volume/price divergence across {sectorCount} sectors.
                </div>
            </div>
        </div>
    );
}
