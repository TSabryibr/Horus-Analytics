import datetime
import io
import os
import sys
from PIL import Image, ImageDraw, ImageFont

from core import TimeUtils
from core.settings import settings

# Path to the signal card template
TEMPLATE_PATH = settings.get_resource_path("signal_card_template.jpg")


def _resolve_symbol(name: str, fallback: any) -> any:
    mod = sys.modules.get("core.ReportGenerator")
    if mod and hasattr(mod, name):
        return getattr(mod, name)
    mod2 = sys.modules.get("core.reports")
    if mod2 and hasattr(mod2, name):
        return getattr(mod2, name)
    return fallback


def _resolve_horus_logo_path() -> str:
    """Resolve the branded eagle logo path across dev and packaged runtime."""
    candidates = [
        settings.get_resource_path("horus 1.PNG"),
        os.path.join(os.getcwd(), "horus 1.PNG"),
        os.path.join(os.path.dirname(__file__), "..", "horus 1.PNG"),
    ]
    for candidate in candidates:
        try:
            resolved = os.path.abspath(candidate)
            if os.path.exists(resolved):
                return resolved
        except Exception:
            continue
    return ""


LOGO_PATH = _resolve_horus_logo_path()


def _load_matplotlib():
    import matplotlib

    # Force a headless backend before importing pyplot to avoid tkinter cleanup noise.
    matplotlib.use("Agg", force=True)
    import matplotlib.patches as patches
    import matplotlib.pyplot as plt

    return plt, patches


def _get_card_font(font_type: str, size: int):
    """Load a readable cross-platform font for generated Telegram cards."""
    paths = []
    if os.name == "nt":
        if font_type == "serif":
            paths = [r"C:\Windows\Fonts\georgiab.ttf", r"C:\Windows\Fonts\timesbd.ttf", "georgiab.ttf"]
        else:
            paths = [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf", "arialbd.ttf"]
    elif font_type == "serif":
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]

    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _clean_text_for_drawing(text: str) -> str:
    if not isinstance(text, str):
        return ""
    cleaned = "".join(c for c in text if ord(c) < 0xFFFF)
    emoji_ranges = [
        (0x2000, 0x3300),
    ]
    for r_start, r_end in emoji_ranges:
        cleaned = "".join(c for c in cleaned if not (r_start <= ord(c) <= r_end))

    return cleaned.strip()


def _draw_centered_text(draw: ImageDraw.ImageDraw, xy, text: str, font, fill):
    cleaner = _resolve_symbol("_clean_text_for_drawing", _clean_text_for_drawing)
    cleaned = cleaner(text)
    bbox = draw.textbbox((0, 0), cleaned, font=font)
    x, y = xy
    draw.text((x - (bbox[2] - bbox[0]) / 2, y - (bbox[3] - bbox[1]) / 2), cleaned, font=font, fill=fill)


def _draw_right_text(draw: ImageDraw.ImageDraw, xy, text: str, font, fill):
    cleaner = _resolve_symbol("_clean_text_for_drawing", _clean_text_for_drawing)
    cleaned = cleaner(text)
    bbox = draw.textbbox((0, 0), cleaned, font=font)
    x, y = xy
    draw.text((x - (bbox[2] - bbox[0]), y), cleaned, font=font, fill=fill)


def create_signal_card(ticker, signal_type, entry, sl, tp, score, signal_date):
    """
    Generates a professional Signal Card image (PNG).
    """
    plt, patches = _resolve_symbol("_load_matplotlib", _load_matplotlib)()

    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor("#0E1117")
    ax.set_facecolor("#0E1117")
    ax.axis("off")

    c_text = "#FFFFFF"
    c_accent = "#00FF00" if signal_type == "BUY" else "#FF0000"
    c_card = "#1E1E1E"

    rect = patches.FancyBboxPatch((0.05, 0.05), 0.9, 0.9, boxstyle="round,pad=0.02", linewidth=2, edgecolor=c_accent, facecolor=c_card)
    ax.add_patch(rect)

    ax.text(0.1, 0.85, ticker, fontsize=28, weight="bold", color=c_text, fontname="Arial")
    ax.text(0.9, 0.85, signal_date, fontsize=10, color="#AAAAAA", ha="right", va="center")

    badge_color = c_accent
    badge = patches.FancyBboxPatch((0.1, 0.72), 0.2, 0.08, boxstyle="round,pad=0.01", linewidth=0, facecolor=badge_color)
    ax.add_patch(badge)
    ax.text(0.2, 0.76, signal_type, fontsize=12, weight="bold", color="#000000", ha="center", va="center")

    stars = "*" * int(score) + "." * (5 - int(score))
    ax.text(0.9, 0.76, f"Score: {stars}", fontsize=12, color="#FFD700", ha="right", va="center")

    ax.text(0.1, 0.60, "ENTRY", fontsize=10, color="#AAAAAA")
    ax.text(0.1, 0.52, f"{entry:.4f}", fontsize=18, weight="bold", color=c_text)

    ax.text(0.45, 0.60, "TARGET", fontsize=10, color="#AAAAAA", ha="center")
    ax.text(0.45, 0.52, f"{tp:.4f}", fontsize=18, weight="bold", color="#00FF00", ha="center")

    ax.text(0.9, 0.60, "STOP LOSS", fontsize=10, color="#AAAAAA", ha="right")
    ax.text(0.9, 0.52, f"{sl:.4f}", fontsize=18, weight="bold", color="#FF4B4B", ha="right")

    y_bar = 0.35
    bar_h = 0.03

    total_range = (tp - sl) * 1.2
    range_min = sl - (tp - sl) * 0.1

    def get_x(price):
        return 0.1 + ((price - range_min) / total_range) * 0.8

    x_sl = get_x(sl)
    x_entry = get_x(entry)
    x_tp = get_x(tp)

    rect_risk = patches.Rectangle((x_sl, y_bar), x_entry - x_sl, bar_h, color="#FF4B4B", alpha=0.8)
    ax.add_patch(rect_risk)

    rect_reward = patches.Rectangle((x_entry, y_bar), x_tp - x_entry, bar_h, color="#00FF00", alpha=0.8)
    ax.add_patch(rect_reward)

    ax.text(x_sl, y_bar - 0.05, "SL", fontsize=8, color="#FF4B4B", ha="center")
    ax.text(x_entry, y_bar - 0.05, "Ent", fontsize=8, color=c_text, ha="center")
    ax.text(x_tp, y_bar - 0.05, "TP", fontsize=8, color="#00FF00", ha="center")

    loss_dist = entry - sl
    gain_dist = tp - entry
    if loss_dist > 0:
        r_mult = gain_dist / loss_dist
        ax.text(0.5, 0.2, f"Risk/Reward: 1:{r_mult:.1f}", fontsize=12, color="#AAAAAA", ha="center")

    ax.text(0.5, 0.1, "Generated by HORUS ANALYTICS - EGX", fontsize=8, color="#555555", ha="center")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#0E1117")
    buf.seek(0)
    plt.close(fig)
    return buf


def create_morning_brief(regime_data, top_signals):
    """
    Generates a Morning Brief summary image.
    """
    plt, patches = _resolve_symbol("_load_matplotlib", _load_matplotlib)()

    fig, ax = plt.subplots(figsize=(8, 10))
    fig.patch.set_facecolor("#0E1117")
    ax.set_facecolor("#0E1117")
    ax.axis("off")

    c_text = "#FFFFFF"

    date_str = TimeUtils.now().strftime("%Y-%m-%d")
    ax.text(0.5, 0.95, "MORNING BRIEF", fontsize=24, weight="bold", color=c_text, ha="center")
    ax.text(0.5, 0.91, date_str, fontsize=14, color="#AAAAAA", ha="center")

    regime = regime_data.get("regime", "NEUTRAL")
    score = regime_data.get("score", 5)

    r_color = "#00FF00" if regime == "BULLISH" else "#FF0000" if regime == "BEARISH" else "#FFFF00"

    circle = patches.Circle((0.5, 0.8), 0.05, color=r_color)
    ax.add_patch(circle)
    ax.text(0.5, 0.72, f"MARKET IS {regime}", fontsize=18, weight="bold", color=r_color, ha="center")
    ax.text(0.5, 0.68, f"Breadth Score: {score}/10", fontsize=12, color="#AAAAAA", ha="center")

    ax.text(0.1, 0.60, "TOP PICKS", fontsize=16, weight="bold", color=c_text)

    y_start = 0.55
    y_step = 0.08

    ax.text(0.1, y_start, "TICKER", fontsize=12, color="#AAAAAA", weight="bold")
    ax.text(0.3, y_start, "ENTRY", fontsize=12, color="#AAAAAA", weight="bold")
    ax.text(0.5, y_start, "TARGET", fontsize=12, color="#AAAAAA", weight="bold")
    ax.text(0.7, y_start, "STOP", fontsize=12, color="#AAAAAA", weight="bold")

    current_y = y_start - y_step

    for s in top_signals[:5]:
        ticker = s.get("Ticker", "N/A")
        entry = s.get("Entry", s.get("Price", 0))
        tp = s.get("TP1", s.get("Target_1", 0))
        sl = s.get("SL", s.get("Stop_Loss", 0))

        ax.text(0.1, current_y, ticker, fontsize=14, color=c_text, weight="bold")
        ax.text(0.3, current_y, f"{entry:.4f}", fontsize=14, color=c_text)
        ax.text(0.5, current_y, f"{tp:.4f}", fontsize=14, color="#00FF00")
        ax.text(0.7, current_y, f"{sl:.4f}", fontsize=14, color="#FF4B4B")

        ax.plot([0.1, 0.9], [current_y - 0.02, current_y - 0.02], color="#333333", linewidth=1)
        current_y -= y_step

    ax.text(0.5, 0.05, "Horus Analytics", fontsize=10, color="#555555", ha="center")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#0E1117")
    buf.seek(0)
    plt.close(fig)
    return buf


def create_horus_signal_card(
    ticker,
    entry,
    stop_loss,
    tp1,
    tp2=None,
    signal_datetime=None,
    score=None,
    rsi=None,
    volume_x=None,
    confirmation=None,
    regime=None,
    signal_data_date=None,
    signal_label=None,
):
    """
    Creates the unified Horus signal card style used across session broadcasts.
    """
    if signal_datetime is None:
        signal_datetime = TimeUtils.now()

    draw_centered = _resolve_symbol("_draw_centered_text", _draw_centered_text)
    draw_right = _resolve_symbol("_draw_right_text", _draw_right_text)
    font_getter = _resolve_symbol("_get_card_font", _get_card_font)
    logo_path = _resolve_symbol("LOGO_PATH", LOGO_PATH)

    width, height = 1200, 720
    navy = "#07111E"
    panel = "#101A27"
    gold = "#D6A84A"
    gold_light = "#F5D88B"
    muted = "#7C8794"
    text = "#F7FAFC"
    accent = "#12E66A"
    accent_soft = "#184B37"

    img = Image.new("RGB", (width, height), navy)
    draw = ImageDraw.Draw(img)

    for y in range(height):
        blend = y / max(height - 1, 1)
        r = int(7 + blend * 13)
        g = int(17 + blend * 10)
        b = int(30 + blend * 2)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    pyramid_fill = "#0B1726"
    draw.polygon([(760, 650), (980, 235), (1190, 650)], fill=pyramid_fill)
    draw.polygon([(615, 650), (790, 320), (970, 650)], fill="#0D1B2B")
    for x in range(0, width, 90):
        draw.line([(x, 0), (width // 2, height)], fill="#162235", width=1)
    for x in range(62, width - 62, 86):
        draw.rectangle((x, 34, x + 38, 43), fill=gold)
        draw.rectangle((x + 12, height - 48, x + 50, height - 39), fill=gold)

    margin = 58
    draw.rounded_rectangle((margin, 54, width - margin, height - 54), radius=34, fill=panel, outline=gold, width=3)
    draw.rounded_rectangle((margin + 18, 76, width - margin - 18, height - 76), radius=28, outline=accent, width=4)
    draw.line((150, 282, width - 150, 282), fill="#273344", width=2)
    draw.line((150, 444, width - 150, 444), fill="#273344", width=2)

    logo_size = 132
    logo_x, logo_y = 92, 92
    draw.ellipse((logo_x - 8, logo_y - 8, logo_x + logo_size + 8, logo_y + logo_size + 8), fill="#05101D", outline=gold, width=3)
    if os.path.exists(logo_path):
        resampling = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else getattr(Image, "LANCZOS", 1)
        with Image.open(logo_path) as logo_src:
            logo = logo_src.convert("RGB")
        logo.thumbnail((logo_size, logo_size), resampling)  # type: ignore[arg-type]
        logo_canvas = Image.new("RGB", (logo_size, logo_size), navy)
        lx = (logo_size - logo.width) // 2
        ly = (logo_size - logo.height) // 2
        logo_canvas.paste(logo, (lx, ly))
        mask = Image.new("L", (logo_size, logo_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, logo_size, logo_size), fill=255)
        img.paste(logo_canvas, (logo_x, logo_y), mask)
    else:
        draw.ellipse((logo_x, logo_y, logo_x + logo_size, logo_y + logo_size), fill="#17243A")
        draw_centered(draw, (logo_x + logo_size / 2, logo_y + logo_size / 2), "HORUS", font_getter("serif", 24), gold_light)

    font_brand = font_getter("sans", 28)
    font_kicker = font_getter("sans", 22)
    font_header = font_getter("sans", 44)
    font_ticker = font_getter("sans", 76)
    font_value = font_getter("sans", 34)
    font_label = font_getter("sans", 22)
    font_micro = font_getter("sans", 18)
    font_footer = font_getter("serif", 20)

    draw.text((252, 110), "Horus Analytics", font=font_brand, fill=gold_light)
    draw.text((252, 148), "CAIRO SESSION | NILE RISK DESK", font=font_kicker, fill=muted)
    draw_right(draw, (width - 104, 112), signal_datetime.strftime("%d %b %Y"), font_micro, gold_light)
    draw_right(draw, (width - 104, 144), signal_datetime.strftime("%H:%M EET"), font_micro, muted)

    card_title = (signal_label or "SIGNAL CONFIRMED").upper()
    draw_centered(draw, (width / 2, 229), card_title, font_header, accent)

    # Fit the badge text cleanly so it never clips.
    badge_text = "EGYPTIAN MARKET SIGNAL ALERT"
    badge_font_size = 33
    badge_font = font_getter("sans", badge_font_size)
    while badge_font_size > 18:
        badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_text_w = badge_bbox[2] - badge_bbox[0]
        if badge_text_w <= 470:
            break
        badge_font_size -= 1
        badge_font = font_getter("sans", badge_font_size)

    badge_w = max(330, min(560, badge_text_w + 44))
    badge_h = 36
    badge_left = int((width - badge_w) / 2)
    badge_top = 302
    draw.rounded_rectangle(
        (badge_left, badge_top, badge_left + badge_w, badge_top + badge_h),
        radius=18,
        fill=accent_soft,
        outline=accent,
        width=1,
    )
    draw_centered(draw, (width / 2, badge_top + badge_h / 2), badge_text, badge_font, gold_light)

    draw.text((150, 345), str(ticker).upper(), font=font_ticker, fill=text)
    draw.text((154, 423), "TICKER", font=font_label, fill=muted)

    meta_text = []
    if score is not None:
        meta_text.append(f"SCORE {float(score):.1f}/10")
    if rsi is not None:
        meta_text.append(f"RSI {float(rsi):.1f}")
    if volume_x is not None:
        meta_text.append(f"VOL {float(volume_x):.1f}x")
    if confirmation:
        meta_text.append(str(confirmation).upper())
    if regime:
        meta_text.append(str(regime).upper())
    meta_render = " | ".join(meta_text) if meta_text else "READY"
    meta_font_size = 24
    meta_font = font_getter("sans", meta_font_size)
    while meta_font_size > 17:
        meta_bbox = draw.textbbox((0, 0), meta_render, font=meta_font)
        meta_w = meta_bbox[2] - meta_bbox[0]
        if meta_w <= 690:
            break
        meta_font_size -= 1
        meta_font = font_getter("sans", meta_font_size)

    draw_right(draw, (1050, 355), meta_render, meta_font, accent)
    draw_right(draw, (1050, 423), "SIGNAL META", font_label, muted)

    draw.rounded_rectangle((150, 484, 505, 604), radius=22, fill="#0B1421", outline="#273344", width=2)
    draw.rounded_rectangle((422, 484, 777, 604), radius=22, fill="#0B1421", outline="#273344", width=2)
    draw.rounded_rectangle((695, 484, 1050, 604), radius=22, fill="#0B1421", outline="#273344", width=2)
    draw_centered(draw, (327, 522), "ENTRY PRICE", font_label, muted)
    draw_centered(draw, (327, 566), f"{float(entry):.4f}", font_value, text)
    draw_centered(draw, (600, 522), "STOP LOSS", font_label, muted)
    draw_centered(draw, (600, 566), f"{float(stop_loss):.4f}", font_value, "#FF4B55")
    draw_centered(draw, (872, 522), "TARGET 1", font_label, muted)
    draw_centered(draw, (872, 566), f"{float(tp1):.4f}", font_value, accent)

    footer_y = 622
    motifs = ["ANKH", "RA", "NILE", "HORUS"]
    x = 162
    for motif in motifs:
        draw.rounded_rectangle((x, footer_y - 17, x + 104, footer_y + 17), radius=7, fill="#0B1421", outline="#2B384B", width=1)
        draw_centered(draw, (x + 52, footer_y + 1), motif, font_micro, gold)
        x += 128
    draw_right(draw, (width - 148, footer_y - 11), "Horus Analytics | EGX Cairo", font_footer, "#8D6E32")

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf


def _exit_card_presentation(reason, pnl_pct):
    reason_upper = str(reason or "").upper().replace(" ", "_")
    is_profit = pnl_pct >= 0
    is_target = reason_upper.startswith("TARGET")
    is_stop_loss = reason_upper == "STOP_LOSS"
    is_trailing_stop = reason_upper == "TRAILING_STOP"
    is_breakeven_stop = reason_upper in {"BREAKEVEN_STOP", "BREAKEVEN_STOP_HIT"}

    if is_target:
        return {
            "reason_upper": reason_upper,
            "accent": "#12E66A",
            "accent_soft": "#184B37",
            "header_text": f"{reason_upper.replace('_', ' ')} CLAIMED",
            "price_label": "EXIT PRICE",
        }
    if is_trailing_stop or (is_stop_loss and pnl_pct > 0):
        return {
            "reason_upper": reason_upper,
            "accent": "#D6A84A",
            "accent_soft": "#4A3616",
            "header_text": "TRAILING STOP HIT",
            "price_label": "TRAIL STOP",
        }
    if is_breakeven_stop or (is_stop_loss and abs(pnl_pct) < 0.005):
        return {
            "reason_upper": reason_upper,
            "accent": "#D6A84A",
            "accent_soft": "#4A3616",
            "header_text": "BREAKEVEN STOP HIT",
            "price_label": "STOP PRICE",
        }
    if is_stop_loss:
        return {
            "reason_upper": reason_upper,
            "accent": "#FF4B55",
            "accent_soft": "#5B2027",
            "header_text": "STOP LOSS HIT",
            "price_label": "STOP PRICE",
        }
    return {
        "reason_upper": reason_upper,
        "accent": "#12E66A" if is_profit else "#FF4B55",
        "accent_soft": "#184B37" if is_profit else "#5B2027",
        "header_text": "POSITION CLOSED",
        "price_label": "EXIT PRICE",
    }


def create_exit_card(ticker, exit_price, entry_price, pnl_pct, reason, exit_time=None):
    """
    Generates a branded Egyptian-inspired Exit Card image.
    """
    try:
        entry_val = float(entry_price or 0.0)
    except (TypeError, ValueError):
        entry_val = 0.0
    if entry_val <= 0:
        raise ValueError(f"Cannot generate exit card for {ticker}: entry price must be positive (got {entry_price})")

    if exit_time is None:
        exit_time = TimeUtils.now()

    draw_centered = _resolve_symbol("_draw_centered_text", _draw_centered_text)
    draw_right = _resolve_symbol("_draw_right_text", _draw_right_text)
    font_getter = _resolve_symbol("_get_card_font", _get_card_font)
    logo_path = _resolve_symbol("LOGO_PATH", LOGO_PATH)
    presentation_fn = _resolve_symbol("_exit_card_presentation", _exit_card_presentation)

    width, height = 1200, 720
    presentation = presentation_fn(reason, pnl_pct)
    is_profit = pnl_pct >= 0

    accent = presentation["accent"]
    accent_soft = presentation["accent_soft"]
    navy = "#07111E"
    panel = "#101A27"
    gold = "#D6A84A"
    gold_light = "#F5D88B"
    muted = "#7C8794"
    text = "#F7FAFC"

    img = Image.new("RGB", (width, height), navy)
    draw = ImageDraw.Draw(img)

    # Warm Egyptian night gradient.
    for y in range(height):
        blend = y / max(height - 1, 1)
        r = int(7 + blend * 13)
        g = int(17 + blend * 10)
        b = int(30 + blend * 2)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Subtle pyramid silhouettes and Nile-gold rays.
    pyramid_fill = "#0B1726"
    draw.polygon([(760, 650), (980, 235), (1190, 650)], fill=pyramid_fill)
    draw.polygon([(615, 650), (790, 320), (970, 650)], fill="#0D1B2B")
    for x in range(0, width, 90):
        draw.line([(x, 0), (width // 2, height)], fill="#162235", width=1)
    for x in range(62, width - 62, 86):
        draw.rectangle((x, 34, x + 38, 43), fill=gold)
        draw.rectangle((x + 12, height - 48, x + 50, height - 39), fill=gold)

    # Main card shell.
    margin = 58
    draw.rounded_rectangle((margin, 54, width - margin, height - 54), radius=34, fill=panel, outline=gold, width=3)
    draw.rounded_rectangle((margin + 18, 76, width - margin - 18, height - 76), radius=28, outline=accent, width=4)
    draw.line((150, 282, width - 150, 282), fill="#273344", width=2)
    draw.line((150, 444, width - 150, 444), fill="#273344", width=2)

    # Logo medallion.
    logo_size = 132
    logo_x, logo_y = 92, 92
    draw.ellipse((logo_x - 8, logo_y - 8, logo_x + logo_size + 8, logo_y + logo_size + 8), fill="#05101D", outline=gold, width=3)
    if os.path.exists(logo_path):
        resampling = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else getattr(Image, "LANCZOS", 1)
        with Image.open(logo_path) as logo_src:
            logo = logo_src.convert("RGB")
        logo.thumbnail((logo_size, logo_size), resampling)  # type: ignore[arg-type]
        logo_canvas = Image.new("RGB", (logo_size, logo_size), navy)
        lx = (logo_size - logo.width) // 2
        ly = (logo_size - logo.height) // 2
        logo_canvas.paste(logo, (lx, ly))
        mask = Image.new("L", (logo_size, logo_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, logo_size, logo_size), fill=255)
        img.paste(logo_canvas, (logo_x, logo_y), mask)
    else:
        draw.ellipse((logo_x, logo_y, logo_x + logo_size, logo_y + logo_size), fill="#17243A")
        draw_centered(draw, (logo_x + logo_size / 2, logo_y + logo_size / 2), "HORUS", font_getter("serif", 24), gold_light)

    font_brand = font_getter("sans", 28)
    font_kicker = font_getter("sans", 22)
    font_header = font_getter("sans", 44)
    font_ticker = font_getter("sans", 76)
    font_pnl = font_getter("sans", 76)
    font_label = font_getter("sans", 22)
    font_value = font_getter("sans", 34)
    font_footer = font_getter("serif", 20)
    font_micro = font_getter("sans", 18)

    draw.text((252, 110), "Horus Analytics", font=font_brand, fill=gold_light)
    draw.text((252, 148), "CAIRO SESSION | NILE RISK DESK", font=font_kicker, fill=muted)
    draw_right(draw, (width - 104, 112), exit_time.strftime("%d %b %Y"), font_micro, gold_light)
    draw_right(draw, (width - 104, 144), exit_time.strftime("%H:%M EET"), font_micro, muted)

    header_text = presentation["header_text"]
    pnl_str = f"+{pnl_pct:.2f}%" if is_profit else f"{pnl_pct:.2f}%"

    draw_centered(draw, (width / 2, 229), header_text, font_header, accent)
    draw.rounded_rectangle((445, 302, 755, 338), radius=18, fill=accent_soft, outline=accent, width=1)
    draw_centered(draw, (600, 321), "EGYPTIAN MARKET EXIT ALERT", font_micro, gold_light)

    draw.text((150, 345), str(ticker).upper(), font=font_ticker, fill=text)
    draw.text((154, 423), "TICKER", font=font_label, fill=muted)
    draw_right(draw, (1050, 345), pnl_str, font_pnl, fill=accent)
    draw_right(draw, (1050, 423), "REALIZED P/L", font_label, muted)

    # Price detail tablets.
    draw.rounded_rectangle((150, 484, 505, 604), radius=22, fill="#0B1421", outline="#273344", width=2)
    draw.rounded_rectangle((695, 484, 1050, 604), radius=22, fill="#0B1421", outline="#273344", width=2)
    draw_centered(draw, (327, 522), "ENTRY PRICE", font_label, muted)
    draw_centered(draw, (327, 566), f"{entry_price:.4f}", font_value, text)
    draw_centered(draw, (872, 522), presentation["price_label"], font_label, muted)
    draw_centered(draw, (872, 566), f"{exit_price:.4f}", font_value, accent)

    # Small hieroglyph-inspired footer rail.
    footer_y = 622
    motifs = ["ANKH", "RA", "NILE", "HORUS"]
    x = 162
    for motif in motifs:
        draw.rounded_rectangle((x, footer_y - 17, x + 104, footer_y + 17), radius=7, fill="#0B1421", outline="#2B384B", width=1)
        draw_centered(draw, (x + 52, footer_y + 1), motif, font_micro, gold)
        x += 128

    draw_right(draw, (width - 148, footer_y - 11), "Horus Analytics | EGX Cairo", font_footer, "#8D6E32")

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf
