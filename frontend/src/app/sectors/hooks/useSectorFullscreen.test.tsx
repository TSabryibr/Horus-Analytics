import { act, renderHook } from '@testing-library/react';

import { useSectorFullscreen } from './useSectorFullscreen';

describe('useSectorFullscreen', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('opens, closes, and responds to the Escape key', () => {
        const { result } = renderHook(() => useSectorFullscreen());

        expect(result.current.isFullscreen).toBe(false);

        act(() => {
            result.current.openFullscreen();
        });

        expect(result.current.isFullscreen).toBe(true);

        act(() => {
            window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
        });

        expect(result.current.isFullscreen).toBe(false);
    });

    it('removes the keydown listener on unmount', () => {
        const removeSpy = jest.spyOn(window, 'removeEventListener');

        const { unmount } = renderHook(() => useSectorFullscreen());

        unmount();

        expect(removeSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
    });
});
