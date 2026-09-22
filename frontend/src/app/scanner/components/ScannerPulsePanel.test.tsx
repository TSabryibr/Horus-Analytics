import { render, screen } from '@testing-library/react';

import { ScannerPulsePanel } from './ScannerPulsePanel';

describe('ScannerPulsePanel', () => {
    it('renders market pulse cards when scanner data is present', () => {
        render(
            <ScannerPulsePanel
                data={{
                    regime: 'BULLISH',
                    breadth: 62.5,
                    signals_count: 3,
                    strategy_profile: {
                        profile_id: 8,
                        profile_name: 'Ready Pine Breakout',
                        source_type: 'PINE',
                        market: 'EGX70',
                        timeframe: '1D',
                        profile_state: 'ACTIVE',
                        ready_at: '2026-03-29T09:20:00',
                        activated_at: '2026-03-30T09:45:00',
                        activation_count: 1,
                        backtest_summary: {
                            total_return: 18.5,
                            trade_count: 7,
                            win_rate: 57.1,
                            max_drawdown: 6.4,
                        },
                        compatibility_summary: {
                            readiness: 'READY',
                            compatibility_score: 92,
                            messages: [
                                'Uses supported ta.sma crossover logic',
                                'No unsupported Pine constructs detected',
                            ],
                        },
                        ranking_summary: {
                            performance_score: 80,
                            alignment_score: 61,
                            combined_score: 74.5,
                            recommended: true,
                        },
                        activation_history: [
                            {
                                event_type: 'ACTIVATED',
                                activated_at: '2026-03-30T09:45:00',
                                previous_active_profile_name: 'Active Pine Trend',
                            },
                        ],
                    },
                    signals: [],
                    whale_trap_diagnostics: {
                        rollout_mode: ' ',
                        supportive_whale_alignments: 2,
                        whale_conflicts: 1,
                        high_trap_risk_count: 1,
                        severe_trap_risk_count: 0,
                        top_trap_risk_reasons: { distribution_against_breakout: 1 },
                        threshold_analysis: {
                            rollout_mode: ' ',
                            would_review_count: 1,
                            would_block_count: 0,
                            top_block_reasons: {},
                        },
                    },
                    enforcement_diagnostics: {
                        rollout_mode: 'visible_but_blocked',
                        allow_count: 1,
                        watch_only_count: 1,
                        block_count: 1,
                        counts_by_reason: { severe_trap_risk: 1 },
                        counts_by_profile: {
                            EGX30_GUARDED: { allow_count: 1, watch_only_count: 0, block_count: 0 },
                            EGX70_HARDENED: { allow_count: 0, watch_only_count: 1, block_count: 1 },
                        },
                        counts_by_market_segment: {
                            EGX30: { allow_count: 1, watch_only_count: 0, block_count: 0 },
                            EGX70: { allow_count: 0, watch_only_count: 1, block_count: 1 },
                        },
                    },
                    calibration_diagnostics: {
                        rollout_mode: 'compare_only',
                        market_segments: {
                            EGX30: {
                                active_enforcement_profile: 'EGX30_GUARDED',
                                rollback_profile: 'EGX30_BALANCED',
                                candidate_calibration_profiles: ['EGX30_BALANCED'],
                                calibration_summary: {
                                    baseline_counts: { allow_count: 0, watch_only_count: 1, block_count: 0 },
                                    candidates: {
                                        EGX30_BALANCED: {
                                            counts: { allow_count: 1, watch_only_count: 0, block_count: 0 },
                                            deltas: {
                                                allow_delta: 1,
                                                watch_only_delta: -1,
                                                block_delta: 0,
                                                reason_deltas: {},
                                            },
                                            top_delta_reasons: [],
                                            top_reclassified_names: [
                                                {
                                                    ticker: 'COMI',
                                                    baseline_state: 'WATCH_ONLY',
                                                    candidate_state: 'ALLOW',
                                                    baseline_reason: 'high_trap_risk',
                                                    candidate_reason: 'not_enforced',
                                                },
                                            ],
                                        },
                                    },
                                },
                            },
                        },
                    },
                }}
            />,
        );

        expect(screen.getByText('Market Regime')).toBeInTheDocument();
        expect(screen.getByText('BULLISH')).toBeInTheDocument();
        expect(screen.getByText('Market Breadth')).toBeInTheDocument();
        expect(screen.getByText('62.5%')).toBeInTheDocument();
        expect(screen.getByText('Signals Found')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
        expect(screen.getByText('Shadow Observability')).toBeInTheDocument();
        expect(screen.getByText('2 supportive')).toBeInTheDocument();
        expect(screen.getByText('1 conflict')).toBeInTheDocument();
        expect(screen.getByText('1 high')).toBeInTheDocument();
        expect(screen.getByText('Shadow Legend')).toBeInTheDocument();
        expect(screen.getByText('Whale Support favors long setups with accumulation.')).toBeInTheDocument();
        expect(screen.getByText(/Future gates:\s*1 review \/ 0 block/)).toBeInTheDocument();
        expect(screen.getByText('Enforcement Rollup')).toBeInTheDocument();
        expect(screen.getByText('1 allow')).toBeInTheDocument();
        expect(screen.getByText('1 watch-only')).toBeInTheDocument();
        expect(screen.getByText('1 blocked')).toBeInTheDocument();
        expect(screen.getByText('Top enforcement reason: severe trap risk')).toBeInTheDocument();
        expect(screen.getByText('Calibration Compare')).toBeInTheDocument();
        expect(screen.getByText('EGX30_GUARDED -> EGX30_BALANCED')).toBeInTheDocument();
        expect(screen.getByText('Rollback: EGX30_BALANCED')).toBeInTheDocument();
        expect(screen.getByText('Delta: +1 allow / -1 watch / +0 block')).toBeInTheDocument();
        expect(screen.getByText('Scanner Profile')).toBeInTheDocument();
        expect(screen.getByText('Ready Pine Breakout')).toBeInTheDocument();
        expect(screen.getByText('Activated 2026-03-30 09:45')).toBeInTheDocument();
        expect(screen.getByText('Activations: 1')).toBeInTheDocument();
        expect(screen.getByText(/replaced Active Pine Trend/)).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /Open in Pine Lab/i })).toHaveAttribute(
            'href',
            '/optimization?mode=PINE_LAB&profileId=8',
        );
        expect(screen.getByText('Profile Ranking')).toBeInTheDocument();
        expect(screen.getByText('Combined Score')).toBeInTheDocument();
        expect(screen.getByText('74.5')).toBeInTheDocument();
        expect(screen.getByText('Performance')).toBeInTheDocument();
        expect(screen.getByText('80.0')).toBeInTheDocument();
        expect(screen.getByText('Alignment')).toBeInTheDocument();
        expect(screen.getByText('61.0')).toBeInTheDocument();
        expect(screen.getByText('Recommended for scanner promotion')).toBeInTheDocument();
        expect(screen.getByText('Backtest Snapshot')).toBeInTheDocument();
        expect(screen.getByText('Return')).toBeInTheDocument();
        expect(screen.getByText('18.5%')).toBeInTheDocument();
        expect(screen.getByText('Win Rate')).toBeInTheDocument();
        expect(screen.getByText('57.1%')).toBeInTheDocument();
        expect(screen.getByText('Trades')).toBeInTheDocument();
        expect(screen.getByText('7')).toBeInTheDocument();
        expect(screen.getByText('Max DD')).toBeInTheDocument();
        expect(screen.getByText('6.4%')).toBeInTheDocument();
        expect(screen.getByText('Compatibility Check')).toBeInTheDocument();
        expect(screen.getByText('Ready')).toBeInTheDocument();
        expect(screen.getByText('Score')).toBeInTheDocument();
        expect(screen.getByText('92.0')).toBeInTheDocument();
        expect(screen.getByText('Uses supported ta.sma crossover logic')).toBeInTheDocument();
    });

    it('renders nothing when no scanner data is present', () => {
        const { container } = render(<ScannerPulsePanel data={null} />);

        expect(container).toBeEmptyDOMElement();
    });

    it('shows borderline promotion warnings for active Pine profiles close to ready thresholds', () => {
        render(
            <ScannerPulsePanel
                data={{
                    regime: 'CAUTIOUS',
                    breadth: 41.2,
                    signals_count: 1,
                    strategy_profile: {
                        profile_id: 12,
                        profile_name: 'Borderline Pine Profile',
                        source_type: 'PINE',
                        market: 'EGX30',
                        timeframe: '1D',
                        profile_state: 'ACTIVE',
                        compatibility_summary: {
                            readiness: 'READY',
                            compatibility_score: 74,
                            messages: ['Limited margin above compatibility floor'],
                        },
                        backtest_summary: {
                            total_return: 4.2,
                            trade_count: 4,
                            win_rate: 51,
                            max_drawdown: 31,
                        },
                        ranking_summary: {
                            performance_score: 64,
                            alignment_score: 58,
                            combined_score: 63,
                            recommended: true,
                        },
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
                    signals: [],
                }}
            />,
        );

        expect(screen.getByText('Borderline Promotion Margin')).toBeInTheDocument();
        expect(screen.getByText('Scanner is active, but this Pine profile is running close to one or more promotion thresholds.')).toBeInTheDocument();
        expect(screen.getByText('Compatibility margin: 74.0 vs ready floor 70.0')).toBeInTheDocument();
        expect(screen.getByText('Combined score margin: 63.0 vs ready floor 60.0')).toBeInTheDocument();
        expect(screen.getByText('Drawdown headroom: 31.0% vs 35.0% max')).toBeInTheDocument();
    });

    it('renders native Horus scanner summary without N/A telemetry placeholders', () => {
        render(
            <ScannerPulsePanel
                data={{
                    regime: 'BULLISH',
                    breadth: 73,
                    signals_count: 0,
                    strategy_profile: {
                        profile_name: 'Horus Core',
                        source_type: 'HORUS',
                        market: 'ALL',
                        timeframe: '1D',
                    },
                    signals: [],
                }}
            />,
        );

        expect(screen.getByText('Scanner Profile')).toBeInTheDocument();
        expect(screen.getByText('Horus Core')).toBeInTheDocument();
        expect(screen.getByText('Native Engine')).toBeInTheDocument();
        expect(screen.getByText('Signal Model')).toBeInTheDocument();
        expect(screen.getByText('Horus Core Engine')).toBeInTheDocument();
        expect(screen.getByText('Scan Snapshot')).toBeInTheDocument();
        expect(screen.getByText('Breadth')).toBeInTheDocument();
        expect(screen.getAllByText('73.0%').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('Native Execution')).toBeInTheDocument();
        expect(screen.getAllByText('Ready').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText(/Activate a Pine scanner profile to unlock ranking, backtest, and compatibility telemetry./i)).toBeInTheDocument();
        expect(screen.queryByText('N/A')).not.toBeInTheDocument();
    });
});
