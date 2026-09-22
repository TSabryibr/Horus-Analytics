import { render, screen } from '@testing-library/react';
import { LiveChartTooltip } from './LiveChartTooltip';
import { Candle } from '../hooks/useLiveRuntime';

describe('LiveChartTooltip', () => {
    it('returns null if inactive or missing payload', () => {
        const { container } = render(<LiveChartTooltip active={false} />);
        expect(container.firstChild).toBeNull();
    });

    it('renders candle targets bounded by pure transforms', () => {
        const candle: Partial<Candle> = {
            timeLabel: '10:00 AM',
            Open: 100,
            High: 110,
            Low: 90,
            Close: 105.1235,
            Volume: 50000.5,
            isBullish: true
        };

        render(
            <LiveChartTooltip
                active={true}
                payload={[{ payload: candle as Candle }]}
            />
        );

        expect(screen.getByText('10:00 AM')).toBeInTheDocument();
        expect(screen.getByText('100.000')).toBeInTheDocument(); // Open
        expect(screen.getByText('110.000')).toBeInTheDocument(); // High
        expect(screen.getByText('90.000')).toBeInTheDocument(); // Low
        expect(screen.getByText('105.123')).toBeInTheDocument(); // Close
        expect(screen.getByText('50,001')).toBeInTheDocument(); // Volume rounded
    });

    it('renders bearish candles with appropriate classes implicitly', () => {
        const candle: Partial<Candle> = {
            timeLabel: '11:00 AM',
            Close: 90,
            isBullish: false
        };

        const { container } = render(
            <LiveChartTooltip
                active={true}
                payload={[{ payload: candle as Candle }]}
            />
        );
        
        const closeSpan = container.querySelectorAll('span')[7];
        expect(closeSpan).toHaveClass('text-rose-300'); // Validates the red bearish assignment
    });
});
