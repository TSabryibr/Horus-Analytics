"""
DATABASE MODELS PACKAGE
=======================
Re-exports all Peewee ORM models and database proxy.
"""

from .base import BaseModel, db
from .portfolio import (
    BrokerOrder,
    Portfolio,
    PortfolioDefaultState,
    PortfolioSnapshot,
    Position,
    Trade,
)
from .signals import (
    BackfillIntradayCheckpoint,
    HorusExecution,
    LegacySignalOutcome,
    PublishedSignalFollowUp,
    PublishedSignalLifecycle,
    PublishedSignalLifecycleEvent,
    Signal,
    SignalDeskState,
    SignalExecutionAttribution,
    SignalGuardState,
    SignalOutcome,
    SignalRecommendation,
    SignalRun,
    SignalStateArchive,
    SignalSuppressionLog,
    SignalValidationRun,
    TickerStrategyMetrics,
    SignalDelivery,
)
from .market import (
    AssetAiReport,
    Holiday,
    ProvisioningState,
    ScannerStrategyProfile,
    SovereignState,
)
from .accounts import (
    Client,
    ClientApiKey,
    ClientEntitlement,
    SignalAuditEvent,
    SubscriptionDelivery,
)

__all__ = [
    "db",
    "BaseModel",
    # Portfolio
    "Portfolio",
    "PortfolioDefaultState",
    "Position",
    "Trade",
    "BrokerOrder",
    "PortfolioSnapshot",
    # Signals
    "Signal",
    "BackfillIntradayCheckpoint",
    "SignalRun",
    "SignalRecommendation",
    "SignalDelivery",
    "SignalOutcome",
    "PublishedSignalLifecycle",
    "PublishedSignalLifecycleEvent",
    "PublishedSignalFollowUp",
    "HorusExecution",
    "SignalExecutionAttribution",
    "SignalValidationRun",
    "TickerStrategyMetrics",
    "LegacySignalOutcome",
    "SignalSuppressionLog",
    "SignalGuardState",
    "SignalDeskState",
    "SignalStateArchive",
    # Market & System
    "Holiday",
    "ProvisioningState",
    "SovereignState",
    "ScannerStrategyProfile",
    "AssetAiReport",
    # Accounts & Clients
    "Client",
    "ClientApiKey",
    "ClientEntitlement",
    "SubscriptionDelivery",
    "SignalAuditEvent",
]
