import { fireEvent, render, screen, within } from '@testing-library/react';

import { ScannerControls } from './ScannerControls';

describe('ScannerControls', () => {
    it('renders control inputs and delegates filter and scan actions', () => {
        const setIndex = jest.fn();
        const setIsIntraday = jest.fn();
        const setSelectedProfileId = jest.fn();
        const onRunScan = jest.fn();

        render(
            <ScannerControls
                index="ALL"
                isIntraday={false}
                loading={false}
                progress=""
                scannerProfiles={[
                    {
                        profile_id: 7,
                        profile_name: 'EGX Breakout Pine',
                        source_type: 'PINE',
                        market: 'EGX30',
                        timeframe: '1D',
                        profile_state: 'DRAFT',
                    },
                ]}
                selectedProfile={null}
                selectedProfileId=""
                setIndex={setIndex}
                setIsIntraday={setIsIntraday}
                setSelectedProfileId={setSelectedProfileId}
                onRunScan={onRunScan}
            />,
        );

        fireEvent.change(screen.getByLabelText(/Market Universe/i), { target: { value: 'EGX70' } });
        fireEvent.change(screen.getByLabelText(/Scanner Strategy/i), { target: { value: '7' } });
        fireEvent.click(screen.getByRole('button', { name: /Daily/i }));
        fireEvent.click(screen.getByRole('button', { name: /Initialize Scan/i }));

        expect(setIndex).toHaveBeenCalledWith('EGX70');
        expect(setSelectedProfileId).toHaveBeenCalledWith('7');
        expect(setIsIntraday).toHaveBeenCalledWith(true);
        expect(onRunScan).toHaveBeenCalledTimes(1);
    });

    it('shows progress and disables the scan button while loading', () => {
        render(
            <ScannerControls
                index="EGX30"
                isIntraday
                loading
                progress="Scanning COMI [1/10]"
                scannerProfiles={[]}
                selectedProfile={null}
                selectedProfileId=""
                setIndex={jest.fn()}
                setIsIntraday={jest.fn()}
                setSelectedProfileId={jest.fn()}
                onRunScan={jest.fn()}
            />,
        );

        expect(screen.getByRole('button', { name: /Scanning COMI \[1\/10\]/i })).toBeDisabled();
        expect(screen.getByRole('button', { name: /Intraday/i })).toBeInTheDocument();
    });

    it('shows an active badge when the selected Pine strategy is the scanner default', () => {
        render(
            <ScannerControls
                index="EGX30"
                isIntraday={false}
                loading={false}
                progress=""
                scannerProfiles={[
                    {
                        profile_id: 7,
                        profile_name: 'EGX Breakout Pine',
                        source_type: 'PINE',
                        market: 'EGX30',
                        timeframe: '1D',
                        profile_state: 'ACTIVE',
                        is_active: true,
                    },
                ]}
                selectedProfile={{
                    profile_id: 7,
                    profile_name: 'EGX Breakout Pine',
                    source_type: 'PINE',
                    market: 'EGX30',
                    timeframe: '1D',
                    profile_state: 'ACTIVE',
                    is_active: true,
                }}
                selectedProfileId="7"
                setIndex={jest.fn()}
                setIsIntraday={jest.fn()}
                setSelectedProfileId={jest.fn()}
                onRunScan={jest.fn()}
            />,
        );

        expect(screen.getByText(/Active Default/i)).toBeInTheDocument();
        expect(screen.getByText(/Saved EGX30 \/ 1D/i)).toBeInTheDocument();
    });

    it('shows Pine profile audit details when a scanner profile is selected', () => {
        render(
            <ScannerControls
                index="EGX70"
                isIntraday={false}
                loading={false}
                progress=""
                scannerProfiles={[
                    {
                        profile_id: 8,
                        profile_name: 'Ready Pine Breakout',
                        source_type: 'PINE',
                        market: 'EGX70',
                        timeframe: '1D',
                        profile_state: 'ACTIVE',
                        is_active: true,
                        created_at: '2026-03-29T09:15:00',
                        ready_at: '2026-03-29T09:20:00',
                        activated_at: '2026-03-30T09:45:00',
                        activation_count: 1,
                        activation_history: [
                            {
                                event_type: 'ACTIVATED',
                                activated_at: '2026-03-30T09:45:00',
                                previous_active_profile_name: 'Active Pine Trend',
                            },
                        ],
                    },
                ]}
                selectedProfile={{
                    profile_id: 8,
                    profile_name: 'Ready Pine Breakout',
                    source_type: 'PINE',
                    market: 'EGX70',
                    timeframe: '1D',
                    profile_state: 'ACTIVE',
                    is_active: true,
                    created_at: '2026-03-29T09:15:00',
                    ready_at: '2026-03-29T09:20:00',
                    activated_at: '2026-03-30T09:45:00',
                    activation_count: 1,
                    activation_history: [
                        {
                            event_type: 'ACTIVATED',
                            activated_at: '2026-03-30T09:45:00',
                            previous_active_profile_name: 'Active Pine Trend',
                        },
                    ],
                }}
                selectedProfileId="8"
                setIndex={jest.fn()}
                setIsIntraday={jest.fn()}
                setSelectedProfileId={jest.fn()}
                onRunScan={jest.fn()}
            />,
        );

        expect(screen.getByText(/Profile Audit/i)).toBeInTheDocument();
        expect(screen.getByText(/Created: 2026-03-29 09:15/i)).toBeInTheDocument();
        expect(screen.getByText(/Ready: 2026-03-29 09:20/i)).toBeInTheDocument();
        expect(screen.getByText(/Activated: 2026-03-30 09:45/i)).toBeInTheDocument();
        expect(screen.getByText(/Activations: 1/i)).toBeInTheDocument();
        expect(screen.getByText(/replaced Active Pine Trend/i)).toBeInTheDocument();
    });

    it('shows borderline promotion warning when the selected Pine profile is close to ready thresholds', () => {
        render(
            <ScannerControls
                index="EGX30"
                isIntraday={false}
                loading={false}
                progress=""
                scannerProfiles={[
                    {
                        profile_id: 12,
                        profile_name: 'Borderline Pine Profile',
                        source_type: 'PINE',
                        market: 'EGX30',
                        timeframe: '1D',
                        profile_state: 'ACTIVE',
                        is_active: true,
                        promotion_summary: {
                            profile_state: 'ACTIVE',
                            failed_gates: [],
                            thresholds: {
                                compatibility_score: 70,
                                combined_score: 60,
                                trade_count: 3,
                                total_return: 0,
                                max_drawdown: 35,
                            },
                            actuals: {
                                readiness: 'READY',
                                compatibility_score: 74,
                                combined_score: 63,
                                trade_count: 4,
                                total_return: 4.2,
                                max_drawdown: 31,
                            },
                        },
                    },
                ]}
                selectedProfile={{
                    profile_id: 12,
                    profile_name: 'Borderline Pine Profile',
                    source_type: 'PINE',
                    market: 'EGX30',
                    timeframe: '1D',
                    profile_state: 'ACTIVE',
                    is_active: true,
                    promotion_summary: {
                        profile_state: 'ACTIVE',
                        failed_gates: [],
                        thresholds: {
                            compatibility_score: 70,
                            combined_score: 60,
                            trade_count: 3,
                            total_return: 0,
                            max_drawdown: 35,
                        },
                        actuals: {
                            readiness: 'READY',
                            compatibility_score: 74,
                            combined_score: 63,
                            trade_count: 4,
                            total_return: 4.2,
                            max_drawdown: 31,
                        },
                    },
                }}
                selectedProfileId="12"
                setIndex={jest.fn()}
                setIsIntraday={jest.fn()}
                setSelectedProfileId={jest.fn()}
                onRunScan={jest.fn()}
            />,
        );

        expect(screen.getByText(/Promotion Margin Warning/i)).toBeInTheDocument();
        expect(screen.getByText(/Selected Pine scanner profile is close to one or more promotion thresholds./i)).toBeInTheDocument();
        expect(screen.getByText('Compatibility margin: 74.0 vs ready floor 70.0')).toBeInTheDocument();
        expect(screen.getByText('Combined score margin: 63.0 vs ready floor 60.0')).toBeInTheDocument();
        expect(screen.getByText('Drawdown headroom: 31.0% vs 35.0% max')).toBeInTheDocument();
    });

    it('labels price-action profiles accurately inside the scanner audit panel', () => {
        render(
            <ScannerControls
                index="EGX30"
                isIntraday={false}
                loading={false}
                progress=""
                scannerProfiles={[
                    {
                        profile_id: 31,
                        profile_name: 'EGX Price Action Pack',
                        source_type: 'PRICE_ACTION',
                        market: 'EGX30',
                        timeframe: '1D',
                        profile_state: 'READY',
                        is_active: false,
                    },
                ]}
                selectedProfile={{
                    profile_id: 31,
                    profile_name: 'EGX Price Action Pack',
                    source_type: 'PRICE_ACTION',
                    market: 'EGX30',
                    timeframe: '1D',
                    profile_state: 'READY',
                    is_active: false,
                    promotion_summary: {
                        failed_gates: [],
                        thresholds: {
                            compatibility_score: 70,
                            combined_score: 60,
                            trade_count: 3,
                            total_return: 0,
                            max_drawdown: 35,
                        },
                        actuals: {
                            readiness: 'READY',
                            compatibility_score: 71,
                            combined_score: 61,
                            trade_count: 4,
                            total_return: 3.1,
                            max_drawdown: 34,
                        },
                    },
                }}
                selectedProfileId="31"
                setIndex={jest.fn()}
                setIsIntraday={jest.fn()}
                setSelectedProfileId={jest.fn()}
                onRunScan={jest.fn()}
            />,
        );

        expect(screen.getByText(/Price-action scanner profile with persisted market, timeframe, and audit telemetry./i)).toBeInTheDocument();
        expect(screen.getByText(/Selected price-action scanner profile is close to one or more promotion thresholds./i)).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: /View Full Profile/i }));
        expect(screen.getByText(/Price Action Profile Details/i)).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /Open in Strategy Lab/i })).toHaveAttribute('href', '/strategy?mode=PRICE_ACTION&profileId=31');
    });

    it('opens shared Pine profile details from scanner controls', () => {
        render(
            <ScannerControls
                index="EGX70"
                isIntraday={false}
                loading={false}
                progress=""
                scannerProfiles={[
                    {
                        profile_id: 21,
                        profile_name: 'Scanner Deep Dive Pine',
                        source_type: 'PINE',
                        market: 'EGX70',
                        timeframe: '1D',
                        profile_state: 'READY',
                        is_active: false,
                        created_at: '2026-03-28T08:00:00',
                        ready_at: '2026-03-28T09:10:00',
                        activated_at: null,
                        activation_count: 0,
                        activation_history: [],
                        backtest_summary: {
                            total_return: 11.4,
                            trade_count: 6,
                            win_rate: 66.7,
                            max_drawdown: 7.8,
                        },
                        compatibility_summary: {
                            readiness: 'READY',
                            compatibility_score: 91,
                            messages: ['Detected long entry and exit semantics'],
                        } as any,
                        ranking_summary: {
                            combined_score: 88,
                            performance_score: 83,
                            alignment_score: 71,
                            recommended: true,
                        } as any,
                        promotion_summary: {
                            failed_gates: [],
                            thresholds: {
                                compatibility_score: 70,
                                combined_score: 60,
                                trade_count: 3,
                                total_return: 0,
                                max_drawdown: 35,
                            },
                            actuals: {
                                readiness: 'READY',
                                compatibility_score: 91,
                                combined_score: 88,
                                trade_count: 6,
                                total_return: 11.4,
                                max_drawdown: 7.8,
                            },
                        },
                    },
                ]}
                selectedProfile={{
                    profile_id: 21,
                    profile_name: 'Scanner Deep Dive Pine',
                    source_type: 'PINE',
                    market: 'EGX70',
                    timeframe: '1D',
                    profile_state: 'READY',
                    is_active: false,
                    created_at: '2026-03-28T08:00:00',
                    ready_at: '2026-03-28T09:10:00',
                    activated_at: null,
                    activation_count: 0,
                    activation_history: [],
                    backtest_summary: {
                        total_return: 11.4,
                        trade_count: 6,
                        win_rate: 66.7,
                        max_drawdown: 7.8,
                    },
                    compatibility_summary: {
                        readiness: 'READY',
                        compatibility_score: 91,
                        messages: ['Detected long entry and exit semantics'],
                    } as any,
                    ranking_summary: {
                        combined_score: 88,
                        performance_score: 83,
                        alignment_score: 71,
                        recommended: true,
                    } as any,
                    promotion_summary: {
                        failed_gates: [],
                        thresholds: {
                            compatibility_score: 70,
                            combined_score: 60,
                            trade_count: 3,
                            total_return: 0,
                            max_drawdown: 35,
                        },
                        actuals: {
                            readiness: 'READY',
                            compatibility_score: 91,
                            combined_score: 88,
                            trade_count: 6,
                            total_return: 11.4,
                            max_drawdown: 7.8,
                        },
                    },
                } as any}
                selectedProfileId="21"
                setIndex={jest.fn()}
                setIsIntraday={jest.fn()}
                setSelectedProfileId={jest.fn()}
                onRunScan={jest.fn()}
            />,
        );

        fireEvent.click(screen.getByRole('button', { name: /View Full Profile/i }));

        const dialog = screen.getByRole('dialog', { name: /Strategy profile details/i });
        expect(dialog).toBeInTheDocument();
        expect(within(dialog).getByText(/Pine Profile Details/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/Scanner Deep Dive Pine/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/Recommendation: Promote to scanner/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/Detected long entry and exit semantics/i)).toBeInTheDocument();
        expect(within(dialog).getByText(/^Combined Score: 88.0$/i)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Close Profile Details/i }));

        expect(screen.queryByRole('dialog', { name: /Strategy profile details/i })).not.toBeInTheDocument();
    });
});
