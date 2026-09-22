'use client';

import { RRGChart } from './components/RRGChart';
import { SectorFullscreenModal } from './components/SectorFullscreenModal';
import { SectorRankingsTable } from './components/SectorRankingsTable';
import { SectorRrgPanel } from './components/SectorRrgPanel';
import { SectorShell } from './components/SectorShell';
import { useSectorFullscreen } from './hooks/useSectorFullscreen';
import { useSectorRuntime } from './hooks/useSectorRuntime';

export default function SectorPage() {
    const {
        data,
        fetchData,
        loading,
        quadrantCounts,
        sectorsList,
        selectedSector,
        setSelectedSector,
        setViewMode,
        sortedData,
        viewMode,
    } = useSectorRuntime();
    const { closeFullscreen, isFullscreen, openFullscreen } = useSectorFullscreen();

    return (
        <SectorShell
            loading={loading}
            onRefresh={fetchData}
            sectorsList={sectorsList}
            selectedSector={selectedSector}
            setSelectedSector={setSelectedSector}
            setViewMode={setViewMode}
            viewMode={viewMode}
            leadingCount={quadrantCounts.LEADING}
            benchmark="EGX30"
        >
            {loading ? (
                <div className="flex-1 flex flex-col justify-center items-center space-y-3">
                    <div className="w-10 h-10 text-purple-500 animate-spin border-2 border-current border-t-transparent rounded-full" />
                    <p className="text-slate-500 font-mono text-[10px] uppercase tracking-widest">Mapping the bifröst...</p>
                </div>
            ) : (
                <div className="flex flex-col gap-4">
                    <SectorRrgPanel data={data} onOpenFullscreen={openFullscreen} />

                    <SectorFullscreenModal isOpen={isFullscreen} onClose={closeFullscreen}>
                        <RRGChart data={data} width={1800} height={900} />
                    </SectorFullscreenModal>

                    <SectorRankingsTable
                        dataCount={data.length}
                        quadrantCounts={quadrantCounts}
                        rows={sortedData}
                        viewMode={viewMode}
                    />
                </div>
            )}
        </SectorShell>
    );
}
