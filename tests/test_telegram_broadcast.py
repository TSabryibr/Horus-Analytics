"""
TELEGRAM BROADCAST TEST
========================
Sends live test messages for all 3 signal types:
  1. PRE-CLOSE signal
  2. DAILY SIGNAL
  3. INTRADAY signal

Run:  python tests/test_telegram_broadcast.py
"""

from core.settings import settings
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import TelegramBot_Alerts
from core import AlertManager
FAKE_SIGNALS = [
    {
        "Ticker": "COMI",
        "Signal_Type": "BREAKOUT",
        "Entry_Price": 52.30,
        "Stop_Loss": 49.80,
        "Target_Price": 57.50,
        "Target_Price_2": 61.00,
        "Score": 9,
        "RSI": 62.4,
        "Volume_x": 2.3,
    },
    {
        "Ticker": "SWDY",
        "Signal_Type": "MOMENTUM",
        "Entry_Price": 18.75,
        "Stop_Loss": 17.50,
        "Target_Price": 21.00,
        "Target_Price_2": 23.00,
        "Score": 8,
        "RSI": 58.1,
        "Volume_x": 1.8,
    },
    {
        "Ticker": "FWRY",
        "Signal_Type": "BREAKOUT",
        "Entry_Price": 7.42,
        "Stop_Loss": 6.90,
        "Target_Price": 8.50,
        "Target_Price_2": 9.10,
        "Score": 7,
        "RSI": 55.7,
        "Volume_x": 1.6,
    },
]


def send_signal_broadcast(scan_label: str, signals: list):
    """Broadcast a signal set with the given label (PRE-CLOSE / DAILY SIGNAL / INTRADAY)."""
    print(f"\n{'='*50}")
    print(f"  Sending {scan_label} broadcast...")
    print(f"{'='*50}")

    # 1. Header
    res = AlertManager.broadcast_alert(
        f"🔍 *{scan_label} SCAN COMPLETE*\n"
        f"Signals Found: {len(signals)}"
    )
    print(f"  [1/3] Header: {res}")

    # 2. Signal cards with images (top 3)
    try:
        from core import ReportGenerator
        for i, s in enumerate(signals[:3]):
            ticker = s.get("Ticker", "")
            entry = float(s.get("Entry_Price", 0))
            sl = float(s.get("Stop_Loss", 0))
            tp1 = float(s.get("Target_Price", 0))
            tp2 = float(s.get("Target_Price_2", 0)) if s.get("Target_Price_2") is not None else None
            score = int(s.get("Score", 0))
            rsi = s.get("RSI")
            volume_x = s.get("Volume_x")

            img_buf = ReportGenerator.create_horus_signal_card(
                ticker=ticker,
                entry=entry,
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                score=score,
                rsi=rsi,
                volume_x=volume_x,
                signal_label=scan_label,
            )
            rsi_text = f"{float(rsi):.1f}" if rsi is not None else "N/A"
            vol_text = f"{float(volume_x):.1f}x" if volume_x is not None else "N/A"
            caption = (
                f"[TOP {i+1}] {ticker} | Score: {score}/10\n"
                f"RSI: {rsi_text} | Vol Spike: {vol_text}"
            )
            res_img = AlertManager.broadcast_image(img_buf, caption)
            print(f"  [2/3] Card {i+1} ({ticker}): {res_img}")
    except Exception as e:
        print(f"  [2/3] Card generation error: {e}")

    # 3. Full text summary
    full_msg = TelegramBot_Alerts.format_signal_alert(signals)
    if full_msg:
        res_summary = AlertManager.broadcast_alert(f"📋 *{scan_label} FULL SUMMARY*\n\n{full_msg}")
        print(f"  [3/3] Summary: {res_summary}")

    print(f"  ✅ {scan_label} broadcast complete!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("  HORUS — TELEGRAM BROADCAST TEST")
    print("=" * 60)
    print(f"  Token:   {settings.TELEGRAM_TOKEN[:12]}...")
    print(f"  Chat ID: {settings.CHAT_ID}")
    print(f"  Enabled: {settings.TELEGRAM_ENABLED}")
    print("=" * 60)

    if not settings.TELEGRAM_TOKEN or not settings.CHAT_ID:
        print("\n❌ Telegram not configured. Set TELEGRAM_TOKEN and CHAT_ID.")
        sys.exit(1)

    # Test 1: PRE-CLOSE
    send_signal_broadcast("PRE-CLOSE", FAKE_SIGNALS)

    # Test 2: DAILY SIGNAL
    send_signal_broadcast("DAILY SIGNAL", FAKE_SIGNALS)

    # Test 3: INTRADAY
    send_signal_broadcast("INTRADAY", FAKE_SIGNALS[:2])  # fewer signals for intraday

    print("=" * 60)
    print("  ✅ ALL 3 BROADCASTS SENT — Check your Telegram channel!")
    print("=" * 60)
