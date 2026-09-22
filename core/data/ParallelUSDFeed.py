"""
Parallel USD/EGP Feed Integration
=================================
Maintains live and cached parallel USD/EGP market rates used for real-value
unit (RVU) conversions and sovereign hedge validation.
"""
from __future__ import annotations

import time
import logging
from typing import Tuple

from core.settings import settings

logger = logging.getLogger("horus.data.usd_parallel_feed")


class ParallelUSDFeed:
    """Provides live and cached parallel market USD/EGP rate with freshness tracking."""

    def __init__(
        self,
        fallback_rate: float | None = None,
        max_stale_seconds: float = 300.0,
    ) -> None:
        if fallback_rate is not None:
            self.fallback_rate = float(fallback_rate)
        else:
            self.fallback_rate = float(getattr(settings, "USD_EGP_RATE", 48.5) or 48.5)
        self.max_stale_seconds = float(max_stale_seconds)
        self._current_rate: float = self.fallback_rate
        self._last_update_time: float = time.time()

    def update_rate(self, rate: float) -> None:
        """Manually or stream-updated rate."""
        self._current_rate = float(rate)
        self._last_update_time = time.time()

    def get_live_rvu_rate(self) -> Tuple[float, bool]:
        """
        Returns (current_rate, is_fresh).
        """
        age = time.time() - self._last_update_time
        is_fresh = age <= self.max_stale_seconds
        return self._current_rate, is_fresh


def _create_default_feed() -> ParallelUSDFeed:
    feed = ParallelUSDFeed()
    try:
        from utils.currency_fetcher import get_parallel_usd_egp_rate
        live_val = get_parallel_usd_egp_rate()
        if live_val and live_val > 0:
            feed.update_rate(float(live_val))
    except Exception as exc:
        logger.debug(f"[ParallelUSDFeed] Initial load fallback used: {exc}")
    return feed


usd_parallel_feed = _create_default_feed()
