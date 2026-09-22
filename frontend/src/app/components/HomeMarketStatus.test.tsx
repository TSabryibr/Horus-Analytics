import { render, screen } from '@testing-library/react';

import { HomeMarketStatus } from './HomeMarketStatus';

const mockUseSWR = jest.fn();

jest.mock('swr', () => ({
    __esModule: true,
    default: (...args: unknown[]) => mockUseSWR(...args),
}));

describe('HomeMarketStatus', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        jest.setSystemTime(new Date('2026-03-18T11:15:00'));
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    it('shows live market status when telemetry time is within market hours', () => {
        mockUseSWR.mockReturnValue({ data: null });

        render(<HomeMarketStatus />);

        expect(screen.getByText('Telemetry Time')).toBeInTheDocument();
        expect(screen.getByText('Market Active')).toBeInTheDocument();
    });
});
