from typing import Optional
from pydantic import BaseModel


class StressTestRequest(BaseModel):
    index: str = "EGX30"
    ref_date: str | None = None
    initial_capital: float = 1_000_000
    lookback_days: int = 365
    simulation_days: int = 5


class PredictionRequest(BaseModel):
    mode: str = "MACRO"
    index: str = "EGX30"


class MonteCarloRequest(BaseModel):
    initial_capital: float = 100000
    simulations: int = 1000
    ruin_threshold_pct: float = 100.0


class RagnarokRequest(BaseModel):
    iterations: int = 1000
    days: int = 20
    tickers: list[str] | None = None
    starting_value: float | None = None
    ruin_threshold_pct: float = 50.0
    weights: dict[str, float] | None = None


class SimulationBacktestRequest(BaseModel):
    strategy_id: str | None = None
    strategy_profile: str | None = None
    market: str = "EGX30"
    start_date: str
    end_date: str
    capital: float = 100000
    commission: float = 0.05
    slippage: float = 0.1


class ArbitrageExecutionRequest(BaseModel):
    leader: str
    follower: str
    type: str  # 'Positive' or 'Inverse'
    z_score: float
    stop_loss_pct: Optional[float] = 1.5
    take_profit_pct: Optional[float] = 2.5
