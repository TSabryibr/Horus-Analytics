import { fireEvent, render, screen } from '@testing-library/react';

import { HomeShell } from './HomeShell';
import { OPEN_SYSTEM_BOOT_EVENT } from './systemBootModel';

describe('HomeShell', () => {
    it('renders the top-level chrome, error banner, and action button', () => {
        const onInitializeRun = jest.fn();
        const dispatchSpy = jest.spyOn(window, 'dispatchEvent');

        render(
            <HomeShell
                dataSource="LIVE"
                error="Sync failed"
                deskMode="AI_ASSIST"
                autopilotArmed
                failedDeliveryCount={2}
                laneSummary={{ intraday: 2, swing: 1, position: 1 }}
                publishReadinessLabel="4 candidates ready"
                initializeLoading={false}
                marketStatus={<div>market-status</div>}
                health={{ win_rate: 64, avg_gain: 5.2 }}
                metrics={{ total_pnl: 1500, win_rate: 64, profit_factor: 1.9 }}
                isSourceLoading={false}
                focusMode="FULL"
                onSetFocusMode={jest.fn()}
                onInitializeRun={onInitializeRun}
            >
                <div>home-body</div>
            </HomeShell>
        );

        expect(screen.getByText(/Horus Analytics/i)).toBeInTheDocument();
        expect(screen.getByText('System Online')).toBeInTheDocument();
        expect(screen.getByText('Intervention Required')).toBeInTheDocument();
        expect(screen.getByText('Resolve Failed Dispatches')).toBeInTheDocument();
        expect(screen.getByText('Command Desk')).toBeInTheDocument();
        expect(screen.getAllByText('Dispatch Readiness').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('Delivery Status')).toBeInTheDocument();
        expect(screen.getAllByText('4 candidates ready')).toHaveLength(2);
        expect(screen.getByText('market-status')).toBeInTheDocument();
        expect(screen.getByText('ERROR DETECTED: Sync failed')).toBeInTheDocument();
        expect(screen.getByText('home-body')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /system check/i })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Initialize Pipeline/i }));
        expect(onInitializeRun).toHaveBeenCalledTimes(1);

        fireEvent.click(screen.getByRole('button', { name: /system check/i }));
        expect(dispatchSpy).toHaveBeenCalledWith(expect.objectContaining({ type: OPEN_SYSTEM_BOOT_EVENT }));

        dispatchSpy.mockRestore();
    });

    it('disables the action button while initialize-run is in flight', () => {
        render(
            <HomeShell
                dataSource="FALLBACK"
                error={null}
                deskMode="MANUAL"
                autopilotArmed={false}
                failedDeliveryCount={0}
                laneSummary={{ intraday: 0, swing: 0, position: 0 }}
                publishReadinessLabel="Desk idle"
                initializeLoading
                marketStatus={<div>market-status</div>}
                health={null}
                metrics={null}
                isSourceLoading
                focusMode="FULL"
                onSetFocusMode={jest.fn()}
                onInitializeRun={jest.fn()}
            >
                <div>home-body</div>
            </HomeShell>
        );

        expect(screen.getByText('Archive Mode')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Initialize Pipeline/i })).toBeDisabled();
    });

    it('renders Swing Conviction Leading posture with technical sub-title and risk telemetry', () => {
        render(
            <HomeShell
                dataSource="LIVE"
                error={null}
                deskMode="AUTOPILOT"
                autopilotArmed
                failedDeliveryCount={0}
                laneSummary={{ intraday: 1, swing: 4, position: 1 }}
                publishReadinessLabel="6 candidates ready"
                initializeLoading={false}
                marketStatus={<div>market-status</div>}
                health={null}
                metrics={null}
                isSourceLoading={false}
                focusMode="FULL"
                onSetFocusMode={jest.fn()}
                onInitializeRun={jest.fn()}
            >
                <div>home-body</div>
            </HomeShell>
        );

        expect(screen.getByText('Swing Conviction Leading')).toBeInTheDocument();
        expect(screen.getByText(/SWING CONVICTION: 4 CANDIDATE\(S\) STAGED \| RISK GUARD: ATR ACTIVE/i)).toBeInTheDocument();
        expect(screen.getByText(/SWING HORIZON LEAD \(4 SETUPS • 5-20 DAYS\)/i)).toBeInTheDocument();
        expect(screen.getByText(/ATR Trailing Stop Active • Kelly Cap 2.5%/i)).toBeInTheDocument();
    });
});
