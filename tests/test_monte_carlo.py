from core import MonteCarlo
def test_run_returns_statistics_keys():
    trades = [{"pnl_pct": 2.0}, {"pnl_pct": -1.0}, {"pnl_pct": 3.0}] * 5
    result = MonteCarlo.run_monte_carlo(trades, initial_equity=100_000, simulations=200)

    assert result is not None
    expected_keys = {
        "simulations",
        "median_equity",
        "worst_case_equity",
        "best_case_equity",
        "avg_max_drawdown",
        "median_max_drawdown",
        "worst_max_drawdown",
        "loss_probability",
        "ruin_probability",
        "ruin_threshold_pct",
        "ruin_floor",
        "drawdown_probability_20",
        "drawdown_probability_50",
        "plot_paths",
    }
    assert expected_keys.issubset(set(result.keys()))


def test_run_empty_trades_returns_none():
    assert MonteCarlo.run_monte_carlo([], initial_equity=100_000) is None


def test_run_with_pnl_pct():
    trades = [{"pnl_pct": 5.0}] * 10
    result = MonteCarlo.run_monte_carlo(trades, initial_equity=100_000, simulations=100)

    assert result is not None
    assert result["simulations"] == 100
    # All trades are positive, so median should exceed starting equity
    assert result["median_equity"] > 100_000


def test_run_with_pnl_absolute():
    trades = [{"pnl": 1000}] * 10
    result = MonteCarlo.run_monte_carlo(trades, initial_equity=100_000, simulations=100)

    assert result is not None
    assert result["median_equity"] > 100_000


def test_ruin_probability_zero_for_all_wins():
    trades = [{"pnl_pct": 1.0}] * 20  # Only winning trades
    result = MonteCarlo.run_monte_carlo(trades, initial_equity=100_000, simulations=200)

    assert result is not None
    assert result["ruin_probability"] == 0.0


def test_threshold_ruin_probability_uses_requested_floor():
    trades = [{"pnl_pct": -20.0}] * 3 + [{"pnl_pct": 10.0}] * 2
    result = MonteCarlo.run_monte_carlo(
        trades,
        initial_equity=100_000,
        simulations=300,
        ruin_threshold_pct=50,
    )

    assert result is not None
    assert result["ruin_threshold_pct"] == 50.0
    assert result["ruin_floor"] == 50_000.0
    assert result["loss_probability"] >= result["ruin_probability"]


def test_median_equity_increases_for_winning_strategy():
    # Net positive expectancy: +3 * 5 wins, -1 * 5 losses = +10 net
    trades = [{"pnl_pct": 3.0}] * 5 + [{"pnl_pct": -1.0}] * 5
    result = MonteCarlo.run_monte_carlo(trades, initial_equity=100_000, simulations=500)

    assert result is not None
    assert result["median_equity"] > 100_000
