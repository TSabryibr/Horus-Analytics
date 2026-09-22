import { render, screen } from '@testing-library/react';

import { ScannerShell } from './ScannerShell';

describe('ScannerShell', () => {
    it('renders the page chrome, controls slot, and body content', () => {
        render(
            <ScannerShell controls={<div>scanner-controls</div>}>
                <div>scanner-body</div>
            </ScannerShell>,
        );

        expect(screen.getByText('Market Scanner')).toBeInTheDocument();
        expect(screen.getByText(/Real-time technical analysis engine/i)).toBeInTheDocument();
        expect(screen.getByText('scanner-controls')).toBeInTheDocument();
        expect(screen.getByText('scanner-body')).toBeInTheDocument();
    });

    it('renders the top-level error banner when an error is present', () => {
        render(
            <ScannerShell
                controls={<div>scanner-controls</div>}
                error="Read-only stale mode is active. (SYNCING)"
                errorTitle="Read-Only Stale Mode"
            >
                <div>scanner-body</div>
            </ScannerShell>,
        );

        expect(screen.getByText('Read-Only Stale Mode')).toBeInTheDocument();
        expect(screen.getByText('Read-only stale mode is active. (SYNCING)')).toBeInTheDocument();
    });

    it('hides holiday confirmation when stale data matches the expected trading day', () => {
        render(
            <ScannerShell
                controls={<div>scanner-controls</div>}
                error="Sync worker is refreshing data. Read-only stale mode is active. (SYNCING)"
                errorTitle="Read-Only Stale Mode"
                staleMeta={{
                    lastUpdated: '2026-03-26',
                    expectedDate: '2026-03-26',
                    pipelineState: 'SYNCING',
                }}
                onBypassStale={() => {}}
                onConfirmHoliday={() => {}}
            >
                <div>scanner-body</div>
            </ScannerShell>,
        );

        expect(screen.getByRole('button', { name: /Proceed with Current Data/i })).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Mark as Holiday/i })).not.toBeInTheDocument();
    });
});
