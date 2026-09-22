import pytest
from fastapi import HTTPException

from core import subscriptions


def test_subscriber_entitlement_is_cumulative():
    assert subscriptions.subscriber_entitled_to_service(
        subscriptions.SIGNALS_ONLY,
        subscriptions.SIGNALS_ONLY,
    )
    assert subscriptions.subscriber_entitled_to_service(
        subscriptions.SIGNALS_PLUS_PORTFOLIO_RECS,
        subscriptions.SIGNALS_ONLY,
    )
    assert subscriptions.subscriber_entitled_to_service(
        subscriptions.MANAGED_ADVISORY,
        subscriptions.SIGNALS_PLUS_PORTFOLIO_RECS,
    )
    assert not subscriptions.subscriber_entitled_to_service(
        subscriptions.SIGNALS_ONLY,
        subscriptions.SIGNALS_PLUS_PORTFOLIO_RECS,
    )


def test_main_channel_broadcast_level_is_cumulative():
    assert not subscriptions.main_channel_includes_service("none", subscriptions.SIGNALS_ONLY)
    assert subscriptions.main_channel_includes_service("type_1", subscriptions.SIGNALS_ONLY)
    assert not subscriptions.main_channel_includes_service("type_1", subscriptions.SIGNALS_PLUS_PORTFOLIO_RECS)
    assert subscriptions.main_channel_includes_service("type_2", subscriptions.SIGNALS_ONLY)
    assert subscriptions.main_channel_includes_service("type_2", subscriptions.SIGNALS_PLUS_PORTFOLIO_RECS)
    assert not subscriptions.main_channel_includes_service("type_2", subscriptions.MANAGED_ADVISORY)
    assert subscriptions.main_channel_includes_service("type_3", subscriptions.SIGNALS_ONLY)
    assert subscriptions.main_channel_includes_service("type_3", subscriptions.SIGNALS_PLUS_PORTFOLIO_RECS)
    assert subscriptions.main_channel_includes_service("type_3", subscriptions.MANAGED_ADVISORY)


def test_main_channel_broadcast_level_normalizes_aliases_and_rejects_invalid_values():
    assert subscriptions.normalize_main_channel_broadcast_level("type 2") == "type_2"
    assert subscriptions.normalize_main_channel_broadcast_level("TYPE3") == "type_3"

    with pytest.raises(HTTPException):
        subscriptions.normalize_main_channel_broadcast_level("all")
