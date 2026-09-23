import { formatPrice, toNumber, truncatePrice } from './forms';

describe('portfolio form helpers', () => {
    it('normalizes numeric strings with comma separators', () => {
        expect(toNumber('1,250.5')).toBe(1250.5);
        expect(toNumber('')).toBe(0);
        expect(toNumber(undefined)).toBe(0);
    });

    it('truncates prices without rounding up', () => {
        expect(truncatePrice(12.3459)).toBe('12.345');
        expect(truncatePrice('98.1')).toBe('98.100');
    });

    it('formats current prices through the default truncation precision', () => {
        expect(formatPrice(45.67891)).toBe('45.678');
    });
});
