import json
from typing import Any
from database import (
    Portfolio,
    Position,
    Trade,
    HorusExecution,
    PortfolioSnapshot,
    SignalExecutionAttribution,
    SignalOutcome,
)
from core import TimeUtils

class PerformanceTracker:
    SYSTEM_LANE_PORTFOLIOS = {"Intraday Signals", "Swing Signals", "Position Signals"}
    FILLED_EXECUTION_STATES = {"OPEN", "UPDATED", "CLOSED"}

    @staticmethod
    def get_portfolio_performance(portfolio_id: int, days: int = 90) -> dict:
        portfolio = Portfolio.get_by_id(portfolio_id)
        if PerformanceTracker._is_strategy_portfolio(portfolio):
            return PerformanceTracker._get_strategy_attribution_performance(portfolio)
        return PerformanceTracker._get_execution_portfolio_performance(portfolio)

    @staticmethod
    def _is_strategy_portfolio(portfolio: Portfolio) -> bool:
        portfolio_type = str(portfolio.type or "").upper()
        if portfolio_type == "STRATEGY":
            return True
        if portfolio_type == "USER" and bool(portfolio.auto_manage):
            has_direct_attribution = SignalExecutionAttribution.select().where(
                SignalExecutionAttribution.strategy_portfolio == portfolio.id
            ).exists()
            if has_direct_attribution:
                return True
            return SignalExecutionAttribution.select().where(
                SignalExecutionAttribution.strategy_profile_name == portfolio.name
            ).exists()
        return False

    @staticmethod
    def _empty_metrics(max_drawdown: float = 0.0) -> dict[str, float]:
        return {
            "win_rate": 0.0,
            "avg_pnl_pct": 0.0,
            "total_pnl": 0.0,
            "sharpe": 0.0,
            "max_drawdown": round(float(max_drawdown or 0.0), 2),
            "profit_factor": 0.0,
            "avg_holding_days": 0.0,
            "total_trades": 0,
        }

    @staticmethod
    def _portfolio_max_drawdown(portfolio_id: int) -> float:
        snapshots = list(
            PortfolioSnapshot.select()
            .where(PortfolioSnapshot.portfolio == portfolio_id)
            .order_by(PortfolioSnapshot.date.asc())
        )
        max_dd = 0.0
        peak = 0.0
        for snapshot in snapshots:
            equity = float(snapshot.equity_egp or 0.0)
            if equity > peak:
                peak = equity
            if peak > 0:
                dd = (peak - equity) / peak * 100.0
                if dd > max_dd:
                    max_dd = dd
        return max_dd

    @staticmethod
    def _execution_metrics(trades: list[Trade], open_positions: int, max_drawdown: float) -> tuple[dict, dict]:
        if not trades:
            return (
                PerformanceTracker._empty_metrics(max_drawdown=max_drawdown),
                {
                    "open_positions": int(open_positions or 0),
                    "winners": 0,
                    "losers": 0,
                    "best_trade": 0.0,
                    "worst_trade": 0.0,
                },
            )

        total_pnl = sum(float(trade.pnl or 0.0) for trade in trades)
        winners = [trade for trade in trades if float(trade.pnl or 0.0) > 0]
        losers = [trade for trade in trades if float(trade.pnl or 0.0) <= 0]
        win_rate = (len(winners) / len(trades) * 100.0) if trades else 0.0
        avg_pnl_pct = sum(float(trade.pnl_pct or 0.0) for trade in trades) / len(trades)

        gross_profit = sum(float(trade.pnl or 0.0) for trade in winners)
        gross_loss = abs(sum(float(trade.pnl or 0.0) for trade in losers))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)

        holding_days: list[int] = []
        for trade in trades:
            if trade.entry_date and trade.exit_date:
                holding_days.append(max(0, (trade.exit_date - trade.entry_date).days))
        avg_holding = (sum(holding_days) / len(holding_days)) if holding_days else 0.0

        metrics = {
            "win_rate": round(win_rate, 2),
            "avg_pnl_pct": round(avg_pnl_pct, 2),
            "total_pnl": round(total_pnl, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(float(max_drawdown or 0.0), 2),
            "avg_holding_days": round(avg_holding, 1),
            "total_trades": len(trades),
        }
        summary = {
            "open_positions": int(open_positions or 0),
            "winners": len(winners),
            "losers": len(losers),
            "best_trade": round(max(float(trade.pnl_pct or 0.0) for trade in trades), 2),
            "worst_trade": round(min(float(trade.pnl_pct or 0.0) for trade in trades), 2),
        }
        return metrics, summary

    @staticmethod
    def _build_signal_quality(attributions: list[SignalExecutionAttribution]) -> dict[str, Any]:
        generated = len(attributions)
        state_counts: dict[str, int] = {}
        recommendation_ids: set[int] = set()
        for attribution in attributions:
            execution_state = str(getattr(attribution.execution, "state", "") or "").upper()
            state_counts[execution_state] = int(state_counts.get(execution_state, 0) + 1)
            if attribution.recommendation_id:
                recommendation_ids.add(int(attribution.recommendation_id))

        filled_count = sum(state_counts.get(state, 0) for state in PerformanceTracker.FILLED_EXECUTION_STATES)
        skipped_count = int(state_counts.get("SKIPPED", 0))
        failed_count = int(state_counts.get("FAILED", 0))
        pending_count = int(state_counts.get("PENDING_OPEN", 0))
        no_fill_count = skipped_count + failed_count

        outcome_counts: dict[str, int] = {}
        if recommendation_ids:
            for outcome in SignalOutcome.select().where(SignalOutcome.recommendation.in_(list(recommendation_ids))):
                key = str(outcome.outcome_status or "UNKNOWN").upper()
                outcome_counts[key] = int(outcome_counts.get(key, 0) + 1)

        no_trade_count = int(outcome_counts.get("NO_TRADE", 0))
        fill_rate = (filled_count / generated * 100.0) if generated > 0 else 0.0
        no_fill_rate = (no_fill_count / generated * 100.0) if generated > 0 else 0.0
        no_trade_rate = (no_trade_count / generated * 100.0) if generated > 0 else 0.0

        return {
            "generated_count": generated,
            "active_count": generated,
            "filled_count": filled_count,
            "pending_count": pending_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "no_fill_count": no_fill_count,
            "fill_rate": round(fill_rate, 2),
            "no_fill_rate": round(no_fill_rate, 2),
            "no_trade_rate": round(no_trade_rate, 2),
            "outcome_distribution": outcome_counts,
            "execution_state_distribution": state_counts,
        }

    @staticmethod
    def _get_execution_portfolio_performance(portfolio: Portfolio) -> dict:
        trades = list(Trade.select().where(Trade.portfolio == portfolio.id).order_by(Trade.exit_date.desc()))
        open_positions = Position.select().where((Position.portfolio == portfolio.id) & (Position.status == "OPEN")).count()
        max_dd = PerformanceTracker._portfolio_max_drawdown(portfolio.id)
        metrics, summary = PerformanceTracker._execution_metrics(trades, open_positions, max_dd)
        attributions = list(
            SignalExecutionAttribution.select(SignalExecutionAttribution, HorusExecution)
            .join(HorusExecution)
            .where(SignalExecutionAttribution.execution_portfolio == portfolio.id)
        )
        signal_quality = PerformanceTracker._build_signal_quality(attributions)

        return {
            "portfolio": {"id": portfolio.id, "name": portfolio.name, "type": portfolio.type},
            "scope": "LANE_EXECUTION",
            "metrics": metrics,
            "summary": summary,
            "signal_quality": signal_quality,
        }

    @staticmethod
    def _resolve_trade_for_execution(execution: HorusExecution, fallback_portfolio_id: int | None = None) -> Trade | None:
        if execution.trade_id:
            trade = Trade.get_or_none(Trade.id == execution.trade_id)
            if trade is not None:
                return trade
        portfolio_id = int(fallback_portfolio_id or execution.portfolio_id or 0)
        if portfolio_id <= 0:
            return None
        return (
            Trade.select()
            .where(
                (Trade.portfolio == portfolio_id) &
                (Trade.ticker == execution.ticker) &
                (Trade.exit_date >= (execution.created_at or TimeUtils.now()))
            )
            .order_by(Trade.exit_date.desc(), Trade.id.desc())
            .first()
        )

    @staticmethod
    def _get_strategy_attribution_performance(portfolio: Portfolio) -> dict:
        attributions = list(
            SignalExecutionAttribution.select(SignalExecutionAttribution, HorusExecution)
            .join(HorusExecution)
            .where(SignalExecutionAttribution.strategy_portfolio == portfolio.id)
            .order_by(SignalExecutionAttribution.created_at.desc())
        )

        trade_map: dict[int, Trade] = {}
        open_pairs: set[tuple[int, str]] = set()
        execution_portfolio_ids: set[int] = set()
        lanes: set[str] = set()
        profile_names: set[str] = set()

        for attribution in attributions:
            execution = attribution.execution
            execution_portfolio_id = int(attribution.execution_portfolio_id or execution.portfolio_id or 0)
            if execution_portfolio_id > 0:
                execution_portfolio_ids.add(execution_portfolio_id)
            if attribution.lane:
                lanes.add(str(attribution.lane).upper())
            if attribution.strategy_profile_name:
                profile_names.add(str(attribution.strategy_profile_name))

            state = str(execution.state or "").upper()
            if state in {"OPEN", "UPDATED", "PENDING_OPEN"} and execution_portfolio_id > 0:
                open_pairs.add((execution_portfolio_id, str(execution.ticker or "").upper()))

            trade = PerformanceTracker._resolve_trade_for_execution(execution, fallback_portfolio_id=execution_portfolio_id)
            if trade is not None:
                trade_map[int(trade.id)] = trade

        open_positions = 0
        for execution_portfolio_id, ticker in open_pairs:
            exists = Position.select().where(
                (Position.portfolio == execution_portfolio_id) &
                (Position.ticker == ticker) &
                (Position.status == "OPEN")
            ).exists()
            if exists:
                open_positions += 1

        trades = list(trade_map.values())
        max_dd = PerformanceTracker._portfolio_max_drawdown(portfolio.id)
        metrics, summary = PerformanceTracker._execution_metrics(trades, open_positions, max_dd)
        signal_quality = PerformanceTracker._build_signal_quality(attributions)

        return {
            "portfolio": {"id": portfolio.id, "name": portfolio.name, "type": portfolio.type},
            "scope": "STRATEGY_ATTRIBUTION",
            "metrics": metrics,
            "summary": summary,
            "signal_quality": signal_quality,
            "attribution": {
                "strategy_profile_names": sorted(profile_names),
                "execution_portfolio_ids": sorted(execution_portfolio_ids),
                "lanes": sorted(lanes),
            },
        }

    @staticmethod
    def get_system_comparison() -> dict:
        portfolios = list(
            Portfolio.select().where(
                (Portfolio.type == "SYSTEM") &
                (Portfolio.name.in_(list(PerformanceTracker.SYSTEM_LANE_PORTFOLIOS)))
            )
        )
        comparison = []
        for p in portfolios:
            comparison.append(PerformanceTracker.get_portfolio_performance(p.id))
        return {"count": len(comparison), "portfolios": comparison}

    @staticmethod
    def get_execution_history(portfolio_id: int, limit: int = 50) -> list:
        portfolio = Portfolio.get_by_id(portfolio_id)
        history = []
        if PerformanceTracker._is_strategy_portfolio(portfolio):
            attributions = list(
                SignalExecutionAttribution.select(SignalExecutionAttribution, HorusExecution)
                .join(HorusExecution)
                .where(SignalExecutionAttribution.strategy_portfolio == portfolio.id)
                .order_by(HorusExecution.created_at.desc())
                .limit(limit)
            )
            for attribution in attributions:
                history.append(
                    PerformanceTracker._serialize_execution_history_item(
                        execution=attribution.execution,
                        attribution=attribution,
                    )
                )
            return history

        executions = list(
            HorusExecution.select()
            .where(HorusExecution.portfolio == portfolio.id)
            .order_by(HorusExecution.created_at.desc())
            .limit(limit)
        )
        if not executions:
            return history
        execution_ids = [execution.id for execution in executions]
        attribution_by_execution = {
            attribution.execution_id: attribution
            for attribution in SignalExecutionAttribution.select().where(
                SignalExecutionAttribution.execution.in_(execution_ids)
            )
        }
        for execution in executions:
            history.append(
                PerformanceTracker._serialize_execution_history_item(
                    execution=execution,
                    attribution=attribution_by_execution.get(execution.id),
                )
            )
        return history

    @staticmethod
    def _serialize_execution_history_item(
        execution: HorusExecution,
        attribution: SignalExecutionAttribution | None = None,
    ) -> dict[str, Any]:
        details = json.loads(execution.details_json or "{}")
        trailing = json.loads(execution.trailing_state or "{}")
        state = execution.state
        close_reason = execution.close_reason
        trade_id = execution.trade_id
        updated_at = execution.updated_at

        trade = PerformanceTracker._resolve_trade_for_execution(
            execution,
            fallback_portfolio_id=getattr(attribution, "execution_portfolio_id", None),
        )
        if trade:
            details.setdefault("exit_price", float(trade.exit_price or 0.0))
            details.setdefault("realized_pnl", float(trade.pnl or 0.0))
            details.setdefault("realized_pnl_pct", float(trade.pnl_pct or 0.0))
            if state in ("OPEN", "UPDATED"):
                state = "CLOSED"
            close_reason = close_reason or trade.reason
            trade_id = trade_id or trade.id
            if trade.exit_date and (updated_at is None or trade.exit_date > updated_at):
                updated_at = trade.exit_date

        execution_portfolio = None
        strategy_portfolio = None
        if attribution is not None:
            execution_portfolio = attribution.execution_portfolio
            strategy_portfolio = attribution.strategy_portfolio
        if execution_portfolio is None:
            execution_portfolio = execution.portfolio

        return {
            "id": execution.id,
            "ticker": execution.ticker,
            "state": state,
            "trigger": execution.trigger_source,
            "planned_entry": float(execution.planned_entry_price or 0.0),
            "actual_entry": float(execution.actual_entry_price or 0.0),
            "gap_pct": float(execution.gap_pct or 0.0),
            "current_sl": float(execution.active_stop_loss or 0.0),
            "current_tp": float(execution.active_target_price or 0.0),
            "close_reason": close_reason,
            "trade_id": trade_id,
            "details": details,
            "trailing": trailing,
            "execution_portfolio_id": execution_portfolio.id if execution_portfolio else execution.portfolio_id,
            "execution_portfolio_name": execution_portfolio.name if execution_portfolio else None,
            "strategy_portfolio_id": strategy_portfolio.id if strategy_portfolio else None,
            "strategy_portfolio_name": strategy_portfolio.name if strategy_portfolio else None,
            "lane": str(getattr(attribution, "lane", "") or "").upper() or None,
            "scan_type": str(getattr(attribution, "scan_type", "") or "").upper() or None,
            "strategy_profile_name": getattr(attribution, "strategy_profile_name", None),
            "strategy_source_type": getattr(attribution, "strategy_source_type", None),
            "created_at": execution.created_at.isoformat() if execution.created_at else None,
            "updated_at": updated_at.isoformat() if updated_at else None,
        }
