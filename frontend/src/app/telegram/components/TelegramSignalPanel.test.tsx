import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { TelegramSignalPanel } from './TelegramSignalPanel';

describe('TelegramSignalPanel', () => {
    it('renders signal and report controls and forwards actions', () => {
        const setSignalForm = jest.fn();
        const onDeskRelease = jest.fn();
        const onAutopilotRun = jest.fn();
        const onRetryFailedDeliveries = jest.fn();
        const onSignalBroadcast = jest.fn();
        const onAiDailyReport = jest.fn();
        const onAnalysisReport = jest.fn();
        const onScan = jest.fn();

        render(
            <TelegramSignalPanel
                signalForm={{
                    ticker: 'ABC',
                    entry: '85.5',
                    sl: '82',
                    tp1: '92',
                    tp2: '',
                    caption: '',
                }}
                sending={false}
                activeRunId={91}
                autopilotReady
                failedDeliveryCount={2}
                setSignalForm={setSignalForm}
                onDeskRelease={onDeskRelease}
                onAutopilotRun={onAutopilotRun}
                onRetryFailedDeliveries={onRetryFailedDeliveries}
                onSignalBroadcast={onSignalBroadcast}
                onAiDailyReport={onAiDailyReport}
                onAnalysisReport={onAnalysisReport}
                onScan={onScan}
            />
        );

        fireEvent.change(screen.getByPlaceholderText('e.g. COMI'), {
            target: { value: 'COMI' },
        });
        fireEvent.click(screen.getByRole('button', { name: /Run Autopilot Dispatch/i }));
        fireEvent.click(screen.getByRole('button', { name: /Dispatch Latest Desk Run/i }));
        fireEvent.click(screen.getByRole('button', { name: /Retry Failed Deliveries/i }));
        fireEvent.click(screen.getByRole('button', { name: /Blast Horus Signal Card/i }));
        fireEvent.click(screen.getByRole('button', { name: /Broadcast AI Daily Report/i }));
        fireEvent.click(screen.getByRole('button', { name: /Broadcast Weekly Report/i }));
        fireEvent.click(screen.getByRole('button', { name: /Broadcast Intraday/i }));

        expect(setSignalForm).toHaveBeenCalledWith(
            expect.objectContaining({
                ticker: 'COMI',
            })
        );
        expect(onAutopilotRun).toHaveBeenCalled();
        expect(onDeskRelease).toHaveBeenCalled();
        expect(onRetryFailedDeliveries).toHaveBeenCalled();
        expect(onSignalBroadcast).toHaveBeenCalled();
        expect(onAiDailyReport).toHaveBeenCalled();
        expect(onAnalysisReport).toHaveBeenCalledWith('weekly');
        expect(onScan).toHaveBeenCalledWith('INTRADAY');
    });
});
