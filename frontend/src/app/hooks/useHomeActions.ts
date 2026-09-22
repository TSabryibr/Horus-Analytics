import { useState } from 'react';
import { getBaseUrl } from '@/lib/api';
import { useSignalDeskData } from '../context/GlobalDataContext';

export function useHomeActions() {
    const [initializeLoading, setInitializeLoading] = useState(false);
    const { setOperatingMode } = useSignalDeskData();

    const initializeRun = async () => {
        const apiBase = getBaseUrl();
        setInitializeLoading(true);

        try {
            await fetch(`${apiBase}/api/v1/control/scan`, {
                method: 'POST',
                body: JSON.stringify({ type: 'DAILY', notify: true }),
                headers: { 'Content-Type': 'application/json' },
            });
        } catch (error) {
            console.error(error);
        } finally {
            setInitializeLoading(false);
        }
    };

    const setDeskMode = async (
        operatingMode: 'MANUAL' | 'AI_ASSIST' | 'AUTOPILOT',
        autopilotArmed?: boolean,
    ) => setOperatingMode(operatingMode, autopilotArmed);

    return {
        initializeLoading,
        initializeRun,
        setDeskMode,
    };
}
