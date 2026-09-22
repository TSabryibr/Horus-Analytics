import time
import json
from types import SimpleNamespace
from typing import Any, Callable, List, Optional

from core.settings import settings
from utils.currency_fetcher import get_parallel_usd_egp_rate, get_historical_usd_egp_rate
from fastapi import HTTPException

from core import TelegramBot_Alerts, TimeUtils
from core.enforcement_calibration import summarize_calibration_diagnostics
from core import subscriptions
from database import Client, Portfolio, SignalDelivery, SignalRecommendation, SignalRun, ClientEntitlement
from utils.logger import setup_logger
logger = setup_logger("horus.signals.publishing")

from .boundary import (
    error_context,
    get_publish_window_status,
    noop_context,
    validated_publish_channel,
    window_context,
)
from core.signals.guard import get_guard_state, guard_context, serialize_run


def serialize_delivery(delivery: SignalDelivery):
    return {
        "id": delivery.id,
        "run_id": delivery.run.id if delivery.run else None,
        "portfolio_id": delivery.portfolio.id if delivery.portfolio else None,
        "portfolio_name": delivery.portfolio.name if delivery.portfolio else None,
        "channel": delivery.channel,
        "service_tier": delivery.service_tier,
        "destination_type": delivery.destination_type,
        "destination_id": delivery.destination_id,
        "destination_name": delivery.destination_name,
        "destination_chat_id": delivery.destination_chat_id,
        "status": delivery.status,
        "attempts": delivery.attempts,
        "provider_message_id": delivery.provider_message_id,
        "last_error": delivery.last_error,
        "sent_at": delivery.sent_at.isoformat() if delivery.sent_at else None,
        "latency_ms": getattr(delivery, "latency_ms", None),
    }


def increment_reason_count(bucket: dict, key: str) -> None:
    bucket[key] = bucket.get(key, 0) + 1


def _destination_id_for_portfolio(portfolio: Optional[Portfolio]) -> Optional[str]:
    return str(portfolio.id) if portfolio else None


def _build_publish_destinations(
    *,
    portfolios: list[Portfolio],
    service_tier: str,
    include_subscribers: bool = True,
    include_main_channel: bool = True,
) -> list[dict[str, Any]]:
    destinations: list[dict[str, Any]] = []
    seen: set[tuple[str, Optional[str]]] = set()

    for portfolio in portfolios:
        destination_id = _destination_id_for_portfolio(portfolio)
        key = ("PORTFOLIO", destination_id)
        if key in seen:
            continue
        seen.add(key)
        chat_id = None
        try:
            entitlement = (
                ClientEntitlement.select(ClientEntitlement, Client)
                .join(Client)
                .where(
                    (ClientEntitlement.portfolio == portfolio)
                    & (ClientEntitlement.is_active == True)
                    & (Client.is_active == True)
                )
                .first()
            )
            if entitlement and entitlement.client and entitlement.client.telegram_chat_id:
                chat_id = str(entitlement.client.telegram_chat_id).strip()
        except Exception:
            pass

        destinations.append(
            {
                "portfolio": portfolio,
                "service_tier": service_tier,
                "destination_type": "PORTFOLIO",
                "destination_id": destination_id,
                "destination_name": portfolio.name,
                "destination_chat_id": chat_id,
                "delivery": None,
            }
        )

    if include_subscribers:
        for client in Client.select().where((Client.is_active == True) & (Client.delivery_paused == False)).order_by(Client.name.asc()):
            try:
                if not subscriptions.subscriber_entitled_to_service(client.subscription_tier, service_tier):
                    continue
            except HTTPException:
                continue
            chat_id = str(client.telegram_chat_id or "").strip()
            if not chat_id:
                continue
            destination_id = str(client.id)
            key = ("SUBSCRIBER", destination_id)
            if key in seen:
                continue
            seen.add(key)
            destinations.append(
                {
                    "portfolio": None,
                    "service_tier": service_tier,
                    "destination_type": "SUBSCRIBER",
                    "destination_id": destination_id,
                    "destination_name": client.name,
                    "destination_chat_id": chat_id,
                    "delivery": None,
                }
            )

    channel_level = getattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "none")
    if include_main_channel and subscriptions.main_channel_includes_service(channel_level, service_tier):
        chat_id = str(getattr(settings, "CHAT_ID", "") or "").strip()
        if chat_id:
            key = ("MAIN_CHANNEL", "main")
            if key not in seen:
                seen.add(key)
                destinations.append(
                    {
                        "portfolio": None,
                        "service_tier": service_tier,
                        "destination_type": "MAIN_CHANNEL",
                        "destination_id": "main",
                        "destination_name": "Main Telegram Channel",
                        "destination_chat_id": chat_id,
                        "delivery": None,
                    }
                )

    return destinations


def _destination_from_delivery(delivery: SignalDelivery, *, fallback_service_tier: str) -> dict[str, Any]:
    portfolio = delivery.portfolio
    destination_type = str(delivery.destination_type or ("PORTFOLIO" if portfolio else "LEGACY")).upper().strip()
    destination_id = delivery.destination_id or _destination_id_for_portfolio(portfolio)
    destination_name = delivery.destination_name or (portfolio.name if portfolio else destination_type.title())
    return {
        "portfolio": portfolio,
        "service_tier": delivery.service_tier or fallback_service_tier,
        "destination_type": destination_type,
        "destination_id": destination_id,
        "destination_name": destination_name,
        "destination_chat_id": delivery.destination_chat_id,
        "delivery": delivery,
    }


def _find_existing_delivery_for_destination(
    run: SignalRun,
    channel: str,
    destination: dict[str, Any],
) -> Optional[SignalDelivery]:
    delivery = SignalDelivery.get_or_none(
        (SignalDelivery.run == run)
        & (SignalDelivery.channel == channel)
        & (SignalDelivery.destination_type == destination["destination_type"])
        & (SignalDelivery.destination_id == destination["destination_id"])
    )
    if delivery is not None:
        return delivery

    portfolio = destination.get("portfolio")
    if destination.get("destination_type") != "PORTFOLIO" or portfolio is None:
        return None

    return SignalDelivery.get_or_none(
        (SignalDelivery.run == run)
        & (SignalDelivery.channel == channel)
        & (SignalDelivery.portfolio == portfolio)
        & ((SignalDelivery.destination_id.is_null(True)) | (SignalDelivery.destination_id == ""))
    )


UNRECOVERABLE_TELEGRAM_PATTERNS = (
    "chat not found",
    "bot was blocked by the user",
    "user is deactivated",
    "bot can't initiate conversation",
    "chat was deleted",
    "group chat was deactivated",
)


def _is_unrecoverable_telegram_error(resp: Optional[dict]) -> bool:
    if not resp or not isinstance(resp, dict):
        return False
    if resp.get("ok"):
        return False
    error_code = resp.get("error_code")
    desc = str(resp.get("description", "")).lower()
    if error_code in (400, 401, 403):
        return True
    return any(pat in desc for pat in UNRECOVERABLE_TELEGRAM_PATTERNS)


def _send_delivery_message(
    send_message_fn: Callable[..., dict],
    message: str,
    *,
    destination_chat_id: Optional[str],
) -> dict:
    if destination_chat_id:
        return send_message_fn(message, chat_id=destination_chat_id)
    return send_message_fn(message)



def build_delivery_message(
    run: SignalRun,
    recommendations: List[SignalRecommendation],
    portfolio: Optional[Portfolio],
    *,
    recommendation_target2_fn: Callable[[SignalRecommendation], float] = lambda rec: float(rec.target_price or 0),
    watch_only_recommendations: Optional[List[SignalRecommendation]] = None,
    language: Optional[str] = None,
    **kwargs,
) -> str:
    resolved_lang = str(
        language
        or getattr(settings, "TELEGRAM_REPORT_LANGUAGE", "EN")
        or "EN"
    ).strip().upper()
    is_ar = resolved_lang == "AR"
    precision = int(getattr(settings, "TELEGRAM_PRICE_PRECISION", 2))
    currency = "ج.م" if is_ar else "LE"

    workspace_name = portfolio.name if portfolio else "Premium Channel"
    if is_ar:
        header = (
            f"🚀 *إشارات حورس الذكية*\n"
            f"التاريخ: `{run.run_date.strftime('%Y-%m-%d')}` | Workspace: {workspace_name}\n"
            "═════════════════════════\n"
        )
    else:
        header = (
            f"🚀 *HORUS INTELLIGENCE | TRADING SIGNALS*\n"
            f"Date: `{run.run_date.strftime('%Y-%m-%d')}` | Workspace: {workspace_name}\n"
            "═════════════════════════\n"
        )

    lines = []
    for rec in recommendations[:10]:
        tp2 = recommendation_target2_fn(rec)
        vol_x = 0.0
        try:
            rat_dict = json.loads(rec.rationale_json) if rec.rationale_json else {}
            vol_x = float(rat_dict.get("volume_x") or 0)
        except Exception:
            pass

        turnover = 0.0
        try:
            from core.DataManager import DataManager
            df_stock = DataManager.get_stock_data(rec.ticker, include_live=False)
            if df_stock is not None and not df_stock.empty:
                turnover = float(df_stock['Avg_Turnover'].iloc[-1] if 'Avg_Turnover' in df_stock.columns else 0)
        except Exception:
            pass

        badge_list = []
        if vol_x > 3.0:
            badge_list.append("[⚠️ HIGH SLIPPAGE]" if not is_ar else "[⚠️ انزلاق مرتفع]")
        if turnover > 0 and turnover < 6000000.0:
            badge_list.append("[⚠️ LOW LIQUIDITY]" if not is_ar else "[⚠️ سيولة منخفضة]")
        badge_str = " " + " ".join(badge_list) if badge_list else ""

        entry = float(rec.entry_price or 0.0)
        sl = float(rec.stop_loss or 0.0)
        tp1 = float(rec.target_price or 0.0)
        tp2_val = float(tp2 or 0.0)

        tp1_pct = ((tp1 - entry) / entry * 100) if entry > 0 and tp1 > 0 else 0.0
        tp2_pct = ((tp2_val - entry) / entry * 100) if entry > 0 and tp2_val > 0 else 0.0
        sl_pct = ((entry - sl) / entry * 100) if entry > 0 and sl > 0 else 0.0

        risk = entry - sl
        reward = tp1 - entry
        rr_ratio = (reward / risk) if risk > 0 and reward > 0 else 0.0
        rr_str = f"1 : {rr_ratio:.1f}" if rr_ratio > 0 else "N/A"

        if is_ar:
            side_ar = "شراء" if rec.side == "BUY" else ("بيع" if rec.side == "SELL" else rec.side)
            rec_line = (
                f"🔹 *{rec.ticker}* ({side_ar}){badge_str}\n"
                f"   • سعر الدخول: *{entry:.{precision}f} {currency}*\n"
                f"   • الهدف الأول: *{tp1:.{precision}f} {currency}* (+{tp1_pct:.1f}%)\n"
            )
            if tp2_val > 0:
                rec_line += f"   • الهدف الثاني: *{tp2_val:.{precision}f} {currency}* (+{tp2_pct:.1f}%)\n"
            rec_line += (
                f"   • وقف الخسارة: *{sl:.{precision}f} {currency}* (-{sl_pct:.1f}%)\n"
                f"   • العائد للمخاطرة: *{rr_str}* | التقييم: *{rec.score}/10* ({rec.confidence:.0f}%)"
            )
            lines.append(rec_line)
        else:
            rec_line = (
                f"🔹 *{rec.ticker}* ({rec.side}){badge_str}\n"
                f"   • Entry: *{entry:.{precision}f} {currency}*\n"
                f"   • TP1: *{tp1:.{precision}f} {currency}* (+{tp1_pct:.1f}%)\n"
            )
            if tp2_val > 0:
                rec_line += f"   • TP2: *{tp2_val:.{precision}f} {currency}* (+{tp2_pct:.1f}%)\n"
            rec_line += (
                f"   • Stop Loss: *{sl:.{precision}f} {currency}* (-{sl_pct:.1f}%)\n"
                f"   • Risk/Reward: *{rr_str}* | Score: *{rec.score}/10* ({rec.confidence:.0f}%)"
            )
            lines.append(rec_line)

    watch_only_recommendations = watch_only_recommendations or []
    if watch_only_recommendations:
        watch_header = "قائمة المراقبة" if is_ar else "WATCHLIST"
        watch_lines = [f"👁️ *{watch_header}*"]
        for rec in watch_only_recommendations[:10]:
            enforcement = _recommendation_enforcement_payload(rec)
            reason = str(enforcement.get("enforcement_reason") or "watch_only").replace("_", " ")
            watch_lines.append(f"• {rec.ticker} ({reason})")
        lines.append("\n".join(watch_lines))

    if not lines:
        lines.append(
            "لا توجد توصيات نشطة لهذا التشغيل. No active recommendations for this run."
            if is_ar
            else "No active recommendations for this run."
        )

    rate = get_parallel_usd_egp_rate()
    footer = f"\n\n💵 Parallel FX: {rate:.2f} EGP/USD"
    try:
        import datetime
        prev_rate = get_historical_usd_egp_rate(TimeUtils.now() - datetime.timedelta(days=1))
        rate_change = abs(rate - prev_rate) / prev_rate * 100
        if rate_change > 2.0:
            footer += f"\n⚠️ [CURRENCY_VOLATILITY] Parallel FX shifted {rate_change:.2f}% in 24h ({prev_rate:.2f} -> {rate:.2f})"
    except Exception:
        pass

    deval_warning = ""
    if portfolio:
        try:
            from core.analyzers.TreasuryLedger import get_hoard_status
            hoard = get_hoard_status(portfolio_id=portfolio.id)
            deval_positions = []
            for pos in hoard.get("positions", []):
                if pos.get("risk_status") == "DEVALUATION_LOSS":
                    deval_positions.append(pos.get("ticker"))
            if deval_positions:
                deval_warning = f"\n⚠️ [DEVALUATION_LOSS] The following positions show EGP gains but USD losses: {', '.join(deval_positions)}"
        except Exception:
            pass

    if deval_warning:
        footer += deval_warning

    if is_ar:
        disclaimer = (
            "\n\n⚠️ *إخلاء مسؤولية تعليمي:* تم إنشاء هذه البيانات لأغراض البحث والتعليم فقط. "
            "لا تعد استشارة مالية أو دعوة للاستثمار."
        )
    else:
        disclaimer = (
            "\n\n⚠️ [EDUCATIONAL DISCLAIMER] Generated for educational and research purposes only. "
            "Not financial advice. Under Egyptian law, trade signals are not licensed for investment execution."
        )
    return header + "\n\n".join(lines) + footer + disclaimer


def publish_signal_run_logic(
    req,
    *,
    validated_publish_channel_fn: Callable[[str], str] = validated_publish_channel,
    error_context_fn: Callable[..., dict] = error_context,
    get_guard_state_fn= get_guard_state,
    guard_context_fn: Callable[..., dict] = guard_context,
    emit_audit_event_fn: Callable[..., Any] = lambda **kwargs: None,
    get_publish_window_status_fn: Callable[..., dict] = get_publish_window_status,
    window_context_fn: Callable[[dict], dict] = window_context,
    build_delivery_message_fn: Callable[..., str] = build_delivery_message,
    now_fn: Callable[[], Any] = TimeUtils.now,
    is_telegram_configured_fn: Optional[Callable[[], bool]] = None,
    send_message_fn: Optional[Callable[[str], dict]] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    increment_reason_count_fn: Callable[[dict, str], None] = increment_reason_count,
    serialize_run_fn: Callable[[SignalRun], dict] = serialize_run,
    recommendation_filter_fn: Optional[Callable[[SignalRecommendation], bool]] = None,
    create_lifecycle_records_fn: Optional[Callable[..., Any]] = None,
):
    channel = validated_publish_channel_fn(req.channel)
    try:
        service_tier = subscriptions.normalize_tier(getattr(req, "service_tier", subscriptions.SIGNALS_ONLY))
    except HTTPException as exc:
        raise exc
    custom_telegram_configured_fn = is_telegram_configured_fn is not None
    is_telegram_configured_fn = is_telegram_configured_fn or (
        lambda: bool(settings.TELEGRAM_TOKEN)
    )
    send_message_fn = send_message_fn or TelegramBot_Alerts.send_message

    if req.run_id is not None:
        run = SignalRun.get_or_none(SignalRun.id == req.run_id)
    else:
        run = (
            SignalRun.select()
            .where(SignalRun.status == "COMPLETED")
            .order_by(SignalRun.run_date.desc(), SignalRun.completed_at.desc())
            .first()
        )
    if not run:
        raise HTTPException(
            status_code=404,
            detail=error_context_fn(
                "not_found",
                "signal_run_not_found",
                "Signal run not found",
                run_id=req.run_id,
                channel=channel,
            ),
        )
    if run.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=error_context_fn(
                "state",
                "run_not_completed",
                "Only COMPLETED runs can be published",
                run_id=run.id,
                run_status=run.status,
                channel=channel,
            ),
        )

    guard = get_guard_state_fn()
    if guard.is_blocked and not req.ignore_guard:
        current_guard_context = guard_context_fn(guard)
        emit_audit_event_fn(
            event_type="PUBLISH_BLOCKED_GUARD",
            severity="WARN",
            actor_type="SYSTEM",
            run=run,
            entity_type="SIGNAL_PUBLISH",
            entity_id=str(run.id),
            message="Publish blocked by guard",
            details=current_guard_context,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Publish blocked by guard: {guard.reason or 'No reason provided'}",
                **current_guard_context,
            },
        )

    if req.enforce_window:
        window = get_publish_window_status_fn(run.run_date)
        if not window["ok"]:
            current_window_context = window_context_fn(window)
            emit_audit_event_fn(
                event_type="PUBLISH_BLOCKED_WINDOW",
                severity="WARN",
                actor_type="SYSTEM",
                run=run,
                entity_type="SIGNAL_PUBLISH",
                entity_id=str(run.id),
                message="Publish blocked by time window",
                details=current_window_context,
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"Publish blocked by window: {window['reason']}",
                    **current_window_context,
                },
            )

    recs = list(
        SignalRecommendation.select()
        .where(SignalRecommendation.run == run)
        .order_by(SignalRecommendation.score.desc())
    )
    if recommendation_filter_fn is not None:
        recs = [rec for rec in recs if recommendation_filter_fn(rec)]
    actionable_recs, watch_only_recs, blocked_recs, enforcement_summary = _partition_recommendations_for_publish(recs)

    include_portfolios = bool(getattr(req, "include_portfolios", True))
    include_subscribers = bool(getattr(req, "include_subscribers", True))
    include_main_channel = bool(getattr(req, "include_main_channel", True))
    requested_portfolio_ids = getattr(req, "portfolio_ids", None)

    if include_portfolios and requested_portfolio_ids:
        portfolios = list(
            Portfolio.select().where(
                (Portfolio.id.in_(requested_portfolio_ids)) & (Portfolio.type == "USER")
            )
        )
    elif include_portfolios:
        portfolios = list(Portfolio.select().where(Portfolio.type == "USER"))
    else:
        portfolios = []

    retry_delivery_ids = [
        int(item)
        for item in (getattr(req, "retry_delivery_ids", None) or [])
        if str(item or "").strip().isdigit()
    ]
    if retry_delivery_ids:
        retry_deliveries = list(
            SignalDelivery.select().where(
                (SignalDelivery.run == run)
                & (SignalDelivery.channel == channel)
                & (SignalDelivery.id.in_(retry_delivery_ids))
            )
        )
        destinations = [
            _destination_from_delivery(delivery, fallback_service_tier=service_tier)
            for delivery in retry_deliveries
        ]
    else:
        destinations = _build_publish_destinations(
            portfolios=portfolios,
            service_tier=service_tier,
            include_subscribers=include_subscribers,
            include_main_channel=include_main_channel,
        )

    if not destinations:
        raise HTTPException(
            status_code=404,
            detail=error_context_fn(
                "eligibility",
                "no_eligible_signal_destinations",
                "No eligible signal destinations to publish",
                requested_portfolio_ids=requested_portfolio_ids,
                include_portfolios=include_portfolios,
                include_subscribers=include_subscribers,
                include_main_channel=include_main_channel,
                channel=channel,
                service_tier=service_tier,
            ),
        )

    calibration_rows = _build_calibration_rows(recs)
    calibration_summary = summarize_calibration_diagnostics(calibration_rows)

    summary = {
        "sent": 0,
        "failed": 0,
        "dry_run": 0,
        "skipped": 0,
        "skip_reasons": {
            "no_recommendations": 0,
            "telegram_not_configured": 0,
        },
        "failure_reasons": {},
        "enforcement": enforcement_summary,
        "calibration": calibration_summary,
        "promotion": _build_promotion_summary(calibration_summary),
    }

    for rec in blocked_recs:
        payload = _recommendation_enforcement_payload(rec)
        emit_audit_event_fn(
            event_type="PUBLISH_RECOMMENDATION_BLOCKED",
            severity="WARN",
            actor_type="SYSTEM",
            run=run,
            entity_type="SIGNAL_RECOMMENDATION",
            entity_id=rec.ticker,
            message="Recommendation excluded from actionable publishing by enforcement",
            details={
                "ticker": rec.ticker,
                "enforcement_state": payload.get("enforcement_state"),
                "enforcement_reason": payload.get("enforcement_reason"),
                "enforcement_profile": payload.get("enforcement_profile"),
            },
        )
    for rec in watch_only_recs:
        payload = _recommendation_enforcement_payload(rec)
        emit_audit_event_fn(
            event_type="PUBLISH_RECOMMENDATION_WATCH_ONLY",
            severity="INFO",
            actor_type="SYSTEM",
            run=run,
            entity_type="SIGNAL_RECOMMENDATION",
            entity_id=rec.ticker,
            message="Recommendation downgraded to watch-only in publishing",
            details={
                "ticker": rec.ticker,
                "enforcement_state": payload.get("enforcement_state"),
                "enforcement_reason": payload.get("enforcement_reason"),
                "enforcement_profile": payload.get("enforcement_profile"),
            },
        )

    for destination in destinations:
        portfolio = destination["portfolio"]
        delivery = destination.get("delivery")
        if delivery is None:
            delivery = _find_existing_delivery_for_destination(run, channel, destination)
        if not delivery:
            delivery = SignalDelivery.create(
                run=run,
                portfolio=portfolio,
                channel=channel,
                service_tier=destination["service_tier"],
                destination_type=destination["destination_type"],
                destination_id=destination["destination_id"],
                destination_name=destination["destination_name"],
                destination_chat_id=destination["destination_chat_id"],
                status="PENDING",
            )
        else:
            delivery.portfolio = portfolio
            delivery.service_tier = destination["service_tier"]
            delivery.destination_type = destination["destination_type"]
            delivery.destination_id = destination["destination_id"]
            delivery.destination_name = destination["destination_name"]
            delivery.destination_chat_id = destination["destination_chat_id"]
        delivery.last_error = None

        if not recs:
            delivery.status = "SKIPPED"
            delivery.last_error = "No recommendations available for this run"
            delivery.sent_at = now_fn()
            summary["skipped"] += 1
            summary["skip_reasons"]["no_recommendations"] += 1
            delivery.save()
            continue

        if req.dry_run:
            delivery.status = "DRY_RUN"
            delivery.sent_at = now_fn()
            summary["dry_run"] += 1
            delivery.save()
            continue

        if custom_telegram_configured_fn:
            telegram_ready = bool(is_telegram_configured_fn())
        else:
            telegram_ready = bool(is_telegram_configured_fn()) and bool(
                destination["destination_chat_id"]
                or str(getattr(settings, "CHAT_ID", "") or "").strip()
            )
        if not telegram_ready:
            delivery.status = "SKIPPED"
            delivery.last_error = "Telegram not configured"
            delivery.sent_at = now_fn()
            summary["skipped"] += 1
            summary["skip_reasons"]["telegram_not_configured"] += 1
            delivery.save()
            continue

        message = build_delivery_message_fn(
            run,
            actionable_recs,
            portfolio,
            watch_only_recommendations=watch_only_recs,
        )
        tg_resp = None
        send_start = time.perf_counter()
        for attempt in range(req.max_retries + 1):
            delivery.attempts += 1
            tg_resp = _send_delivery_message(
                send_message_fn,
                message,
                destination_chat_id=destination["destination_chat_id"],
            )
            if tg_resp and tg_resp.get("ok"):
                break
            if _is_unrecoverable_telegram_error(tg_resp):
                logger.warning(
                    f"[Publisher] Unrecoverable Telegram error for destination "
                    f"'{destination.get('destination_name')}' (chat_id={destination.get('destination_chat_id')}): "
                    f"{(tg_resp or {}).get('description', 'Unknown')}. Aborting retries immediately."
                )
                break
            if attempt < req.max_retries and req.backoff_ms > 0:
                sleep_fn((req.backoff_ms / 1000.0) * (2 ** attempt))

        delivery.latency_ms = round((time.perf_counter() - send_start) * 1000, 2)

        if tg_resp and tg_resp.get("ok"):
            delivery.status = "SENT"
            message_id = tg_resp.get("result", {}).get("message_id")
            delivery.provider_message_id = str(message_id) if message_id is not None else None
            delivery.sent_at = now_fn()
            summary["sent"] += 1
            if destination["destination_type"] == "SUBSCRIBER" and destination["destination_id"]:
                try:
                    client = Client.get_or_none(Client.id == int(destination["destination_id"]))
                    if client and client.delivery_fail_count > 0:
                        client.delivery_fail_count = 0
                        client.save()
                except Exception as exc:
                    logger.debug(f"[Publisher] Failed to reset client delivery fail count: {exc}")
        else:
            delivery.status = "FAILED"
            delivery.last_error = (tg_resp or {}).get("description", "Unknown delivery error")
            summary["failed"] += 1
            increment_reason_count_fn(summary["failure_reasons"], delivery.last_error)
            if destination["destination_type"] == "SUBSCRIBER" and destination["destination_id"]:
                try:
                    client = Client.get_or_none(Client.id == int(destination["destination_id"]))
                    if client:
                        error_str = str(delivery.last_error).lower()
                        if _is_unrecoverable_telegram_error(tg_resp) or any(pat in error_str for pat in UNRECOVERABLE_TELEGRAM_PATTERNS):
                            client.delivery_fail_count += 1
                            if client.delivery_fail_count >= 3:
                                client.delivery_paused = True
                                logger.warning(
                                    f"[Publisher] Client {client.name} (ID: {client.id}) delivery automatically paused "
                                    f"due to {client.delivery_fail_count} consecutive delivery failures: {delivery.last_error}"
                                )
                            client.save()
                except Exception as exc:
                    logger.warning(f"[Publisher] Failed to update client delivery fail count: {exc}")
        delivery.save()
        if delivery.status == "SENT" and create_lifecycle_records_fn is not None:
            try:
                create_lifecycle_records_fn(
                    run=run,
                    delivery=delivery,
                    portfolio=portfolio,
                    recommendations=actionable_recs,
                    operating_mode=getattr(req, "operating_mode", "MANUAL"),
                    published_at=delivery.sent_at or now_fn(),
                )
            except Exception as exc:
                increment_reason_count_fn(summary["failure_reasons"], "lifecycle_create_failed")
                emit_audit_event_fn(
                    event_type="PUBLISH_LIFECYCLE_CREATE_FAILED",
                    severity="ERROR",
                    actor_type="SYSTEM",
                    run=run,
                    portfolio=portfolio,
                    entity_type="SIGNAL_DELIVERY",
                    entity_id=str(delivery.id),
                    message="Published signal lifecycle creation failed after Telegram send",
                    details={
                        "delivery_id": delivery.id,
                        "portfolio_id": portfolio.id if portfolio else None,
                        "error": str(exc),
                    },
                )

    run.published_count = SignalDelivery.select().where(
        (SignalDelivery.run == run) & (SignalDelivery.status == "SENT")
    ).count()
    run.save()
    emit_audit_event_fn(
        event_type="PUBLISH_COMPLETED",
        severity="INFO" if summary["failed"] == 0 else "WARN",
        actor_type="SYSTEM",
        run=run,
        entity_type="SIGNAL_PUBLISH",
        entity_id=str(run.id),
        message="Signal publish execution completed",
        details={
            "channel": channel,
            "service_tier": service_tier,
            "dry_run": req.dry_run,
            "portfolio_ids": requested_portfolio_ids,
            "include_portfolios": include_portfolios,
            "include_subscribers": include_subscribers,
            "include_main_channel": include_main_channel,
            "destination_count": len(destinations),
            "summary": summary,
            "published_count": run.published_count,
        },
    )
    return {
        "status": "completed",
        "run_id": run.id,
        "channel": channel,
        "summary": summary,
        "run": serialize_run_fn(run),
    }


def _recommendation_enforcement_payload(rec: SignalRecommendation) -> dict[str, Any]:
    if not rec.rationale_json:
        return {}
    try:
        payload = json.loads(rec.rationale_json)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _partition_recommendations_for_publish(
    recommendations: List[SignalRecommendation],
) -> tuple[list[SignalRecommendation], list[SignalRecommendation], list[SignalRecommendation], dict[str, Any]]:
    actionable: list[SignalRecommendation] = []
    watch_only: list[SignalRecommendation] = []
    blocked: list[SignalRecommendation] = []
    counts_by_reason: dict[str, int] = {}

    for rec in recommendations:
        payload = _recommendation_enforcement_payload(rec)
        state = str(payload.get("enforcement_state") or "ALLOW").strip().upper()
        reason = str(payload.get("enforcement_reason") or "").strip()

        if state == "BLOCK_EXECUTION":
            blocked.append(rec)
            if reason:
                increment_reason_count(counts_by_reason, reason)
        elif state == "WATCH_ONLY":
            watch_only.append(rec)
            if reason:
                increment_reason_count(counts_by_reason, reason)
        else:
            actionable.append(rec)

    summary = {
        "actionable_count": len(actionable),
        "watch_only_count": len(watch_only),
        "blocked_count": len(blocked),
        "counts_by_reason": counts_by_reason,
        "watch_only_tickers": [rec.ticker for rec in watch_only],
        "blocked_tickers": [rec.ticker for rec in blocked],
    }
    return actionable, watch_only, blocked, summary


def _build_calibration_rows(
    recommendations: List[SignalRecommendation],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rec in recommendations:
        payload = _recommendation_enforcement_payload(rec)
        rows.append(
            {
                "ticker": rec.ticker,
                "trap_risk_band": payload.get("trap_risk_band"),
                "whale_alignment": payload.get("whale_alignment"),
                "route_profile": payload.get("route_profile") or payload.get("enforcement_profile"),
                "market_segment": payload.get("market_segment"),
                "enforcement_state": payload.get("enforcement_state"),
                "enforcement_reason": payload.get("enforcement_reason"),
                "enforcement_profile": payload.get("enforcement_profile"),
            }
        )
    return rows


def _build_promotion_summary(
    calibration_summary: dict[str, Any],
) -> dict[str, Any]:
    market_segments = dict(calibration_summary.get("market_segments") or {})
    promotion_segments: dict[str, Any] = {}

    for segment, segment_summary in market_segments.items():
        promotion_segments[str(segment)] = {
            "previous_active_profile": segment_summary.get("previous_active_profile"),
            "new_active_profile": segment_summary.get("new_active_profile"),
            "rollback_profile": segment_summary.get("rollback_profile"),
            "promotion_rationale": segment_summary.get("promotion_rationale"),
            "promotion_evidence": segment_summary.get("promotion_evidence"),
        }

    return {
        "market_segments": promotion_segments,
    }


def retry_failed_deliveries_logic(
    req,
    *,
    validated_publish_channel_fn: Callable[[str], str] = validated_publish_channel,
    error_context_fn: Callable[..., dict] = error_context,
    noop_context_fn: Callable[..., dict] = noop_context,
    emit_audit_event_fn: Callable[..., Any] = lambda **kwargs: None,
    publish_signal_run_logic_fn: Callable[[Any], dict] = publish_signal_run_logic,
    retry_request_builder_fn: Callable[..., Any] = lambda **kwargs: SimpleNamespace(**kwargs),
):
    channel = validated_publish_channel_fn(req.channel)
    run = SignalRun.get_or_none(SignalRun.id == req.run_id)
    if not run:
        raise HTTPException(
            status_code=404,
            detail=error_context_fn(
                "not_found",
                "signal_run_not_found",
                "Signal run not found",
                run_id=req.run_id,
                channel=channel,
            ),
        )

    failed = list(
        SignalDelivery.select().where(
            (SignalDelivery.run == run)
            & (SignalDelivery.channel == channel)
            & (SignalDelivery.status == "FAILED")
        )
    )
    if not failed:
        emit_audit_event_fn(
            event_type="PUBLISH_RETRY_NOOP",
            actor_type="SYSTEM",
            run=run,
            entity_type="SIGNAL_PUBLISH",
            entity_id=str(run.id),
            message="Retry requested but no failed deliveries found",
            details={
                "channel": channel,
                "noop_type": "retry",
                "noop_reason": "no_failed_deliveries",
            },
        )
        return {
            "status": "noop",
            "run_id": req.run_id,
            "channel": channel,
            **noop_context_fn("retry", "no_failed_deliveries", "No failed deliveries to retry."),
        }

    retry_delivery_ids = [delivery.id for delivery in failed]
    retry_service_tier = str(failed[0].service_tier or subscriptions.SIGNALS_ONLY).upper().strip()
    retry_req = retry_request_builder_fn(
        run_id=req.run_id,
        portfolio_ids=[],
        channel=req.channel,
        service_tier=retry_service_tier,
        retry_delivery_ids=retry_delivery_ids,
        dry_run=False,
        max_retries=req.max_retries,
        backoff_ms=req.backoff_ms,
        enforce_window=req.enforce_window,
    )
    result = publish_signal_run_logic_fn(retry_req)
    emit_audit_event_fn(
        event_type="PUBLISH_RETRY_EXECUTED",
        severity="INFO" if result.get("summary", {}).get("failed", 0) == 0 else "WARN",
        actor_type="SYSTEM",
        run=run,
        entity_type="SIGNAL_PUBLISH",
        entity_id=str(run.id),
        message="Retry execution completed",
        details={
            "channel": channel,
            "retry_delivery_ids": retry_delivery_ids,
            "result_summary": result.get("summary"),
        },
    )
    return result
