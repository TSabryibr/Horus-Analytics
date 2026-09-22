import { fireEvent, render, screen } from '@testing-library/react';

import { AnalyticsShell } from './AnalyticsShell';

describe('AnalyticsShell', () => {
    it('renders the page chrome and dispatches the scan action', () => {
        const onRunScan = jest.fn();

        render(
            <AnalyticsShell
                dataCount={30}
                isScanning={false}
                lastUpdatedLabel="Mar 18, 14:00"
                onRunScan={onRunScan}
                bullCount={18}
                bearCount={12}
                highConvictionCount={6}
            >
                <div>analytics-body</div>
            </AnalyticsShell>
        );

        expect(screen.getByText('Full Market Analytics')).toBeInTheDocument();
        expect(screen.getByText('🟢 18 Bull / 🔴 12 Bear')).toBeInTheDocument();
        expect(screen.getByText('6 Setups')).toBeInTheDocument();
        expect(screen.getAllByText(/30 tickers/i).length).toBeGreaterThan(0);
        expect(screen.getByText('analytics-body')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Run Fresh Scan/i }));
        expect(onRunScan).toHaveBeenCalledTimes(1);
    });

    it('disables the scan action while a scan is already running', () => {
        render(
            <AnalyticsShell
                dataCount={0}
                isScanning
                lastUpdatedLabel="-"
                onRunScan={jest.fn()}
            >
                <div>analytics-body</div>
            </AnalyticsShell>
        );

        expect(screen.getByRole('button', { name: /Scanning/i })).toBeDisabled();
    });
});
