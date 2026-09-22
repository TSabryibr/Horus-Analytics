'use client';

import type { ReactNode } from 'react';
import { useEffect, useRef, useState } from 'react';

type MeasuredChartFrameProps = {
    className?: string;
    fallbackHeight?: number;
    fallbackWidth?: number;
    children: (size: { width: number; height: number }) => ReactNode;
};

const IS_TEST_ENV = process.env.NODE_ENV === 'test';

export function MeasuredChartFrame({
    className,
    fallbackHeight = 320,
    fallbackWidth = 960,
    children,
}: MeasuredChartFrameProps) {
    const frameRef = useRef<HTMLDivElement | null>(null);
    const [size, setSize] = useState(() => (
        IS_TEST_ENV
            ? { width: fallbackWidth, height: fallbackHeight }
            : { width: 0, height: 0 }
    ));

    useEffect(() => {
        const frame = frameRef.current;
        if (!frame) {
            return;
        }

        const updateSize = () => {
            const bounds = frame.getBoundingClientRect();
            const measuredWidth = Math.max(0, Math.round(bounds.width));
            const measuredHeight = Math.max(0, Math.round(bounds.height));
            const nextWidth = IS_TEST_ENV && measuredWidth === 0 ? fallbackWidth : measuredWidth;
            const nextHeight = IS_TEST_ENV && measuredHeight === 0 ? fallbackHeight : measuredHeight;

            setSize((current) => {
                if (current.width === nextWidth && current.height === nextHeight) {
                    return current;
                }

                return { width: nextWidth, height: nextHeight };
            });
        };

        updateSize();

        if (typeof ResizeObserver === 'undefined') {
            window.addEventListener('resize', updateSize);
            return () => window.removeEventListener('resize', updateSize);
        }

        const resizeObserver = new ResizeObserver(() => updateSize());
        resizeObserver.observe(frame);
        window.addEventListener('resize', updateSize);

        return () => {
            resizeObserver.disconnect();
            window.removeEventListener('resize', updateSize);
        };
    }, []);

    const canRenderChart = size.width > 0 && size.height > 0;

    return (
        <div ref={frameRef} className={className}>
            {canRenderChart ? children(size) : null}
        </div>
    );
}
