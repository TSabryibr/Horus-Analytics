from __future__ import annotations
"""Simple scoring for price-action signals."""



def build_signal_score(*, confirmations: int, warnings: int, liquidity_ok: bool, relative_volume: float) -> int:
    score = confirmations * 20
    if liquidity_ok:
        score += 15
    if relative_volume >= 1.5:
        score += 10
    elif relative_volume >= 1.0:
        score += 5
    score -= warnings * 15
    return max(0, min(100, score))
