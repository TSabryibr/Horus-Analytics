import { useEffect, useRef } from 'react';

type PollingOptions = {
  enabled?: boolean;
  intervalMs: number;
  runImmediately?: boolean;
  pauseWhenHidden?: boolean;
};

/**
 * Lightweight polling hook that avoids overlapping requests and pauses when tab is hidden.
 */
export function usePolling(task: () => void | Promise<void>, options: PollingOptions): void {
  const {
    enabled = true,
    intervalMs,
    runImmediately = true,
    pauseWhenHidden = true,
  } = options;

  const taskRef = useRef(task);
  const runningRef = useRef(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    taskRef.current = task;
  }, [task]);

  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;

    const clearTimer = () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };

    const schedule = () => {
      if (cancelled) return;
      clearTimer();
      timeoutRef.current = setTimeout(tick, intervalMs);
    };

    const tick = async () => {
      if (cancelled) return;
      if (pauseWhenHidden && typeof document !== 'undefined' && document.hidden) {
        schedule();
        return;
      }
      if (runningRef.current) {
        schedule();
        return;
      }

      runningRef.current = true;
      try {
        await taskRef.current();
      } finally {
        runningRef.current = false;
        schedule();
      }
    };

    if (runImmediately) {
      void tick();
    } else {
      schedule();
    }

    return () => {
      cancelled = true;
      clearTimer();
    };
  }, [enabled, intervalMs, runImmediately, pauseWhenHidden]);
}
