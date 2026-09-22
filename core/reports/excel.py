import datetime
import importlib.util
import io
from typing import Literal
import pandas as pd


def _preferred_excel_engine() -> Literal["xlsxwriter", "openpyxl"]:
    return "xlsxwriter" if importlib.util.find_spec("xlsxwriter") is not None else "openpyxl"


def save_styled_excel(data_dict: dict, path: str | None = None, file_tag: str = "Report") -> io.BytesIO | None:
    """
    Saves DataFrames to a styled Excel file (XlsxWriter) matching MomentumBreakoutScanner.py's professional format.
    """
    output = io.BytesIO()
    engine = _preferred_excel_engine()

    try:
        with pd.ExcelWriter(output, engine=engine) as writer:
            if engine != "xlsxwriter":
                for sheet_name, df in data_dict.items():
                    if df is None or df.empty:
                        df = pd.DataFrame({"Message": ["No Data Available"]})
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                output.seek(0)
                if path:
                    try:
                        with open(path, "wb") as f:
                            f.write(output.getvalue())
                    except Exception as e:
                        print(f"Error saving Excel to disk: {e}")
                        return None
                    return None
                return output

            workbook = writer.book

            # --- FORMAT DEFINITIONS (Matching MomentumBreakoutScanner.py) ---

            # Header
            header_fmt = workbook.add_format({
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#1A1A2E",  # Dark Navy
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            })

            # Base styles
            center_fmt = workbook.add_format({"align": "center", "valign": "vcenter", "border": 1})
            left_fmt = workbook.add_format({"align": "left", "valign": "vcenter", "border": 1})

            # Status Styles
            status_styles = {
                "HIGH CONVICTION BUY": workbook.add_format({"bg_color": "#FFD700", "font_color": "#000000", "bold": True, "border": 1}),
                "STRONG BUY": workbook.add_format({"bg_color": "#32CD32", "font_color": "#FFFFFF", "bold": True, "border": 1}),
                "MODERATE BUY": workbook.add_format({"bg_color": "#FFA500", "font_color": "#FFFFFF", "bold": True, "border": 1}),
                "INSTITUTIONAL ACTIVITY": workbook.add_format({"bg_color": "#9370DB", "font_color": "#FFFFFF", "bold": True, "border": 1}),
                "BREAKOUT - CONFIRMED": workbook.add_format({"bg_color": "#4169E1", "font_color": "#FFFFFF", "bold": True, "border": 1}),
                "BREAKOUT": workbook.add_format({"bg_color": "#87CEEB", "font_color": "#000000", "bold": True, "border": 1}),
                "WATCHLIST": workbook.add_format({"bg_color": "#F0E68C", "font_color": "#000000", "bold": True, "border": 1}),
                "ACCUMULATION": workbook.add_format({"bg_color": "#D3D3D3", "font_color": "#666666", "border": 1}),
            }

            # Critical Points
            cp_fmt = workbook.add_format({"bg_color": "#FFF8DC", "font_color": "#8B4513", "bold": True, "border": 1, "num_format": "0.0000"})
            cp1_fmt = workbook.add_format({"bg_color": "#FFE4B5", "font_color": "#D2691E", "bold": True, "border": 1, "num_format": "0.0000"})
            cp2_fmt = workbook.add_format({"bg_color": "#FFE4E1", "font_color": "#CD853F", "bold": True, "border": 1, "num_format": "0.0000"})

            # Targets
            tp_fmt = workbook.add_format({"bg_color": "#E0FFE0", "font_color": "#006400", "bold": True, "border": 1, "num_format": "0.0000"})
            sl_fmt = workbook.add_format({"bg_color": "#E0FFE0", "font_color": "#8B0000", "bold": True, "border": 1, "num_format": "0.0000"})

            # Trends
            bull_fmt = workbook.add_format({"font_color": "#006400", "bold": True, "align": "center", "border": 1})
            bear_fmt = workbook.add_format({"font_color": "#8B0000", "bold": True, "align": "center", "border": 1})

            # Numeric Formats
            price_fmt = workbook.add_format({"num_format": "0.0000", "align": "center", "border": 1})
            pct_fmt = workbook.add_format({'num_format': '0.00"%"', "align": "center", "border": 1})
            vol_fmt = workbook.add_format({'num_format': '0.00"x"', "align": "center", "border": 1})
            money_fmt = workbook.add_format({'num_format': '0.00"M"', "align": "center", "border": 1})
            rr_fmt = workbook.add_format({'num_format': '0.00":1"', "align": "center", "border": 1})

            # Score Gradients (Simplified mapping for xlsxwriter)
            score_fmts = {}
            for i in range(11):
                color = "#8B0000"  # Default dark red
                font_c = "#FFFFFF"
                if i >= 10:
                    color = "#006400"
                elif i >= 9:
                    color = "#228B22"
                elif i >= 8:
                    color = "#32CD32"
                elif i >= 7:
                    color = "#7FFF00"
                    font_c = "#000000"
                elif i >= 6:
                    color = "#9ACD32"
                    font_c = "#000000"
                elif i >= 5:
                    color = "#FFD700"
                    font_c = "#000000"
                elif i >= 4:
                    color = "#FFA500"
                elif i >= 3:
                    color = "#FF8C00"
                elif i >= 2:
                    color = "#FF6347"
                elif i >= 1:
                    color = "#FF0000"

                score_fmts[i] = workbook.add_format({"bg_color": color, "font_color": font_c, "bold": True, "align": "center", "border": 1})

            # Institutional Signal
            loki_yes_fmt = workbook.add_format({"bg_color": "#FFD700", "font_color": "#000000", "bold": True, "align": "center", "border": 1})
            loki_no_fmt = workbook.add_format({"bg_color": "#E8E8E8", "align": "center", "border": 1})

            for sheet_name, df in data_dict.items():
                if df is None or df.empty:
                    df = pd.DataFrame({"Message": ["No Data Available"]})

                # Write data first (without index)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]

                # Freeze panes
                worksheet.freeze_panes(1, 1)  # Freeze top row and first column

                # Set specific column widths (matching MomentumBreakoutScanner.py)
                col_widths = {
                    "Ticker": 10,
                    "Currency": 10,
                    "Status": 35,
                    "Signal_Score": 8,
                    "Signal_Reasons": 25,
                    "Trend": 10,
                    "Price": 10,
                    "EMA9": 10,
                    "RSI": 8,
                    "Rel_Volume": 10,
                    "Price_Move_%": 11,
                    "Avg_Turnover_M": 12,
                    "Institutional_Signal": 10,
                    "Resistance_20D": 13,
                    "Key_Resistance_1": 13,
                    "Key_Resistance_2": 13,
                    "Distance_%": 11,
                    "Key_Res_1_Dist_%": 13,
                    "Key_Res_2_Dist_%": 13,
                    "ATR": 8,
                    "Force_Power": 11,
                    "Stop_Loss": 10,
                    "Target_1": 10,
                    "Target_2": 10,
                    "Target_3": 12,
                    "Target_4": 14,
                    "Risk_Reward_Ratio": 10,
                }

                # Apply headers styling and column widths
                for col_num, col_name in enumerate(df.columns):
                    worksheet.write(0, col_num, col_name, header_fmt)

                    # Set width
                    width = col_widths.get(col_name, 15)
                    worksheet.set_column(col_num, col_num, width)

                # Row Formatting Loop
                for row_idx, row in df.iterrows():
                    excel_row = row_idx + 1  # 0-based dataframe index -> 1-based Excel row (header is 0)

                    for col_num, col_name in enumerate(df.columns):
                        val = row[col_name]
                        cell_fmt = center_fmt  # Default

                        # Status Formatting
                        if col_name == "Status":
                            cell_fmt = left_fmt  # Default alignment
                            for key, fmt in status_styles.items():
                                if key in str(val):
                                    cell_fmt = fmt
                                    break

                        # Signal Score
                        elif col_name == "Signal_Score":
                            try:
                                score = int(val)
                                if score in score_fmts:
                                    cell_fmt = score_fmts[score]
                            except Exception:
                                pass

                        # Institutional Signal
                        elif col_name == "Institutional_Signal":
                            cell_fmt = loki_yes_fmt if val == "✅" else loki_no_fmt

                        # Trend
                        elif col_name == "Trend":
                            if val == "BULLISH":
                                cell_fmt = bull_fmt
                            elif val == "BEARISH":
                                cell_fmt = bear_fmt

                        # Critical Points
                        elif col_name == "Resistance_20D":
                            cell_fmt = cp_fmt
                        elif col_name == "Key_Resistance_1":
                            cell_fmt = cp1_fmt
                        elif col_name == "Key_Resistance_2":
                            cell_fmt = cp2_fmt

                        # Targets
                        elif col_name == "Stop_Loss":
                            cell_fmt = sl_fmt
                        elif col_name.startswith("Target_"):
                            cell_fmt = tp_fmt

                        # Numbers / Metrics
                        elif col_name in ["Price", "EMA9", "ATR"]:
                            cell_fmt = price_fmt
                        elif col_name in ["Rel_Volume"]:
                            cell_fmt = vol_fmt
                        elif col_name in ["Avg_Turnover_M"]:
                            cell_fmt = money_fmt
                        elif col_name in ["Risk_Reward_Ratio"]:
                            cell_fmt = rr_fmt
                        elif "%" in col_name:
                            cell_fmt = pct_fmt

                        # RSI Conditional
                        elif col_name == "RSI":
                            try:
                                r = float(val)
                                if r >= 70:
                                    cell_fmt = workbook.add_format({"font_color": "#8B0000", "bold": True, "align": "center", "border": 1})
                                elif r <= 30:
                                    cell_fmt = workbook.add_format({"font_color": "#006400", "bold": True, "align": "center", "border": 1})
                                elif 50 <= r < 70:
                                    cell_fmt = workbook.add_format({"font_color": "#228B22", "align": "center", "border": 1})
                            except Exception:
                                pass

                        # Write with format
                        worksheet.write(excel_row, col_num, val, cell_fmt)

                # Auto-filter
                worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)

    except Exception as e:
        print(f"Excel generation error: {e}")
        return None

    output.seek(0)

    if path:
        try:
            with open(path, "wb") as f:
                f.write(output.getvalue())
        except Exception as e:
            print(f"Error saving Excel to disk: {e}")
            return None
        return None
    else:
        return output


def generate_portfolio_excel(portfolio_id, trades, open_positions):
    """
    Generates a professional Excel (.xlsx) workbook with multiple sheets for auditing.
    """
    output = io.BytesIO()

    engine = _preferred_excel_engine()

    with pd.ExcelWriter(output, engine=engine) as writer:

        # Sheet 1: Summary
        summary_df = pd.DataFrame([
            ["Generated At", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["Portfolio ID", portfolio_id],
            ["Open Positions", len(open_positions)],
            ["Total Trades", len(trades)],
            ["Win Rate", f"{sum(1 for t in trades if t.get('pnl',0) > 0) / len(trades) * 100:.1f}%" if trades else "0.0%"],
        ], columns=["Metric", "Value"])

        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        # Sheet 2: Open Positions
        if open_positions:
            df_open = pd.DataFrame(open_positions)
            df_open.to_excel(writer, sheet_name="Open Positions", index=False)

        # Sheet 3: Trade History
        if trades:
            df_trades = pd.DataFrame(trades)
            df_trades.to_excel(writer, sheet_name="Trade History", index=False)

    output.seek(0)
    return output
