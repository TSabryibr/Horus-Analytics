"""
CORE REPORT GENERATOR FACADE
============================
Backwards-compatible facade preserving all public functions, card generators,
Excel builders, and constants for core.ReportGenerator.
"""

from core.reports import (
    LOGO_PATH,
    TEMPLATE_PATH,
    _clean_text_for_drawing,
    _draw_centered_text,
    _draw_right_text,
    _exit_card_presentation,
    _get_card_font,
    _load_matplotlib,
    _preferred_excel_engine,
    _resolve_horus_logo_path,
    create_exit_card,
    create_horus_signal_card,
    create_morning_brief,
    create_signal_card,
    generate_portfolio_excel,
    generate_portfolio_html_summary,
    save_report_to_disk,
    save_styled_excel,
)

__all__ = [
    "TEMPLATE_PATH",
    "LOGO_PATH",
    "_resolve_horus_logo_path",
    "_load_matplotlib",
    "_preferred_excel_engine",
    "_get_card_font",
    "_clean_text_for_drawing",
    "_draw_centered_text",
    "_draw_right_text",
    "save_styled_excel",
    "create_signal_card",
    "create_morning_brief",
    "create_horus_signal_card",
    "_exit_card_presentation",
    "create_exit_card",
    "generate_portfolio_excel",
    "generate_portfolio_html_summary",
    "save_report_to_disk",
]

if __name__ == "__main__":
    print("Generating test Horus signal card...")
    buf = create_horus_signal_card("COMI", 100.0, 95.0, 108.0)
    with open("test_horus_card.png", "wb") as f:
        f.write(buf.getbuffer())
    print("Done")
