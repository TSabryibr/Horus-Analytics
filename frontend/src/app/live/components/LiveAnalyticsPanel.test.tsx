import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import { LiveAnalyticsPanel } from './LiveAnalyticsPanel';

const radarItems = [
    {
        Ticker: 'COMI',
        Signal_Score: 9,
        Price: '104.250',
        Risk_Reward_Ratio: '2.8',
        Resistance_20D: '110.500',
        Key_Resistance_1: '112.400',
    },
];

describe('LiveAnalyticsPanel', () => {
    it('renders radar items and forwards ticker selection', () => {
        const onSelectTicker = jest.fn();

        render(
            <LiveAnalyticsPanel
                showRadar={true}
                analyticsLoading={false}
                radarItems={radarItems}
                onSelectTicker={onSelectTicker}
            />
        );

        expect(screen.getByText('COMI')).toBeInTheDocument();
        expect(screen.getByText('SCORE 9')).toBeInTheDocument();
        expect(screen.getByText('RR 2.8X')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /Open COMI/i }));
        expect(onSelectTicker).toHaveBeenCalledWith('COMI');
    });

    it('renders loading and empty states when no radar items exist', () => {
        const { rerender } = render(
            <LiveAnalyticsPanel
                showRadar={true}
                analyticsLoading={true}
                radarItems={[]}
                onSelectTicker={jest.fn()}
            />
        );

        expect(screen.getByText(/Loading analytics radar/i)).toBeInTheDocument();

        rerender(
            <LiveAnalyticsPanel
                showRadar={true}
                analyticsLoading={false}
                radarItems={[]}
                onSelectTicker={jest.fn()}
            />
        );

        expect(screen.getByText(/No analytics candidates available yet/i)).toBeInTheDocument();
    });

    it('renders nothing when radar mode is hidden', () => {
        const { container } = render(
            <LiveAnalyticsPanel
                showRadar={false}
                analyticsLoading={false}
                radarItems={radarItems}
                onSelectTicker={jest.fn()}
            />
        );

        expect(container).toBeEmptyDOMElement();
    });
});
