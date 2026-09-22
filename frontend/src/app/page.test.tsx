import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import HomePage from './page';

const mockUseHomeRuntime = jest.fn();
const mockUseHomeActions = jest.fn();
const mockRouterPush = jest.fn();

jest.mock('next/navigation', () => ({
    useRouter: () => ({
        push: mockRouterPush,
    }),
}));

jest.mock('next/dynamic', () => (
    () => function MockDynamicChart() {
        return <div data-testid="home-equity-chart">Home Equity Chart</div>;
    }
));

jest.mock('./hooks/useHomeRuntime', () => ({
    useHomeRuntime: () => mockUseHomeRuntime(),
}));

jest.mock('./hooks/useHomeActions', () => ({
    useHomeActions: () => mockUseHomeActions(),
}));

jest.mock('./components/HomeArchivesModal', () => ({
    HomeArchivesModal: ({ isOpen }: { isOpen: boolean }) => (
        isOpen ? <div>Matrix Archive Logs</div> : null
    ),
}));

type LaneCandidates = Array<{ ticker: string; side: string; confidence: number; source_module?: string }>;

type HomeRuntimeMock = {
    archivesByDate: Record<string, Array<{ ticker: string; signal_type: string; price: number; score: number }>>;
    curve: Array<{ date: string; equity: number }>;
    dataSource: 'LIVE' | 'FALLBACK' | 'LOADING';
    error: string | null;
    hasCurve: boolean;
    health: { win_rate: number; avg_gain?: number } | null;
    metrics: { total_pnl: number } | null;
    refreshDesk: jest.Mock;
    setShowArchives: jest.Mock;
    signalDesk: {
        operatingMode: 'MANUAL' | 'AI_ASSIST' | 'AUTOPILOT';
        autopilotArmed: boolean;
        intradayCount: number;
        swingCount: number;
        positionCount: number;
        failedDeliveryCount: number;
        latestFailedDelivery: Record<string, unknown> | null;
        loading: boolean;
        error: string | null;
        desk: {
            operating_mode: 'MANUAL' | 'AI_ASSIST' | 'AUTOPILOT';
            autopilot_armed: boolean;
            failed_delivery_count?: number;
            latest_failed_delivery?: Record<string, unknown> | null;
            lanes: {
                intraday: { count: number; candidates: LaneCandidates };
                swing: { count: number; candidates: LaneCandidates };
                position: { count: number; candidates: LaneCandidates };
            };
        };
    };
    showArchives: boolean;
    signals: Array<{ ticker: string; regime: string; price: number; confidence: number }>;
    isSourceLoading: boolean;
};

function makeRuntime(overrides: Partial<HomeRuntimeMock> = {}): HomeRuntimeMock {
    return {
        archivesByDate: {},
        curve: [{ date: '2026-04-12', equity: 100 }],
        dataSource: 'LIVE',
        error: null,
        hasCurve: true,
        health: { win_rate: 64, avg_gain: 5.1 },
        metrics: { total_pnl: 12.4 },
        refreshDesk: jest.fn(),
        setShowArchives: jest.fn(),
        signalDesk: {
            operatingMode: 'AI_ASSIST',
            autopilotArmed: true,
            intradayCount: 1,
            swingCount: 1,
            positionCount: 0,
            failedDeliveryCount: 0,
            latestFailedDelivery: null,
            loading: false,
            error: null,
            desk: {
                operating_mode: 'AI_ASSIST',
                autopilot_armed: true,
                failed_delivery_count: 0,
                latest_failed_delivery: null,
                lanes: {
                    intraday: {
                        count: 1,
                        candidates: [{ ticker: 'COMI', side: 'BUY', confidence: 84.1, source_module: 'SCANNER' }],
                    },
                    swing: {
                        count: 1,
                        candidates: [{ ticker: 'HRHO', side: 'BUY', confidence: 74.2, source_module: 'ORACLE' }],
                    },
                    position: {
                        count: 0,
                        candidates: [],
                    },
                },
            },
        },
        showArchives: false,
        signals: [
            { ticker: 'COMI', regime: 'Bullish', price: 102.55, confidence: 84.1 },
        ],
        isSourceLoading: false,
        ...overrides,
    };
}

describe('Home dashboard view', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders the signal desk chrome with charts, readiness, and lanes', () => {
        mockUseHomeRuntime.mockReturnValue(makeRuntime());
        mockUseHomeActions.mockReturnValue({
            initializeLoading: false,
            initializeRun: jest.fn(),
            setDeskMode: jest.fn(),
        });

        render(<HomePage />);

        expect(screen.getByText('Horus Analytics')).toBeInTheDocument();
        expect(screen.getByText('Command Desk')).toBeInTheDocument();
        expect(screen.getByText('Horizon Distribution')).toBeInTheDocument();
        expect(screen.getByTestId('home-equity-chart')).toBeInTheDocument();
        expect(screen.getByText('Daily Signal Desk')).toBeInTheDocument();
        expect(screen.getAllByText('AI_ASSIST').length).toBeGreaterThan(0);
        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('HRHO')).toBeInTheDocument();
    });

    it('surfaces failed delivery warnings inside the home desk', () => {
        const runtime = makeRuntime();
        mockUseHomeRuntime.mockReturnValue(makeRuntime({
            signalDesk: {
                ...runtime.signalDesk,
                failedDeliveryCount: 2,
                latestFailedDelivery: { status: 'FAILED', last_error: 'transport down' },
                desk: {
                    ...runtime.signalDesk.desk,
                    failed_delivery_count: 2,
                    latest_failed_delivery: { status: 'FAILED', last_error: 'transport down' },
                },
            },
        }));
        mockUseHomeActions.mockReturnValue({
            initializeLoading: false,
            initializeRun: jest.fn(),
            setDeskMode: jest.fn(),
        });

        render(<HomePage />);

        expect(screen.getByText('Intervention Required')).toBeInTheDocument();
        expect(screen.getByText('Resolve Failed Dispatches')).toBeInTheDocument();
        expect(screen.getByText(/2 failed dispatches require retry/i)).toBeInTheDocument();
    });

    it('shows the initialization empty state and delegates core-engine start', () => {
        const initializeRun = jest.fn();

        mockUseHomeRuntime.mockReturnValue(makeRuntime({
            curve: [],
            hasCurve: false,
            isSourceLoading: false,
            signalDesk: {
                operatingMode: 'MANUAL',
                autopilotArmed: false,
                intradayCount: 0,
                swingCount: 0,
                positionCount: 0,
                failedDeliveryCount: 0,
                latestFailedDelivery: null,
                loading: false,
                error: null,
                desk: {
                    operating_mode: 'MANUAL',
                    autopilot_armed: false,
                    failed_delivery_count: 0,
                    latest_failed_delivery: null,
                    lanes: {
                        intraday: { count: 0, candidates: [] },
                        swing: { count: 0, candidates: [] },
                        position: { count: 0, candidates: [] },
                    },
                },
            },
            signals: [],
        }));
        mockUseHomeActions.mockReturnValue({
            initializeLoading: false,
            initializeRun,
            setDeskMode: jest.fn(),
        });

        render(<HomePage />);

        expect(screen.getByText(/Awaiting pipeline initialization/i)).toBeInTheDocument();

        fireEvent.click(screen.getAllByRole('button', { name: /Initialize Pipeline/i })[0]);
        expect(initializeRun).toHaveBeenCalledTimes(1);
    });

    it('shows the empty lane state when no candidates are available', () => {
        mockUseHomeRuntime.mockReturnValue(makeRuntime({
            signalDesk: {
                operatingMode: 'MANUAL',
                autopilotArmed: false,
                intradayCount: 0,
                swingCount: 0,
                positionCount: 0,
                failedDeliveryCount: 0,
                latestFailedDelivery: null,
                loading: false,
                error: null,
                desk: {
                    operating_mode: 'MANUAL',
                    autopilot_armed: false,
                    failed_delivery_count: 0,
                    latest_failed_delivery: null,
                    lanes: {
                        intraday: { count: 0, candidates: [] },
                        swing: { count: 0, candidates: [] },
                        position: { count: 0, candidates: [] },
                    },
                },
            },
            signals: [],
        }));
        mockUseHomeActions.mockReturnValue({
            initializeLoading: false,
            initializeRun: jest.fn(),
            setDeskMode: jest.fn(),
        });

        render(<HomePage />);

        expect(screen.getAllByText('Pipeline Clear')[0]).toBeInTheDocument();
    });

    it('opens archive navigation through the runtime setter', () => {
        const setShowArchives = jest.fn();

        mockUseHomeRuntime.mockReturnValue(makeRuntime({
            setShowArchives,
        }));
        mockUseHomeActions.mockReturnValue({
            initializeLoading: false,
            initializeRun: jest.fn(),
            setDeskMode: jest.fn(),
        });

        render(<HomePage />);

        fireEvent.click(screen.getByRole('button', { name: /Signal Archive/i }));
        expect(setShowArchives).toHaveBeenCalledWith(true);
    });

    it('renders the archives modal when the runtime toggles it open', () => {
        mockUseHomeRuntime.mockReturnValue(makeRuntime({
            showArchives: true,
            archivesByDate: {
                '2026-04-12': [
                    { ticker: 'COMI', signal_type: 'BUY', price: 102.5, score: 8.2 },
                ],
            },
        }));
        mockUseHomeActions.mockReturnValue({
            initializeLoading: false,
            initializeRun: jest.fn(),
            setDeskMode: jest.fn(),
        });

        render(<HomePage />);

        expect(screen.getByText('Matrix Archive Logs')).toBeInTheDocument();
    });

    it('routes execute deep scan to Oracle with the entered ticker', () => {
        mockUseHomeRuntime.mockReturnValue(makeRuntime());
        mockUseHomeActions.mockReturnValue({
            initializeLoading: false,
            initializeRun: jest.fn(),
            setDeskMode: jest.fn(),
        });

        render(<HomePage />);

        fireEvent.change(screen.getByLabelText(/Deep Scan Symbol/i), { target: { value: 'mfot' } });
        fireEvent.click(screen.getByRole('button', { name: /Analyze/i }));

        expect(mockRouterPush).toHaveBeenCalledWith('/oracle?ticker=MFOT');
    });

    it('routes override to Oracle even without a ticker', () => {
        mockUseHomeRuntime.mockReturnValue(makeRuntime());
        mockUseHomeActions.mockReturnValue({
            initializeLoading: false,
            initializeRun: jest.fn(),
            setDeskMode: jest.fn(),
        });

        render(<HomePage />);

        fireEvent.click(screen.getByRole('button', { name: /Override/i }));

        expect(mockRouterPush).toHaveBeenCalledWith('/oracle');
    });

    it('routes the operator to Telegram from the release rail action', () => {
        mockUseHomeRuntime.mockReturnValue(makeRuntime());
        mockUseHomeActions.mockReturnValue({
            initializeLoading: false,
            initializeRun: jest.fn(),
            setDeskMode: jest.fn(),
        });
        render(<HomePage />);

        fireEvent.click(screen.getAllByRole('button', { name: /Dispatch Rail/i })[0]);

        expect(mockRouterPush).toHaveBeenCalledWith('/telegram');
    });
});
