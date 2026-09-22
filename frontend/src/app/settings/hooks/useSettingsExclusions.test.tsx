import { act, renderHook } from '@testing-library/react';

import { useSettingsExclusions } from './useSettingsExclusions';

describe('useSettingsExclusions', () => {
    it('adds uppercase exclusions and clears the input', () => {
        const setExcluded = jest.fn();
        const { result } = renderHook(() =>
            useSettingsExclusions({
                excluded: ['COMI'],
                setExcluded,
                allTickers: ['COMI', 'ETEL', 'SWDY'],
            })
        );

        act(() => {
            result.current.setNewExclusion('swdy');
        });

        act(() => {
            result.current.addExclusion('swdy');
        });

        expect(setExcluded).toHaveBeenCalledWith(['COMI', 'SWDY']);
        expect(result.current.newExclusion).toBe('');
    });

    it('ignores empty and duplicate exclusions', () => {
        const setExcluded = jest.fn();
        const { result } = renderHook(() =>
            useSettingsExclusions({
                excluded: ['COMI'],
                setExcluded,
                allTickers: ['COMI', 'ETEL', 'SWDY'],
            })
        );

        act(() => {
            result.current.setNewExclusion('comi');
            result.current.addExclusion();
            result.current.setNewExclusion('   ');
            result.current.addExclusion();
        });

        expect(setExcluded).not.toHaveBeenCalled();
    });

    it('removes exclusions and computes autocomplete suggestions', () => {
        const setExcluded = jest.fn();
        const { result, rerender } = renderHook(
            ({ excluded }) =>
                useSettingsExclusions({
                    excluded,
                    setExcluded,
                    allTickers: ['COMI', 'ETEL', 'ETRS', 'SWDY'],
                }),
            { initialProps: { excluded: ['COMI'] } }
        );

        act(() => {
            result.current.removeExclusion('COMI');
        });

        expect(setExcluded).toHaveBeenCalledWith([]);

        rerender({ excluded: ['COMI'] });

        act(() => {
            result.current.setNewExclusion('ET');
        });

        expect(result.current.autocompleteOptions).toEqual(['ETEL', 'ETRS']);
    });
});
