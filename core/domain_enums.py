import sys
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum
    class StrEnum(str, Enum):
        pass


class PipelineState(StrEnum):
    FRESH = "FRESH"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    STARTING = "STARTING"
    UNKNOWN = "UNKNOWN"


class MarketRegime(StrEnum):
    BULLISH = "BULLISH"
    CAUTIOUS = "CAUTIOUS"
    DEFENSIVE = "DEFENSIVE"
    BEARISH = "BEARISH"


class SessionMode(StrEnum):
    LIVE = "LIVE"
    ANALYSIS = "ANALYSIS"
    HYBRID = "HYBRID"


class ProvisioningStatus(StrEnum):
    IDLE = "IDLE"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    ERROR = "ERROR"


class SignalAction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    EXIT = "EXIT"
