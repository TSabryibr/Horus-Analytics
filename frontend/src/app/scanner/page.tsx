'use client';

import { useEffect, useRef } from 'react';
import { ScannerControls } from './components/ScannerControls';
import { ScannerPulsePanel } from './components/ScannerPulsePanel';
import { ScannerResultsTable } from './components/ScannerResultsTable';
import { ScannerShell } from './components/ScannerShell';
import { useScannerExecution } from './hooks/useScannerExecution';
import { useScannerRuntime } from './hooks/useScannerRuntime';
import { useScannerAudio } from './hooks/useScannerAudio';
import { useSignalDeskData } from '../context/GlobalDataContext';

export default function ScannerPage() {
    const { promoteCandidate } = useSignalDeskData();
    const {
        data,
        error,
        errorTitle,
        index,
        isIntraday,
        loading,
        progress,
        scannerProfiles,
        selectedProfileId,
        setData,
        setError,
        setErrorTitle,
        setIndex,
        setIsIntraday,
        setLoading,
        setProgress,
        setSelectedProfileId,
        setIsPolling,
        isPolling
    } = useScannerRuntime();

    const selectedProfile = scannerProfiles.find((profile) => String(profile.profile_id) === selectedProfileId) || null;
    
    const { runScan, staleMeta, bypassStaleMode, confirmHoliday } = useScannerExecution({
        index,
        isIntraday,
        isPolling,
        selectedProfileId,
        setData,
        setError,
        setErrorTitle,
        setIsPolling,
        setLoading,
        setProgress,
    });

    const { isMuted, toggleMute, playSound } = useScannerAudio();
    
    // Audio trigger logic
    const prevLoading = useRef(loading);
    const prevSevereCount = useRef(0);

    useEffect(() => {
        // Scan Complete trigger
        if (prevLoading.current === true && loading === false && data) {
            playSound('SCAN_COMPLETE');
        }
        prevLoading.current = loading;

        // Threat Detected trigger
        const severeCount = data?.whale_trap_diagnostics?.severe_trap_risk_count || 0;
        if (severeCount > prevSevereCount.current) {
            playSound('THREAT_DETECTED');
        }
        prevSevereCount.current = severeCount;
    }, [data, loading, playSound]);

    return (
        <ScannerShell
            controls={
                <ScannerControls
                    index={index}
                    isIntraday={isIntraday}
                    loading={loading}
                    progress={progress}
                    scannerProfiles={scannerProfiles}
                    selectedProfile={selectedProfile}
                    selectedProfileId={selectedProfileId}
                    setIndex={setIndex}
                    setIsIntraday={setIsIntraday}
                    setSelectedProfileId={setSelectedProfileId}
                    onRunScan={runScan}
                    isMuted={isMuted}
                    onToggleMute={toggleMute}
                />
            }
            error={error}
            errorTitle={errorTitle}
            staleMeta={staleMeta}
            onBypassStale={bypassStaleMode}
            onConfirmHoliday={confirmHoliday}
        >
            <ScannerPulsePanel data={data} />
            <ScannerResultsTable data={data} loading={loading} onPromoteCandidate={promoteCandidate} />
        </ScannerShell>
    );
}
