"""
CORE REPORTS PACKAGE
====================
Modular reporting tools: visual signal cards, styled Excel spreadsheets,
HTML statements, and automated report generators.
"""

from core.reports.cards import (
    TEMPLATE_PATH,
    _resolve_horus_logo_path,
    LOGO_PATH,
    _load_matplotlib,
    _get_card_font,
    _clean_text_for_drawing,
    _draw_centered_text,
    _draw_right_text,
    create_signal_card,
    create_morning_brief,
    create_horus_signal_card,
    _exit_card_presentation,
    create_exit_card,
)

from core.reports.excel import (
    _preferred_excel_engine,
    save_styled_excel,
    generate_portfolio_excel,
)

from core.reports.html import (
    generate_portfolio_html_summary,
    save_report_to_disk,
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
