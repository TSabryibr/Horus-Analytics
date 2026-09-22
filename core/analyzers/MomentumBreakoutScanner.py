"""
LEGACY FACADE: core.analyzers.MomentumBreakoutScanner
=====================================================
Maintains complete backwards compatibility by re-exporting all scanner methods,
manipulation sentry checks, indicators, and Excel export routines from `core.analyzers.breakout`.
"""

from core.analyzers.breakout import *
from core.analyzers.breakout import __all__

if __name__ == "__main__":
    scan_full_market()
