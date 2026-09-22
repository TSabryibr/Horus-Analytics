"""
LEGACY FACADE: core.market.HistoricalBackfill
=============================================
Maintains backwards compatibility by re-exporting all backfill engine symbols,
lock state, and runner routines from `core.market.backfill`.
"""

from core.market.backfill import *
from core.market.backfill import __all__
