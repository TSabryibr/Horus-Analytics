import { getPollingStatus } from './telemetry';

describe('getPollingStatus', () => {
    it('reports HTTP polling without claiming a WebSocket connection', () => {
        expect(getPollingStatus(false, false)).toEqual({
            label: 'Transport',
            value: '🔄 HTTP POLL',
            tone: 'success',
        });
    });

    it('reports an unavailable API when polling fails', () => {
        expect(getPollingStatus(false, true)).toEqual({
            label: 'Transport',
            value: '🔌 API UNAVAILABLE',
            tone: 'danger',
        });
    });

    it('reports an in-progress poll', () => {
        expect(getPollingStatus(true, false)).toEqual({
            label: 'Transport',
            value: '⏳ POLLING',
            tone: 'warning',
        });
    });
});
