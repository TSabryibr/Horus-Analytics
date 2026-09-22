import { fireEvent, render, screen } from '@testing-library/react';

import { HomeSignalsPanel } from './HomeSignalsPanel';

describe('HomeSignalsPanel', () => {
    it('renders lane cards, queue counts, and action links', () => {
        const onOpenArchives = jest.fn();
        const onOpenTelegram = jest.fn();

        render(
            <HomeSignalsPanel
                hasSignals
                isSourceLoading={false}
                onOpenArchives={onOpenArchives}
                onOpenTelegram={onOpenTelegram}
                operatingMode="AI_ASSIST"
                autopilotArmed
                failedDeliveryCount={1}
                lifecycle={{ activeCount: 4, ambiguousCount: 1, openCount: 2, tp1Count: 1 }}
                followUps={{ total: 5, pendingCount: 2, readyCount: 1, failedCount: 1, suppressedCount: 1, stalePendingCount: 1 }}
                lanes={{
                    intraday: {
                        count: 1,
                        candidates: [
                            { ticker: 'COMI', side: 'BUY', confidence: 81, source_module: 'SCANNER', strategy_profile_name: 'EGX Breakout Pine' },
                        ],
                    },
                    swing: {
                        count: 1,
                        candidates: [
                            { ticker: 'HRHO', side: 'BUY', confidence: 73, source_module: 'ORACLE' },
                        ],
                    },
                    position: {
                        count: 0,
                        candidates: [],
                    },
                }}
            />
        );

        expect(screen.getByText('Daily Signal Desk')).toBeInTheDocument();
        expect(screen.getByText('Signal Desk')).toBeInTheDocument();
        expect(screen.getByText('AI_ASSIST')).toBeInTheDocument();
        expect(screen.getByText('AUTOPILOT ARMED')).toBeInTheDocument();
        expect(screen.getByText('Total Pipeline')).toBeInTheDocument();
        expect(screen.getAllByText('Intraday').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Swing').length).toBeGreaterThan(0);
        expect(screen.getByText('Signal Horizon Matrix')).toBeInTheDocument();
        expect(screen.getByText('Dispatch Status')).toBeInTheDocument();
        expect(screen.getByText('2 Pending Follow-Ups')).toBeInTheDocument();
        expect(screen.getByText('1 Failed Dispatches')).toBeInTheDocument();
        expect(screen.getByText('Intraday Horizon')).toBeInTheDocument();
        expect(screen.getByText('Swing Horizon')).toBeInTheDocument();
        expect(screen.getByText('Position Horizon')).toBeInTheDocument();
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('EGX Breakout Pine')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
        expect(screen.getByText(/1 failed dispatch requires retry/i)).toBeInTheDocument();
        expect(screen.getByText(/2 follow-up updates pending · 1 failed in dispatch pipeline/i)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Signal Archive · 30 Days/i }));
        expect(onOpenArchives).toHaveBeenCalledTimes(1);

        fireEvent.click(screen.getByRole('button', { name: /Open Dispatch Rail/i }));
        expect(onOpenTelegram).toHaveBeenCalledTimes(1);
    });

    it('renders the empty state when there are no signals', () => {
        render(
            <HomeSignalsPanel
                hasSignals={false}
                isSourceLoading={false}
                onOpenArchives={jest.fn()}
                onOpenTelegram={jest.fn()}
                operatingMode="MANUAL"
                autopilotArmed={false}
                failedDeliveryCount={0}
                lifecycle={{ activeCount: 0, ambiguousCount: 0, openCount: 0, tp1Count: 0 }}
                followUps={{ total: 0, pendingCount: 0, readyCount: 0, failedCount: 0, suppressedCount: 0, stalePendingCount: 0 }}
                lanes={{
                    intraday: { count: 0, candidates: [] },
                    swing: { count: 0, candidates: [] },
                    position: { count: 0, candidates: [] },
                }}
            />
        );

        expect(screen.getByText('Pipeline Clear')).toBeInTheDocument();
        expect(screen.getByText(/All scanners active. No horizon has produced a qualified dispatch candidate./i)).toBeInTheDocument();
    });
});
