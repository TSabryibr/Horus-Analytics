import { formatClockHHMM, formatStatusTimestamp } from './sidebarTransforms';

describe('sidebarTransforms', () => {
    describe('formatClockHHMM', () => {
        it('formats a date correctly', () => {
            const date = new Date('2026-03-19T08:05:00Z');
            // Assuming local timezone matches to test. Using getHours on specific UTC might be flaky depending on system running tests.
            // We'll mock the Date object's getHours/getMinutes for absolute safety.
            jest.spyOn(date, 'getHours').mockReturnValue(14);
            jest.spyOn(date, 'getMinutes').mockReturnValue(9);
            expect(formatClockHHMM(date)).toBe('14:09');
        });
    });

    describe('formatStatusTimestamp', () => {
        it('returns --:-- for nulls or undefined', () => {
            expect(formatStatusTimestamp(null)).toBe('--:--');
            expect(formatStatusTimestamp(undefined)).toBe('--:--');
            expect(formatStatusTimestamp('')).toBe('--:--');
        });

        it('handles valid string with T separator', () => {
            expect(formatStatusTimestamp('2026-03-19T13:45:00Z')).toBe('13:45');
        });

        it('handles string with space separator via fast-path regex', () => {
            expect(formatStatusTimestamp('2026-03-19 09:15:00')).toBe('09:15');
        });

        it('handles bare date string by appending time and returning 00:00', () => {
            expect(formatStatusTimestamp('2026-03-19')).toBe('00:00');
        });

        it('returns --:-- for invalid date strings', () => {
            expect(formatStatusTimestamp('not-a-date')).toBe('--:--');
        });

        it('handles valid Date objects', () => {
            const date = new Date();
            jest.spyOn(date, 'getHours').mockReturnValue(5);
            jest.spyOn(date, 'getMinutes').mockReturnValue(30);
            expect(formatStatusTimestamp(date)).toBe('05:30');
        });

        it('returns --:-- for invalid Date objects', () => {
            const date = new Date('invalid');
            expect(formatStatusTimestamp(date)).toBe('--:--');
        });
    });
});
