import logging

logger = logging.getLogger("HumanSlippageModel")

class HumanSlippageModel:
    def __init__(self, default_slippage_bps: int = 25):
        self.default_slippage_bps = default_slippage_bps

    def calculate_adjusted_targets(self, entry_price: float, target_1: float, target_2: float, stop_loss: float, slippage_bps: int = None) -> dict:
        """
        Adjusts signal entry and target parameters to reflect manual human subscriber
        execution latency (30s) and market bid-ask spread slippage.
        """
        if entry_price <= 0:
            return {
                "adjusted_entry": entry_price,
                "adjusted_target_1": target_1,
                "adjusted_target_2": target_2,
                "adjusted_stop_loss": stop_loss,
                "slippage_bps": 0
            }

        bps = slippage_bps if slippage_bps is not None else self.default_slippage_bps
        slippage_factor = 1.0 + (bps / 10000.0)

        adj_entry = round(entry_price * slippage_factor, 2)
        adj_t1 = round(target_1, 2) if target_1 > 0 else 0.0
        adj_t2 = round(target_2, 2) if target_2 > 0 else 0.0
        adj_sl = round(stop_loss, 2) if stop_loss > 0 else 0.0

        return {
            "raw_entry": round(entry_price, 2),
            "adjusted_entry": adj_entry,
            "adjusted_target_1": adj_t1,
            "adjusted_target_2": adj_t2,
            "adjusted_stop_loss": adj_sl,
            "slippage_bps": bps
        }

human_slippage_model = HumanSlippageModel()
