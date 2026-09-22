"""
HORUS ANALYTICS - BOUNDED WORKER POOL MANAGER
=============================================
Centralized, bounded ThreadPoolExecutor management for CPU and I/O tasks.
Provides lifecycle cleanup, thread naming, and async-to-sync bridge helpers.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import functools
import logging
import os
import threading
from typing import Any, Callable, Coroutine, Dict, Optional, TypeVar

logger = logging.getLogger("horus.worker_pool")

T = TypeVar("T")


class WorkerPoolManager:
    """
    Manages bounded ThreadPoolExecutor instances across the application.
    Prevents thread exhaustion and guarantees orderly shutdown.
    """

    _instance: Optional[WorkerPoolManager] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._pools: Dict[str, concurrent.futures.ThreadPoolExecutor] = {}
        self._pool_lock = threading.Lock()
        self._is_shutdown = False

        # Default bounded worker counts
        cpu_count = os.cpu_count() or 4
        self._default_io_workers = max(4, min(32, cpu_count * 4))
        self._default_compute_workers = max(2, min(16, cpu_count * 2))

    @classmethod
    def get_instance(cls) -> WorkerPoolManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_executor(
        self,
        name: str = "default",
        max_workers: Optional[int] = None,
    ) -> concurrent.futures.ThreadPoolExecutor:
        """
        Retrieves or initializes a named ThreadPoolExecutor.
        """
        with self._pool_lock:
            if self._is_shutdown:
                raise RuntimeError(f"Cannot request executor '{name}': WorkerPoolManager is shutting down.")

            if name not in self._pools:
                if max_workers is None:
                    if "io" in name.lower() or "net" in name.lower():
                        max_workers = self._default_io_workers
                    elif "compute" in name.lower() or "scan" in name.lower() or "opt" in name.lower():
                        max_workers = self._default_compute_workers
                    else:
                        max_workers = min(16, (os.cpu_count() or 4) * 2)

                prefix = f"horus-{name}"
                logger.debug(f"[WorkerPool] Creating executor '{name}' (workers={max_workers}, prefix='{prefix}')")
                self._pools[name] = concurrent.futures.ThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix=prefix,
                )
            return self._pools[name]

    def submit(
        self,
        fn: Callable[..., T],
        *args: Any,
        pool_name: str = "default",
        **kwargs: Any,
    ) -> concurrent.futures.Future[T]:
        """
        Submits a callable to a named thread pool.
        """
        executor = self.get_executor(name=pool_name)
        return executor.submit(fn, *args, **kwargs)

    async def run_in_thread(
        self,
        fn: Callable[..., T],
        *args: Any,
        pool_name: str = "default",
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> T:
        """
        Executes a blocking function in a background thread pool and awaits the result asynchronously.
        """
        loop = asyncio.get_running_loop()
        executor = self.get_executor(name=pool_name)
        func = functools.partial(fn, *args, **kwargs) if kwargs else fn

        if timeout is not None:
            return await asyncio.wait_for(
                loop.run_in_executor(executor, func, *args if not kwargs else ()),
                timeout=timeout,
            )
        return await loop.run_in_executor(executor, func, *args if not kwargs else ())

    def shutdown(self, wait: bool = True, cancel_futures: bool = True) -> None:
        """
        Shuts down all managed ThreadPoolExecutor instances.
        """
        with self._pool_lock:
            self._is_shutdown = True
            for name, executor in list(self._pools.items()):
                try:
                    logger.info(f"[WorkerPool] Shutting down executor '{name}' (wait={wait}, cancel={cancel_futures})...")
                    executor.shutdown(wait=wait, cancel_futures=cancel_futures)
                except Exception as e:
                    logger.warning(f"[WorkerPool] Error shutting down executor '{name}': {e}")
            self._pools.clear()


# -----------------------------------------------------------------------------
# Module-level convenience functions
# -----------------------------------------------------------------------------
def get_worker_pool() -> WorkerPoolManager:
    """Returns the WorkerPoolManager singleton."""
    return WorkerPoolManager.get_instance()


def get_executor(name: str = "default", max_workers: Optional[int] = None) -> concurrent.futures.ThreadPoolExecutor:
    """Convenience helper to retrieve a named ThreadPoolExecutor."""
    return get_worker_pool().get_executor(name=name, max_workers=max_workers)


async def run_in_thread(
    fn: Callable[..., T],
    *args: Any,
    pool_name: str = "default",
    timeout: Optional[float] = None,
    **kwargs: Any,
) -> T:
    """Convenience helper to run a blocking function in a background thread pool."""
    return await get_worker_pool().run_in_thread(
        fn,
        *args,
        pool_name=pool_name,
        timeout=timeout,
        **kwargs,
    )


def shutdown_worker_pools(wait: bool = False, cancel_futures: bool = True) -> None:
    """Shuts down all active thread pools."""
    get_worker_pool().shutdown(wait=wait, cancel_futures=cancel_futures)
