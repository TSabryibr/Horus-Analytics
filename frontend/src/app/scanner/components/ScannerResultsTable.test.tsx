import { act, fireEvent, render, screen } from '@testing-library/react';

import { ScannerResultsTable } from './ScannerResultsTable';

const scannerData = {
    regime: 'BULLISH',
    breadth: 62.5,
    signals_count: 1,
    signals: [
        {
            Ticker: 'COMI',
            Signal_Type: 'BUY',
            Signal_Setup: 'BREAKOUT',
            Conviction: 'HIGH',
            Entry_Price: 104.5,
            Stop_Loss: 99.9,
            Target_Price: 110,
            Target_Price_2: 114,
            Score: 4.2,
            Volume_x: 2.3,
            VSA_Valid: true,
            Route_Profile: 'EGX30_TREND_PROFILE',
            Liquidity_Tier: 'LIQUID',
            Sector_RS_14: 0.12,
            Routing_Reason: 'egx30_trend',
            Whale_Alignment: 'SUPPORTIVE',
            Trap_Risk_Band: 'LOW',
            Enforcement_State: 'ALLOW',
            Enforcement_Reason: 'not_enforced',
            Enforcement_Notes: 'No whale/trap enforcement threshold breached.',
        },
        {
            Ticker: 'FWRY',
            Signal_Type: 'BUY',
            Signal_Setup: 'BREAKOUT',
            Conviction: 'TACTICAL',
            Entry_Price: 20.5,
            Stop_Loss: 18.9,
            Target_Price: 23,
            Target_Price_2: 24,
            Score: 3.7,
            Volume_x: 2.1,
            VSA_Valid: false,
            Route_Profile: 'EGX70_TACTICAL_PROFILE',
            Liquidity_Tier: 'TRADABLE',
            Sector_RS_14: -0.04,
            Routing_Reason: 'egx70_tactical',
            Whale_Alignment: 'CONFLICT',
            Trap_Risk_Band: 'SEVERE',
            Enforcement_State: 'BLOCK_EXECUTION',
            Enforcement_Reason: 'severe_trap_risk',
            Enforcement_Notes: 'Blocked for execution because severe trap risk breached the threshold.',
        },
    ],
};

describe('ScannerResultsTable', () => {
    it('renders the idle empty state when no data is available', () => {
        render(<ScannerResultsTable data={null} loading={false} />);

        expect(screen.getByText('Ready for Mission Control')).toBeInTheDocument();
        expect(screen.getByText('Initialize a scan to begin market telemetry.')).toBeInTheDocument();
    });

    it('renders scanner signal rows when data is available', async () => {
        const onPromoteCandidate = jest.fn();
        render(<ScannerResultsTable data={scannerData as any} loading={false} onPromoteCandidate={onPromoteCandidate} />);

        expect(screen.getAllByText('COMI').length).toBeGreaterThan(0);
        expect(screen.getAllByText('BUY')).toHaveLength(2);
        expect(screen.getAllByText('BREAKOUT')).toHaveLength(2);
        expect(screen.getByText('104.500')).toBeInTheDocument();
        expect(screen.getByText('2.3x')).toBeInTheDocument();
        expect(screen.getByText('EGX30 Trend')).toBeInTheDocument();
        expect(screen.getByText('LIQUID')).toBeInTheDocument();
        expect(screen.getByText('VSA OK')).toBeInTheDocument();
        expect(screen.getByText('Sector RS +0.12')).toBeInTheDocument();
        expect(screen.getByText('Whale Support')).toBeInTheDocument();
        expect(screen.getByText('Whale Support')).toHaveAttribute('title', 'Accumulation aligns with the long setup.');
        expect(screen.getByText('Trap Low')).toBeInTheDocument();
        expect(screen.getByText('Trap Low')).toHaveAttribute('title', 'Limited trap pressure under the current scoring mix.');
        expect(screen.getByText('Whale Conflict')).toBeInTheDocument();
        expect(screen.getByText('Whale Conflict')).toHaveAttribute('title', 'Distribution is pushing against the long setup.');
        expect(screen.getByText('Trap Severe')).toBeInTheDocument();
        expect(screen.getByText('Trap Severe')).toHaveAttribute('title', 'Stacked risk from multiple pressure signals.');
        expect(screen.getByText('Actionable')).toBeInTheDocument();
        expect(screen.getByText('Actionable')).toHaveAttribute('title', 'No whale/trap enforcement threshold is active for this setup.');
        expect(screen.getByText('Blocked')).toBeInTheDocument();
        expect(screen.getByText('Blocked')).toHaveAttribute('title', 'Execution is blocked, but the row stays visible for operator review.');
        expect(screen.getByText('severe trap risk')).toBeInTheDocument();

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /Promote COMI to swing lane/i }));
        });
        expect(onPromoteCandidate).toHaveBeenCalledWith(expect.objectContaining({
            lane: 'SWING',
            ticker: 'COMI',
            source_module: 'SCANNER',
        }));
    });

    it('locks promotion buttons while candidate promotion is in flight', async () => {
        let resolvePromise: (val?: unknown) => void;
        const onPromoteCandidate = jest.fn(() => new Promise((resolve) => { resolvePromise = resolve; }));

        render(<ScannerResultsTable data={scannerData as any} loading={false} onPromoteCandidate={onPromoteCandidate} />);

        const swingBtn = screen.getByRole('button', { name: /Promote COMI to swing lane/i });
        await act(async () => {
            fireEvent.click(swingBtn);
        });

        expect(swingBtn).toHaveTextContent('Promoting...');
        expect(swingBtn).toBeDisabled();

        await act(async () => {
            resolvePromise!();
        });

        expect(swingBtn).toHaveTextContent('Swing');
        expect(swingBtn).not.toBeDisabled();
    });
});
