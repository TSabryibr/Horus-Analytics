import { normalizeTrapsPayload } from './marketTransforms';

describe('marketTransforms', () => {
    describe('normalizeTrapsPayload', () => {
        it('returns null for non-object input', () => {
            expect(normalizeTrapsPayload(null)).toBeNull();
            expect(normalizeTrapsPayload(undefined)).toBeNull();
            expect(normalizeTrapsPayload("string")).toBeNull();
        });

        it('normalizes flat payload', () => {
            const flat = {
                bull_traps: [{ Ticker: 'COMI' }],
                bear_traps: [],
            };
            const result = normalizeTrapsPayload(flat);
            expect(result?.bull_traps).toHaveLength(1);
            expect(result?.bear_traps).toHaveLength(0);
        });

        it('normalizes nested data payload', () => {
            const nested = {
                data: {
                    bull_traps: [],
                    bear_traps: [{ Ticker: 'HRHO' }],
                }
            };
            const result = normalizeTrapsPayload(nested);
            expect(result?.bear_traps).toHaveLength(1);
            expect(result?.bull_traps).toHaveLength(0);
        });

        it('returns null for object without trap keys', () => {
            const empty = { other: 'data' };
            expect(normalizeTrapsPayload(empty)).toBeNull();
        });

        it('handles missing keys in valid payload as empty arrays', () => {
             const partial = { bull_traps: [{ Ticker: 'COMI' }] };
             const result = normalizeTrapsPayload(partial);
             expect(result?.bull_traps).toHaveLength(1);
             expect(result?.bear_traps).toHaveLength(0);
        });
    });
});
