/**
 * Unit tests for arbitrageTransforms.ts.
 */

import {
    getZScoreClass,
    getConfidenceClass,
    getEchoTypeClass,
    getActionStatusClass,
    filterMirrors,
} from './arbitrageTransforms';

describe('arbitrageTransforms', () => {
    describe('getZScoreClass', () => {
        it('returns cyan for |z| > 2', () => {
            expect(getZScoreClass(2.5)).toBe('text-cyan-400');
            expect(getZScoreClass(-3)).toBe('text-cyan-400');
        });

        it('returns gray for |z| <= 2', () => {
            expect(getZScoreClass(2)).toBe('text-gray-300');
            expect(getZScoreClass(0)).toBe('text-gray-300');
        });
    });

    describe('getConfidenceClass', () => {
        it('returns emerald for confidence > 75', () => {
            expect(getConfidenceClass(80)).toBe('text-emerald-500');
        });

        it('returns yellow for confidence <= 75', () => {
            expect(getConfidenceClass(75)).toBe('text-yellow-500');
            expect(getConfidenceClass(50)).toBe('text-yellow-500');
        });
    });

    describe('getEchoTypeClass', () => {
        it('returns emerald for Positive echo', () => {
            expect(getEchoTypeClass('Positive')).toContain('emerald-500');
        });

        it('returns rose for Negative echo', () => {
            expect(getEchoTypeClass('Negative')).toContain('rose-500');
        });
    });

    describe('getActionStatusClass', () => {
        it('returns emerald styling for success', () => {
            expect(getActionStatusClass('success')).toContain('emerald');
        });

        it('returns red styling for error', () => {
            expect(getActionStatusClass('error')).toContain('red');
        });
    });

    describe('filterMirrors', () => {
        const mirrors = [
            { Leader: 'COMI', Follower: 'HRHO' },
            { Leader: 'ETEL', Follower: 'FWRY' },
        ];

        it('returns all mirrors for an empty filter', () => {
            expect(filterMirrors(mirrors, '')).toHaveLength(2);
        });

        it('filters case-insensitively by Leader or Follower', () => {
            expect(filterMirrors(mirrors, 'fWRy')).toHaveLength(1);
            expect(filterMirrors(mirrors, 'comi')).toHaveLength(1);
        });

        it('returns empty array when nothing matches', () => {
            expect(filterMirrors(mirrors, 'ZZZZ')).toHaveLength(0);
        });

        it('returns empty array when mirrors is undefined/empty', () => {
            expect(filterMirrors([], 'COMI')).toHaveLength(0);
        });
    });
});
