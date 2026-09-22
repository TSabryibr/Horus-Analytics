"""
Tests for Horus WorkerPoolManager (Bounded Thread Pools, Async Bridging, and Lifecycle).
"""

import asyncio
import time
import pytest
from core.worker_pool import (
    WorkerPoolManager,
    get_executor,
    get_worker_pool,
    run_in_thread,
    shutdown_worker_pools,
)


def blocking_add(a: int, b: int) -> int:
    time.sleep(0.05)
    return a + b


def slow_task(duration: float = 0.5) -> str:
    time.sleep(duration)
    return "done"


def test_worker_pool_run_in_thread_success():
    async def _run():
        return await run_in_thread(blocking_add, 10, 25, pool_name="test_compute")

    assert asyncio.run(_run()) == 35


def test_worker_pool_run_in_thread_timeout():
    async def _run():
        await run_in_thread(slow_task, 0.5, pool_name="test_timeout", timeout=0.05)

    with pytest.raises(asyncio.TimeoutError):
        asyncio.run(_run())


def test_worker_pool_executor_naming():
    pool_mgr = get_worker_pool()
    executor = pool_mgr.get_executor(name="custom_scanner", max_workers=2)
    assert executor._max_workers == 2
    assert executor._thread_name_prefix == "horus-custom_scanner"


def test_worker_pool_submit():
    pool_mgr = get_worker_pool()
    future = pool_mgr.submit(blocking_add, 5, 15, pool_name="test_submit")
    assert future.result(timeout=2.0) == 20
