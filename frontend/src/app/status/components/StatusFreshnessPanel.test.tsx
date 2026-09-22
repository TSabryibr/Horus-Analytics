import { fireEvent, render, screen } from '@testing-library/react';

import { StatusFreshnessPanel } from './StatusFreshnessPanel';

const status = {
    freshness: { session_mode: 'LIVE' },
    data_status: {
        history: { status: 'FRESH', last_updated: '2026-03-17' },
        intraday: { status: 'LIVE', last_bar: '2026-03-18 10:31' },
    },
};

describe('StatusFreshnessPanel', () => {
    it('renders freshness metrics and delegates the sync action', () => {
        const triggerDataSync = jest.fn();

        render(
            <StatusFreshnessPanel
                status={status}
                syncingData={false}
                syncStatusMessage="Data sync completed."
                triggerDataSync={triggerDataSync}
                historySymbolCount={120}
                historyAgeHours={24}
                sourceEngine="DirectFN Feed"
                driftValue="1 Minutes"
            />
        );

        expect(screen.getByText('Data Lake Freshness')).toBeInTheDocument();
        expect(screen.getByText('Data sync completed.')).toBeInTheDocument();
        expect(screen.getByText('Retention Depth')).toBeInTheDocument();
        expect(screen.getByText('DirectFN Feed')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Sync History \+ Intraday/i }));
        expect(triggerDataSync).toHaveBeenCalledTimes(1);
    });

    it('shows when realtime intraday is live while the archive source is stale', () => {
        render(
            <StatusFreshnessPanel
                status={{
                    ...status,
                    data_status: {
                        ...status.data_status,
                        source: {
                            intraday_provider: 'MUBASHER_DB',
                            intraday_decision: { reason: 'upstream_intraday_stale' },
                            realtime_overlay: {
                                active: true,
                                status: 'ACTIVE',
                                price_field: '55',
                                guard: 'session_range',
                            },
                        },
                    },
                }}
                syncingData={false}
                syncStatusMessage={null}
                triggerDataSync={jest.fn()}
                historySymbolCount={120}
                historyAgeHours={24}
                sourceEngine="Mubasher DB"
                driftValue="1 Minutes"
            />
        );

        expect(screen.getByText('Realtime live, archive stale')).toBeInTheDocument();
        expect(screen.getByText('Realtime Overlay')).toBeInTheDocument();
        expect(screen.getByText('ACTIVE (field 55)')).toBeInTheDocument();
        expect(screen.getByText('Overlay Guard')).toBeInTheDocument();
        expect(screen.getByText('session_range')).toBeInTheDocument();
    });
});
