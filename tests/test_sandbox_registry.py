from core.analyzers import SandboxRegistry


def test_get_top_liquid_stocks_logs_ascii_progress(monkeypatch, capsys):
    monkeypatch.setattr("core.market.MarketLists.get_market_list", lambda *_args, **_kwargs: [])

    result = SandboxRegistry.get_top_liquid_stocks(limit=5)

    captured = capsys.readouterr().out
    assert result == []
    assert "[SandboxRegistry] Scoring 0 tickers for liquidity (EGX100 default universe)..." in captured
    assert "[SandboxRegistry] No stocks passed liquidity threshold. Reducing threshold..." in captured
    assert "Ã°" not in captured
    assert "Ã¢" not in captured


def test_get_top_liquid_stocks_extended_uses_data_manager_universe(monkeypatch, capsys):
    monkeypatch.setattr(
        SandboxRegistry.DataManager.DataManager,
        "list_tickers",
        lambda: ["AAA", "BBB", "REPORT"],
    )
    monkeypatch.setattr(
        "core.market.MarketLists.get_market_list",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not use market list")),
    )
    monkeypatch.setattr(
        SandboxRegistry.DataManager.DataManager,
        "get_stock_data",
        lambda *_args, **_kwargs: None,
    )

    result = SandboxRegistry.get_top_liquid_stocks(limit=5, universe="extended")

    captured = capsys.readouterr().out
    assert result == ["AAA", "BBB"]
    assert "[SandboxRegistry] Scoring 2 tickers for liquidity (extended market universe)..." in captured
