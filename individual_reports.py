"""
individual_reports.py
Generates one PDF per designer (CAD + Manual) containing:
  - Full-page Scorecard
  - Work Summary (scorecard KPIs)
  - Complete Work Done list (all rows)
  - Products checklist
"""

import os
import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import pandas as pd
from datetime import datetime

from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
    KeepTogether, PageBreak, Image
)
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from pdf_styles import (
    PS,
    C_NAVY, C_GOLD, C_GOLD_LIGHT, C_GREEN, C_GREEN_BG,
    C_RED, C_RED_BG, C_ORANGE, C_ORANGE_BG, C_BLUE, C_BLUE_LIGHT,
    C_GREY_DARK, C_WHITE, C_GREY_MID, C_ROW_EVEN, C_ROW_ODD,
    STATUS_COLORS, get_styles, compact_table_style, standard_table_style,
)

PW, PH   = landscape(A4)
MARGIN   = 10 * mm
CW       = PW - 2 * MARGIN
COMPANY  = "MAWSIM GOLD"


# ── helpers ─────────────────────────────────────────────────────

def _P(text, style):
    return Paragraph(str(text), style)


def _page_title(text, subtitle=""):
    s  = PS(fontName="Helvetica-Bold", fontSize=14,
            textColor=C_WHITE, alignment=TA_CENTER)
    s2 = PS(fontName="Helvetica",      fontSize=8,
            textColor=C_GOLD_LIGHT,    alignment=TA_CENTER)
    rows = [[_P(text, s)]]
    if subtitle:
        rows.append([_P(subtitle, s2)])
    t = Table(rows, colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LINEBELOW",     (0,-1),(-1,-1), 2.5, C_GOLD),
    ]))
    return t


def _section_hdr(text):
    s = PS(fontName="Helvetica-Bold", fontSize=9,
           textColor=C_WHITE, alignment=TA_LEFT)
    t = Table([[_P(f"  {text}", s)]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LINEBELOW",     (0,0),(-1,-1), 1.5, C_GOLD),
    ]))
    return t


def _fig_to_rl(fig, w, h):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=w, height=h)


def _donut(pct, w=48, h=48):
    fig, ax = plt.subplots(figsize=(w/72, h/72), dpi=150)
    fig.patch.set_alpha(0)
    color  = "#2E7D32" if pct >= 80 else ("#E65100" if pct >= 50 else "#C62828")
    remain = max(0, 100 - pct)
    ax.pie([min(pct, 100), remain],
           colors=[color, "#E8ECEF"],
           startangle=90,
           wedgeprops={"width": 0.38, "edgecolor": "white", "linewidth": 0.8})
    ax.text(0, 0, f"{pct:.0f}%", ha="center", va="center",
            fontsize=9, fontweight="bold", color=color)
    ax.axis("equal")
    fig.tight_layout(pad=0)
    return _fig_to_rl(fig, w, h)


def _pct_bar(pct, w, h=8):
    color  = C_GREEN if pct >= 80 else (C_ORANGE if pct >= 50 else C_RED)
    filled = max(2, min(pct / 100, 1.0)) * w
    empty  = max(0, w - filled)
    t = Table([["", ""]], colWidths=[filled, empty], rowHeights=[h])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,0), color),
        ("BACKGROUND",    (1,0),(1,0), HexColor("#E0E0E0")),
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))
    return t


def _kpi_tile(label, val, accent, bg, tile_w):
    v_s = PS(fontName="Helvetica-Bold",
             fontSize=13 if len(str(val)) <= 6 else 10,
             textColor=HexColor(accent), alignment=TA_CENTER)
    l_s = PS(fontName="Helvetica", fontSize=7,
             textColor=C_GREY_DARK, alignment=TA_CENTER)
    t = Table([[_P(str(val), v_s)], [_P(label, l_s)]], colWidths=[tile_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor(bg)),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("BOX",           (0,0),(-1,-1), 0.4, HexColor("#CCCCCC")),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
    ]))
    return t


# ── CAD individual report ────────────────────────────────────────

def _build_cad_individual(row, cad_raw, month):
    name     = row["cad_designer"].title()
    pct      = row["achievement_pct"]
    stat     = row["status"]
    location = cad_raw[cad_raw["cad_designer"] == row["cad_designer"]]["cad_location"].mode()
    location = location.iloc[0].title() if len(location) > 0 else "—"
    stat_bg  = C_GREEN if stat == "On Track" else (C_ORANGE if stat == "Below Target" else C_RED)

    elems = []

    # ── PAGE 1: Scorecard ──────────────────────────────────────────
    elems.append(_page_title(
        f"INDIVIDUAL DESIGNER REPORT — {name.upper()}",
        f"CAD Designer  |  {month}  |  Location: {location}  |  Rank #{int(row['rank'])}"
    ))
    elems.append(Spacer(1, 8))

    # Status badge
    stat_s = PS(fontName="Helvetica-Bold", fontSize=11,
                textColor=C_WHITE, alignment=TA_CENTER)
    badge = Table([[_P(f"  {stat}  ", stat_s)]], colWidths=[CW])
    badge.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), stat_bg),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
    ]))
    elems.append(badge)
    elems.append(Spacer(1, 6))

    # KPI tiles  (6 tiles + donut)
    tile_w = CW / 7
    donut_img = _donut(min(pct, 100), w=52, h=52)
    donut_cell = Table([[donut_img]], colWidths=[tile_w])
    donut_cell.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), HexColor("#F5F7FA")),
        ("BOX",        (0,0),(-1,-1), 0.4, HexColor("#CCCCCC")),
        ("ALIGN",      (0,0),(-1,-1), "CENTER"),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
    ]))
    kpi_row = Table([[
        _kpi_tile("Designs",     int(row["total_designs"]),                "#1A237E", "#E8EAF6", tile_w),
        _kpi_tile("NOD",         int(row["total_nod"]),                    "#1565C0", "#E3F2FD", tile_w),
        _kpi_tile("Points",      f"{row['total_points']:.2f}",             "#283593", "#E8EAF6", tile_w),
        _kpi_tile("Target",      f"{row['target']:.2f}",                   "#E65100", "#FFF8E1", tile_w),
        _kpi_tile("Remaining",   f"{row['remaining']:.2f}",                "#BF360C", "#FFF3E0", tile_w),
        _kpi_tile("Avg Pts",     f"{row['avg_pts_per_design']:.3f}",       "#4A148C", "#F3E5F5", tile_w),
        donut_cell,
    ]], colWidths=[tile_w] * 7)
    kpi_row.setStyle(TableStyle([
        ("LEFTPADDING",   (0,0),(-1,-1), 1),
        ("RIGHTPADDING",  (0,0),(-1,-1), 1),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
    ]))
    elems.append(kpi_row)
    elems.append(Spacer(1, 4))

    # Progress bar
    bar = _pct_bar(min(pct, 100), w=int(CW - 10), h=10)
    bar_lbl = PS(fontName="Helvetica", fontSize=7.5,
                 textColor=C_GREY_MID, alignment=TA_RIGHT)
    bar_sec = Table([
        [bar],
        [_P(f"Achievement: {pct:.1f}%  |  Contribution: {row['contribution_pct']:.1f}%  |  Grade: {row['grade']}", bar_lbl)],
    ], colWidths=[CW - 6])
    bar_sec.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 1),
        ("LEFTPADDING",   (0,0),(-1,-1), 3),
        ("RIGHTPADDING",  (0,0),(-1,-1), 3),
    ]))
    elems.append(bar_sec)
    elems.append(Spacer(1, 8))

    # Breakdown tables: Product | Project | Collection | Location
    ddf = cad_raw[cad_raw["cad_designer"] == row["cad_designer"]]
    tw  = (CW - 10) / 4

    def _mini_tbl(df, group_col, val_col, hdr_label, w, count_col=None):
        if df.empty or group_col not in df.columns:
            return Spacer(w, 1)
        if count_col:
            g = df.groupby(group_col).agg(
                cnt=(count_col, "count"), pts=(val_col, "sum")
            ).reset_index().sort_values("pts", ascending=False).head(8)
            header = [hdr_label, "Des", "Pts"]
            rows   = [[str(r[group_col]).title()[:18],
                       str(int(r["cnt"])), f"{r['pts']:.2f}"] for _, r in g.iterrows()]
            cws = [w * 0.54, w * 0.20, w * 0.26]
        else:
            g = df.groupby(group_col)[val_col].sum().reset_index()\
                  .sort_values(val_col, ascending=False).head(8)
            header = [hdr_label, "Pts"]
            rows   = [[str(r[group_col]).title()[:18], f"{r[val_col]:.2f}"]
                      for _, r in g.iterrows()]
            cws = [w * 0.62, w * 0.38]
        data = [header] + rows
        t = Table(data, colWidths=cws)
        t.setStyle(compact_table_style())
        return t

    prod_t = _mini_tbl(ddf, "product",      "points", "Product",    tw, count_col="cad_design_no")
    proj_t = _mini_tbl(ddf, "project",      "points", "Project",    tw, count_col="cad_design_no")
    coll_t = _mini_tbl(ddf, "collection_name", "points", "Collection", tw, count_col="cad_design_no")
    loc_t  = _mini_tbl(ddf, "cad_location", "points", "Location",   tw, count_col="cad_design_no")

    breakdown = Table([[prod_t, proj_t, coll_t, loc_t]], colWidths=[tw] * 4)
    breakdown.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 2),
        ("RIGHTPADDING", (0,0),(-1,-1), 2),
        ("TOPPADDING",   (0,0),(-1,-1), 2),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
    ]))
    elems.append(_section_hdr("PERFORMANCE BREAKDOWN — Product / Project / Collection / Location"))
    elems.append(breakdown)

    # ── PAGE 2: Complete Work Done List ────────────────────────────
    elems.append(PageBreak())
    elems.append(_page_title(
        f"COMPLETE WORK REGISTER — {name.upper()}",
        f"Total Designs: {int(row['total_designs'])}  |  Total NOD: {int(row['total_nod'])}  |  Total Points: {row['total_points']:.2f}"
    ))
    elems.append(Spacer(1, 6))

    hdrs = ["#", "Design No", "Date", "Collection", "Project",
            "Product", "Order Type", "Karat", "DC/Die", "Location", "NOD", "Points"]
    cws  = [22, CW*0.13, 50, CW*0.13, CW*0.11,
            CW*0.09, 58, 32, 35, 60, 28, 42]

    df_sorted = ddf.sort_values("cam_date")
    rows = []
    for i, (_, r) in enumerate(df_sorted.iterrows(), 1):
        date_str = r["cam_date"].strftime("%d/%m/%Y") if pd.notna(r["cam_date"]) else "—"
        rows.append([
            str(i),
            str(r.get("cad_design_no", ""))[:14],
            date_str,
            str(r.get("collection_name", "")).title()[:16],
            str(r.get("project", "")).title()[:14],
            str(r.get("product", "")).title()[:12],
            str(r.get("order_type", "")).title()[:10],
            str(r.get("karat", "")),
            str(r.get("dc_die", "")),
            str(r.get("cad_location", "")).title()[:10],
            str(int(r.get("nod", 0))),
            f"{float(r.get('points', 0)):.2f}",
        ])

    # Totals row
    rows.append(["", "TOTALS", "", "", "", "", "", "", "", "",
                 str(int(row["total_nod"])), f"{row['total_points']:.2f}"])

    work_tbl = Table([hdrs] + rows, colWidths=cws)
    ts = standard_table_style()
    ts.add("BACKGROUND", (0, len(rows)), (-1, len(rows)), C_NAVY)
    ts.add("TEXTCOLOR",  (0, len(rows)), (-1, len(rows)), C_GOLD)
    ts.add("FONTNAME",   (0, len(rows)), (-1, len(rows)), "Helvetica-Bold")
    work_tbl.setStyle(ts)
    elems.append(work_tbl)

    # ── PAGE 3: Products Checklist ──────────────────────────────────
    elems.append(PageBreak())
    elems.append(_page_title(
        f"PRODUCTS CHECKLIST — {name.upper()}",
        "All products worked on this period — for verification"
    ))
    elems.append(Spacer(1, 8))

    prod_summary = ddf.groupby("product").agg(
        designs=("cad_design_no", "count"),
        total_nod=("nod", "sum"),
        total_pts=("points", "sum"),
    ).reset_index().sort_values("total_pts", ascending=False)

    p_hdrs = ["Product", "Designs", "Total NOD", "Total Points", "Contribution %"]
    total_pts_all = prod_summary["total_pts"].sum()
    p_rows = []
    for _, r in prod_summary.iterrows():
        contrib = (r["total_pts"] / total_pts_all * 100) if total_pts_all > 0 else 0
        p_rows.append([
            r["product"].title(),
            str(int(r["designs"])),
            str(int(r["total_nod"])),
            f"{r['total_pts']:.2f}",
            f"{contrib:.1f}%",
        ])
    # Total row
    p_rows.append(["TOTAL", str(int(prod_summary["designs"].sum())),
                   str(int(prod_summary["total_nod"].sum())),
                   f"{total_pts_all:.2f}", "100.0%"])

    cws_p = [CW * 0.35, 70, 70, 80, 80]
    p_tbl = Table([p_hdrs] + p_rows, colWidths=cws_p)
    ts2   = standard_table_style()
    ts2.add("BACKGROUND", (0, len(p_rows)), (-1, len(p_rows)), C_NAVY)
    ts2.add("TEXTCOLOR",  (0, len(p_rows)), (-1, len(p_rows)), C_GOLD)
    ts2.add("FONTNAME",   (0, len(p_rows)), (-1, len(p_rows)), "Helvetica-Bold")
    p_tbl.setStyle(ts2)
    elems.append(p_tbl)

    # ── PAGE 4: Vinsmera & Customer Order Type Analysis ─────────────
    elems.append(PageBreak())
    elems.append(_page_title(
        f"ORDER TYPE ANALYSIS — {name.upper()}",
        "Breakdown by Order Type: VINSMERA vs CUSTOMER"
    ))
    elems.append(Spacer(1, 8))

    # Split raw data into VINSMERA and CUSTOMER
    ddf_v = ddf[ddf["order_type"].str.upper() == "VINSMERA"] if "order_type" in ddf.columns else ddf.iloc[0:0]
    ddf_c = ddf[ddf["order_type"].str.upper() == "CUSTOMER"] if "order_type" in ddf.columns else ddf.iloc[0:0]

    tot_pts   = ddf["points"].sum() if not ddf.empty else 0
    v_pts     = ddf_v["points"].sum() if not ddf_v.empty else 0
    c_pts     = ddf_c["points"].sum() if not ddf_c.empty else 0
    v_nod     = int(ddf_v["nod"].sum()) if not ddf_v.empty else 0
    c_nod     = int(ddf_c["nod"].sum()) if not ddf_c.empty else 0
    v_designs = int(len(ddf_v))
    c_designs = int(len(ddf_c))
    v_pct     = (v_pts / tot_pts * 100) if tot_pts > 0 else 0
    c_pct     = (c_pts / tot_pts * 100) if tot_pts > 0 else 0

    # Summary KPI tiles — VINSMERA (left 3) | CUSTOMER (right 3) | separator
    tile_w = CW / 7
    ot_kpi_row = Table([[
        _kpi_tile("VINSMERA Des",  v_designs,         "#4A148C", "#F3E5F5", tile_w),
        _kpi_tile("VINSMERA NOD",  v_nod,             "#6A1B9A", "#EDE7F6", tile_w),
        _kpi_tile("VINSMERA Pts",  f"{v_pts:.2f}",    "#7B1FA2", "#F3E5F5", tile_w),
        _kpi_tile("Split",         f"{v_pct:.1f}% / {c_pct:.1f}%", "#37474F", "#ECEFF1", tile_w),
        _kpi_tile("CUSTOMER Des",  c_designs,         "#1565C0", "#E3F2FD", tile_w),
        _kpi_tile("CUSTOMER NOD",  c_nod,             "#1976D2", "#E8EAF6", tile_w),
        _kpi_tile("CUSTOMER Pts",  f"{c_pts:.2f}",    "#1A237E", "#E3F2FD", tile_w),
    ]], colWidths=[tile_w] * 7)
    ot_kpi_row.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 1),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 1),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elems.append(ot_kpi_row)
    elems.append(Spacer(1, 8))

    # Side-by-side breakdown: VINSMERA | CUSTOMER
    half_w = (CW - 10) / 2

    def _ot_section(label, sub_df, w, color):
        """Mini breakdown table for one order type."""
        if sub_df.empty:
            s = PS(fontName="Helvetica", fontSize=8,
                   textColor=C_GREY_MID, alignment=TA_CENTER)
            return Table([[_P(f"No {label} designs this period", s)]], colWidths=[w])

        # Header banner
        hdr_s  = PS(fontName="Helvetica-Bold", fontSize=9,
                    textColor=C_WHITE, alignment=TA_CENTER)
        banner = Table([[_P(f"  {label}  ", hdr_s)]], colWidths=[w])
        banner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), color),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW",     (0, 0), (-1, -1), 1.5, C_GOLD),
        ]))

        tw = (w - 6) / 3

        def _mb(df, grp, val, hdr, mw, count_col=None):
            if df.empty or grp not in df.columns:
                return Spacer(mw, 1)
            if count_col:
                g = df.groupby(grp).agg(
                    cnt=(count_col, "count"), pts=(val, "sum")
                ).reset_index().sort_values("pts", ascending=False).head(8)
                header = [hdr, "Des", "Pts"]
                rows_d = [[str(r[grp]).title()[:16], str(int(r["cnt"])), f"{r['pts']:.2f}"]
                          for _, r in g.iterrows()]
                cws_d  = [mw * 0.54, mw * 0.20, mw * 0.26]
            else:
                g = df.groupby(grp)[val].sum().reset_index().sort_values(val, ascending=False).head(8)
                header = [hdr, "Pts"]
                rows_d = [[str(r[grp]).title()[:18], f"{r[val]:.2f}"] for _, r in g.iterrows()]
                cws_d  = [mw * 0.62, mw * 0.38]
            t = Table([header] + rows_d, colWidths=cws_d)
            t.setStyle(compact_table_style())
            return t

        prod_t = _mb(sub_df, "product",         "points", "Product",    tw, count_col="cad_design_no")
        proj_t = _mb(sub_df, "project",          "points", "Project",    tw, count_col="cad_design_no")
        coll_t = _mb(sub_df, "collection_name",  "points", "Collection", tw, count_col="cad_design_no")

        bk = Table([[prod_t, proj_t, coll_t]], colWidths=[tw] * 3)
        bk.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ]))

        section = Table([[banner], [Spacer(1, 4)], [bk]], colWidths=[w])
        section.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        return section

    from reportlab.lib.colors import HexColor as HC
    v_section = _ot_section("VINSMERA", ddf_v, half_w, HC("#6A1B9A"))
    c_section = _ot_section("CUSTOMER", ddf_c, half_w, HC("#1565C0"))

    elems.append(_section_hdr("BREAKDOWN BY ORDER TYPE — Product / Project / Collection"))
    side_by_side = Table([[v_section, c_section]], colWidths=[half_w, half_w])
    side_by_side.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LINEAFTER",     (0, 0), (0, -1),  0.5, HC("#CCCCCC")),
    ]))
    elems.append(side_by_side)
    elems.append(Spacer(1, 10))

    # Full detail table for both order types combined, sorted by order_type then date
    elems.append(_section_hdr("FULL ORDER TYPE REGISTER — All Designs"))
    elems.append(Spacer(1, 4))

    ot_hdrs = ["#", "Order Type", "Design No", "Date", "Collection",
               "Product", "Project", "Karat", "NOD", "Points"]
    ot_cws  = [22, 68, CW * 0.13, 50, CW * 0.13,
               CW * 0.10, CW * 0.10, 36, 28, 42]

    ot_df = ddf.copy()
    if "order_type" in ot_df.columns:
        ot_df = ot_df.sort_values(["order_type", "cam_date"])
    ot_rows = []
    for i, (_, r) in enumerate(ot_df.iterrows(), 1):
        date_str = r["cam_date"].strftime("%d/%m/%Y") if pd.notna(r["cam_date"]) else "—"
        ot = str(r.get("order_type", "")).upper()
        ot_rows.append([
            str(i),
            ot,
            str(r.get("cad_design_no", ""))[:14],
            date_str,
            str(r.get("collection_name", "")).title()[:16],
            str(r.get("product", "")).title()[:12],
            str(r.get("project", "")).title()[:12],
            str(r.get("karat", "")),
            str(int(r.get("nod", 0))),
            f"{float(r.get('points', 0)):.2f}",
        ])

    ot_tbl = Table([ot_hdrs] + ot_rows, colWidths=ot_cws)
    ot_ts  = standard_table_style()
    # Colour-code VINSMERA rows purple, CUSTOMER rows blue
    for idx, (_, r) in enumerate(ot_df.iterrows(), 1):
        ot = str(r.get("order_type", "")).upper()
        if ot == "VINSMERA":
            ot_ts.add("BACKGROUND", (1, idx), (1, idx), HC("#EDE7F6"))
            ot_ts.add("TEXTCOLOR",  (1, idx), (1, idx), HC("#6A1B9A"))
            ot_ts.add("FONTNAME",   (1, idx), (1, idx), "Helvetica-Bold")
        else:
            ot_ts.add("BACKGROUND", (1, idx), (1, idx), HC("#E3F2FD"))
            ot_ts.add("TEXTCOLOR",  (1, idx), (1, idx), HC("#1565C0"))
    ot_tbl.setStyle(ot_ts)
    elems.append(ot_tbl)

    return elems


# ── Manual individual report ─────────────────────────────────────

def _build_manual_individual(row, designer_raw, month):
    name    = row["designer_name"].title()
    sel     = row["selection_pct"]
    stat    = row["status"]
    location = row.get("location", "")
    if not location:
        # fallback: from raw
        ddf = designer_raw[designer_raw["designer_name"] == row["designer_name"]]
        loc_vals = ddf["location"].dropna() if "location" in ddf.columns else pd.Series()
        location = loc_vals.mode().iloc[0].title() if len(loc_vals) > 0 else "—"
    else:
        location = location.title()
    stat_bg = C_GREEN if stat == "Excellent" else (C_BLUE if stat == "Good" else C_RED)

    elems = []

    # ── PAGE 1: Scorecard ──────────────────────────────────────────
    elems.append(_page_title(
        f"INDIVIDUAL DESIGNER REPORT — {name.upper()}",
        f"Manual Designer  |  {month}  |  Location: {location}  |  Rank #{int(row['rank'])}"
    ))
    elems.append(Spacer(1, 8))

    stat_s = PS(fontName="Helvetica-Bold", fontSize=11,
                textColor=C_WHITE, alignment=TA_CENTER)
    badge  = Table([[_P(f"  {stat}  ", stat_s)]], colWidths=[CW])
    badge.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), stat_bg),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
    ]))
    elems.append(badge)
    elems.append(Spacer(1, 6))

    # KPI tiles — no points for manual
    tile_w = CW / 6
    donut_img = _donut(min(sel, 100), w=52, h=52)
    donut_cell = Table([[donut_img]], colWidths=[tile_w])
    donut_cell.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), HexColor("#F5F7FA")),
        ("BOX",        (0,0),(-1,-1), 0.4, HexColor("#CCCCCC")),
        ("ALIGN",      (0,0),(-1,-1), "CENTER"),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
    ]))
    kpi_row = Table([[
        _kpi_tile("Total Jobs",   int(row["total_jobs"]),    "#1A237E", "#E8EAF6", tile_w),
        _kpi_tile("Total Qty",    int(row["total_qty"]),     "#1565C0", "#E3F2FD", tile_w),
        _kpi_tile("Selected",     int(row["selection_qty"]), "#2E7D32", "#E8F5E9", tile_w),
        _kpi_tile("Rejected",     int(row["rejection_qty"]), "#C62828", "#FFEBEE", tile_w),
        _kpi_tile("Selection %",  f"{sel:.1f}%",            "#2E7D32", "#E8F5E9", tile_w),
        donut_cell,
    ]], colWidths=[tile_w] * 6)
    kpi_row.setStyle(TableStyle([
        ("LEFTPADDING",   (0,0),(-1,-1), 1),
        ("RIGHTPADDING",  (0,0),(-1,-1), 1),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
    ]))
    elems.append(kpi_row)
    elems.append(Spacer(1, 4))

    # Selection % bar
    bar = _pct_bar(min(sel, 100), w=int(CW - 10), h=10)
    bar_lbl = PS(fontName="Helvetica", fontSize=7.5,
                 textColor=C_GREY_MID, alignment=TA_RIGHT)
    bar_sec = Table([
        [bar],
        [_P(f"Selection %: {sel:.1f}%  |  Rejection %: {row['rejection_pct']:.1f}%  |  Grade: {row['grade']}", bar_lbl)],
    ], colWidths=[CW - 6])
    bar_sec.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 1),
        ("LEFTPADDING",   (0,0),(-1,-1), 3),
        ("RIGHTPADDING",  (0,0),(-1,-1), 3),
    ]))
    elems.append(bar_sec)
    elems.append(Spacer(1, 8))

    # Breakdown tables — Product | Project | Collection | Location
    ddf = designer_raw[designer_raw["designer_name"] == row["designer_name"]]
    tw  = (CW - 10) / 4

    def _mini_tbl(df, group_col, val_col, hdr_label, w):
        if df.empty or group_col not in df.columns:
            return Spacer(w, 1)
        g = df.groupby(group_col)[val_col].sum().reset_index()\
              .sort_values(val_col, ascending=False).head(8)
        g = g[g[group_col].str.strip().ne("")]
        header = [hdr_label, "Qty"]
        rows   = [[str(r[group_col]).title()[:18], str(int(r[val_col]))]
                  for _, r in g.iterrows()]
        data   = [header] + rows
        t      = Table(data, colWidths=[w * 0.65, w * 0.35])
        t.setStyle(compact_table_style())
        return t

    prod_t = _mini_tbl(ddf, "product",    "qty", "Product",    tw)
    proj_t = _mini_tbl(ddf, "project",    "qty", "Project",    tw)
    coll_t = _mini_tbl(ddf, "collection", "qty", "Collection", tw)
    loc_t  = _mini_tbl(ddf, "location",   "qty", "Location",   tw)

    breakdown = Table([[prod_t, proj_t, coll_t, loc_t]], colWidths=[tw] * 4)
    breakdown.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 2),
        ("RIGHTPADDING", (0,0),(-1,-1), 2),
        ("TOPPADDING",   (0,0),(-1,-1), 2),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
    ]))
    elems.append(_section_hdr("PERFORMANCE BREAKDOWN — Product / Project / Collection / Location"))
    elems.append(breakdown)

    # ── PAGE 2: Complete Work Done List ────────────────────────────
    elems.append(PageBreak())
    elems.append(_page_title(
        f"COMPLETE WORK REGISTER — {name.upper()}",
        f"Total Jobs: {int(row['total_jobs'])}  |  Total Qty: {int(row['total_qty'])}  |  Selected: {int(row['selection_qty'])}  |  Rejected: {int(row['rejection_qty'])}"
    ))
    elems.append(Spacer(1, 6))

    hdrs = ["#", "Design No", "Date", "Product", "Project",
            "Collection", "Location", "Qty", "Sel Qty", "Rej Qty", "Approved"]
    cws  = [22, CW*0.12, 50, CW*0.10, CW*0.10,
            CW*0.15, 60, 35, 45, 45, 50]

    df_sorted = ddf.sort_values("date") if "date" in ddf.columns else ddf
    rows = []
    for i, (_, r) in enumerate(df_sorted.iterrows(), 1):
        date_str = r["date"].strftime("%d/%m/%Y") if "date" in r and pd.notna(r["date"]) else "—"
        approved = str(r.get("design_approved", "")).strip().upper()
        rows.append([
            str(i),
            str(r.get("design_no", ""))[:14],
            date_str,
            str(r.get("product", "")).title()[:12],
            str(r.get("project", "")).title()[:12],
            str(r.get("collection", "")).title()[:18],
            str(r.get("location", "")).title()[:10],
            str(int(r.get("qty", 0))),
            str(int(r.get("selection_qty", 0))) if "selection_qty" in r else "—",
            str(int(r.get("rejection_qty", 0))) if "rejection_qty" in r else "—",
            approved if approved in ("YES", "NO") else "—",
        ])

    # Totals row
    rows.append(["", "TOTALS", "", "", "", "", "",
                 str(int(row["total_qty"])), str(int(row["selection_qty"])),
                 str(int(row["rejection_qty"])), ""])

    work_tbl = Table([hdrs] + rows, colWidths=cws)
    ts = standard_table_style()
    ts.add("BACKGROUND", (0, len(rows)), (-1, len(rows)), C_NAVY)
    ts.add("TEXTCOLOR",  (0, len(rows)), (-1, len(rows)), C_GOLD)
    ts.add("FONTNAME",   (0, len(rows)), (-1, len(rows)), "Helvetica-Bold")
    work_tbl.setStyle(ts)
    elems.append(work_tbl)

    # ── PAGE 3: Products Checklist ──────────────────────────────────
    elems.append(PageBreak())
    elems.append(_page_title(
        f"PRODUCTS CHECKLIST — {name.upper()}",
        "All products worked on this period — for verification"
    ))
    elems.append(Spacer(1, 8))

    prod_summary = ddf.groupby("product").agg(
        jobs=("sno", "count"),
        total_qty=("qty", "sum"),
    ).reset_index().sort_values("total_qty", ascending=False)
    prod_summary = prod_summary[prod_summary["product"].str.strip().ne("")]

    p_hdrs = ["Product", "Jobs", "Total Qty", "Contribution %"]
    total_qty_all = prod_summary["total_qty"].sum()
    p_rows = []
    for _, r in prod_summary.iterrows():
        contrib = (r["total_qty"] / total_qty_all * 100) if total_qty_all > 0 else 0
        p_rows.append([
            r["product"].title(),
            str(int(r["jobs"])),
            str(int(r["total_qty"])),
            f"{contrib:.1f}%",
        ])
    p_rows.append(["TOTAL", str(int(prod_summary["jobs"].sum())),
                   str(int(total_qty_all)), "100.0%"])

    cws_p = [CW * 0.40, 70, 80, 80]
    p_tbl = Table([p_hdrs] + p_rows, colWidths=cws_p)
    ts2   = standard_table_style()
    ts2.add("BACKGROUND", (0, len(p_rows)), (-1, len(p_rows)), C_NAVY)
    ts2.add("TEXTCOLOR",  (0, len(p_rows)), (-1, len(p_rows)), C_GOLD)
    ts2.add("FONTNAME",   (0, len(p_rows)), (-1, len(p_rows)), "Helvetica-Bold")
    p_tbl.setStyle(ts2)
    elems.append(p_tbl)

    return elems


# ── Page header/footer ───────────────────────────────────────────

class _HF:
    def __init__(self, name, month, company):
        self.name = name; self.month = month; self.company = company

    def __call__(self, canvas, doc):
        from reportlab.lib.colors import HexColor
        canvas.saveState()
        w = PW
        canvas.setStrokeColor(C_GOLD)
        canvas.setLineWidth(1)
        canvas.line(MARGIN, 10*mm, w - MARGIN, 10*mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor("#78909C"))
        canvas.drawString(MARGIN, 7*mm,
                          f"{self.company}  |  {self.name}  |  {self.month}  |  Confidential")
        canvas.drawRightString(w - MARGIN, 7*mm, f"Page {doc.page}")
        canvas.restoreState()


# ── PUBLIC: generate all individual PDFs ─────────────────────────

def generate_individual_reports(data, output_dir):
    """
    Generate one PDF per designer (both CAD and Manual).
    Each PDF is named: Individual_<SafeName>_<ts>.pdf
    """
    month = data["reporting_month"]
    ts    = datetime.now().strftime("%Y%m%d_%H%M")
    os.makedirs(output_dir, exist_ok=True)
    generated = []

    # ── CAD designers ──
    cad     = data["cad_summary"]
    cad_raw = data["cad_raw"]

    for _, row in cad.iterrows():
        name     = row["cad_designer"].title()
        safe     = name.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "").strip()
        pdf_path = os.path.join(output_dir, f"Individual_CAD_{safe}_{ts}.pdf")

        hf  = _HF(name, month, COMPANY)
        cw  = PW - 2 * MARGIN
        ch  = PH - 2 * MARGIN - 8 * mm
        doc = BaseDocTemplate(
            pdf_path,
            pagesize=landscape(A4),
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=MARGIN,  bottomMargin=13*mm,
            title=f"Individual Report — {name} — {month}",
            author=COMPANY,
        )
        frame = Frame(MARGIN, 13*mm, cw, ch,
                      leftPadding=0, rightPadding=0,
                      topPadding=0,  bottomPadding=0, id="main")
        doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=hf)])
        story = _build_cad_individual(row, cad_raw, month)
        doc.build(story)
        print(f"[Individual] CAD: {pdf_path}")
        generated.append(pdf_path)

    # ── Manual designers ──
    manual       = data["manual_summary"]
    designer_raw = data["designer_raw"]

    for _, row in manual.iterrows():
        if not row["designer_name"].strip():
            continue
        name     = row["designer_name"].title()
        safe     = name.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "").strip()
        pdf_path = os.path.join(output_dir, f"Individual_Manual_{safe}_{ts}.pdf")

        hf  = _HF(name, month, COMPANY)
        cw  = PW - 2 * MARGIN
        ch  = PH - 2 * MARGIN - 8 * mm
        doc = BaseDocTemplate(
            pdf_path,
            pagesize=landscape(A4),
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=MARGIN,  bottomMargin=13*mm,
            title=f"Individual Report — {name} — {month}",
            author=COMPANY,
        )
        frame = Frame(MARGIN, 13*mm, cw, ch,
                      leftPadding=0, rightPadding=0,
                      topPadding=0,  bottomPadding=0, id="main")
        doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=hf)])
        story = _build_manual_individual(row, designer_raw, month)
        doc.build(story)
        print(f"[Individual] Manual: {pdf_path}")
        generated.append(pdf_path)

    return generated
