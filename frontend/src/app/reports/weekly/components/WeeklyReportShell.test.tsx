import { fireEvent, render, screen } from '@testing-library/react';

import { WeeklyReportShell } from './WeeklyReportShell';

describe('WeeklyReportShell', () => {
    it('renders shell chrome and dispatches period, refresh, and broadcast actions', () => {
        const onSetPeriod = jest.fn();
        const onRefresh = jest.fn();
        const onBroadcast = jest.fn();

        render(
            <WeeklyReportShell
                broadcasting={false}
                loading={false}
                onBroadcast={onBroadcast}
                onRefresh={onRefresh}
                onSetPeriod={onSetPeriod}
                period="weekly"
            >
                <div>weekly-report-body</div>
            </WeeklyReportShell>,
        );

        expect(screen.getByText('Market Analysis Report')).toBeInTheDocument();
        expect(screen.getByText('📅 WEEKLY REVIEW')).toBeInTheDocument();
        expect(screen.getByText('weekly-report-body')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Monthly/i }));
        fireEvent.click(screen.getByRole('button', { name: /Refresh/i }));
        fireEvent.click(screen.getByRole('button', { name: /Broadcast/i }));

        expect(onSetPeriod).toHaveBeenCalledWith('monthly');
        expect(onRefresh).toHaveBeenCalledTimes(1);
        expect(onBroadcast).toHaveBeenCalledTimes(1);
    });

    it('renders error and feedback banners and disables actions while busy', () => {
        render(
            <WeeklyReportShell
                broadcasting
                error="Failed to load analysis report."
                feedback="Weekly report broadcast sent to Telegram."
                loading
                onBroadcast={jest.fn()}
                onRefresh={jest.fn()}
                onSetPeriod={jest.fn()}
                period="monthly"
            >
                <div>weekly-report-body</div>
            </WeeklyReportShell>,
        );

        expect(screen.getByText('Failed to load analysis report.')).toBeInTheDocument();
        expect(screen.getByText('Weekly report broadcast sent to Telegram.')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Monthly/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Refresh/i })).toBeDisabled();
        expect(screen.getByRole('button', { name: /Broadcast/i })).toBeDisabled();
    });

    it('shows cache freshness indicator when cacheInfo is provided', () => {
        render(
            <WeeklyReportShell
                broadcasting={false}
                cacheInfo={{ cached: true, ttlSec: 900, ageSec: 120 }}
                loading={false}
                onBroadcast={jest.fn()}
                onRefresh={jest.fn()}
                onSetPeriod={jest.fn()}
                period="weekly"
            >
                <div>body</div>
            </WeeklyReportShell>,
        );

        expect(screen.getByText('⚡ CACHED (2m ago)')).toBeInTheDocument();
    });

    it('shows stale warning when cache age exceeds 5 minutes', () => {
        render(
            <WeeklyReportShell
                broadcasting={false}
                cacheInfo={{ cached: true, ttlSec: 600, ageSec: 600 }}
                loading={false}
                onBroadcast={jest.fn()}
                onRefresh={jest.fn()}
                onSetPeriod={jest.fn()}
                period="weekly"
            >
                <div>body</div>
            </WeeklyReportShell>,
        );

        expect(screen.getByText('⚡ CACHED (10m ago)')).toBeInTheDocument();
    });
});
