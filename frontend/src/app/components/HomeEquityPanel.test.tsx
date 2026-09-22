import { render, screen } from '@testing-library/react';

import { HomeEquityPanel } from './HomeEquityPanel';

describe('HomeEquityPanel', () => {
    it('renders the provided chart content when curve data exists', () => {
        render(
            <HomeEquityPanel hasCurve chart={<div>equity-chart</div>} />
        );

        expect(screen.getByText('EQUITY_CURVE_REALTIME')).toBeInTheDocument();
        expect(screen.getByText('equity-chart')).toBeInTheDocument();
    });

    it('renders the empty state when there is no curve data', () => {
        render(
            <HomeEquityPanel hasCurve={false} chart={<div>equity-chart</div>} />
        );

        expect(screen.getByText('Telemetry Offline')).toBeInTheDocument();
    });
});
