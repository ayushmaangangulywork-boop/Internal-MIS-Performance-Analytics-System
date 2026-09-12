"""
excel_export.py
Generates Excel summary workbook with multiple sheets.
"""
import os
import pandas as pd


def _fmt_header(wb, ws, headers, col_widths=None):
    """Write bold header row with navy background."""
    import xlsxwriter
    hdr_fmt = wb.add_format({
        "bold": True, "bg_color": "#0D1B2A", "font_color": "#FFFFFF",
        "border": 1, "align": "center", "valign": "vcenter",
        "font_size": 9,
    })
    for ci, h in enumerate(headers):
        ws.write(0, ci, h, hdr_fmt)
    if col_widths:
        for ci, w in enumerate(col_widths):
            ws.set_column(ci, ci, w)


def _write_df(wb, ws, df, start_row=1, formats=None):
    """Write dataframe rows with alternating colours."""
    import pandas as pd
    import numpy as np
    even_fmt = wb.add_format({"bg_color": "#FAFAFA", "border": 1,
                               "font_size": 8, "valign": "vcenter"})
    odd_fmt  = wb.add_format({"bg_color": "#EEF2F7", "border": 1,
                               "font_size": 8, "valign": "vcenter"})
    date_fmt_even = wb.add_format({"bg_color": "#FAFAFA", "border": 1,
                                    "font_size": 8, "valign": "vcenter",
                                    "num_format": "dd/mm/yyyy"})
    date_fmt_odd  = wb.add_format({"bg_color": "#EEF2F7", "border": 1,
                                    "font_size": 8, "valign": "vcenter",
                                    "num_format": "dd/mm/yyyy"})
    for ri, (_, row) in enumerate(df.iterrows()):
        is_even = ri % 2 == 0
        fmt      = even_fmt if is_even else odd_fmt
        date_fmt = date_fmt_even if is_even else date_fmt_odd
        for ci, val in enumerate(row.values):
            try:
                if isinstance(val, (pd.Timestamp,)) or (hasattr(val, 'date') and not isinstance(val, float)):
                    if pd.notna(val):
                        ws.write_datetime(start_row + ri, ci, val.to_pydatetime(), date_fmt)
                    else:
                        ws.write(start_row + ri, ci, "", fmt)
                elif isinstance(val, float) and np.isnan(val):
                    ws.write(start_row + ri, ci, "", fmt)
                elif isinstance(val, (int, float, np.integer, np.floating)):
                    ws.write_number(start_row + ri, ci, float(val), fmt)
                else:
                    ws.write(start_row + ri, ci, str(val) if val is not None else "", fmt)
            except Exception:
                ws.write(start_row + ri, ci, str(val) if val is not None else "", fmt)


def build_excel_report(data, output_path):
    import xlsxwriter
    wb = xlsxwriter.Workbook(output_path, {'default_date_format': 'dd/mm/yyyy'})

    title_fmt = wb.add_format({
        "bold": True, "font_size": 14, "font_color": "#0D1B2A",
        "align": "center", "valign": "vcenter",
    })
    gold_fmt = wb.add_format({
        "bold": True, "bg_color": "#C9A84C", "font_color": "#FFFFFF",
        "border": 1, "align": "center", "font_size": 9,
    })
    total_fmt = wb.add_format({
        "bold": True, "bg_color": "#0D1B2A", "font_color": "#C9A84C",
        "border": 1, "align": "center", "font_size": 9,
    })

    # ── Sheet 1: CAD Summary ──────────────────
    ws = wb.add_worksheet("CAD Summary")
    ws.merge_range("A1:J1", f"CAD Designer Summary – {data['reporting_month']}", title_fmt)
    ws.set_row(0, 22)
    cad = data["cad_summary"]
    if not cad.empty:
        hdrs = ["Rank", "Designer", "NOD", "Total Points", "Target",
                "Remaining", "Achievement %", "Contribution %", "Status"]
        cws  = [6, 22, 6, 12, 10, 12, 14, 14, 16]
        _fmt_header(wb, ws, hdrs, cws)
        ws.set_row(1, 16)
        df_out = cad[["rank","cad_designer","total_nod","total_points",
                       "target","remaining","achievement_pct","contribution_pct",
                       "status"]].copy()
        df_out["cad_designer"] = df_out["cad_designer"].str.title()
        _write_df(wb, ws, df_out, start_row=2)
        # Totals
        tr = len(df_out) + 2
        ws.merge_range(tr, 0, tr, 1, "TOTAL", total_fmt)
        for ci, val in enumerate([
            int(cad["total_nod"].sum()),
            round(cad["total_points"].sum(),2),
            round(cad["target"].sum(),2),
            round(cad["remaining"].sum(),2),
            f"{round((cad['total_points'].sum()/cad['target'].sum())*100,1) if cad['target'].sum() else 0}%",
            "","",""
        ], 2):
            ws.write(tr, ci, val, total_fmt)

    # ── Sheet 2: Manual Summary ───────────────
    ws2 = wb.add_worksheet("Manual Summary")
    ws2.merge_range("A1:J1", f"Manual Designer Summary – {data['reporting_month']}", title_fmt)
    ws2.set_row(0, 22)
    manual = data["manual_summary"]
    if not manual.empty:
        hdrs2 = ["Rank","Designer","Total Jobs","Total Qty","Selection Qty",
                 "Rejection Qty","Selection %","Rejection %","Status"]
        cws2  = [6, 22, 10, 10, 12, 12, 12, 12, 16]
        _fmt_header(wb, ws2, hdrs2, cws2)
        df_m = manual[["rank","designer_name","total_jobs","total_qty",
                        "selection_qty","rejection_qty","selection_pct",
                        "rejection_pct","status"]].copy()
        df_m["designer_name"] = df_m["designer_name"].str.title()
        _write_df(wb, ws2, df_m, start_row=2)

    # ── Sheet 3: Project Analysis ─────────────
    ws3 = wb.add_worksheet("Project Analysis")
    proj = data["project_analysis"]
    if not proj.empty:
        ws3.merge_range("A1:E1", f"Project Analysis – {data['reporting_month']}", title_fmt)
        ws3.set_row(0, 22)
        _fmt_header(wb, ws3, ["Project","Designs","NOD","Points","Contribution%"],
                    [20,10,8,12,14])
        df_p = proj[["project","designs","total_nod","total_points","contribution_pct"]].copy()
        df_p["project"] = df_p["project"].str.title()
        _write_df(wb, ws3, df_p, start_row=2)

    # ── Sheet 4: Collection Analysis ──────────
    ws4 = wb.add_worksheet("Collection Analysis")
    coll = data["collection_analysis"]
    if not coll.empty:
        ws4.merge_range("A1:E1", f"Collection Analysis – {data['reporting_month']}", title_fmt)
        ws4.set_row(0, 22)
        _fmt_header(wb, ws4, ["Collection","Designs","NOD","Points","Contribution%"],
                    [22,10,8,12,14])
        df_c = coll[["collection_name","designs","total_nod","total_points","contribution_pct"]].copy()
        df_c["collection_name"] = df_c["collection_name"].str.title()
        _write_df(wb, ws4, df_c, start_row=2)

    # ── Sheet 5: Product Analysis ─────────────
    ws5 = wb.add_worksheet("Product Analysis")
    prod = data["product_analysis"]
    if not prod.empty:
        ws5.merge_range("A1:E1", f"Product Analysis – {data['reporting_month']}", title_fmt)
        ws5.set_row(0, 22)
        _fmt_header(wb, ws5, ["Product","Designs","NOD","Points","Contribution%"],
                    [20,10,8,12,14])
        df_pr = prod[["product","designs","total_nod","total_points","contribution_pct"]].copy()
        df_pr["product"] = df_pr["product"].str.title()
        _write_df(wb, ws5, df_pr, start_row=2)

    # ── Sheet 6: Raw CAD Data ─────────────────
    ws6 = wb.add_worksheet("CAD Raw Data")
    cad_raw = data["cad_raw"]
    if not cad_raw.empty:
        ws6.merge_range(0, 0, 0, len(cad_raw.columns)-1,
                        f"CAD Raw Data – {data['reporting_month']}", title_fmt)
        ws6.set_row(0, 22)
        hdrs_raw = [c.replace("_"," ").title() for c in cad_raw.columns]
        _fmt_header(wb, ws6, hdrs_raw)
        _write_df(wb, ws6, cad_raw, start_row=2)

    wb.close()
    print(f"[Excel] Saved: {output_path}")
