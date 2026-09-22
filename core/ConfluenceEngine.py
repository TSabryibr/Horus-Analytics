"""
CONFLUENCE ENGINE (SOVEREIGN HEDGE DEPRECATION FACADE)
======================================================
DEPRECATION NOTICE:
This module is preserved for backward compatibility.
Use 'core.sovereign_confluence' directly to avoid class and module name
collisions with 'core.confluence'.
"""
import warnings

from core.sovereign_confluence import (
    SovereignConfluenceEngine,
    sovereign_confluence_engine,
    SovereignConfluenceEngine as ConfluenceEngine,
    sovereign_confluence_engine as confluence_engine,
)

__all__ = [
    "SovereignConfluenceEngine",
    "sovereign_confluence_engine",
    "ConfluenceEngine",
    "confluence_engine",
]
