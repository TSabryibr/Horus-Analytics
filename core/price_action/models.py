from __future__ import annotations
"""Typed contracts for the EGX price-action strategy pack."""


from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class PriceActionStrategyFamily(str, Enum):
    INTRADAY = "INTRADAY"
    SWING = "SWING"
    POSITION = "POSITION"


class PriceActionSignalType(str, Enum):
    BUY = "BUY"
    BUY_CANDIDATE = "BUY_CANDIDATE"
    WARNING_ONLY = "WARNING_ONLY"
    BLOCKED = "BLOCKED"


class PriceActionStrategyStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    RESEARCH = "RESEARCH"


@dataclass(frozen=True)
class PriceActionSourceAttribution:
    title: str
    filename: str
    concept: str


@dataclass(frozen=True)
class PriceActionStrategy:
    strategy_id: str
    display_name: str
    family: PriceActionStrategyFamily
    summary: str
    regime: str
    source_attributions: tuple[PriceActionSourceAttribution, ...]
    required_data: tuple[str, ...]
    entry_conditions: tuple[str, ...]
    confirmation_conditions: tuple[str, ...]
    avoidance_rules: tuple[str, ...]
    exit_rules: tuple[str, ...]
    risk_model: str
    status: PriceActionStrategyStatus = PriceActionStrategyStatus.DRAFT
    warning_only: bool = False
    long_entry_allowed: bool = True
    data_gate: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.strategy_id or self.strategy_id.strip() != self.strategy_id:
            raise ValueError("strategy_id must be a non-empty trimmed string")
        if not self.display_name.strip():
            raise ValueError("display_name must be non-empty")
        if not self.source_attributions:
            raise ValueError("source_attributions must contain at least one source")
        if not self.required_data:
            raise ValueError("required_data must contain at least one requirement")
        if self.warning_only and self.long_entry_allowed:
            raise ValueError("warning-only strategies cannot allow long entries")
        if self.family is PriceActionStrategyFamily.INTRADAY and not self.data_gate:
            raise ValueError("intraday strategies must declare a data_gate")
        if self.family is not PriceActionStrategyFamily.INTRADAY and self.data_gate:
            raise ValueError("only intraday strategies may declare a data_gate")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["family"] = self.family.value
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True)
class PriceActionSignal:
    signal_type: PriceActionSignalType
    timeframe_family: PriceActionStrategyFamily
    ticker: str
    setup_name: str
    strategy_id: str
    explanation: str
    score: float = 0.0
    entry_price: float | None = None
    stop_loss: float | None = None
    target_1: float | None = None
    target_2: float | None = None
    confirmations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    avoidance_flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.ticker or self.ticker.strip() != self.ticker:
            raise ValueError("ticker must be a non-empty trimmed string")
        if not self.setup_name.strip():
            raise ValueError("setup_name must be non-empty")
        if not self.strategy_id.strip():
            raise ValueError("strategy_id must be non-empty")
        if not self.explanation.strip():
            raise ValueError("explanation must be non-empty")
        if self.signal_type in {PriceActionSignalType.BUY, PriceActionSignalType.BUY_CANDIDATE}:
            missing = [
                field_name
                for field_name, value in (
                    ("entry_price", self.entry_price),
                    ("stop_loss", self.stop_loss),
                    ("target_1", self.target_1),
                )
                if value is None
            ]
            if missing:
                raise ValueError(f"trade candidate signals require: {', '.join(missing)}")
        if self.signal_type is PriceActionSignalType.WARNING_ONLY:
            if self.entry_price is not None or self.stop_loss is not None:
                raise ValueError("warning-only signals cannot include trade execution prices")
        if self.signal_type is PriceActionSignalType.BLOCKED and not self.avoidance_flags:
            raise ValueError("blocked signals must include at least one avoidance flag")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["signal_type"] = self.signal_type.value
        payload["timeframe_family"] = self.timeframe_family.value
        return payload
