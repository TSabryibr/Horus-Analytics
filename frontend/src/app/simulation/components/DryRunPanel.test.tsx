import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

import type { DryRunStatus } from '../hooks/useDryRun';
import { DryRunPanel } from './DryRunPanel';

jest.mock('recharts', () => {
    const MockContainer = () => <div data-testid="mock-recharts-container" />;
    return {
        ResponsiveContainer: MockContainer,
        BarChart: MockContainer,
        Bar: MockContainer,
        XAxis: () => null,
        YAxis: () => null,
        Tooltip: () => null,
        Cell: () => null,
    };
});

describe('DryRunPanel', () => {
    const mockProps = {
        dryrunDate: '2026-07-18',
        setDryrunDate: jest.fn(),
        dryrunNotify: false,
        setDryrunNotify: jest.fn(),
        dryrunReport: true,
        setDryrunReport: jest.fn(),
        dryrunAiReport: false,
        setDryrunAiReport: jest.fn(),
        dryrunLoading: false,
        dryrunStatus: null,
        dryrunError: null,
        selectedProfileLabel: 'Horus Core',
        onStart: jest.fn(),
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders form controls and handles date input change', () => {
        render(<DryRunPanel {...mockProps} />);

        const dateInput = screen.getByDisplayValue('2026-07-18');
        expect(dateInput).toBeInTheDocument();

        fireEvent.change(dateInput, { target: { value: '2026-07-19' } });
        expect(mockProps.setDryrunDate).toHaveBeenCalledWith('2026-07-19');
    });

    it('triggers toggle callbacks on option chips', () => {
        render(<DryRunPanel {...mockProps} />);

        const telegramButton = screen.getByRole('button', { name: /Telegram/i });
        const localReportsButton = screen.getByRole('button', { name: /Local Reports/i });
        const aiReportButton = screen.getByRole('button', { name: /AI Report/i });

        fireEvent.click(telegramButton);
        expect(mockProps.setDryrunNotify).toHaveBeenCalledWith(true);

        fireEvent.click(localReportsButton);
        expect(mockProps.setDryrunReport).toHaveBeenCalledWith(false);

        fireEvent.click(aiReportButton);
        expect(mockProps.setDryrunAiReport).toHaveBeenCalledWith(true);
    });

    it('handles fire button click', () => {
        render(<DryRunPanel {...mockProps} />);

        const fireButton = screen.getByRole('button', { name: /FIRE DRY RUN/i });
        fireEvent.click(fireButton);

        expect(mockProps.onStart).toHaveBeenCalled();
    });

    it('renders pipeline steps and results when active', () => {
        const dryrunStatus: DryRunStatus = {
            status: 'COMPLETED',
            date: '2026-07-18',
            notify: false,
            report: true,
            ai_report: false,
            started_at: '2026-07-18T10:00:00',
            completed_at: '2026-07-18T10:00:12',
            signals_found: 2,
            regime: 'BULLISH',
            duration_sec: 12,
            profile_name: 'Pine Standard',
            steps: [
                { step: 'Ingest Data', status: 'completed', duration_sec: 2, started_at: '2026-07-18T10:00:00', result: null, error: null },
                { step: 'Run Scan', status: 'completed', duration_sec: 10, started_at: '2026-07-18T10:00:02', result: null, error: null },
            ],
            signals: [
                { ticker: 'COMI', type: 'BUY', score: 8, entry: 100, stop_loss: 95, target: 110 },
            ],
            breadth: 0.75,
            report_generated: true,
            ai_report_generated: false,
            telegram_messages_sent: 1,
            error: null,
        };

        render(<DryRunPanel {...mockProps} dryrunStatus={dryrunStatus} />);

        expect(screen.getByText('Pine Standard')).toBeInTheDocument();
        expect(screen.getByText('DRILL PASSED ⚡')).toBeInTheDocument();
        expect(screen.getByText('BULLISH')).toBeInTheDocument();
        expect(screen.getByText('12s')).toBeInTheDocument();
        expect(screen.getByText('Ingest Data')).toBeInTheDocument();
        expect(screen.getByText('COMI')).toBeInTheDocument();
    });
});
