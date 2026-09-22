import React from 'react';
import { render, screen } from '@testing-library/react';

import { LiveStatusPanel } from './LiveStatusPanel';

describe('LiveStatusPanel', () => {
    it('renders the market metrics and running system state', () => {
        render(
            <LiveStatusPanel
                lastPrice="103.000"
                pctChange="1.25"
                priceChangePositive={true}
                volumeLabel="18,000"
                liveRunning={true}
                marketOpen={true}
                pollLabel="15s"
                liveLastUpdate="10:30:00 AM"
            />
        );

        expect(screen.getByText('103.000')).toBeInTheDocument();
        expect(screen.getByText('1.25%')).toBeInTheDocument();
        expect(screen.getByText('18,000')).toBeInTheDocument();
        expect(screen.getByText(/Feed running/i)).toBeInTheDocument();
        expect(screen.getByText(/Poll 15s/i)).toBeInTheDocument();
    });

    it('renders the paused and market-closed status copy', () => {
        render(
            <LiveStatusPanel
                lastPrice="0.000"
                pctChange="-0.50"
                priceChangePositive={false}
                volumeLabel="0"
                liveRunning={false}
                marketOpen={false}
                pollLabel="15s"
                liveLastUpdate="N/A"
            />
        );

        expect(screen.getByText(/Feed paused/i)).toBeInTheDocument();
        expect(screen.getByText(/Market Closed/i)).toBeInTheDocument();
    });
});
