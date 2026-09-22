"""
SUBSCRIBER INTAKE TEMPLATE GENERATOR & PARSER MODULE
====================================================
Generates downloadable, guided Excel (.xlsx) and CSV templates for clients and subscribers
to fill with their current portfolio holdings, and parses uploaded files into validated intake payloads.
"""

import io
import csv
import re
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from typing import List, Dict, Any, Optional

EGX_TICKER_ALIASES: Dict[str, str] = {
    "CIB": "COMI",
    "COMMERCIAL INTERNATIONAL BANK": "COMI",
    "TMG": "TMGH",
    "TALAAT MOSTAFA": "TMGH",
    "HRHO": "EFGD",
    "EFG": "EFGD",
    "EFG HERMES": "EFGD",
    "HERMES": "EFGD",
    "SWDY": "SWDY",
    "ELSEWEDY": "SWDY",
    "ELSEWEDY ELECTRIC": "SWDY",
    "ABUK": "ABUK",
    "ABU QIR": "ABUK",
    "ETEL": "ETEL",
    "TELECOM EGYPT": "ETEL",
    "FWRY": "FWRY",
    "FAWRY": "FWRY",
    "AMOC": "AMOC",
    "ESRS": "ESRS",
    "EZZ STEEL": "ESRS",
    "EKHO": "EKHO",
    "EKHOA": "EKHOA",
    "MFPC": "MFPC",
    "MOPCO": "MFPC",
    "SKPC": "SKPC",
    "SIDI KERIR": "SKPC",
    "HELI": "HELI",
    "HELIOPOLIS": "HELI",
    "MNHD": "MASR",
    "MADINET MASR": "MASR",
    "OCDI": "OCDI",
    "SODIC": "OCDI",
    "PHDC": "PHDC",
    "PALM HILLS": "PHDC",
    "ADIB": "ADIB",
    "ABU DHABI ISLAMIC BANK": "ADIB",
    "CIEB": "CIEB",
    "CREDIT AGRICOLE": "CIEB",
    "QNBA": "QNBA",
    "QNB": "QNBA",
    "HDBK": "HDBK",
    "HOUSING AND DEVELOPMENT BANK": "HDBK",
    "FAIT": "FAIT",
    "FAISAL": "FAIT",
    "JUFO": "JUFO",
    "JUHAYNA": "JUFO",
    "DOMT": "DOMT",
    "DOMTY": "DOMT",
    "ISPH": "ISPH",
    "IBN SINA": "ISPH",
    "CLHO": "CLHO",
    "CLEOPATRA HOSPITAL": "CLHO",
    "ALCN": "ALCN",
    "ALEXANDRIA CONTAINERS": "ALCN",
    "ORAS": "ORAS",
    "ORASCOM CONSTRUCTION": "ORAS",
    "ORHD": "ORHD",
    "ORASCOM DEVELOPMENT": "ORHD",
}


def resolve_ticker_alias(ticker: str) -> str:
    """Normalize common Egyptian ticker aliases to official EGX exchange symbols."""
    cleaned = str(ticker or "").strip().upper()
    return EGX_TICKER_ALIASES.get(cleaned, cleaned)


def _clean_numeric(value: Any) -> Optional[float]:
    """Tolerantly extract a clean float from formatted numerical, currency, or unit strings."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "")
    if not s:
        return None
    match = re.search(r"[-+]?\d*\.?\d+", s)
    if match:
        try:
            return float(match.group(0))
        except (ValueError, TypeError):
            return None
    return None


def build_subscriber_intake_excel_template() -> bytes:
    """Generate a 2-sheet guided Excel workbook template for subscriber intake.

    Sheets:
      1. Instructions: Detailed instructions on filling the file, rules, and examples.
      2. Holdings Intake: Pre-formatted table with headers, data formats, and sample rows.

    Returns:
        bytes: Binary XLSX content ready to be downloaded by user.
    """
    wb = openpyxl.Workbook()
    if wb.active is not None:
        wb.remove(wb.active)

    font_family = "Segoe UI"
    title_font = Font(name=font_family, size=15, bold=True, color="0F172A")
    subtitle_font = Font(name=font_family, size=10, italic=True, color="64748B")
    section_font = Font(name=font_family, size=11, bold=True, color="1E293B")
    bold_font = Font(name=font_family, size=10, bold=True, color="0F172A")
    regular_font = Font(name=font_family, size=10, color="334155")
    sample_font = Font(name=font_family, size=10, italic=True, color="64748B")

    header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    required_header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    optional_header_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    sample_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    thin_border = Border(
        left=thin_border_side,
        right=thin_border_side,
        top=thin_border_side,
        bottom=thin_border_side,
    )

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    def auto_fit_columns(ws, max_cols: int | None = None):
        ws.views.sheetView[0].showGridLines = True
        cols = range(1, (max_cols or ws.max_column) + 1)
        for col in cols:
            max_len = 0
            col_letter = get_column_letter(col)
            for row in range(1, ws.max_row + 1):
                val = ws.cell(row=row, column=col).value
                if val is not None:
                    max_len = max(max_len, len(str(val)))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    # -------------------------------------------------------------------------
    # SHEET 1: Instructions
    # -------------------------------------------------------------------------
    ws_guide = wb.create_sheet(title="Instructions")
    ws_guide.cell(row=1, column=1, value="HORUS ANALYTICS II — SUBSCRIBER PORTFOLIO INTAKE").font = title_font
    ws_guide.cell(row=2, column=1, value="Fill the 'Holdings Intake' sheet with your existing stock holdings and upload it to the platform.").font = subtitle_font

    ws_guide.cell(row=4, column=1, value="HOW TO COMPLETE THIS TEMPLATE").font = section_font
    
    steps = [
        ("Step 1", "Switch to the 'Holdings Intake' sheet tab below."),
        ("Step 2", "Delete or replace the sample rows with your actual active positions."),
        ("Step 3", "Enter your Ticker Symbol (e.g. COMI, ABUK, ETEL, SWDY), Shares count, and Average Entry Price."),
        ("Step 4", "(Optional) Fill Stop Loss, Target Price 1, and Target Price 2. If left blank, Horus auto-calculates default risk levels."),
        ("Step 5", "(Optional) Set Currency (default: EGP), Sector, and any private Notes."),
        ("Step 6", "Save this Excel file and upload it in the Horus Portfolio Desk → Management Service modal."),
    ]

    for idx, (step_label, step_text) in enumerate(steps, start=5):
        c1 = ws_guide.cell(row=idx, column=1, value=step_label)
        c2 = ws_guide.cell(row=idx, column=2, value=step_text)
        c1.font = bold_font; c1.border = thin_border; c1.alignment = align_center
        c2.font = regular_font; c2.border = thin_border; c2.alignment = align_left

    ws_guide.cell(row=12, column=1, value="FIELD DEFINITIONS & RULES").font = section_font
    
    field_rules = [
        ("Field Column", "Requirement", "Data Type", "Description / Example"),
        ("Ticker", "REQUIRED", "Text", "Standard market ticker symbol (e.g. COMI, ESRS, HRHO)."),
        ("Shares", "REQUIRED", "Integer > 0", "Total number of shares currently held (e.g. 500)."),
        ("Entry_Price", "REQUIRED", "Number > 0", "Average execution entry price per share in local currency (e.g. 104.50)."),
        ("Stop_Loss", "OPTIONAL", "Number", "Planned stop-loss price. If omitted, default risk % is applied."),
        ("Target_Price_1", "OPTIONAL", "Number", "First take-profit target price. If omitted, default TP1 % is applied."),
        ("Target_Price_2", "OPTIONAL", "Number", "Second target price for extended swing runs. If omitted, TP1 + 4% is applied."),
        ("Currency", "OPTIONAL", "Text (EGP / USD)", "Currency denomination for this asset. Defaults to 'EGP'."),
        ("Sector", "OPTIONAL", "Text", "Industry sector (e.g. Banking, Industrial Goods, Healthcare)."),
        ("Notes", "OPTIONAL", "Text", "Custom notes or client account reference identifiers."),
    ]

    for idx, (col_name, req, d_type, desc) in enumerate(field_rules, start=13):
        r_row = idx
        c1 = ws_guide.cell(row=r_row, column=1, value=col_name)
        c2 = ws_guide.cell(row=r_row, column=2, value=req)
        c3 = ws_guide.cell(row=r_row, column=3, value=d_type)
        c4 = ws_guide.cell(row=r_row, column=4, value=desc)
        
        if idx == 13:
            for col in (c1, c2, c3, c4):
                col.font = header_font; col.fill = header_fill; col.alignment = align_center; col.border = thin_border
        else:
            c1.font = bold_font; c1.alignment = align_left; c1.border = thin_border
            c2.font = bold_font if req == "REQUIRED" else regular_font
            c2.alignment = align_center; c2.border = thin_border
            c3.font = regular_font; c3.alignment = align_center; c3.border = thin_border
            c4.font = regular_font; c4.alignment = align_left; c4.border = thin_border

    auto_fit_columns(ws_guide, max_cols=4)

    # -------------------------------------------------------------------------
    # SHEET 2: Holdings Intake
    # -------------------------------------------------------------------------
    ws_intake = wb.create_sheet(title="Holdings Intake")
    
    headers = [
        ("Ticker*", required_header_fill),
        ("Shares*", required_header_fill),
        ("Entry_Price*", required_header_fill),
        ("Stop_Loss", optional_header_fill),
        ("Target_Price_1", optional_header_fill),
        ("Target_Price_2", optional_header_fill),
        ("Currency", optional_header_fill),
        ("Sector", optional_header_fill),
        ("Notes", optional_header_fill),
    ]

    for col_idx, (h_title, h_fill) in enumerate(headers, start=1):
        cell = ws_intake.cell(row=1, column=col_idx, value=h_title)
        cell.font = header_font
        cell.fill = h_fill
        cell.alignment = align_center
        cell.border = thin_border

    # Sample rows for illustration
    samples = [
        ("COMI", 1000, 105.50, 99.80, 114.00, 118.50, "EGP", "Banking", "Sample: Client core holding"),
        ("ABUK", 500, 78.20, 74.00, 84.50, 88.00, "EGP", "Basic Resources", "Sample: Swing breakout entry"),
    ]

    for row_idx, sample_row in enumerate(samples, start=2):
        for col_idx, val in enumerate(sample_row, start=1):
            cell = ws_intake.cell(row=row_idx, column=col_idx, value=val)
            cell.font = sample_font
            cell.fill = sample_fill
            cell.border = thin_border
            cell.alignment = align_right if col_idx in (2, 3, 4, 5, 6) else align_center

            if col_idx in (3, 4, 5, 6):
                cell.number_format = "#,##0.00"
            elif col_idx == 2:
                cell.number_format = "#,##0"

    auto_fit_columns(ws_intake, max_cols=9)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def build_subscriber_intake_csv_template() -> str:
    """Generate a clean CSV template string for subscriber intake."""
    headers = [
        "Ticker", "Shares", "Entry_Price", "Stop_Loss",
        "Target_Price_1", "Target_Price_2", "Currency", "Sector", "Notes"
    ]
    sample_rows = [
        ["COMI", 1000, 105.50, 99.80, 114.00, 118.50, "EGP", "Banking", "Sample row"],
        ["ABUK", 500, 78.20, 74.00, 84.50, 88.00, "EGP", "Basic Resources", "Sample row"],
    ]

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in sample_rows:
        writer.writerow(row)
    return output.getvalue()


def parse_subscriber_intake_file(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """Parse an uploaded Excel (.xlsx, .xls) or CSV file into a list of normalized holding dicts.

    Returns:
        List of dictionaries with keys:
          ticker, shares, entry_price, stop_loss, target_price, target_price_2, currency, sector, notes
    """
    if not file_bytes:
        raise ValueError("Uploaded file is empty")

    name_lower = filename.lower().strip()
    is_excel = name_lower.endswith((".xlsx", ".xls"))
    is_csv = name_lower.endswith(".csv") or not is_excel

    raw_rows: List[Dict[str, Any]] = []

    if is_excel:
        try:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        except Exception as exc:
            raise ValueError(f"Invalid Excel file: {exc}")

        # Choose the sheet: prefer 'Holdings Intake' or first sheet
        ws = None
        for sheetname in wb.sheetnames:
            if "intake" in sheetname.lower() or "holding" in sheetname.lower():
                ws = wb[sheetname]
                break
        if ws is None:
            ws = wb.active or wb.worksheets[0]

        rows_iter = list(ws.iter_rows(values_only=True))
        if not rows_iter:
            raise ValueError("Excel sheet has no rows")

        # Find header row
        header_idx = -1
        col_names: List[str] = []
        for r_i, row in enumerate(rows_iter):
            cleaned_cols = [str(c or "").strip().replace("*", "").lower().replace(" ", "_") for c in row]
            if "ticker" in cleaned_cols and ("shares" in cleaned_cols or "entry_price" in cleaned_cols or "price" in cleaned_cols):
                header_idx = r_i
                col_names = cleaned_cols
                break

        if header_idx == -1:
            raise ValueError("Could not find a valid header row containing 'Ticker' and 'Shares/Entry_Price'")

        for row in rows_iter[header_idx + 1:]:
            if not row or not any(row):
                continue
            row_dict = {}
            for col_idx, col_name in enumerate(col_names):
                if col_idx < len(row):
                    row_dict[col_name] = row[col_idx]
            raw_rows.append(row_dict)

    else:
        # CSV parsing
        try:
            text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = file_bytes.decode("latin-1")
            except Exception:
                raise ValueError("CSV must be UTF-8 or Latin-1 encoded")

        reader = csv.DictReader(io.StringIO(text), skipinitialspace=True)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")

        for row in reader:
            clean_row = {
                str(k or "").strip().replace("*", "").lower().replace(" ", "_"): v
                for k, v in row.items()
            }
            raw_rows.append(clean_row)

    # Normalize into standard ManagedHoldingInput dictionary structure
    normalized_holdings: List[Dict[str, Any]] = []

    for row in raw_rows:
        raw_ticker = str(
            row.get("ticker") or
            row.get("symbol") or
            row.get("position_ticker") or
            ""
        ).strip().upper()

        if not raw_ticker:
            continue

        raw_ticker = resolve_ticker_alias(raw_ticker)

        # Skip rows marked as samples
        notes_val = str(row.get("notes") or "").lower()
        if "sample" in raw_ticker.lower() or "sample" in notes_val:
            # If user kept the exact sample ticker and notes, ignore it
            if raw_ticker in ("COMI", "ABUK") and "sample" in notes_val:
                continue

        # Shares
        raw_shares = row.get("shares") or row.get("position_shares") or row.get("qty") or row.get("quantity")
        shares = _clean_numeric(raw_shares)

        # Entry Price
        raw_price = (
            row.get("entry_price") or
            row.get("price") or
            row.get("avg_entry_price") or
            row.get("position_entry_price") or
            row.get("cost")
        )
        entry_price = _clean_numeric(raw_price)

        # Stop Loss
        raw_sl = row.get("stop_loss") or row.get("sl") or row.get("position_stop_loss")
        stop_loss = _clean_numeric(raw_sl)

        # Target Price 1
        raw_tp1 = (
            row.get("target_price_1") or
            row.get("target_price") or
            row.get("tp1") or
            row.get("tp") or
            row.get("target_1") or
            row.get("position_target_price")
        )
        target_price = _clean_numeric(raw_tp1)

        # Target Price 2
        raw_tp2 = (
            row.get("target_price_2") or
            row.get("tp2") or
            row.get("target_2") or
            row.get("position_target_price_2")
        )
        target_price_2 = _clean_numeric(raw_tp2)

        currency = str(row.get("currency") or row.get("position_currency") or "EGP").strip().upper() or "EGP"
        sector = str(row.get("sector") or row.get("position_sector") or "").strip() or None
        notes = str(row.get("notes") or row.get("position_notes") or "").strip() or None

        normalized_holdings.append({
            "ticker": raw_ticker,
            "shares": shares,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "target_price": target_price,
            "target_price_2": target_price_2,
            "currency": currency,
            "sector": sector,
            "notes": notes,
        })

    return normalized_holdings
