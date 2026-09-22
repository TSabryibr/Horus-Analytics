import asyncio
import base64
import concurrent.futures
import os
import sys
from typing import Any
from fastapi import APIRouter, HTTPException, Request
import requests

from core import MonteCarlo, RagnarokSimulator, TimeUtils
from core.analyzers import SandboxRegistry
from core.price_action.backtest import run_price_action_backtest
from core.price_action.catalog import get_price_action_strategy
from core.simulation import StressTest
from database import Position, Trade
from routes.analytics.cache import (
    _arbitrage_cache_bucket,
    _cache_is_fresh,
    _cache_ttl_seconds,
    _mark_cache_timestamp,
    _normalize_arbitrage_universe,
)
from routes.analytics.models import (
    ArbitrageExecutionRequest,
    MonteCarloRequest,
    RagnarokRequest,
    SimulationBacktestRequest,
    StressTestRequest,
)
from routes.shared import limiter

public_router = APIRouter(tags=["analytics"])
router = APIRouter(tags=["analytics"])

# Dedicated compute worker pool strictly capped to avoid saturating FastAPI ASGI event loop
_SIM_COMPUTE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="HorusComputeWorker",
)


def get_sim_executor_stats() -> dict[str, Any]:
    """Return runtime stats for the simulations compute executor."""
    return {
        "max_workers": getattr(_SIM_COMPUTE_EXECUTOR, "_max_workers", 2),
        "threads_alive": len(getattr(_SIM_COMPUTE_EXECUTOR, "_threads", [])),
    }


async def _run_in_sim_executor(func, *args, **kwargs):
    """Execute a CPU-bound simulation function inside the dedicated worker pool."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_SIM_COMPUTE_EXECUTOR, lambda: func(*args, **kwargs))


def _resolve_symbol(name: str, fallback: any) -> any:
    mod = sys.modules.get("routes.analytics")
    if mod and hasattr(mod, name):
        return getattr(mod, name)
    return fallback


@router.post("/api/v1/stress-test", summary="Portfolio Stress Test", description="Runs stress scenarios on valid portfolios against specific market indices.")
async def run_stress_test_api(req: StressTestRequest):
    try:
        stress_test = _resolve_symbol("StressTest", StressTest)
        provided_fields = getattr(req, "model_fields_set", set())
        if provided_fields.intersection({"ref_date", "initial_capital", "lookback_days", "simulation_days"}):
            result = await _run_in_sim_executor(
                stress_test.run_stress_test,
                req.index,
                ref_date=req.ref_date,
                initial_capital=req.initial_capital,
                lookback_days=req.lookback_days,
                simulation_days=req.simulation_days,
            )
        else:
            result = await _run_in_sim_executor(stress_test.run_stress_test, req.index)
        if not result:
            return {
                "status": "no_data",
                "data": None,
                "message": "Unable to run stress test for the selected inputs.",

            }
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@public_router.get("/api/v1/arbitrage", summary="Arbitrage Opportunities", description="Finds statistical arbitrage opportunities using lagged correlation analysis.")
def get_arbitrage(universe: str = "default"):
    universe_mode = _normalize_arbitrage_universe(universe)
    cache_bucket = _arbitrage_cache_bucket(universe_mode)
    ttl = _cache_ttl_seconds("ARBITRAGE_CACHE_TTL_SEC", 300)
    if cache_bucket["data"] and _cache_is_fresh(cache_bucket, ttl):
        return cache_bucket["data"]
    sandbox = _resolve_symbol("SandboxRegistry", SandboxRegistry)
    cache_bucket["data"] = sandbox.get_lagged_correlations(universe=universe_mode)
    _mark_cache_timestamp(cache_bucket)
    return cache_bucket["data"]


@router.post("/api/v1/execute-arbitrage", summary="Execute Arbitrage Spread", description="Executes a lead-lag arbitrage spread trade via Trading 212 API.")
@limiter.limit("5/minute")
def execute_arbitrage(req: ArbitrageExecutionRequest, request: Request):
    api_key = os.getenv("T212_API_KEY")
    api_secret = os.getenv("T212_API_SECRET")
    env = os.getenv("T212_ENV", "live")
    base_url = f"https://{env}.trading212.com"

    if not api_key or not api_secret:
        raise HTTPException(status_code=401, detail="Trading 212 credentials missing. Ensure T212_API_KEY and T212_API_SECRET are set.")

    auth_string = f"{api_key}:{api_secret}"
    b64_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/json",
    }

    try:
        target_ticker = req.follower.strip().upper()
        if "_EQ" not in target_ticker and "_CRYPTO" not in target_ticker:
            target_ticker = f"{target_ticker}_US_EQ"

        is_buy = True
        if req.type.lower() == "positive" and req.z_score < 0:
            is_buy = False
        elif req.type.lower() == "inverse" and req.z_score > 0:
            is_buy = False

        qty = 1 if is_buy else -1
        sl_pct = req.stop_loss_pct or 1.5
        tp_pct = req.take_profit_pct or 2.5

        payload = {
            "ticker": target_ticker,
            "quantity": qty,
        }

        response = requests.post(f"{base_url}/api/v0/equity/orders/market", headers=headers, json=payload, timeout=5)

        if response.status_code in [200, 201]:
            resp_data = response.json()
            return {
                "status": "success",
                "message": f"Successfully routed {'BUY' if is_buy else 'SELL'} order for {target_ticker} (Unhedged Lead-Lag | SL -{sl_pct}%, TP +{tp_pct}%)",
                "data": resp_data,
                "brackets": {"stop_loss_pct": sl_pct, "take_profit_pct": tp_pct},
            }
        else:
            err_msg = response.text
            try:
                err_msg = response.json()
            except Exception:
                pass
            raise HTTPException(status_code=response.status_code, detail=f"Broker execution failed: {err_msg}")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Trading 212 API: {str(e)}")


@router.post("/api/v1/montecarlo", summary="Monte Carlo Simulation", description="Runs Monte Carlo simulations on trade history to project future performance.")
@limiter.limit("5/minute")
async def run_monte_carlo_sim(req: MonteCarloRequest, request: Request):
    try:
        from routes.scanner import sanitize_floats
        monte_carlo = _resolve_symbol("MonteCarlo", MonteCarlo)
        time_utils = _resolve_symbol("TimeUtils", TimeUtils)
        trade_model = _resolve_symbol("Trade", Trade)

        # Fetch closed trades from DB
        trades = list(trade_model.select().where(trade_model.exit_date <= time_utils.now()).dicts().iterator())

        if not trades:
            return {"status": "warning", "message": "No closed trades found for simulation."}

        formatted_trades = []
        for t in trades:
            pnl = t.get("pnl", 0)
            entry = t.get("entry_price", 1)
            shares = t.get("shares", 1)

            if "pnl_pct" in t and t["pnl_pct"] is not None:
                pnl_pct = t["pnl_pct"]
            else:
                cost_basis = entry * shares
                pnl_pct = (pnl / cost_basis * 100) if cost_basis else 0

            formatted_trades.append({"pnl": pnl, "pnl_pct": pnl_pct})

        if "ruin_threshold_pct" in getattr(req, "model_fields_set", set()):
            result = await _run_in_sim_executor(
                monte_carlo.run_monte_carlo,
                formatted_trades,
                req.initial_capital,
                req.simulations,
                ruin_threshold_pct=req.ruin_threshold_pct,
            )
        else:
            result = await _run_in_sim_executor(
                monte_carlo.run_monte_carlo,
                formatted_trades,
                req.initial_capital,
                req.simulations,
            )
        return {"status": "success", "data": sanitize_floats(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/ragnarok", summary="Ragnarok Monte Carlo", description="Simulates portfolio ruin probability using correlated historical returns.")
@limiter.limit("5/minute")
async def run_ragnarok(req: RagnarokRequest, request: Request):
    try:
        from routes.scanner import sanitize_floats
        ragnarok = _resolve_symbol("RagnarokSimulator", RagnarokSimulator)
        position_model = _resolve_symbol("Position", Position)

        tickers = []
        if req.tickers:
            tickers = [str(t).strip().upper() for t in req.tickers if str(t).strip()]
        else:
            open_positions = (
                position_model.select(position_model.ticker)
                .where(position_model.status == "OPEN")
                .dicts()
            )
            tickers = [str(row["ticker"]).strip().upper() for row in open_positions if row.get("ticker")]

        tickers = list(dict.fromkeys(tickers))
        if not tickers:
            return {
                "status": "error",
                "message": "No portfolio tickers found. Provide tickers or open positions first.",
            }

        optional_kwargs: dict[str, Any] = {}
        provided_fields = getattr(req, "model_fields_set", set())
        if "starting_value" in provided_fields and req.starting_value is not None:
            optional_kwargs["starting_value"] = req.starting_value
        if "ruin_threshold_pct" in provided_fields:
            optional_kwargs["ruin_threshold_pct"] = req.ruin_threshold_pct
        if "weights" in provided_fields and req.weights:
            optional_kwargs["weights"] = {str(k).strip().upper(): float(v) for k, v in req.weights.items()}

        result = await _run_in_sim_executor(
            ragnarok.run_ragnarok_simulation,
            portfolio_tickers=tickers,
            iterations=req.iterations,
            days=req.days,
            **optional_kwargs,
        )
        return {"status": "success", "data": sanitize_floats(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/api/v1/simulation/backtest",
    summary="Simulation Strategy Backtest",
    description="Runs a historical strategy backtest for simulator validation.",
)
async def run_simulation_backtest(req: SimulationBacktestRequest):
    try:
        get_strategy_fn = _resolve_symbol("get_price_action_strategy", get_price_action_strategy)
        run_backtest_fn = _resolve_symbol("run_price_action_backtest", run_price_action_backtest)

        strategy_id = str(req.strategy_id or req.strategy_profile or "").strip().lower()
        if not strategy_id:
            strategy_id = "ascending_triangle_breakout"
        if get_strategy_fn(strategy_id) is None:
            raise HTTPException(status_code=400, detail=f"Unknown strategy/profile '{strategy_id}'")

        result = await _run_in_sim_executor(
            run_backtest_fn,
            strategy_id=strategy_id,
            market=str(req.market or "EGX30").strip().upper(),
            date_from=str(req.start_date),
            date_to=str(req.end_date),
            capital=float(req.capital),
            commission_pct=float(req.commission),
            slippage_pct=float(req.slippage),
        )

        metrics = result.get("metrics", {}) if isinstance(result, dict) else {}
        return {
            "status": "success",
            "data": {
                "strategy_id": strategy_id,
                "market": str(req.market or "EGX30").strip().upper(),
                "start_date": str(req.start_date),
                "end_date": str(req.end_date),
                "capital": float(req.capital),
                "commission": float(req.commission),
                "slippage": float(req.slippage),
                "equity_curve": result.get("equity_curve", []),
                "trades": result.get("trades", []),
                "total_return": metrics.get("total_return", 0.0),
                "sharpe": None,
                "sortino": None,
                "calmar": None,
                "max_drawdown": metrics.get("max_drawdown", 0.0),
                "profit_factor": metrics.get("profit_factor", 0.0),
                "expectancy": metrics.get("expectancy", 0.0),
                "win_rate": metrics.get("win_rate", 0.0),
                "trade_count": metrics.get("trade_count", 0),
                "raw": result,
            },
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
