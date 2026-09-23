import { formatFakeoutDepth, getTrapCardClasses, getTickerClasses, getDetailBoxClasses } from './trapsTransforms';

describe('trapsTransforms', () => {
    describe('formatFakeoutDepth', () => {
        it('formats bull traps as negative fakeouts', () => {
            expect(formatFakeoutDepth(2.4, 'bull')).toBe('-2.4% Fakeout');
        });
        it('formats bear traps as positive rebounds', () => {
            expect(formatFakeoutDepth(1.9, 'bear')).toBe('+1.9% Rebound');
        });
    });

    describe('getTrapCardClasses', () => {
        it('returns rose classes for bull traps', () => {
            expect(getTrapCardClasses('bull')).toContain('rose');
        });
        it('returns emerald classes for bear traps', () => {
            expect(getTrapCardClasses('bear')).toContain('emerald');
        });
    });

    describe('getTickerClasses', () => {
        it('returns rose hover for bull traps', () => {
            expect(getTickerClasses('bull')).toBe('group-hover:text-rose-400');
        });
        it('returns emerald hover for bear traps', () => {
            expect(getTickerClasses('bear')).toBe('group-hover:text-emerald-400');
        });
    });

    describe('getDetailBoxClasses', () => {
        it('returns rose background for bull traps', () => {
            expect(getDetailBoxClasses('bull')).toContain('rose');
        });
        it('returns emerald background for bear traps', () => {
            expect(getDetailBoxClasses('bear')).toContain('emerald');
        });
    });
});
