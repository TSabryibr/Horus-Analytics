import datetime
import json
import threading
from typing import Any, Callable, Optional

from core import TelegramBot_Alerts, TimeUtils
from database import PublishedSignalFollowUp, PublishedSignalLifecycle

_FOLLOWUP_PROCESS_LOCK = threading.Lock()


_FOLLOWUP_TRIGGER_CONFIG = {
    "TP1_HIT": {"message_type": "UPDATE", "headline": "HORUS UPDATE"},
    "TP2_HIT": {"message_type": "CLOSE", "headline": "HORUS CLOSE"},
    "STOP_LOSS_HIT": {"message_type": "CLOSE", "headline": "HORUS CLOSE"},
    "EXPIRED": {"message_type": "UPDATE", "headline": "HORUS UPDATE"},
    "CANCELLED": {"message_type": "UPDATE", "headline": "HORUS UPDATE"},
}
_QUEUE_STATES = {"PENDING", "READY", "SENT", "FAILED", "SUPPRESSED"}


def _safe_price(value: Any) -> float:
    try:
        price = float(value)
        return price if price > 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def followup_message_type_for_state(state: str) -> Optional[str]:
    config = _FOLLOWUP_TRIGGER_CONFIG.get((state or "").upper().strip())
    return config.get("message_type") if config else None


def should_create_followup_for_state(state: str) -> bool:
    return (state or "").upper().strip() in _FOLLOWUP_TRIGGER_CONFIG


def initial_followup_queue_state(operating_mode: str) -> str:
    mode = (operating_mode or "MANUAL").upper().strip()
    if mode in {"AI_ASSIST", "AUTOPILOT"}:
        return "READY"
    return "PENDING"


def build_followup_draft_message(
    lifecycle: PublishedSignalLifecycle | Any,
    *,
    trigger_state: Optional[str] = None,
    language: Optional[str] = None,
) -> str:
    from core.settings import settings

    state = str(trigger_state or lifecycle.state or "").upper().strip()
    config = _FOLLOWUP_TRIGGER_CONFIG.get(state, {})
    headline = config.get("headline") or "HORUS UPDATE"
    side = str(lifecycle.side or "BUY").upper().strip()
    ticker = str(lifecycle.ticker or "").upper().strip()

    resolved_lang = str(
        language
        or getattr(settings, "TELEGRAM_REPORT_LANGUAGE", "EN")
        or "EN"
    ).strip().upper()
    is_ar = resolved_lang == "AR"
    precision = int(getattr(settings, "TELEGRAM_PRICE_PRECISION", 2))
    currency = "ج.م" if is_ar else "LE"

    if is_ar:
        side_ar = "شراء" if side == "BUY" else ("بيع" if side == "SELL" else side)
        if state == "TP1_HIT":
            sl_price = _safe_price(lifecycle.stop_loss_active)
            tp2_price = _safe_price(lifecycle.target_price_2)
            return (
                "🎯 *تحديث حورس | تحقق الهدف الأول*\n"
                "HORUS UPDATE\n"
                f"🔹 السهم: *{ticker}* ({side_ar})\n"
                "• الحالة: *تم تحقيق الهدف الأول بنجاح*\n"
                f"• الإجراء: نقل وقف الخسارة إلى نقطة التعادل عند *{sl_price:.{precision}f} {currency}*\n"
                f"• الهدف الثاني: ما زال نشطاً عند *{tp2_price:.{precision}f} {currency}*\n"
                "🛡️ رأس المال محمي بالكامل."
            )
        if state == "TP2_HIT":
            close_p = _safe_price(lifecycle.close_price or lifecycle.target_price_2)
            return (
                "🏁 *إغلاق حورس | تحقق الهدف النهائي*\n"
                "HORUS CLOSE\n"
                f"🔹 السهم: *{ticker}* ({side_ar})\n"
                f"• الحالة: *تم تحقيق الهدف النهائي عند {close_p:.{precision}f} {currency}*\n"
                "• الإجراء: تم إغلاق المركز بالكامل وجني الأرباح.\n"
                "✨ صفقة ناجحة ومكتملة."
            )
        if state == "STOP_LOSS_HIT":
            reason_ar = "وقف التعادل" if str(lifecycle.close_reason or "").upper() == "BREAKEVEN_STOP_HIT" else "وقف الخسارة"
            exit_p = _safe_price(lifecycle.close_price or lifecycle.stop_loss_active or lifecycle.stop_loss_initial)
            return (
                "🛑 *إغلاق حورس | تفعيل الوقف*\n"
                "HORUS CLOSE\n"
                f"🔹 السهم: *{ticker}* ({side_ar})\n"
                f"• الحالة: *تم تنفيذ {reason_ar} عند {exit_p:.{precision}f} {currency}*\n"
                "• الإجراء: تم إغلاق المركز لحماية رأس المال.\n"
                "🛡️ الالتزام بالوقف أساس النجاح."
            )
        if state == "EXPIRED":
            return (
                "⏳ *تحديث حورس | انتهاء الصلاحية*\n"
                "HORUS UPDATE\n"
                f"🔹 السهم: *{ticker}* ({side_ar})\n"
                "• لم يتم تفعيل الدخول في الإطار الزمني المحدد.\n"
                "• الإشارة ملغاة ولا يوجد مركز نشط."
            )
        if state == "CANCELLED":
            if str(lifecycle.close_reason or "").upper().strip() == "PRE_CLOSE_NOT_CONFIRMED":
                return (
                    "⚠️ *تنبيه حورس | عدم تأكيد الإشارة*\n"
                    "HORUS CAUTION\n"
                    f"🔹 السهم: *{ticker}* ({side_ar})\n"
                    "• إشارة ما قبل الإغلاق لم تتأكد في المسح اليومي النهائي.\n"
                    "• تم إلغاء الإعداد ولا يوجد إجراء نشط."
                )
            return (
                "⚠️ *تنبيه حورس | إلغاء الإشارة*\n"
                "HORUS UPDATE\n"
                f"🔹 السهم: *{ticker}* ({side_ar})\n"
                "• تم إلغاء الإشارة لعدم استيفاء شروط التنفيذ."
            )
        return (
            f"{headline}\n"
            f"🔹 السهم: *{ticker}* ({side_ar})\n"
            "• تم تحديث حالة الإشارة."
        )

    # English Formatting
    if state == "TP1_HIT":
        sl_price = _safe_price(lifecycle.stop_loss_active)
        tp2_price = _safe_price(lifecycle.target_price_2)
        return (
            "🎯 *HORUS TRADE UPDATE | TARGET 1 HIT*\n"
            f"{headline}\n"
            f"Ticker: *{ticker}* | Direction: *{side}*\n"
            f"• Target 1 reached successfully.\n"
            f"• Move stop loss to breakeven at *{sl_price:.{precision}f} {currency}*.\n"
            f"• Keep Target 2 active at *{tp2_price:.{precision}f} {currency}*.\n"
            "🛡️ Capital protected. Let the runner trade."
        )
    if state == "TP2_HIT":
        close_p = _safe_price(lifecycle.close_price or lifecycle.target_price_2)
        return (
            "🏁 *HORUS TRADE CLOSE | TARGET 2 REACHED*\n"
            f"{headline}\n"
            f"Ticker: *{ticker}* | Direction: *{side}*\n"
            f"• Final target reached at *{close_p:.{precision}f} {currency}*.\n"
            "• Signal fully closed. No further action.\n"
            "✨ Trade complete."
        )
    if state == "STOP_LOSS_HIT":
        reason = "breakeven stop" if str(lifecycle.close_reason or "").upper() == "BREAKEVEN_STOP_HIT" else "stop loss"
        exit_p = _safe_price(lifecycle.close_price or lifecycle.stop_loss_active or lifecycle.stop_loss_initial)
        return (
            "🛑 *HORUS TRADE CLOSE | STOP LOSS HIT*\n"
            f"{headline}\n"
            f"Ticker: *{ticker}* | Direction: *{side}*\n"
            f"• {reason.title()} hit at *{exit_p:.{precision}f} {currency}*.\n"
            "• Signal fully closed. No further action.\n"
            "🛡️ Capital preservation is rule #1."
        )
    if state == "EXPIRED":
        return (
            "⏳ *HORUS TRADE UPDATE | SIGNAL EXPIRED*\n"
            f"{headline}\n"
            f"Ticker: *{ticker}* | Direction: *{side}*\n"
            "• Entry was not triggered in time.\n"
            "• Signal expired and is closed. No further action."
        )
    if state == "CANCELLED":
        if str(lifecycle.close_reason or "").upper().strip() == "PRE_CLOSE_NOT_CONFIRMED":
            return (
                "⚠️ *HORUS CAUTION | SIGNAL UNCONFIRMED*\n"
                "HORUS CAUTION\n"
                f"Ticker: *{ticker}* | Direction: *{side}*\n"
                "• Pre-close signal not confirmed.\n"
                "• Final daily scan did not confirm this setup.\n"
                "• No further action is active on this signal."
            )
        return (
            "⚠️ *HORUS UPDATE | SIGNAL CANCELLED*\n"
            f"{headline}\n"
            f"Ticker: *{ticker}* | Direction: *{side}*\n"
            "• Signal was cancelled.\n"
            "• No further action is active on this setup."
        )
    return (
        f"{headline}\n"
        f"Ticker: *{ticker}* | Direction: *{side}*\n"
        "• Signal status updated."
    )


def create_lifecycle_followup_job(
    lifecycle: PublishedSignalLifecycle,
    *,
    now_fn=TimeUtils.now,
) -> Optional[PublishedSignalFollowUp]:
    trigger_state = (lifecycle.state or "").upper().strip()
    if not should_create_followup_for_state(trigger_state):
        return None

    queue_state = initial_followup_queue_state(lifecycle.operating_mode)
    now_value = now_fn()
    delivery = lifecycle.delivery
    destination_type = getattr(delivery, "destination_type", None) or "PORTFOLIO"
    destination_id = getattr(delivery, "destination_id", None)
    destination_name = getattr(delivery, "destination_name", None)
    destination_chat_id = getattr(delivery, "destination_chat_id", None)
    service_tier = getattr(delivery, "service_tier", None) or "SIGNALS_ONLY"

    client_lang = None
    if destination_type == "SUBSCRIBER" and destination_id:
        try:
            from database import Client
            cl = Client.get_or_none(Client.id == int(destination_id))
            if cl and cl.report_language:
                client_lang = cl.report_language
        except Exception:
            pass

    followup = PublishedSignalFollowUp.get_or_none(
        (PublishedSignalFollowUp.lifecycle == lifecycle)
        & (PublishedSignalFollowUp.trigger_state == trigger_state)
        & (PublishedSignalFollowUp.destination_type == destination_type)
        & (PublishedSignalFollowUp.destination_id == destination_id)
    )
    if followup:
        return followup

    if destination_id:
        followup = PublishedSignalFollowUp.get_or_none(
            (PublishedSignalFollowUp.lifecycle == lifecycle)
            & (PublishedSignalFollowUp.trigger_state == trigger_state)
            & ((PublishedSignalFollowUp.destination_id.is_null(True)) | (PublishedSignalFollowUp.destination_id == ""))
        )
        if followup:
            followup.delivery = delivery
            followup.service_tier = service_tier
            followup.destination_type = destination_type
            followup.destination_id = destination_id
            followup.destination_name = destination_name
            followup.destination_chat_id = destination_chat_id
            followup.updated_at = now_value
            followup.save()
            return followup

    return PublishedSignalFollowUp.create(
        lifecycle=lifecycle,
        trigger_state=trigger_state,
        destination_type=destination_type,
        destination_id=destination_id,
        recommendation=lifecycle.recommendation,
        run=lifecycle.run,
        delivery=delivery,
        portfolio=lifecycle.portfolio,
        ticker=lifecycle.ticker,
        side=lifecycle.side,
        lane=lifecycle.lane,
        source_module=lifecycle.source_module,
        operating_mode=lifecycle.operating_mode,
        channel=lifecycle.channel,
        service_tier=service_tier,
        destination_name=destination_name,
        destination_chat_id=destination_chat_id,
        message_type=followup_message_type_for_state(trigger_state) or "UPDATE",
        queue_state=queue_state,
        draft_message=build_followup_draft_message(lifecycle, trigger_state=trigger_state, language=client_lang),
        ready_at=now_value if queue_state == "READY" else None,
        details_json=json.dumps(
            {
                "trigger_state": trigger_state,
                "lifecycle_state": trigger_state,
                "resolution_source": lifecycle.resolution_source,
            }
        ),
        updated_at=now_value,
    )


def suppress_signal_followup(
    followup: PublishedSignalFollowUp,
    *,
    reason: Optional[str] = None,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
) -> PublishedSignalFollowUp:
    now_value = now_fn()
    followup.queue_state = "SUPPRESSED"  # type: ignore[assignment]
    followup.suppressed_at = now_value  # type: ignore[assignment]
    followup.suppression_reason = reason or "suppressed_by_operator"  # type: ignore[assignment]
    followup.updated_at = now_value  # type: ignore[assignment]
    followup.save()
    return followup


def requeue_signal_followup(
    followup: PublishedSignalFollowUp,
    *,
    force_ready: bool = False,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
) -> PublishedSignalFollowUp:
    now_value = now_fn()
    queue_state = "READY" if force_ready else initial_followup_queue_state(str(getattr(followup, "operating_mode", "MANUAL")))
    followup.queue_state = queue_state  # type: ignore[assignment]
    client_lang = None
    if getattr(followup, "destination_type", None) == "SUBSCRIBER" and getattr(followup, "destination_id", None):
        try:
            from database import Client
            cl = Client.get_or_none(Client.id == int(followup.destination_id))
            if cl and cl.report_language:
                client_lang = cl.report_language
        except Exception:
            pass
    followup.draft_message = build_followup_draft_message(  # type: ignore[assignment]
        followup.lifecycle,  # type: ignore[arg-type]
        trigger_state=str(getattr(followup, "trigger_state", "")) or None,
        language=client_lang,
    )
    followup.last_error = None  # type: ignore[assignment]
    followup.suppressed_at = None  # type: ignore[assignment]
    followup.suppression_reason = None  # type: ignore[assignment]
    followup.ready_at = now_value if queue_state == "READY" else None  # type: ignore[assignment]
    followup.updated_at = now_value  # type: ignore[assignment]
    followup.save()
    return followup


def send_signal_followup(
    followup: PublishedSignalFollowUp,
    *,
    send_message_fn: Callable[..., dict] = TelegramBot_Alerts.send_message,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
) -> PublishedSignalFollowUp:
    if str(followup.queue_state or "").upper() == "SUPPRESSED":
        raise ValueError("suppressed follow-up jobs cannot be sent")

    now_value = now_fn()
    followup.last_attempted_at = now_value  # type: ignore[assignment]
    followup.updated_at = now_value  # type: ignore[assignment]
    if not followup.draft_message:
        client_lang = None
        if getattr(followup, "destination_type", None) == "SUBSCRIBER" and getattr(followup, "destination_id", None):
            try:
                from database import Client
                cl = Client.get_or_none(Client.id == int(followup.destination_id))
                if cl and cl.report_language:
                    client_lang = cl.report_language
            except Exception:
                pass
        followup.draft_message = build_followup_draft_message(  # type: ignore[assignment]
            followup.lifecycle,  # type: ignore[arg-type]
            trigger_state=str(getattr(followup, "trigger_state", "")) or None,
            language=client_lang,
        )

    destination_chat_id = str(followup.destination_chat_id or "").strip()
    if destination_chat_id:
        result = send_message_fn(str(followup.draft_message or ""), chat_id=destination_chat_id)
    else:
        result = send_message_fn(str(followup.draft_message or ""))
    if result and result.get("ok"):
        message_id = ((result or {}).get("result") or {}).get("message_id")
        followup.queue_state = "SENT"  # type: ignore[assignment]
        followup.sent_at = now_value  # type: ignore[assignment]
        followup.telegram_message_id = str(message_id) if message_id is not None else None  # type: ignore[assignment]
        followup.last_error = None  # type: ignore[assignment]
        followup.save()
        return followup

    followup.queue_state = "FAILED"  # type: ignore[assignment]
    followup.retry_count = int(getattr(followup, "retry_count", 0) or 0) + 1  # type: ignore[assignment]
    followup.last_error = str((result or {}).get("description") or "telegram_send_failed")  # type: ignore[assignment]
    followup.save()
    return followup


def process_signal_followups(
    *,
    limit: int = 50,
    queue_states: tuple[str, ...] = ("READY",),
    send_message_fn: Callable[..., dict] = TelegramBot_Alerts.send_message,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
) -> dict[str, Any]:
    with _FOLLOWUP_PROCESS_LOCK:
        normalized_states = tuple(
            state for state in ((item or "").upper().strip() for item in queue_states)
            if state in _QUEUE_STATES
        ) or ("READY",)
        jobs = list(
            PublishedSignalFollowUp.select()
            .where(PublishedSignalFollowUp.queue_state.in_(normalized_states))  # type: ignore
            .order_by(PublishedSignalFollowUp.created_at.asc(), PublishedSignalFollowUp.id.asc())
            .limit(limit)
        )

        summary = {"processed": 0, "sent": 0, "failed": 0}
        for followup in jobs:
            send_signal_followup(
                followup,
                send_message_fn=send_message_fn,
                now_fn=now_fn,
            )
            summary["processed"] += 1
            if str(followup.queue_state or "").upper() == "SENT":
                summary["sent"] += 1
            elif str(followup.queue_state or "").upper() == "FAILED":
                summary["failed"] += 1

        return {"status": "completed", "summary": summary}


def get_signal_followup_summary(*, now_fn=TimeUtils.now) -> dict[str, Any]:
    total = PublishedSignalFollowUp.select().count()
    now_value = now_fn()
    stale_cutoff = now_value - datetime.timedelta(minutes=30)
    latest = (
        PublishedSignalFollowUp.select()
        .order_by(PublishedSignalFollowUp.created_at.desc(), PublishedSignalFollowUp.id.desc())
        .first()
    )
    destination_counts: dict[str, int] = {}
    service_tier_counts: dict[str, int] = {}
    for followup in PublishedSignalFollowUp.select(PublishedSignalFollowUp.destination_type, PublishedSignalFollowUp.service_tier):
        destination_type = str(followup.destination_type or "PORTFOLIO").upper().strip() or "PORTFOLIO"
        service_tier = str(followup.service_tier or "SIGNALS_ONLY").upper().strip() or "SIGNALS_ONLY"
        destination_counts[destination_type] = destination_counts.get(destination_type, 0) + 1
        service_tier_counts[service_tier] = service_tier_counts.get(service_tier, 0) + 1
    return {
        "configured": total > 0,
        "total": total,
        "pending_count": PublishedSignalFollowUp.select().where(PublishedSignalFollowUp.queue_state == "PENDING").count(),
        "ready_count": PublishedSignalFollowUp.select().where(PublishedSignalFollowUp.queue_state == "READY").count(),
        "sent_count": PublishedSignalFollowUp.select().where(PublishedSignalFollowUp.queue_state == "SENT").count(),
        "failed_count": PublishedSignalFollowUp.select().where(PublishedSignalFollowUp.queue_state == "FAILED").count(),
        "suppressed_count": PublishedSignalFollowUp.select().where(PublishedSignalFollowUp.queue_state == "SUPPRESSED").count(),
        "stale_pending_count": PublishedSignalFollowUp.select().where(
            (PublishedSignalFollowUp.queue_state.in_(("PENDING", "READY")))  # type: ignore
            & (PublishedSignalFollowUp.created_at < stale_cutoff)  # type: ignore
        ).count(),
        "destination_counts": destination_counts,
        "service_tier_counts": service_tier_counts,
        "latest_created_at": latest.created_at.isoformat() if latest and latest.created_at else None,
    }
