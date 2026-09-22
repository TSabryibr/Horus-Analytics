import os
import time
import shutil
import logging
from pathlib import Path
import datetime
import yaml

from core import TimeUtils
from core import WalkForwardValidation

# Numpy handling for yaml (if tickets contain numpy objects)
import numpy as np
def _numpy_constructor(loader, node):
    return loader.construct_scalar(node)
yaml.add_constructor('tag:yaml.org,2002:python/object/apply:numpy.core.multiarray.scalar', _numpy_constructor, Loader=yaml.SafeLoader)

logger = logging.getLogger("horus.metrics_parser")

class MetricsParser:
    def __init__(self, watch_dir: str = "reports/edge_pipeline/validation", processed_dir: str = "reports/edge_pipeline/processed"):
        self.watch_dir = Path(watch_dir)
        self.processed_dir = Path(processed_dir)
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def process_ticket(self, file_path: str | Path):
        file_path = Path(file_path)
        if not file_path.exists():
            return

        logger.info(f"[MetricsParser] Processing new validation ticket: {file_path.name}")

        try:
            # We use unsafe_load if there are complex python objects,
            # but SafeLoader + custom constructors is generally preferred.
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    ticket_data = yaml.unsafe_load(f)
                except Exception as e:
                    # Fallback if unsafe_load fails
                    logger.warning(f"[MetricsParser] YAML unsafe_load failed, trying safe_load: {e}")
                    f.seek(0)
                    ticket_data = yaml.safe_load(f)

            if not ticket_data or not isinstance(ticket_data, dict):
                logger.error(f"[MetricsParser] Invalid ticket format in {file_path.name}")
                self._mark_processed(file_path, success=False)
                return

            ticker = ticket_data.get("ticker")
            if not ticker:
                logger.error(f"[MetricsParser] Missing 'ticker' in {file_path.name}")
                self._mark_processed(file_path, success=False)
                return

            # Example validation logic based on the ticket's pre-computed metrics
            win_rate = float(ticket_data.get("win_rate", 0))
            avg_pnl = float(ticket_data.get("avg_pnl", 0))
            signals_count = int(ticket_data.get("total_historical_signals", 0))

            logger.info(f"[MetricsParser] Ticket {ticker} Metrics -> Win Rate: {win_rate:.2f}%, Avg PnL: {avg_pnl:.2f}%, Signals: {signals_count}")

            if signals_count >= 5 and win_rate >= 45.0 and avg_pnl >= 0.0:
                logger.info(f"[MetricsParser] Ticket {ticker} passed baseline filters. Triggering Walk-Forward Calibration...")

                # We do a 12-month lookback for the WFA
                end_date = TimeUtils.now()
                start_date = end_date - datetime.timedelta(days=365)

                try:
                    # Trigger the actual parameter evolution and update GlobalSettings
                    evolution_result = WalkForwardValidation.apply_evolved_params(
                        ticker=ticker,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                        train_months=6,
                        val_months=1
                    )

                    if evolution_result.get("applied"):
                        logger.info(f"[MetricsParser] SUCCESSFULLY evolved parameters for {ticker}. Changes: {list(evolution_result.get('applied_params', {}).keys())}")
                    else:
                        logger.warning(f"[MetricsParser] Parameter evolution failed or blocked for {ticker}. Reason: {evolution_result.get('reason')}")
                        # If it was blocked, we might still consider the "ticket processing" as success,
                        # but usually it means the ticker is just not good enough.

                    self._mark_processed(file_path, success=True)
                except Exception as wfa_err:
                    logger.error(f"[MetricsParser] WFA execution failed for {ticker}: {wfa_err}", exc_info=True)
                    self._mark_processed(file_path, success=False)
            else:
                logger.info(f"[MetricsParser] Ticket {ticker} rejected. Does not meet minimum performance thresholds.")
                self._mark_processed(file_path, success=True)

        except Exception as e:
            logger.error(f"[MetricsParser] Error processing ticket {file_path.name}: {e}", exc_info=True)
            self._mark_processed(file_path, success=False)

    def _mark_processed(self, file_path: Path, success: bool):
        try:
            timestamp = int(time.time())
            status_prefix = "ok" if success else "failed"
            new_name = f"{status_prefix}_{timestamp}_{file_path.name}"
            target_path = self.processed_dir / new_name
            shutil.move(str(file_path), str(target_path))
            logger.debug(f"[MetricsParser] Moved ticket to {target_path}")
        except Exception as e:
            logger.error(f"[MetricsParser] Could not move processed ticket {file_path}: {e}")
