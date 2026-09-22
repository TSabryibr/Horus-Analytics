import React from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react';

import OraclePage from './page';

const mockUseAssetIntelligence = jest.fn();
const mockSearchParamsGet = jest.fn();
const mockPromoteCandidate = jest.fn();

jest.mock('next/navigation', () => ({
    useSearchParams: () => ({
        get: mockSearchParamsGet,
    }),
}));

jest.mock('./hooks/useAssetIntelligence', () => ({
    useAssetIntelligence: () => mockUseAssetIntelligence(),
    normalizeOracleAssetChoice: (value: string) => String(value || '').trim().toUpperCase() === 'UNIVERSE' ? 'ALL' : String(value || '').trim().toUpperCase(),
}));

jest.mock('../context/GlobalDataContext', () => ({
    useSignalDeskData: () => ({
        promoteCandidate: mockPromoteCandidate,
    }),
}));

jest.mock('./components/tac-briefing/SupportResistanceRadar', () => ({
    SupportResistanceRadar: ({ mode, leadTicker }: { mode?: string; leadTicker?: string }) => (
        <div>{mode === 'scope' ? `S/R Radar Scope ${leadTicker}` : 'S/R Radar Surface'}</div>
    ),
}));

jest.mock('./components/tac-briefing/SentimentTimeline', () => ({
    SentimentTimeline: ({ regime, mode, leadTicker }: { regime: string; mode?: string; leadTicker?: string }) => (
        <div>{mode === 'scope' ? `Sentiment Narrative Scope ${regime} ${leadTicker}` : `Sentiment Narrative ${regime}`}</div>
    ),
}));

type OracleRuntimeMock = {
    selectedTicker: string;
    setSelectedTicker: jest.Mock;
    report: any;
    reportLoading: boolean;
    refreshReport: jest.Mock;
    history: Array<{ id: number; ticker: string; generated_at: string; confidence_score: number; source_module: string }>;
    historyLoading: boolean;
    selectedReportId: number | null;
    selectHistoryReport: jest.Mock;
};

function makeRuntime(overrides: Partial<OracleRuntimeMock> = {}): OracleRuntimeMock {
    return {
        selectedTicker: 'CIIC',
        setSelectedTicker: jest.fn(),
        report: {
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
                    target: 24.4,
                    stop: 19.8,
                },
                sentiment: {
                    score: 64,
                    regime: 'POSITIVE',
                },
                news_mentions: [],
                technical_context: {
                    is_bull_trap: false,
                },
                whale_flow: [{ type: 'ACCUMULATION' }],
                arbitrage: {
                    correlation: 0.82,
                },
            },
        },
        reportLoading: false,
        refreshReport: jest.fn(),
        history: [
            {
                id: 9,
                ticker: 'CIIC',
                generated_at: '2026-04-11T11:45:00.000Z',
                confidence_score: 68,
                source_module: 'openai:gpt-5.3-codex',
            },
        ],
        historyLoading: false,
        selectedReportId: null,
        selectHistoryReport: jest.fn(),
        ...overrides,
    };
}

describe('OraclePage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockSearchParamsGet.mockReturnValue(null);
        mockPromoteCandidate.mockResolvedValue(true);
    });

    it('renders the refreshed oracle command shell and tactical rail', () => {
        mockUseAssetIntelligence.mockReturnValue(makeRuntime());

        render(<OraclePage />);

        expect(screen.getByRole('heading', { name: /AI Price Forecast/i })).toBeInTheDocument();
        expect(screen.getByText(/🟢 BULLISH BIAS/i)).toBeInTheDocument();
        expect(screen.getAllByText('72%').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('21.20')).toBeInTheDocument();
        expect(screen.getByText('24.40')).toBeInTheDocument();
        expect(screen.getByText('19.80')).toBeInTheDocument();
        expect(screen.getByText(/Intelligence Stream::CIIC_INTELLIGENCE_BRIEFING/i)).toBeInTheDocument();
        expect(screen.getByText('Tactical Archives')).toBeInTheDocument();
        expect(screen.getByText('Nodes: 1 Archival')).toBeInTheDocument();
        expect(screen.getByText('Tactical Status')).toBeInTheDocument();
        expect(screen.getByText('BULLISH')).toBeInTheDocument();
        expect(screen.getByLabelText(/Oracle Asset Scope/i)).toBeInTheDocument();
    });

    it('renders SWR error recovery card when report fetch fails', () => {
        mockUseAssetIntelligence.mockReturnValue(makeRuntime({
            report: null,
            reportError: new Error('SWR_FETCH_TIMEOUT: Oracle API unreachable'),
        }));

        render(<OraclePage />);

        expect(screen.getByText('Oracle Report Fetch Failure')).toBeInTheDocument();
        expect(screen.getByText('SWR_FETCH_TIMEOUT: Oracle API unreachable')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
    });

    it('submits a ticker through the command lane in uppercase', () => {
        const setSelectedTicker = jest.fn();
        mockUseAssetIntelligence.mockReturnValue(makeRuntime({ setSelectedTicker }));

        render(<OraclePage />);

        const input = screen.getByPlaceholderText(/ENTER TICKER FOR DEEP INTELLIGENCE/i);
        fireEvent.change(input, { target: { value: 'mfot' } });
        fireEvent.click(screen.getByRole('button', { name: /Analyze/i }));

        expect(setSelectedTicker).toHaveBeenCalledWith('MFOT');
        expect((input as HTMLInputElement).value).toBe('');
    });

    it('delegates refresh and history selection actions', () => {
        const refreshReport = jest.fn();
        const selectHistoryReport = jest.fn();

        mockUseAssetIntelligence.mockReturnValue(makeRuntime({
            refreshReport,
            selectHistoryReport,
        }));

        render(<OraclePage />);

        fireEvent.click(screen.getAllByRole('button', { name: /Refresh Intel/i })[0]);
        expect(refreshReport).toHaveBeenCalledTimes(1);

        fireEvent.click(screen.getByText('openai:gpt-5.3-codex'));
        expect(selectHistoryReport).toHaveBeenCalledWith(9);
    });

    it('promotes the active oracle recommendation into the desk lane', async () => {
        mockUseAssetIntelligence.mockReturnValue(makeRuntime());

        render(<OraclePage />);

        await act(async () => {
            fireEvent.click(screen.getByRole('button', { name: /Promote to Swing Lane/i }));
        });

        expect(mockPromoteCandidate).toHaveBeenCalledWith(expect.objectContaining({
            lane: 'SWING',
            ticker: 'CIIC',
            source_module: 'ORACLE',
        }));
    });

    it('shows archive mode chrome and disables shell refresh while loading', () => {
        mockUseAssetIntelligence.mockReturnValue(makeRuntime({
            selectedReportId: 9,
            report: null,
            reportLoading: true,
        }));

        render(<OraclePage />);

        expect(screen.getAllByText(/Archived Briefing/i).length).toBeGreaterThan(0);
        expect(screen.getByText('Archive')).toBeInTheDocument();
        expect(screen.getByLabelText('refresh-oracle')).toBeDisabled();
    });

    it('hydrates the selected ticker from the route query string', () => {
        const setSelectedTicker = jest.fn();
        mockSearchParamsGet.mockImplementation((key: string) => key === 'ticker' ? 'oras' : null);
        mockUseAssetIntelligence.mockReturnValue(makeRuntime({ setSelectedTicker }));

        render(<OraclePage />);

        expect(setSelectedTicker).toHaveBeenCalledWith('ORAS');
    });

    it('switches Oracle market scope through the asset selector', () => {
        const setSelectedTicker = jest.fn();
        mockUseAssetIntelligence.mockReturnValue(makeRuntime({ selectedTicker: 'EGX30', setSelectedTicker }));

        render(<OraclePage />);

        fireEvent.change(screen.getByLabelText(/Oracle Asset Scope/i), { target: { value: 'ALL' } });

        expect(setSelectedTicker).toHaveBeenCalledWith('ALL');
    });

    it('renders hybrid radar and split sentiment for broad market scopes', () => {
        mockUseAssetIntelligence.mockReturnValue(makeRuntime({
            selectedTicker: 'EGX70',
            report: {
                verdict: 'BULLISH',
                confidence: 72,
                generated_at: '2026-04-12T12:00:00.000Z',
                analysis: {
                    short_term: 'Momentum expansion is improving.',
                    tactical_edge: 'Compression resolved with constructive breadth.',
                    risk_profile: 'A failed follow-through would invalidate the setup.',
                },
                snapshot: {
                    scope: 'EGX70',
                    lead_ticker: 'COMI',
                    scope_levels: {
                        supports: [{ price: 79.1, strength: 0.8, members: 3 }],
                        resistances: [{ price: 88.4, strength: 0.76, members: 4 }],
                    },
                    lead_ticker_levels: {
                        ticker: 'COMI',
                        entry: 82.5,
                        stop: 79.0,
                        target: 88.6,
                    },
                    recommendation: {
                        entry: 82.5,
                        target: 88.6,
                        stop: 79.0,
                    },
                    sentiment: {
                        score: 61,
                        regime: 'POSITIVE',
                    },
                    scope_news_mentions: [{ title: 'Scope breadth improves' }],
                    lead_ticker_news_mentions: [{ title: 'COMI extends rally' }],
                },
            },
        }));

        render(<OraclePage />);

        expect(screen.getByText('S/R Radar Scope COMI')).toBeInTheDocument();
        expect(screen.getByText('Sentiment Narrative Scope POSITIVE COMI')).toBeInTheDocument();
    });

    it('uses price-history levels for single-ticker radar when no trade setup exists', () => {
        mockUseAssetIntelligence.mockReturnValue(makeRuntime({
            selectedTicker: 'ACAP',
            report: {
                verdict: 'NEUTRAL',
                confidence: 35,
                generated_at: '2026-05-20T14:04:00.000Z',
                analysis: {
                    short_term: 'No ACAP-specific signal is active yet.',
                    tactical_edge: 'No recommendation levels are currently attached to ACAP.',
                    risk_profile: 'Wait for ticker-specific confirmation.',
                },
                snapshot: {
                    ticker: 'ACAP',
                    price_levels: {
                        current_price: 8.31,
                        supports: [{ price: 8.28, strength: 0.6, members: 2 }],
                        resistances: [{ price: 8.75, strength: 0.55, members: 1 }],
                    },
                    recommendation: {
                        entry: null,
                        target: null,
                        stop: null,
                    },
                    sentiment: {
                        score: 50,
                        regime: 'NEUTRAL',
                    },
                    news_mentions: [],
                    technical_context: {
                        is_bull_trap: false,
                    },
                },
            },
        }));

        render(<OraclePage />);

        expect(screen.getByText('S/R Radar Surface')).toBeInTheDocument();
        expect(screen.getByText('Sentiment Narrative NEUTRAL')).toBeInTheDocument();
        expect(screen.queryByText(/No ACAP support\/resistance levels/i)).not.toBeInTheDocument();
    });

    it('switches between Asset Intel, Market Canary, and Volatility Coil tabs', () => {
        mockUseAssetIntelligence.mockReturnValue(makeRuntime());

        render(<OraclePage />);

        // Default tab should be Asset Intel
        expect(screen.getByText(/Intelligence Stream::CIIC_INTELLIGENCE_BRIEFING/i)).toBeInTheDocument();

        // Switch to Market Canary tab
        fireEvent.click(screen.getByText('Market Canary'));
        expect(screen.getByText(/Price vs Breadth Divergence Engine/i)).toBeInTheDocument();

        // Switch to Volatility Coil tab
        fireEvent.click(screen.getByText('Volatility Coil'));
        expect(screen.getByText('The Coil (Squeezes)')).toBeInTheDocument();
    });
});
