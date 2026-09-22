"""
STRESS TEST FACADE
==================
Backwards-compatible facade re-exporting core.simulation.StressTest.
"""

import sys
from core.simulation import StressTest
from core.simulation.StressTest import *

# Register in sys.modules so imports of "StressTest" resolve directly
sys.modules["StressTest"] = sys.modules[__name__]
