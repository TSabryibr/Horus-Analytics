import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { ReplayPanel } from './ReplayPanel';

const baseProps = {
    replayDate: '2026-05-12',
    setReplayDate: jest.fn(),
    replaySpeed: '50',
    setReplaySpeed: jest.fn(),
    replayNotify: false,
    setReplayNotify: jest.fn(),
    replayReport: false,
    setReplayReport: jest.fn(),
    replayMode: 'SINGLE_DAY' as const,
    setReplayMode: jest.fn(),
    replayStartDate: '2026-05-12',
    setReplayStartDate: jest.fn(),
    replayEndDate: '2026-05-14',
    setReplayEndDate: jest.fn(),
    replayResetPortfolio: true,
    setReplayResetPortfolio: jest.fn(),
    replayCloseOpenPositionsEnd: false,
    setReplayCloseOpenPositionsEnd: jest.fn(),
    replayTreatMissingDaysAsHolidays: false,
    setReplayTreatMissingDaysAsHolidays: jest.fn(),
    replayLiveChannelRouting: false,
    setReplayLiveChannelRouting: jest.fn(),
    replayLoading: false,
    replayError: null,
    selectedProfileLabel: 'Horus Core',
    onStart: jest.fn(),
    onStop: jest.fn(),
};

describe('ReplayPanel', () => {
    it('shows campaign controls and launches with campaign date requirements', () => {
        const setReplayMode = jest.fn();
        const setReplayResetPortfolio = jest.fn();
        const setReplayCloseOpenPositionsEnd = jest.fn();
        const setReplayTreatMissingDaysAsHolidays = jest.fn();
        const setReplayLiveChannelRouting = jest.fn();
        const onStart = jest.fn();

        render(
            <ReplayPanel
                {...baseProps}
                replayStatus={null}
                replayMode="CAMPAIGN"
                setReplayMode={setReplayMode}
                setReplayResetPortfolio={setReplayResetPortfolio}
                setReplayCloseOpenPositionsEnd={setReplayCloseOpenPositionsEnd}
                setReplayTreatMissingDaysAsHolidays={setReplayTreatMissingDaysAsHolidays}
                setReplayLiveChannelRouting={setReplayLiveChannelRouting}
                onStart={onStart}
            />
        );

        expect(screen.getByRole('button', { name: /Single Day/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /^Campaign$/i })).toBeInTheDocument();
        expect(screen.getByText('Campaign Start')).toBeInTheDocument();
        expect(screen.getByText('Campaign End')).toBeInTheDocument();
        expect(screen.getByText('Reset Portfolio')).toBeInTheDocument();
        expect(screen.getByText('Close Open At End')).toBeInTheDocument();
        expect(screen.getByText('Missing Days = Holidays')).toBeInTheDocument();
        expect(screen.getByText('Live Channel Routing')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Single Day/i }));
        fireEvent.click(screen.getByText('Reset Portfolio'));
        fireEvent.click(screen.getByText('Close Open At End'));
        fireEvent.click(screen.getByText('Missing Days = Holidays'));
        fireEvent.click(screen.getByText('Live Channel Routing'));
        fireEvent.click(screen.getByRole('button', { name: /Launch Campaign/i }));

        expect(setReplayMode).toHaveBeenCalledWith('SINGLE_DAY');
        expect(setReplayResetPortfolio).toHaveBeenCalledWith(false);
        expect(setReplayCloseOpenPositionsEnd).toHaveBeenCalledWith(true);
        expect(setReplayTreatMissingDaysAsHolidays).toHaveBeenCalledWith(true);
        expect(setReplayLiveChannelRouting).toHaveBeenCalledWith(true);
        expect(onStart).toHaveBeenCalledTimes(1);
    });

    it('shows replay results from replay status', () => {
        render(
            <ReplayPanel
                {...baseProps}
                replayStatus={{
                    status: 'COMPLETED',
                    date: '2026-05-12',
                    speed: 50,
                    notify: false,
                    report: false,
                    started_at: '2026-05-13T02:23:21',
                    completed_at: '2026-05-13T02:34:03',
                    current_time: '15:00',
                    market_open: '10:00',
                    market_close: '14:30',
                    ticks_completed: 54,
                    total_ticks: 54,
                    progress_pct: 100,
                    signals_found: 16,
                    pending_entries_count: 2,
                    scan_results: [],
                    active_trades: [
                        {
                            ticker: 'SCEM',
                            side: 'BUY',
                            state: 'OPEN',
                            entry_price: 66.8,
                            stop_loss: 64.2489,
                            tp1: 70.2015,
                            tp2: 73.0096,
                            entry_at: '2026-05-12T10:05:00',
                        },
                        {
                            ticker: 'CLOSED',
                            side: 'BUY',
                            state: 'CLOSED',
                            entry_price: 10,
                            stop_loss: 9,
                            tp1: 11,
                            tp2: 12,
                            entry_at: '2026-05-12T10:10:00',
                            exit_at: '2026-05-12T11:20:00',
                            exit_price: 12,
                        },
                    ],
                    error: null,
                }}
            />
        );

        expect(screen.getByText('Replay Results')).toBeInTheDocument();
        expect(screen.getByText('Pending Open')).toBeInTheDocument();
        expect(screen.getByText('SCEM')).toBeInTheDocument();
        expect(screen.getByText('66.80')).toBeInTheDocument();
        expect(screen.getByText('64.25')).toBeInTheDocument();
        expect(screen.getByText('70.20')).toBeInTheDocument();
        expect(screen.getByText('73.01')).toBeInTheDocument();
        expect(screen.getAllByText('CLOSED').length).toBeGreaterThan(0);
        expect(screen.getAllByText('12.00').length).toBeGreaterThan(0);
    });

    it('renders Export Excel button and invokes onDownloadExcel on click', () => {
        const onDownloadExcel = jest.fn();
        render(
            <ReplayPanel
                {...baseProps}
                onDownloadExcel={onDownloadExcel}
                replayStatus={{
                    status: 'COMPLETED',
                    ticks_completed: 50,
                    total_ticks: 50,
                    active_trades: [],
                    scan_results: [],
                } as any}
            />
        );

        const exportBtn = screen.getByRole('button', { name: /EXPORT EXCEL/i });
        expect(exportBtn).toBeInTheDocument();
        expect(exportBtn).not.toBeDisabled();

        fireEvent.click(exportBtn);
        expect(onDownloadExcel).toHaveBeenCalledTimes(1);
    });
});
