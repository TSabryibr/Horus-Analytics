import { fireEvent, render, screen } from '@testing-library/react';

import { OracleAiReportPanel } from './OracleAiReportPanel';

const baseReport = {
    verdict: 'BULLISH',
    confidence: 72,
    generated_at: '2026-04-12T12:00:00.000Z',
    analysis: {
        short_term: 'Momentum expansion is improving.',
        tactical_edge: 'Compression resolved with constructive breadth.',
        risk_profile: 'A failed follow-through would invalidate the setup.',
    },
    snapshot: {
        recommendation: {
            entry: 21.2,
            stop: 19.8,
            target: 24.4,
        },
        technical_context: {
            is_bull_trap: false,
        },
        whale_flow: [{ type: 'ACCUMULATION' }],
        arbitrage: {
            correlation: 0.82,
        },
    },
};

describe('OracleAiReportPanel', () => {
    it('renders the live intelligence briefing and delegates refresh clicks', () => {
        const onRefresh = jest.fn();

        render(
            <OracleAiReportPanel
                title="CIIC Intelligence Briefing"
                report={baseReport}
                isLoading={false}
                onRefresh={onRefresh}
                isHistorical={false}
                onPromote={jest.fn()}
            />
        );

        expect(screen.getByText(/Intelligence Stream::CIIC_INTELLIGENCE_BRIEFING/i)).toBeInTheDocument();
        expect(screen.getByText('BULLISH')).toBeInTheDocument();
        expect(screen.getByText('Short-Term Trajectory')).toBeInTheDocument();
        expect(screen.getByText(/Active Accumulation/i)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Refresh Intel/i }));
        expect(onRefresh).toHaveBeenCalledTimes(1);
    });

    it('renders the loading state when no report is available yet', () => {
        render(
            <OracleAiReportPanel
                title="CIIC Intelligence Briefing"
                report={null}
                isLoading
                onRefresh={jest.fn()}
                isHistorical={false}
                onPromote={jest.fn()}
            />
        );

        expect(screen.getByText(/Retrieving Tactical Snapshot/i)).toBeInTheDocument();
    });

    it('renders the archived badge when viewing a historical report', () => {
        render(
            <OracleAiReportPanel
                title="CIIC Intelligence Briefing"
                report={baseReport}
                isLoading={false}
                onRefresh={jest.fn()}
                isHistorical
                onPromote={jest.fn()}
            />
        );

        expect(screen.getByText(/Archived Briefing/i)).toBeInTheDocument();
    });

    it('delegates lane promotion actions', () => {
        const onPromote = jest.fn();

        render(
            <OracleAiReportPanel
                title="CIIC Intelligence Briefing"
                report={baseReport}
                isLoading={false}
                onRefresh={jest.fn()}
                isHistorical={false}
                onPromote={onPromote}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /Promote to Swing Lane/i }));
        expect(onPromote).toHaveBeenCalledWith('SWING');
    });

    it('disables promotion when the report has no actionable levels', () => {
        render(
            <OracleAiReportPanel
                title="ACAP Intelligence Briefing"
                report={{
                    ...baseReport,
                    verdict: 'NEUTRAL',
                    confidence: 35,
                    snapshot: {
                        ...baseReport.snapshot,
                        recommendation: {
                            entry: null,
                            stop: null,
                            target: null,
                        },
                        technical_context: {
                            is_bull_trap: false,
                        },
                    },
                }}
                isLoading={false}
                onRefresh={jest.fn()}
                isHistorical={false}
                onPromote={jest.fn()}
            />
        );

        expect(screen.getByText(/No actionable levels/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Promote to Swing Lane/i })).toBeDisabled();
        expect(screen.getByText(/Trap Clear/i)).toBeInTheDocument();
    });
});
