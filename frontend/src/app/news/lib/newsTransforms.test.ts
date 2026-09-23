/**
 * Unit tests for newsTransforms.ts.
 * Verifies Tailwind class selection for all sentiment and regime boundaries.
 */

import {
    getSentimentColor,
    getBifrostRegimeClass,
    getBifrostBarColor,
    formatSentimentScore,
} from './newsTransforms';

describe('newsTransforms', () => {
    describe('getSentimentColor', () => {
        it('returns green class for positive scores > 1', () => {
            expect(getSentimentColor(2)).toContain('green-500');
        });

        it('returns red class for negative scores < -1', () => {
            expect(getSentimentColor(-2)).toContain('red-500');
        });

        it('returns gray class for neutral scores between -1 and 1', () => {
            expect(getSentimentColor(0)).toContain('gray-400');
            expect(getSentimentColor(1)).toContain('gray-400');
            expect(getSentimentColor(-1)).toContain('gray-400');
        });
    });

    describe('getBifrostRegimeClass', () => {
        it('returns amber class for "EUXUBERANT GREED"', () => {
            expect(getBifrostRegimeClass('EUXUBERANT GREED')).toContain('amber-300');
        });

        it('returns rose class for "BLOOD PARALYSIS"', () => {
            expect(getBifrostRegimeClass('BLOOD PARALYSIS')).toContain('rose-300');
        });

        it('returns default slate class for unknown or neutral regimes', () => {
            expect(getBifrostRegimeClass('BORING MORTALS')).toContain('slate-300');
            expect(getBifrostRegimeClass('')).toContain('slate-300');
        });
    });

    describe('getBifrostBarColor', () => {
        it('returns amber background for scores >= 70', () => {
            expect(getBifrostBarColor(70)).toBe('bg-amber-400');
            expect(getBifrostBarColor(99)).toBe('bg-amber-400');
        });

        it('returns rose background for scores <= 30', () => {
            expect(getBifrostBarColor(30)).toBe('bg-rose-400');
            expect(getBifrostBarColor(5)).toBe('bg-rose-400');
        });

        it('returns slate background for scores between 31 and 69', () => {
            expect(getBifrostBarColor(50)).toBe('bg-slate-400');
        });
    });

    describe('formatSentimentScore', () => {
        it('prefixes positive scores with +', () => {
            expect(formatSentimentScore(3)).toBe('+3');
        });

        it('does not prefix negative scores (handled by string conversion)', () => {
            expect(formatSentimentScore(-2)).toBe('-2');
        });

        it('returns "0" for neutral zero', () => {
            expect(formatSentimentScore(0)).toBe('0');
        });
    });
});
