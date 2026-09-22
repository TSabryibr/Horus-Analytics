import { useEffect, useState } from 'react';

export function useSectorFullscreen() {
    const [isFullscreen, setIsFullscreen] = useState(false);

    const openFullscreen = () => setIsFullscreen(true);
    const closeFullscreen = () => setIsFullscreen(false);

    useEffect(() => {
        const handleEsc = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                setIsFullscreen(false);
            }
        };

        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, []);

    return {
        closeFullscreen,
        isFullscreen,
        openFullscreen,
    };
}
