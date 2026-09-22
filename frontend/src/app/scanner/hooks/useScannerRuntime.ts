import { useEffect, useState } from 'react';

import { apiFetch, isIgnorableNetworkError } from '@/lib/api';
import { ScannerData } from '@/types';

export type ScannerStrategyProfile = {
    profile_id: number;
    profile_name: string;
    source_type: string;
    market: string;
    timeframe: string;
    profile_state: string;
    is_active?: boolean;
    created_at?: string | null;
    ready_at?: string | null;
    activated_at?: string | null;
    activation_count?: number;
    backtest_summary?: {
        total_return?: number;
        trade_count?: number;
        win_rate?: number;
        max_drawdown?: number;
    };
    compatibility_summary?: {
        readiness?: string;
        compatibility_score?: number;
        messages?: string[];
    };
    ranking_summary?: {
        performance_score?: number;
        alignment_score?: number;
        combined_score?: number;
        recommended?: boolean;
    };
    activation_history?: Array<{
        event_type: string;
        activated_at: string;
        previous_state?: string | null;
        previous_active_profile_id?: number | null;
        previous_active_profile_name?: string | null;
    }>;
    promotion_summary?: {
        profile_state?: string;
        failed_gates?: string[];
        thresholds?: Record<string, number>;
        actuals?: Record<string, string | number>;
    };
};

export function useScannerRuntime() {
    const [data, setData] = useState<ScannerData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [errorTitle, setErrorTitle] = useState('Connection Error');
    const [index, setIndex] = useState('ALL');
    const [isIntraday, setIsIntraday] = useState(false);
    const [progress, setProgress] = useState('');
    const [isPolling, setIsPolling] = useState(false);
    const [scannerProfiles, setScannerProfiles] = useState<ScannerStrategyProfile[]>([]);
    const [selectedProfileId, setSelectedProfileId] = useState('');

    useEffect(() => {
        apiFetch('/scanner/status')
            .then((res) => res.json())
            .then((status) => {
                if (status.status === 'COMPLETED' && status.result) {
                    setData(status.result);
                    const profileId = status.result?.strategy_profile?.profile_id;
                    if (profileId) {
                        setSelectedProfileId(String(profileId));
                    }
                } else if (status.status === 'RUNNING') {
                    setIsPolling(true);
                }
            })
            .catch((err) => {
                if (isIgnorableNetworkError(err)) {
                    return;
                }
                console.error('Scanner Initial Status Error:', err);
            });
    }, []);

    useEffect(() => {
        apiFetch('/strategy/pine/scanner-profiles')
            .then((res) => res.json())
            .then((payload) => {
                if (payload?.status === 'success' && Array.isArray(payload?.profiles)) {
                    setScannerProfiles(payload.profiles);
                    const activeProfileId = payload?.active_profile_id;
                    if (activeProfileId) {
                        setSelectedProfileId((current) => current || String(activeProfileId));
                    }
                }
            })
            .catch((err) => {
                if (isIgnorableNetworkError(err)) {
                    return;
                }
                console.error('Scanner Profile Load Error:', err);
            });
    }, []);

    return {
        data,
        error,
        errorTitle,
        hasData: Boolean(data),
        index,
        isIntraday,
        isPolling,
        loading,
        progress,
        scannerProfiles,
        selectedProfileId,
        setData,
        setError,
        setErrorTitle,
        setIndex,
        setIsIntraday,
        setIsPolling,
        setLoading,
        setProgress,
        setSelectedProfileId,
    };
}
