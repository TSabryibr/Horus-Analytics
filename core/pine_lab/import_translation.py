from __future__ import annotations
from core.settings import settings

import copy
import json
import os
from typing import Any

import requests

from core.ai_report import ollama_model_candidates, strip_code_fences, repair_llm_json

from .import_spec import build_missing_signal, build_rule_spec
from .import_validator import validate_import_rule_spec

_SUPPORTED_SIGNAL_ROLES = ("long_entry", "short_entry", "long_exit", "short_exit")


def _build_seed_signal_map(
    reduced_source_pack: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    candidate_signals = list(reduced_source_pack.get("candidate_signals") or [])
    definitions = list(reduced_source_pack.get("definitions") or [])
    definition_by_name = {
        str(item.get("name") or "").strip(): item
        for item in definitions
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    }

    signal_map: dict[str, dict[str, Any]] = {
        "long_entry": build_missing_signal(),
        "short_entry": build_missing_signal(),
        "long_exit": build_missing_signal(),
        "short_exit": build_missing_signal(),
    }

    for candidate in candidate_signals:
        role = str(candidate.get("role") or "").strip()
        if role not in signal_map:
            continue
        signal_map[role] = {
            "status": "mapped",
            "source_name": candidate.get("name"),
            "expression": candidate.get("expression"),
            "line": candidate.get("line"),
            "depends_on": list(candidate.get("depends_on") or []),
            "confidence": float(candidate.get("confidence") or 0.55),
        }

    return signal_map, definition_by_name


def _apply_signal_overrides(
    signal_map: dict[str, dict[str, Any]],
    definition_by_name: dict[str, dict[str, Any]],
    warnings: list[str],
    signal_overrides: dict[str, Any] | None = None,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    overrides = signal_overrides if isinstance(signal_overrides, dict) else {}
    for role, raw_name in overrides.items():
        if role not in signal_map:
            continue
        source_name = str(raw_name or "").strip()
        if not source_name:
            signal_map[role] = build_missing_signal()
            warnings.append(f"Applied override for {role}: cleared the mapped signal.")
            continue
        definition = definition_by_name.get(source_name)
        if definition is None:
            warnings.append(f'Ignored override for {role}: "{source_name}" was not found in extracted definitions.')
            continue
        signal_map[role] = {
            "status": "mapped",
            "source_name": source_name,
            "expression": definition.get("expression"),
            "line": definition.get("line"),
            "depends_on": list(definition.get("depends_on") or []),
            "confidence": float(signal_map.get(role, {}).get("confidence") or 0.45),
        }
        warnings.append(f"Applied override for {role}: using Pine definition `{source_name}`.")
    return signal_map, warnings


def _coerce_warning_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    warnings: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            warnings.append(text)
    return warnings


def _build_provider_translation_prompts(
    reduced_source_pack: dict[str, Any],
    *,
    script_type: str,
) -> tuple[str, dict[str, Any]]:
    system_prompt = (
        "Translate Pine signal logic into a Horus review draft. "
        "Return valid JSON only. No markdown, no code fences, no commentary outside the JSON. "
        "Do not invent variables, indicators, or expressions. "
        "Choose source_name values only from the provided definitions or candidate_signals. "
        "If a role cannot be mapped confidently, mark it as missing and add a warning. "
        "Output schema: "
        "{"
        '"signals": {'
        '"long_entry": {"status": "mapped|missing", "source_name": "string|null", "confidence": "number 0-1"},'
        '"short_entry": {"status": "mapped|missing", "source_name": "string|null", "confidence": "number 0-1"},'
        '"long_exit": {"status": "mapped|missing", "source_name": "string|null", "confidence": "number 0-1"},'
        '"short_exit": {"status": "mapped|missing", "source_name": "string|null", "confidence": "number 0-1"}'
        "},"
        '"warnings": ["string"]'
        "}"
    )
    user_payload = {
        "script_type": script_type,
        "allowed_signal_roles": list(_SUPPORTED_SIGNAL_ROLES),
        "candidate_signals": list(reduced_source_pack.get("candidate_signals") or []),
        "definitions": list(reduced_source_pack.get("definitions") or []),
        "parameters": list(reduced_source_pack.get("parameters") or []),
        "indicators": list(reduced_source_pack.get("indicators") or []),
        "warnings": list(reduced_source_pack.get("warnings") or []),
    }
    return system_prompt, user_payload


def _call_ollama_import_translation(
    *,
    system_prompt: str,
    user_payload: dict[str, Any],
    api_key: str,
    base_url: str,
    model: str,
    timeout_sec: float,
    num_ctx: int,
) -> tuple[dict[str, Any] | None, str | None]:
    options: dict[str, Any] = {"temperature": 0.1}
    if num_ctx > 0:
        options["num_ctx"] = int(num_ctx)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, default=str)},
        ],
        "stream": False,
        "format": "json",
        "keep_alive": "15m",
        "options": options,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        request_timeout: tuple[float, float | None] = (1.5, timeout_sec if timeout_sec > 0 else None)
        response = requests.post(
            f"{base_url.rstrip('/')}/api/chat",
            headers=headers,
            json=payload,
            timeout=request_timeout,
        )
        if response.status_code >= 400:
            return None, f"Ollama API error {response.status_code}: {response.text[:200]}"
        body = response.json()
        content = ""
        if isinstance(body, dict):
            message = body.get("message")
            if isinstance(message, dict):
                content = str(message.get("content", "")).strip()
            if not content:
                content = str(body.get("response", "")).strip()
        if not content:
            return None, "Ollama returned empty content."
        cleaned = repair_llm_json(content)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = json.loads(strip_code_fences(content))
        if not isinstance(parsed, dict):
            return None, "Ollama response is not a JSON object."
        return parsed, None
    except requests.exceptions.ReadTimeout:
        return None, f"Ollama read timed out after {timeout_sec:.1f}s."
    except Exception as exc:
        return None, f"Ollama call failed: {exc}"


def _attempt_provider_translation(
    *,
    reduced_source_pack: dict[str, Any],
    script_type: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    configured_provider = str(
        getattr(settings, "PINE_IMPORT_TRANSLATION_PROVIDER", "") or os.getenv("PINE_IMPORT_TRANSLATION_PROVIDER", "LOCAL") or "LOCAL"
    ).strip().upper()
    if configured_provider != "OLLAMA":
        return None, None, None

    base_url = str(getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434") or "").strip().rstrip("/")
    primary_model = str(getattr(settings, "AI_REPORT_OLLAMA_MODEL", "qwen3.5:latest") or "").strip()
    api_key = str(getattr(settings, "OLLAMA_API_KEY", "") or "").strip()
    num_ctx = int(getattr(settings, "AI_REPORT_OLLAMA_NUM_CTX", getattr(settings, "OLLAMA_CONTEXT_LENGTH", 8192)) or 8192)
    timeout_sec = float(os.getenv("PINE_IMPORT_OLLAMA_TIMEOUT_SEC", "12") or 12)
    fallback_timeout_sec = float(os.getenv("PINE_IMPORT_OLLAMA_FALLBACK_TIMEOUT_SEC", str(min(6.0, timeout_sec))) or min(6.0, timeout_sec))
    if timeout_sec < 0:
        timeout_sec = 0.0
    if fallback_timeout_sec < 0:
        fallback_timeout_sec = 0.0
    if not base_url or not primary_model:
        return None, None, "Ollama translation settings are incomplete."

    system_prompt, user_payload = _build_provider_translation_prompts(reduced_source_pack, script_type=script_type)
    attempts: list[str] = []
    for index, candidate_model in enumerate(ollama_model_candidates(primary_model)):
        timeout_for_attempt = timeout_sec if index == 0 else fallback_timeout_sec
        parsed, error = _call_ollama_import_translation(
            system_prompt=system_prompt,
            user_payload=user_payload,
            api_key=api_key,
            base_url=base_url,
            model=candidate_model,
            timeout_sec=timeout_for_attempt,
            num_ctx=num_ctx,
        )
        if isinstance(parsed, dict):
            return {
                "provider": "OLLAMA",
                "mode": "AI_TRANSLATED",
                "fallback_used": False,
                "model": candidate_model,
            }, parsed, None
        attempts.append(f"ollama:{candidate_model} -> {error or 'unknown error'}")

    return None, None, "; ".join(attempts) if attempts else "Provider translation was not attempted."


def _merge_provider_signal_map(
    provider_payload: dict[str, Any],
    *,
    base_signal_map: dict[str, dict[str, Any]],
    definition_by_name: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    raw_signals = provider_payload.get("signals")
    if not isinstance(raw_signals, dict):
        raise ValueError("Provider translation did not return a signals object.")

    signal_map = copy.deepcopy(base_signal_map)
    for role in _SUPPORTED_SIGNAL_ROLES:
        raw_signal = raw_signals.get(role)
        if raw_signal is None:
            continue
        if not isinstance(raw_signal, dict):
            raise ValueError(f"Provider translation signal for {role} is not an object.")

        status = str(raw_signal.get("status") or "missing").strip().lower()
        if status == "missing":
            continue
        if status != "mapped":
            raise ValueError(f"Provider translation signal for {role} has unsupported status '{status}'.")

        source_name = str(raw_signal.get("source_name") or "").strip()
        if not source_name:
            raise ValueError(f"Provider translation signal for {role} is missing source_name.")
        definition = definition_by_name.get(source_name)
        if definition is None:
            raise ValueError(f'Provider translation signal for {role} referenced unknown source "{source_name}".')

        signal_map[role] = {
            "status": "mapped",
            "source_name": source_name,
            "expression": definition.get("expression"),
            "line": definition.get("line"),
            "depends_on": list(definition.get("depends_on") or []),
            "confidence": float(raw_signal.get("confidence") or signal_map.get(role, {}).get("confidence") or 0.6),
        }

    return signal_map, _coerce_warning_list(provider_payload.get("warnings"))


def build_deterministic_draft_translation(
    reduced_source_pack: dict[str, Any],
    *,
    script_source: str,
    script_type: str,
    signal_overrides: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ignored_sections = list(reduced_source_pack.get("ignored_sections") or [])
    parameters = list(reduced_source_pack.get("parameters") or [])
    indicators = list(reduced_source_pack.get("indicators") or [])
    signal_map, definition_by_name = _build_seed_signal_map(reduced_source_pack)

    warnings = list(reduced_source_pack.get("warnings") or [])
    signal_map, warnings = _apply_signal_overrides(
        signal_map,
        definition_by_name,
        warnings,
        signal_overrides=signal_overrides,
    )
    warnings.append("Using deterministic draft translation. Review the generated rule spec before any backtest.")

    rule_spec = build_rule_spec(
        script_source=script_source,
        script_type=script_type,
        parameters=parameters,
        indicators=indicators,
        definitions_payload=list(reduced_source_pack.get("definitions") or []),
        signal_map=signal_map,
        ignored_sections=ignored_sections,
        warnings=warnings,
        translation_mode="DETERMINISTIC_DRAFT",
    )
    translation = {
        "mode": "DETERMINISTIC_DRAFT",
        "provider": "LOCAL",
        "fallback_used": True,
    }
    return translation, rule_spec


def build_import_translation(
    reduced_source_pack: dict[str, Any],
    *,
    script_source: str,
    script_type: str,
    signal_overrides: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ignored_sections = list(reduced_source_pack.get("ignored_sections") or [])
    parameters = list(reduced_source_pack.get("parameters") or [])
    indicators = list(reduced_source_pack.get("indicators") or [])
    definitions_payload = list(reduced_source_pack.get("definitions") or [])
    seed_signal_map, definition_by_name = _build_seed_signal_map(reduced_source_pack)

    translation_meta, provider_payload, provider_error = _attempt_provider_translation(
        reduced_source_pack=reduced_source_pack,
        script_type=script_type,
    )
    if translation_meta and provider_payload:
        try:
            signal_map, provider_warnings = _merge_provider_signal_map(
                provider_payload,
                base_signal_map=seed_signal_map,
                definition_by_name=definition_by_name,
            )
            warnings = list(reduced_source_pack.get("warnings") or []) + provider_warnings
            signal_map, warnings = _apply_signal_overrides(
                signal_map,
                definition_by_name,
                warnings,
                signal_overrides=signal_overrides,
            )
            rule_spec = build_rule_spec(
                script_source=script_source,
                script_type=script_type,
                parameters=parameters,
                indicators=indicators,
                definitions_payload=definitions_payload,
                signal_map=signal_map,
                ignored_sections=ignored_sections,
                warnings=warnings,
                translation_mode=str(translation_meta.get("mode") or "AI_TRANSLATED"),
            )
            validate_import_rule_spec(rule_spec, reduced_source_pack)
            return translation_meta, rule_spec
        except Exception as exc:
            provider_error = f"Provider translation rejected: {exc}"

    fallback_translation, fallback_rule_spec = build_deterministic_draft_translation(
        reduced_source_pack,
        script_source=script_source,
        script_type=script_type,
        signal_overrides=signal_overrides,
    )
    if provider_error:
        fallback_translation["attempted_provider"] = "OLLAMA"
        fallback_translation["fallback_reason"] = provider_error
        if provider_error not in fallback_rule_spec["warnings"]:
            fallback_rule_spec["warnings"].insert(0, f"AI translation provider fallback: {provider_error}")
    return fallback_translation, fallback_rule_spec
