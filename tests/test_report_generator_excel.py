import io
import datetime

import pandas as pd

from core import ReportGenerator
from core.ReportGenerator import save_styled_excel


def test_save_styled_excel_falls_back_without_xlsxwriter():
    """save_styled_excel should still return a valid workbook without xlsxwriter."""
    workbook = save_styled_excel(
        {
            "Signals": pd.DataFrame(
                [
                    {
                        "Ticker": "COMI",
                        "Status": "WATCHLIST",
                        "Signal_Score": 5,
                    }
                ]
            )
        }
    )

    assert isinstance(workbook, io.BytesIO)
    assert workbook.getvalue()[:2] == b"PK"


def test_exit_card_labels_trailing_stop_as_trailing_stop(monkeypatch):
    rendered_text = []
    original_draw_centered_text = ReportGenerator._draw_centered_text

    def capture_centered_text(draw, xy, text, font, fill):
        rendered_text.append(str(text))
        return original_draw_centered_text(draw, xy, text, font, fill)

    monkeypatch.setattr(ReportGenerator, "_draw_centered_text", capture_centered_text)

    card = ReportGenerator.create_exit_card(
        "ASCM",
        62.72,
        61.49,
        2.0,
        "TRAILING_STOP",
        exit_time=datetime.datetime(2026, 6, 15, 10, 53),
    )

    assert isinstance(card, io.BytesIO)
    assert "TRAILING STOP HIT" in rendered_text
    assert "TRAIL STOP" in rendered_text
    assert "EXIT PRICE" not in rendered_text


def test_exit_card_labels_profitable_legacy_stop_loss_as_trailing_stop(monkeypatch):
    rendered_text = []
    original_draw_centered_text = ReportGenerator._draw_centered_text

    def capture_centered_text(draw, xy, text, font, fill):
        rendered_text.append(str(text))
        return original_draw_centered_text(draw, xy, text, font, fill)

    monkeypatch.setattr(ReportGenerator, "_draw_centered_text", capture_centered_text)

    card = ReportGenerator.create_exit_card(
        "ASCM",
        62.72,
        61.49,
        2.0,
        "STOP_LOSS",
        exit_time=datetime.datetime(2026, 6, 15, 10, 53),
    )

    assert isinstance(card, io.BytesIO)
    assert "TRAILING STOP HIT" in rendered_text
    assert "TRAIL STOP" in rendered_text
    assert "STOP LOSS HIT" not in rendered_text


def test_exit_card_labels_stop_loss_exit_price_as_stop_price(monkeypatch):
    rendered_text = []
    original_draw_centered_text = ReportGenerator._draw_centered_text

    def capture_centered_text(draw, xy, text, font, fill):
        rendered_text.append(str(text))
        return original_draw_centered_text(draw, xy, text, font, fill)

    monkeypatch.setattr(ReportGenerator, "_draw_centered_text", capture_centered_text)

    card = ReportGenerator.create_exit_card(
        "GPIM",
        1.1466,
        1.15,
        -0.3,
        "STOP_LOSS",
        exit_time=datetime.datetime(2026, 6, 15, 11, 20),
    )

    assert isinstance(card, io.BytesIO)
    assert "STOP LOSS HIT" in rendered_text
    assert "STOP PRICE" in rendered_text
    assert "EXIT PRICE" not in rendered_text
