import type { ReactNode } from 'react';

import { Brain, RefreshCw } from 'lucide-react';
import { CommandHeader } from '@/app/components/custom/CommandHeader';
import { IndustrialButton } from '@/app/components/custom/IndustrialButton';

type OracleShellProps = {
    isLoading: boolean;
    onRefresh: () => void;
    selectedTicker: string;
    selectedTickerLabel?: string;
    isHistorical: boolean;
    forecastTimestamp?: string;
    children: ReactNode;
};

export function OracleShell({ isLoading, onRefresh, selectedTicker, selectedTickerLabel, isHistorical, forecastTimestamp, children }: OracleShellProps) {
    return (
        <div className="page-shell page-shell-wide">
            <CommandHeader
                eyebrow="Oracle Command"
                title="AI Price Forecast"
                description="Market breadth and volatility squeeze analysis tuned for fast tactical reads."
                icon={<Brain className="h-8 w-8" />}
                statusItems={[
                    { label: 'Asset', value: selectedTickerLabel || selectedTicker, tone: 'primary' },
                    { label: 'Mode', value: isHistorical ? 'Archive' : 'Live', tone: isHistorical ? 'warning' : 'success' },
                    { label: 'Telemetry Stream', value: forecastTimestamp ? `Generated ${forecastTimestamp}` : isHistorical ? 'Archive Snapshot' : 'Live Stream', tone: 'info' },
                    { label: 'Sync', value: isLoading ? 'Refreshing' : 'Ready', tone: isLoading ? 'warning' : 'muted' },
                ]}
                actions={
                    <IndustrialButton
                        type="button"
                        variant={isLoading ? 'secondary' : 'primary'}
                        onClick={onRefresh}
                        disabled={isLoading}
                        aria-label="refresh-oracle"
                    >
                        <RefreshCw className={isLoading ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />
                        {isLoading ? 'Synchronizing' : 'Refresh Intel'}
                    </IndustrialButton>
                }
            />
            {children}
        </div>
    );
}
