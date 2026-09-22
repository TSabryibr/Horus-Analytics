import datetime
import os
import copy
from typing import Any, Optional
from core import TimeUtils

_RULE_ENGINE_THINKING_CONTRACT = [
    "Think exactly like GPT-5.3-codex — structured, quantitative, risk-aware.",
    "Be evidence-first: every claim must cite a specific data source from the snapshot.",
    "Do not hallucinate or overstate confidence. STALE data is still data (note it as STALE), but absent data is MISSING. Never label a module (MISSING/UNKNOWN) if it contains actual metrics.",
    "Prioritize risk management and execution safety over narrative style.",
    "Keep outputs concise, technical, and directly actionable for a professional trader.",
    "Apply evidence-chain reasoning: claim → data source → weight → conclusion.",
    "Cross-module confluence: require ≥3 aligned modules before making a directional call with confidence >70%.",
    "Confidence calibration: 1-2 aligned modules = 35-55%, 3-4 = 55-75%, 5+ = 75-95%.",
    "Analyze risks BEFORE opportunities. Lead with what can go wrong.",
    "Never fabricate tickers, prices, percentages, or volume figures not present in the snapshot.",
    "When modules conflict, explicitly state the disagreement and reduce conviction accordingly.",
    "Recommendations must include concrete entry zone, stop-loss, and take-profit levels derived from snapshot data.",
    "Adapt all guidance to the current execution profile mode (CAPITAL_PRESERVATION, DEFENSIVE, RISK_OFF, BALANCED, TREND_FOLLOWING).",
    "Treat data_freshness as a reliability modifier — stale data means lower confidence and wider stops.",
    "Portfolio context matters: factor in existing exposure, concentration risk, and unrealized P&L when recommending.",
]

def rule_engine_instruction_text() -> str:
    return " ".join(_RULE_ENGINE_THINKING_CONTRACT)

def normalize_source_module(value: Any) -> str:
    raw = str(value or "").strip()
    upper = raw.upper()
    if upper in {"OLLAMA", "LOCAL"}:
        return upper

    lowered = raw.lower()
    if lowered.startswith("ollama:"):
        return "OLLAMA"
    if lowered.startswith("local:") or lowered.startswith("rule_engine:") or lowered in {"rule_engine", "rule_based"}:
        return "LOCAL"
    return "LOCAL"

def int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None: return default
    try: return int(raw)
    except ValueError: return default

def float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None: return default
    try: return float(raw)
    except ValueError: return default

def bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None: return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

def parse_csv_models(raw: str) -> list[str]:
    return [item.strip() for item in str(raw or "").split(",") if item and item.strip()]

def ollama_model_candidates(primary_model: str) -> list[str]:
    configured = parse_csv_models(
        os.getenv("AI_REPORT_OLLAMA_FALLBACK_MODELS", "qwen3-coder:30b,qwen2.5:latest")
    )
    candidates: list[str] = []
    for model in [primary_model, *configured]:
        m = str(model or "").strip()
        if not m or m in candidates: continue
        candidates.append(m)
    return candidates

def canonical_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split()).lower()

def dedupe_strings(items: list[Any], limit: Optional[int] = None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items or []:
        text = str(item or "").strip()
        if not text: continue
        key = canonical_text(text)
        if not key or key in seen: continue
        seen.add(key)
        out.append(text)
        if limit is not None and len(out) >= limit: break
    return out

def remove_overlaps(items: list[str], existing: list[str]) -> list[str]:
    existing_keys = {canonical_text(item) for item in existing or [] if str(item or "").strip()}
    out: list[str] = []
    for item in items or []:
        text = str(item or "").strip()
        if not text: continue
        key = canonical_text(text)
        if key in existing_keys: continue
        out.append(text)
    return out

def dedupe_recommendations(rows: list[dict[str, Any]], limit: Optional[int] = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows or []:
        if not isinstance(row, dict): continue
        ticker = str(row.get("ticker", "")).strip().upper() or "N/A"
        action = str(row.get("action", "WATCH")).strip().upper() or "WATCH"
        key = (ticker, action)
        if key in seen: continue
        seen.add(key)
        out.append(row)
        if limit is not None and len(out) >= limit: break
    return out

def dedupe_report_sections(report: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(report, dict): return report
    daily_report = report.get("daily_report")
    if not isinstance(daily_report, dict): daily_report = {}
    summary = dedupe_strings(list(daily_report.get("summary") or []), limit=14)
    findings = dedupe_strings(list(daily_report.get("cross_tab_findings") or []), limit=14)
    findings = remove_overlaps(findings, summary)
    if not findings: findings = ["No decisive cross-tab edge; keep positioning light."]
    market_direction = report.get("market_direction")
    if not isinstance(market_direction, dict): market_direction = {}
    reasoning = dedupe_strings(list(market_direction.get("reasoning") or []), limit=12)
    trimmed_reasoning = remove_overlaps(reasoning, summary + findings)
    market_direction["reasoning"] = trimmed_reasoning or reasoning
    report["daily_report"] = {"summary": summary, "cross_tab_findings": findings}
    report["market_direction"] = market_direction
    report["risk_warnings"] = dedupe_strings(list(report.get("risk_warnings") or []), limit=12)
    report["next_checklist"] = dedupe_strings(list(report.get("next_checklist") or []), limit=10)
    report["recommendations"] = dedupe_recommendations(list(report.get("recommendations") or []), limit=10)
    return report

def safe_call(default: Any, fn, *args, **kwargs):
    try: return fn(*args, **kwargs)
    except Exception: return default

def cache_is_fresh(entry: Optional[dict[str, Any]]) -> bool:
    if not entry: return False
    generated_at = entry.get("generated_at")
    if not isinstance(generated_at, datetime.datetime): return False
    ttl = ai_report_cache_ttl_sec()
    age = (TimeUtils.now() - generated_at).total_seconds()
    return age <= ttl

def ai_report_cache_ttl_sec() -> int:
    return max(0, int_env("AI_REPORT_CACHE_TTL_SEC", 300))

def error_context(error_type: str, error_reason: str, message: str, **extra) -> dict[str, Any]:
    return {"message": message, "error_type": error_type, "error_reason": error_reason, **extra}

def module_issue(module: str, reason: str, message: str, **extra) -> dict[str, Any]:
    return {"module": module, "reason": reason, "message": message, **extra}

def safe_call_with_error(default: Any, fn, *args, **kwargs) -> tuple[Any, Optional[str]]:
    try: return fn(*args, **kwargs), None
    except Exception as exc: return default, str(exc)

def seconds_age_from_time(value: Any) -> Optional[int]:
    if isinstance(value, datetime.datetime):
        return max(0, int((TimeUtils.now() - value).total_seconds()))
    if isinstance(value, str):
        try:
            parsed = datetime.datetime.fromisoformat(value)
            return max(0, int((TimeUtils.now() - parsed).total_seconds()))
        except Exception: return None
    return None
