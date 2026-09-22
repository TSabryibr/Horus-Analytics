from __future__ import annotations

import copy
import json
import logging
import os
import re
from typing import Any, Callable, Optional

import requests

from core.settings import settings
from ..boundary import (
    bool_env,
    dedupe_recommendations,
    dedupe_report_sections,
    dedupe_strings,
    float_env,
    ollama_model_candidates,
)
from .templates import _build_llm_prompts

logger = logging.getLogger("horus.ai_report.generation")


def _strip_code_fences(text: str) -> str:
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if len(lines) >= 3:
            value = "\n".join(lines[1:-1]).strip()
    return value


def _repair_llm_json(raw: str) -> str:
    """Best-effort repair of malformed JSON produced by LLMs.

    Handles: thinking blocks, trailing commas, unescaped control chars,
    truncated output (missing closing brackets/braces), and BOM.
    Returns the repaired string; caller should still wrap json.loads in try/except.
    """
    text = raw.strip().lstrip("\ufeff")

    # Strip <think>...</think> blocks some models emit
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # If the model wrapped the JSON in markdown fences, strip again
    text = _strip_code_fences(text)

    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Escape bare control characters inside string values (\x00-\x1f except valid \t \n \r)
    def _escape_controls(m: re.Match) -> str:
        return m.group(0).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")

    text = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', _escape_controls, text)

    # Auto-close truncated JSON (count unmatched braces/brackets)
    opens = 0
    sq_opens = 0
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            opens += 1
        elif ch == "}":
            opens -= 1
        elif ch == "[":
            sq_opens += 1
        elif ch == "]":
            sq_opens -= 1

    # Strip trailing incomplete tokens before we close braces.
    text = text.rstrip()
    changed = True
    while changed and text:
        changed = False
        if text[-1] in (",", ":"):
            text = text[:-1].rstrip()
            changed = True
        if re.search(r',\s*"[^"]*"\s*$', text):
            text = re.sub(r',\s*"[^"]*"\s*$', "", text)
            changed = True

    # Close unclosed brackets/braces
    if sq_opens > 0:
        text += "]" * sq_opens
    if opens > 0:
        text += "}" * opens

    return text


def _safe_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return dedupe_strings(value)


def _safe_recommendations(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker", "")).strip().upper()
        action = str(row.get("action", "WATCH")).strip().upper()
        confidence = row.get("confidence", 50)
        try:
            confidence_f = float(confidence)
        except Exception:
            confidence_f = 50.0
        out.append(
            {
                "ticker": ticker or "N/A",
                "action": action if action in {"BUY", "SELL", "HOLD", "WATCH"} else "WATCH",
                "confidence": round(max(0.0, min(100.0, confidence_f)), 1),
                "risk": str(row.get("risk", "MEDIUM")).upper(),
                "rationale": str(row.get("rationale", "")).strip(),
                "entry_zone": str(row.get("entry_zone", "")).strip(),
                "stop_loss": str(row.get("stop_loss", "")).strip(),
                "take_profit": str(row.get("take_profit", "")).strip(),
                "horizon": str(row.get("horizon", "1-5d")).strip(),
            }
        )
    return dedupe_recommendations(out)


def _normalize_llm_report(candidate: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(fallback)

    headline = str(candidate.get("headline", "")).strip()
    if headline:
        normalized["headline"] = headline

    md = candidate.get("market_direction")
    if isinstance(md, dict):
        label = str(md.get("label", normalized["market_direction"]["label"])).upper()
        if label in {"BULLISH", "BEARISH", "NEUTRAL"}:
            normalized["market_direction"]["label"] = label
        try:
            conf = float(md.get("confidence", normalized["market_direction"]["confidence"]))
            normalized["market_direction"]["confidence"] = max(0.0, min(100.0, conf))
        except Exception:
            pass
        horizon = str(md.get("time_horizon", "")).strip()
        if horizon:
            normalized["market_direction"]["time_horizon"] = horizon
        reasoning = _safe_string_list(md.get("reasoning"))
        if reasoning:
            normalized["market_direction"]["reasoning"] = reasoning[:10]

    daily = candidate.get("daily_report")
    if isinstance(daily, dict):
        summary = _safe_string_list(daily.get("summary"))
        findings = _safe_string_list(daily.get("cross_tab_findings"))
        if summary:
            normalized["daily_report"]["summary"] = summary[:12]
        if findings:
            normalized["daily_report"]["cross_tab_findings"] = findings[:12]

    recs = _safe_recommendations(candidate.get("recommendations"))
    if recs:
        normalized["recommendations"] = recs[:10]

    warnings = _safe_string_list(candidate.get("risk_warnings"))
    if warnings:
        normalized["risk_warnings"] = warnings[:12]

    checklist = _safe_string_list(candidate.get("next_checklist"))
    if checklist:
        normalized["next_checklist"] = checklist[:12]

    return dedupe_report_sections(normalized)


def _call_ollama_report(
    *,
    api_key: str,
    base_url: str,
    model: str,
    timeout_sec: float,
    num_ctx: Optional[int],
    snapshot: dict[str, Any],
    fallback_report: dict[str, Any],
) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    system_prompt, user_prompt = _build_llm_prompts(snapshot, fallback_report)
    options: dict[str, Any] = {"temperature": 0.2}
    if num_ctx and num_ctx > 0:
        options["num_ctx"] = int(num_ctx)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt, default=str)},
        ],
        "stream": False,
        "format": "json",
        "keep_alive": "30m",
        "options": options,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        request_timeout: tuple[float, Optional[float]] = (10.0, timeout_sec if timeout_sec > 0 else None)
        resp = requests.post(
            f"{base_url.rstrip('/')}/api/chat",
            headers=headers,
            json=payload,
            timeout=request_timeout,
        )
        if resp.status_code >= 400:
            return None, f"Ollama API error {resp.status_code}: {resp.text[:200]}"
        body = resp.json()
        content = ""
        if isinstance(body, dict):
            message = body.get("message")
            if isinstance(message, dict):
                content = str(message.get("content", "")).strip()
            if not content:
                content = str(body.get("response", "")).strip()
        if not content:
            return None, "Ollama returned empty content."
        cleaned = _repair_llm_json(content)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = json.loads(_strip_code_fences(content))
        if not isinstance(parsed, dict):
            return None, "Ollama response is not a JSON object."
        normalized = _normalize_llm_report(parsed, fallback_report)
        return normalized, None
    except requests.exceptions.ReadTimeout:
        return None, (
            f"Ollama read timed out after {timeout_sec:.1f}s. "
            "Increase AI_REPORT_OLLAMA_TIMEOUT_SEC, set AI_REPORT_OLLAMA_TIMEOUT_SEC=0 to disable read timeout, "
            "or reduce model size."
        )
    except Exception as e:
        return None, f"Ollama call failed: {e}"


def _test_ollama_endpoint(
    *,
    api_key: str,
    base_url: str,
    model: str,
    timeout_sec: float,
) -> tuple[bool, str]:
    headers = {}
    if api_key and api_key.strip() and api_key.lower() not in ["none", "your_api_key"]:
        headers["Authorization"] = f"Bearer {api_key.strip()}"

    try:
        url = f"{base_url.rstrip('/')}/api/tags"
        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout_sec,
        )
        if resp.status_code >= 400:
            if resp.status_code == 401:
                return False, "Ollama Authentication Failed (401). Check your API key."
            return False, f"Ollama API error {resp.status_code} at {url}: {resp.text[:200]}"
        body = resp.json() if resp.content else {}
        available_models: list[str] = []
        if isinstance(body, dict):
            models = body.get("models", [])
            if isinstance(models, list):
                for item in models:
                    if isinstance(item, dict):
                        name = str(item.get("name", "")).strip()
                        if name:
                            available_models.append(name)
        if available_models and model and model not in available_models:
            return False, (
                f"Ollama reachable at {base_url}, but model '{model}' is not available. "
                f"Run: ollama pull {model}"
            )
        return True, f"Ollama is reachable at {base_url} and ready for model '{model}'."
    except Exception as e:
        return False, f"Ollama connectivity test failed: {e}"


def _get_bool_env(name: str, default: bool = True) -> bool:
    import sys
    mod = sys.modules.get("core.ai_report.generation")
    if mod and hasattr(mod, "bool_env"):
        return mod.bool_env(name, default)
    return bool_env(name, default)


def _get_float_env(name: str, default: float) -> float:
    import sys
    mod = sys.modules.get("core.ai_report.generation")
    if mod and hasattr(mod, "float_env"):
        return mod.float_env(name, default)
    return float_env(name, default)


def _get_ollama_model_candidates(model: str) -> list[str]:
    import sys
    mod = sys.modules.get("core.ai_report.generation")
    if mod and hasattr(mod, "ollama_model_candidates"):
        return mod.ollama_model_candidates(model)
    return ollama_model_candidates(model)


def _get_settings():
    import sys
    mod = sys.modules.get("core.ai_report.generation")
    if mod and hasattr(mod, "settings"):
        return mod.settings
    from core.settings import settings
    return settings


def _maybe_generate_llm_report(
    snapshot: dict[str, Any],
    fallback_report: dict[str, Any],
    *,
    call_ollama_report: Optional[Callable[..., tuple[Optional[dict[str, Any]], Optional[str]]]] = None,
) -> tuple[Optional[dict[str, Any]], Optional[str], Optional[str], Optional[str]]:

    enabled = _get_bool_env("AI_REPORT_LLM_ENABLED", True)
    if not enabled:
        return None, None, None, None

    active_settings = _get_settings()
    ollama_api_key = str(getattr(active_settings, "OLLAMA_API_KEY", "") or os.getenv("OLLAMA_API_KEY", "")).strip()
    ollama_base_url = str(
        getattr(active_settings, "OLLAMA_BASE_URL", "") or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ).strip().rstrip("/")
    if not ollama_base_url:
        ollama_base_url = "http://127.0.0.1:11434"

    ollama_model = str(
        getattr(active_settings, "AI_REPORT_OLLAMA_MODEL", "") or os.getenv("AI_REPORT_OLLAMA_MODEL", "qwen3-coder:30b")
    ).strip() or "qwen3-coder:30b"
    raw_num_ctx = getattr(
        active_settings,
        "AI_REPORT_OLLAMA_NUM_CTX",
        os.getenv("AI_REPORT_OLLAMA_NUM_CTX", os.getenv("OLLAMA_CONTEXT_LENGTH", "8192")),
    )
    try:
        ollama_num_ctx = int(raw_num_ctx or 0)
    except (TypeError, ValueError):
        ollama_num_ctx = 8192
    ollama_timeout_sec = float(getattr(active_settings, "AI_REPORT_OLLAMA_TIMEOUT_SEC", 300.0))
    if ollama_timeout_sec < 0:
        ollama_timeout_sec = 0.0
    ollama_fallback_timeout_sec = _get_float_env(
        "AI_REPORT_OLLAMA_FALLBACK_TIMEOUT_SEC",
        180.0 if ollama_timeout_sec == 0 else min(180.0, ollama_timeout_sec),
    )
    if ollama_fallback_timeout_sec < 0:
        ollama_fallback_timeout_sec = 0.0

    attempts: list[str] = []
    ollama_caller = call_ollama_report or _call_ollama_report
    for idx, candidate_model in enumerate(_get_ollama_model_candidates(ollama_model)):
        timeout_for_attempt = ollama_timeout_sec if idx == 0 else ollama_fallback_timeout_sec
        report, err = ollama_caller(
            api_key=ollama_api_key,
            base_url=ollama_base_url,
            model=candidate_model,
            timeout_sec=timeout_for_attempt,
            num_ctx=ollama_num_ctx,
            snapshot=snapshot,
            fallback_report=fallback_report,
        )
        if report:
            last_fallback_reason = " | ".join(attempts) if attempts else None
            return report, None, "OLLAMA", last_fallback_reason
        if err:
            attempts.append(f"ollama:{candidate_model} -> {err}")

    if attempts:
        reason = " | ".join(attempts)
        return None, reason, None, reason
    return None, "Ollama report generation failed without an explicit error.", None, None
