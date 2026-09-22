import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { LiveShell } from './LiveShell';

describe('LiveShell', () => {
    it('renders the header toolbar and wires runtime actions', () => {
        const onToggleRadar = jest.fn();
        const onChangeTicker = jest.fn();
        const onChangeAutoRefreshMs = jest.fn();
        const onToggleAutoRefresh = jest.fn();
        const onRefresh = jest.fn();
        const onToggleLiveFeed = jest.fn();

        render(
            <LiveShell
                lastUpdate="10:32:00"
                liveRunning={false}
                marketOpen={true}
                pollOptions={[5000, 15000]}
                autoRefreshMs={15000}
                autoRefreshEnabled={true}
                ticker="COMI"
                tickers={['COMI', 'HRHO']}
                radarCount={3}
                showRadar={false}
                refreshing={false}
                wsConnected={true}
                error={null}
                sovereignAlerts={[]}
                onToggleRadar={onToggleRadar}
                onChangeTicker={onChangeTicker}
                onChangeAutoRefreshMs={onChangeAutoRefreshMs}
                onToggleAutoRefresh={onToggleAutoRefresh}
                onRefresh={onRefresh}
                onToggleLiveFeed={onToggleLiveFeed}
                onDismissSovereignAlert={jest.fn()}
            >
                <div data-testid="live-shell-children" />
            </LiveShell>
        );

        expect(screen.getByRole('heading', { name: /Live Terminal/i })).toBeInTheDocument();
        expect(screen.getByText('10:32:00')).toBeInTheDocument();
        expect(screen.getByText('⚡ WS Live')).toBeInTheDocument();
        expect(screen.getByText('Live Monitoring')).toBeInTheDocument();
        expect(screen.getByTestId('live-shell-children')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Radar/i }));
        fireEvent.change(screen.getByDisplayValue('COMI'), { target: { value: 'HRHO' } });
        fireEvent.change(screen.getByTitle('Polling interval'), { target: { value: '5000' } });
        fireEvent.click(screen.getByRole('button', { name: /Auto On/i }));
        fireEvent.click(screen.getByTitle('Force refresh'));
        fireEvent.click(screen.getByRole('button', { name: /Start Feed/i }));

        expect(onToggleRadar).toHaveBeenCalled();
        expect(onChangeTicker).toHaveBeenCalledWith('HRHO');
        expect(onChangeAutoRefreshMs).toHaveBeenCalledWith(5000);
        expect(onToggleAutoRefresh).toHaveBeenCalled();
        expect(onRefresh).toHaveBeenCalled();
        expect(onToggleLiveFeed).toHaveBeenCalled();
    });

    it('renders error and sovereign alerts and allows dismiss', () => {
        const onDismissSovereignAlert = jest.fn();

        render(
            <LiveShell
                lastUpdate=""
                liveRunning={true}
                marketOpen={true}
                pollOptions={[5000]}
                autoRefreshMs={5000}
                autoRefreshEnabled={false}
                ticker="COMI"
                tickers={['COMI']}
                radarCount={0}
                showRadar={true}
                refreshing={true}
                wsConnected={true}
                error="Feed failed"
                sovereignAlerts={[
                    { Type: 'DEBT_STRESS', Message: 'Yield spike detected' },
                ]}
                onToggleRadar={jest.fn()}
                onChangeTicker={jest.fn()}
                onChangeAutoRefreshMs={jest.fn()}
                onToggleAutoRefresh={jest.fn()}
                onRefresh={jest.fn()}
                onToggleLiveFeed={jest.fn()}
                onDismissSovereignAlert={onDismissSovereignAlert}
            >
                <div />
            </LiveShell>
        );

        expect(screen.getByText('Feed failed')).toBeInTheDocument();
        expect(screen.getByText(/DEBT STRESS/i)).toBeInTheDocument();
        expect(screen.getByText(/Yield spike detected/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Stop Feed/i })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Dismiss/i }));
        expect(onDismissSovereignAlert).toHaveBeenCalledWith(0);
    });

    it('shows alerts offline banner when websocket is disconnected', () => {
        render(
            <LiveShell
                lastUpdate=""
                liveRunning={true}
                marketOpen={true}
                pollOptions={[5000]}
                autoRefreshMs={5000}
                autoRefreshEnabled={false}
                ticker="COMI"
                tickers={['COMI']}
                radarCount={0}
                showRadar={false}
                refreshing={false}
                wsConnected={false}
                error={null}
                sovereignAlerts={[]}
                onToggleRadar={jest.fn()}
                onChangeTicker={jest.fn()}
                onChangeAutoRefreshMs={jest.fn()}
                onToggleAutoRefresh={jest.fn()}
                onRefresh={jest.fn()}
                onToggleLiveFeed={jest.fn()}
                onDismissSovereignAlert={jest.fn()}
            >
                <div />
            </LiveShell>
        );

        expect(screen.getByText(/Sovereign alerts offline/i)).toBeInTheDocument();
    });

    it('hides alerts offline banner when websocket is connected', () => {
        render(
            <LiveShell
                lastUpdate=""
                liveRunning={true}
                marketOpen={true}
                pollOptions={[5000]}
                autoRefreshMs={5000}
                autoRefreshEnabled={false}
                ticker="COMI"
                tickers={['COMI']}
                radarCount={0}
                showRadar={false}
                refreshing={false}
                wsConnected={true}
                error={null}
                sovereignAlerts={[]}
                onToggleRadar={jest.fn()}
                onChangeTicker={jest.fn()}
                onChangeAutoRefreshMs={jest.fn()}
                onToggleAutoRefresh={jest.fn()}
                onRefresh={jest.fn()}
                onToggleLiveFeed={jest.fn()}
                onDismissSovereignAlert={jest.fn()}
            >
                <div />
            </LiveShell>
        );

        expect(screen.queryByText(/Sovereign alerts offline/i)).not.toBeInTheDocument();
    });

    it('disables start feed button when market is closed', () => {
        render(
            <LiveShell
                lastUpdate=""
                liveRunning={false}
                marketOpen={false}
                pollOptions={[5000]}
                autoRefreshMs={5000}
                autoRefreshEnabled={false}
                ticker="COMI"
                tickers={['COMI']}
                radarCount={0}
                showRadar={false}
                refreshing={false}
                wsConnected={true}
                error={null}
                sovereignAlerts={[]}
                onToggleRadar={jest.fn()}
                onChangeTicker={jest.fn()}
                onChangeAutoRefreshMs={jest.fn()}
                onToggleAutoRefresh={jest.fn()}
                onRefresh={jest.fn()}
                onToggleLiveFeed={jest.fn()}
                onDismissSovereignAlert={jest.fn()}
            >
                <div />
            </LiveShell>
        );

        const feedButton = screen.getByRole('button', { name: /Market Closed/i });
        expect(feedButton).toBeDisabled();
    });
});
