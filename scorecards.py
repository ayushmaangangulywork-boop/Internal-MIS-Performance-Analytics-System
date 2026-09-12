"""
scorecards.py  –  Designer Scorecards
2 CAD cards per page, compact BI layout.
"""

import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.platypus import (
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
    C_NAVY, C_GOLD, C_GOLD_LIGHT, C_GREEN, C_GREEN_BG, C_RED, C_RED_BG,
    C_ORANGE, C_ORANGE_BG, C_BLUE, C_BLUE_LIGHT, C_GREY_DARK,
    C_WHITE, C_GREY_MID, C_ROW_EVEN, C_ROW_ODD, STATUS_COLORS,
    get_styles, compact_table_style, scorecard_section_style,
)

PW, PH    = landscape(A4)
MARGIN    = 10 * mm
CW        = PW - 2 * MARGIN
CARD_W    = CW                    # full width
HALF_W    = (CW - 6) / 2         # two cards side by side


def _fig_to_rl(fig, w, h):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=w, height=h)


def _P(text, style):
    return Paragraph(str(text), style)


def _pct_bar(pct, w, h=7):
    color = C_GREEN if pct >= 80 else (C_ORANGE if pct >= 50 else C_RED)
    filled = max(2, min(pct / 100, 1.0)) * w
    empty  = w - filled
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


# ─────────────────────────────────────────────
# Mini sparkline: points vs target donut
# ─────────────────────────────────────────────

def _donut(pct, w=38, h=38):
    fig, ax = plt.subplots(figsize=(w/72, h/72), dpi=150)
    fig.patch.set_alpha(0)
    color  = "#2E7D32" if pct >= 80 else ("#E65100" if pct >= 50 else "#C62828")
    remain = max(0, 100 - pct)
    ax.pie([min(pct, 100), remain],
           colors=[color, "#E8ECEF"],
           startangle=90,
           wedgeprops={"width": 0.38, "edgecolor": "white", "linewidth": 0.8})
    ax.text(0, 0, f"{pct:.0f}%", ha="center", va="center",
            fontsize=7.5, fontweight="bold", color=color)
    ax.axis("equal")
    fig.tight_layout(pad=0)
    return _fig_to_rl(fig, w, h)


# ─────────────────────────────────────────────
# Breakdown mini table
# ─────────────────────────────────────────────

def _mini_tbl(df, group_col, val_col, hdr_label, w, count_col=None, val_hdr="Pts"):
    if df.empty or group_col not in df.columns:
        return Spacer(w, 1)

    if count_col:
        g = df.groupby(group_col).agg(
            cnt=(count_col, "count"),
            pts=(val_col, "sum")
        ).reset_index().sort_values("pts", ascending=False).head(7)
        header = [hdr_label, "Des", val_hdr]
        rows   = [[str(r[group_col]).title()[:16],
                   str(int(r["cnt"])),
                   f"{r['pts']:.2f}"] for _, r in g.iterrows()]
        cws = [w * 0.55, w * 0.20, w * 0.25]
    else:
        g = df.groupby(group_col)[val_col].sum().reset_index()\
              .sort_values(val_col, ascending=False).head(7)
        header = [hdr_label, val_hdr]
        rows   = [[str(r[group_col]).title()[:16],
                   str(int(r[val_col]))] for _, r in g.iterrows()]
        cws = [w * 0.62, w * 0.38]

    data = [header] + rows
    t = Table(data, colWidths=cws)
    t.setStyle(compact_table_style())
    return t


# ─────────────────────────────────────────────
# ONE CAD SCORECARD  (fits in HALF_W)
# ─────────────────────────────────────────────

def _cad_card(row, cad_raw):
    w    = CARD_W
    name = row["cad_designer"].title()
    pct  = row["achievement_pct"]
    stat = row["status"]
    stat_bg = C_GREEN if stat == "On Track" else (C_ORANGE if stat == "Below Target" else C_RED)

    # ── header ──
    n_s  = PS(fontName="Helvetica-Bold", fontSize=11,
                           textColor=C_WHITE, alignment=TA_LEFT)
    s_s  = PS(fontName="Helvetica", fontSize=7.5,
                           textColor=C_GOLD_LIGHT, alignment=TA_LEFT)
    r_s  = PS(fontName="Helvetica-Bold", fontSize=16,
                           textColor=C_GOLD, alignment=TA_RIGHT)
    st_s = PS(fontName="Helvetica-Bold", fontSize=8,
                           textColor=C_WHITE, alignment=TA_CENTER)

    left_cell = Table([
        [_P(name, n_s)],
        [_P(f"CAD Designer  |  Rank #{int(row['rank'])}", s_s)],
    ], colWidths=[w * 0.65])
    left_cell.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), C_NAVY),
        ("LEFTPADDING",(0,0),(-1,-1), 5),
        ("TOPPADDING", (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ]))
    mid_cell = Table([[_P(stat, st_s)]], colWidths=[w * 0.20])
    mid_cell.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), stat_bg),
        ("TOPPADDING",(0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("VALIGN",(0,0),(-1,-1), "MIDDLE"),
    ]))
    rk_cell = Table([[_P(f"#{int(row['rank'])}", r_s)]], colWidths=[w * 0.15])
    rk_cell.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), C_NAVY),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
    ]))
    hdr = Table([[left_cell, mid_cell, rk_cell]],
                colWidths=[w*0.65, w*0.20, w*0.15])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",(0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("LEFTPADDING",(0,0),(-1,-1), 0),
        ("RIGHTPADDING",(0,0),(-1,-1), 0),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LINEBELOW",(0,0),(-1,-1), 2, C_GOLD),
    ]))

    # ── 4 KPI tiles + donut ──
    def _kpi(label, val, accent, bg):
        v_s = PS(fontName="Helvetica-Bold",
                              fontSize=12 if len(str(val)) <= 5 else 10,
                              textColor=HexColor(accent), alignment=TA_CENTER)
        l_s = PS(fontName="Helvetica", fontSize=6.5,
                              textColor=C_GREY_DARK, alignment=TA_CENTER)
        t = Table([[_P(str(val), v_s)], [_P(label, l_s)]],
                  colWidths=[w * 0.18])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1), HexColor(bg)),
            ("TOPPADDING",(0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("BOX",(0,0),(-1,-1), 0.4, HexColor("#CCCCCC")),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ]))
        return t

    donut_img = _donut(min(pct, 100), w=40, h=40)
    donut_cell = Table([[donut_img]], colWidths=[w * 0.18])
    donut_cell.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), HexColor("#F5F7FA")),
        ("BOX",(0,0),(-1,-1), 0.4, HexColor("#CCCCCC")),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
    ]))

    kpi_row = Table([[
        _kpi("NOD",        int(row["total_nod"]),         "#1565C0", "#E3F2FD"),
        _kpi("Points",     f"{row['total_points']:.1f}",  "#283593", "#E8EAF6"),
        _kpi("Target",     f"{row['target']:.1f}",        "#E65100", "#FFF8E1"),
        _kpi("Remaining",  f"{row['remaining']:.1f}",     "#BF360C", "#FFF3E0"),
        donut_cell,
    ]], colWidths=[w * 0.18] * 5)
    kpi_row.setStyle(TableStyle([
        ("LEFTPADDING", (0,0),(-1,-1), 1),
        ("RIGHTPADDING",(0,0),(-1,-1), 1),
        ("TOPPADDING",  (0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
    ]))

    # ── progress bar ──
    bar = _pct_bar(min(pct, 100), w=int(w - 10), h=7)
    bar_lbl = PS(fontName="Helvetica", fontSize=6.5,
                              textColor=C_GREY_MID, alignment=TA_RIGHT)
    bar_sec = Table([
        [bar],
        [_P(f"Achievement: {pct:.1f}%  |  Contribution: {row['contribution_pct']:.1f}%", bar_lbl)],
    ], colWidths=[w - 6])
    bar_sec.setStyle(TableStyle([
        ("TOPPADDING",   (0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 1),
        ("LEFTPADDING",  (0,0),(-1,-1), 3),
        ("RIGHTPADDING", (0,0),(-1,-1), 3),
    ]))

    # ── breakdown tables ──
    ddf = cad_raw[cad_raw["cad_designer"] == row["cad_designer"]]
    tw  = (w - 10) / 3

    prod_t = _mini_tbl(ddf, "product",      "points", "Product",  tw, count_col="cad_design_no")
    proj_t = _mini_tbl(ddf, "project",      "points", "Project",  tw, count_col="cad_design_no")
    loc_t  = _mini_tbl(ddf, "cad_location", "points", "Location", tw, count_col="cad_design_no")

    breakdown = Table([[prod_t, proj_t, loc_t]], colWidths=[tw] * 3)
    breakdown.setStyle(TableStyle([
        ("LEFTPADDING", (0,0),(-1,-1), 2),
        ("RIGHTPADDING",(0,0),(-1,-1), 2),
        ("TOPPADDING",  (0,0),(-1,-1), 2),
        ("VALIGN",      (0,0),(-1,-1), "TOP"),
    ]))

    # ── Vinsmera vs Customer order type section ──
    ddf_v = ddf[ddf["order_type"].str.upper() == "VINSMERA"] if "order_type" in ddf.columns else ddf.iloc[0:0]
    ddf_c = ddf[ddf["order_type"].str.upper() == "CUSTOMER"] if "order_type" in ddf.columns else ddf.iloc[0:0]
    tot_pts = ddf["points"].sum() if not ddf.empty else 1
    v_pts   = ddf_v["points"].sum() if not ddf_v.empty else 0
    c_pts   = ddf_c["points"].sum() if not ddf_c.empty else 0
    v_des   = len(ddf_v)
    c_des   = len(ddf_c)
    v_pct   = (v_pts / tot_pts * 100) if tot_pts > 0 else 0
    c_pct   = (c_pts / tot_pts * 100) if tot_pts > 0 else 0

    # Order type header banner
    ot_hdr_s = PS(fontName="Helvetica-Bold", fontSize=7,
                  textColor=C_WHITE, alignment=TA_CENTER)
    ot_banner = Table([[_P("ORDER TYPE — VINSMERA  vs  CUSTOMER", ot_hdr_s)]], colWidths=[w - 6])
    ot_banner.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LINEBELOW",     (0,0),(-1,-1), 1, C_GOLD),
    ]))

    # 4 compact KPI tiles: VINSMERA Des | VINSMERA Pts | CUSTOMER Des | CUSTOMER Pts + split bar
    ot_tw = (w - 10) / 5
    def _ot_kpi(label, val, accent, bg):
        v_s = PS(fontName="Helvetica-Bold", fontSize=10,
                 textColor=HexColor(accent), alignment=TA_CENTER)
        l_s = PS(fontName="Helvetica", fontSize=6,
                 textColor=C_GREY_DARK, alignment=TA_CENTER)
        t = Table([[_P(str(val), v_s)], [_P(label, l_s)]], colWidths=[ot_tw])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), HexColor(bg)),
            ("TOPPADDING",    (0,0),(-1,-1), 3),
            ("BOTTOMPADDING", (0,0),(-1,-1), 3),
            ("BOX",           (0,0),(-1,-1), 0.4, HexColor("#CCCCCC")),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ]))
        return t

    split_lbl_s = PS(fontName="Helvetica-Bold", fontSize=8,
                     textColor=HexColor("#37474F"), alignment=TA_CENTER)
    split_sub_s = PS(fontName="Helvetica", fontSize=6,
                     textColor=C_GREY_MID, alignment=TA_CENTER)
    split_cell = Table([
        [_P(f"{v_pct:.0f}% / {c_pct:.0f}%", split_lbl_s)],
        [_P("VIN / CUST split", split_sub_s)],
    ], colWidths=[ot_tw])
    split_cell.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#ECEFF1")),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("BOX",           (0,0),(-1,-1), 0.4, HexColor("#CCCCCC")),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
    ]))

    ot_kpi_row = Table([[
        _ot_kpi("VIN Designs",  v_des,           "#6A1B9A", "#F3E5F5"),
        _ot_kpi("VIN Points",   f"{v_pts:.2f}",  "#7B1FA2", "#EDE7F6"),
        split_cell,
        _ot_kpi("CUST Designs", c_des,           "#1565C0", "#E3F2FD"),
        _ot_kpi("CUST Points",  f"{c_pts:.2f}",  "#1A237E", "#E8EAF6"),
    ]], colWidths=[ot_tw] * 5)
    ot_kpi_row.setStyle(TableStyle([
        ("LEFTPADDING",   (0,0),(-1,-1), 1),
        ("RIGHTPADDING",  (0,0),(-1,-1), 1),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
    ]))

    # Split bar — purple for VINSMERA, blue for CUSTOMER
    v_filled = max(2, (v_pct / 100) * (w - 10))
    c_filled = max(2, (w - 10) - v_filled)
    split_bar = Table([["", ""]], colWidths=[v_filled, c_filled], rowHeights=[6])
    split_bar.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,0), HexColor("#7B1FA2")),
        ("BACKGROUND",    (1,0),(1,0), HexColor("#1565C0")),
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))

    ot_section = Table([
        [ot_banner],
        [Spacer(1, 3)],
        [ot_kpi_row],
        [Spacer(1, 2)],
        [split_bar],
        [Spacer(1, 3)],
    ], colWidths=[w - 6])
    ot_section.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ("LEFTPADDING",   (0,0),(-1,-1), 3),
        ("RIGHTPADDING",  (0,0),(-1,-1), 3),
    ]))


    # ── Project vs Location — clean one-line strips ──────────
    def _clean_strip(title, groups, des_vals, pts_vals, total_pts, strip_w):
        """Single banner row + one KPI tile per group side by side."""
        title_s = PS(fontName="Helvetica-Bold", fontSize=7,
                     textColor=C_WHITE, alignment=TA_LEFT)
        grp_s   = PS(fontName="Helvetica-Bold", fontSize=7.5,
                     textColor=HexColor("#0D1B2A"), alignment=TA_CENTER)
        val_s   = PS(fontName="Helvetica-Bold", fontSize=9,
                     textColor=HexColor("#1565C0"), alignment=TA_CENTER)
        sub_s   = PS(fontName="Helvetica", fontSize=6,
                     textColor=HexColor("#78909C"), alignment=TA_CENTER)

        n      = max(len(groups), 1)
        lbl_w  = strip_w * 0.14
        tile_w = (strip_w - lbl_w) / n

        # Label tile (left)
        lbl_cell = Table([[_P(title, title_s)]], colWidths=[lbl_w], rowHeights=[32])
        lbl_cell.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ("LEFTPADDING",   (0,0),(-1,-1), 6),
            ("RIGHTPADDING",  (0,0),(-1,-1), 4),
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
            ("LINERIGHT",     (0,0),(0,0),   2, C_GOLD),
        ]))

        tiles = [lbl_cell]
        bgs   = ["#E8F5E9","#E3F2FD","#FFF8E1","#F3E5F5"]
        for i, (g, d, p) in enumerate(zip(groups, des_vals, pts_vals)):
            pct = round(p / total_pts * 100, 1) if total_pts else 0
            bg  = bgs[i % len(bgs)]
            cell = Table([
                [_P(str(g).title(), grp_s)],
                [_P(f"{d} des  ·  {p:.1f} pts", val_s)],
                [_P(f"{pct}% of total", sub_s)],
            ], colWidths=[tile_w - 2], rowHeights=[10, 14, 8])
            cell.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), HexColor(bg)),
                ("ALIGN",         (0,0),(-1,-1), "CENTER"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                ("TOPPADDING",    (0,0),(-1,-1), 1),
                ("BOTTOMPADDING", (0,0),(-1,-1), 1),
                ("LINEBEFORE",    (0,0),(0,-1),  0.5, HexColor("#CCCCCC")),
            ]))
            tiles.append(cell)

        row = Table([tiles], colWidths=[lbl_w] + [tile_w] * n)
        row.setStyle(TableStyle([
            ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#CCCCCC")),
            ("LINEBELOW",     (0,0),(-1,-1), 1.5, C_GOLD),
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
            ("LEFTPADDING",   (0,0),(-1,-1), 0),
            ("RIGHTPADDING",  (0,0),(-1,-1), 0),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        return row

    # Project strip — group by project, show all with data, title-cased
    _ddf_proj = ddf.copy()
    _ddf_proj["project"] = _ddf_proj["project"].str.strip().str.title()
    proj_agg = _ddf_proj[_ddf_proj["project"] != ""].groupby("project").agg(
        des=("cad_design_no","count"), pts=("points","sum")
    ).sort_values("pts", ascending=False)
    proj_groups = proj_agg.index.tolist()
    proj_des    = [int(v) for v in proj_agg["des"].tolist()]
    proj_pts    = [float(v) for v in proj_agg["pts"].tolist()]

    # Location strip — group by cad_location, title-cased
    _ddf_loc = ddf.copy()
    _ddf_loc["cad_location"] = _ddf_loc["cad_location"].str.strip().str.title()
    loc_agg = _ddf_loc[_ddf_loc["cad_location"] != ""].groupby("cad_location").agg(
        des=("cad_design_no","count"), pts=("points","sum")
    ).sort_values("pts", ascending=False)
    loc_groups = loc_agg.index.tolist()
    loc_des    = [int(v) for v in loc_agg["des"].tolist()]
    loc_pts    = [float(v) for v in loc_agg["pts"].tolist()]

    half_w = (w - 6) / 2
    proj_strip = _clean_strip("PROJECT",  proj_groups, proj_des, proj_pts, tot_pts, half_w)
    loc_strip  = _clean_strip("LOCATION", loc_groups,  loc_des,  loc_pts,  tot_pts, half_w)

    side_by_side = Table([[proj_strip, loc_strip]], colWidths=[half_w, half_w])
    side_by_side.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 3),
        ("RIGHTPADDING", (0,0),(-1,-1), 3),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
    ]))

    # ── assemble ──
    card = Table([
        [hdr],
        [Spacer(1, 2)],
        [kpi_row],
        [bar_sec],
        [Spacer(1, 2)],
        [breakdown],
        [Spacer(1, 4)],
        [ot_section],
        [Spacer(1, 4)],
        [side_by_side],
        [Spacer(1, 3)],
    ], colWidths=[w])
    card.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 0.8, HexColor("#CCCCCC")),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("LINEBELOW",    (0,-1),(-1,-1), 2, C_GOLD),
    ]))
    return card


# ─────────────────────────────────────────────
# Simple name-only breakdown table (no points)
# ─────────────────────────────────────────────

def _mini_tbl_simple(df, group_col, qty_col, hdr_label, w):
    """Two-column breakdown: group name + Qty. No Pts."""
    if df.empty or group_col not in df.columns:
        return Spacer(w, 1)
    g = df.groupby(group_col)[qty_col].sum().reset_index()           .sort_values(qty_col, ascending=False).head(7)
    from reportlab.lib.styles import ParagraphStyle as _PS
    from reportlab.lib.enums import TA_LEFT as _TAL, TA_CENTER as _TAC, TA_RIGHT as _TAR
    hdr_s  = _PS("mth",  fontName="Helvetica-Bold", fontSize=7, textColor=HexColor("#FFFFFF"), alignment=_TAL)
    hdr_n  = _PS("mthn", fontName="Helvetica-Bold", fontSize=7, textColor=HexColor("#FFFFFF"), alignment=_TAC)
    row_s  = _PS("mtr",  fontName="Helvetica",      fontSize=7, textColor=HexColor("#37474F"), alignment=_TAL)
    row_n  = _PS("mtrn", fontName="Helvetica-Bold", fontSize=7, textColor=HexColor("#1565C0"), alignment=_TAC)
    cw_name = w * 0.68
    cw_qty  = w * 0.28
    data = [[Paragraph(hdr_label, hdr_s), Paragraph("Qty", hdr_n)]]
    for _, r in g.iterrows():
        data.append([
            Paragraph(str(r[group_col]).title()[:20], row_s),
            Paragraph(str(int(r[qty_col])), row_n),
        ])
    t = Table(data, colWidths=[cw_name, cw_qty])
    n = len(data)
    cmds = [
        ("BACKGROUND",    (0, 0), (-1,  0), C_NAVY),
        ("LINEBELOW",     (0, 0), (-1,  0), 1.5, C_GOLD),
        ("GRID",          (0, 0), (-1, -1), 0.3, HexColor("#CCCCCC")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i in range(1, n):
        bg = HexColor("#F5F7FA") if i % 2 == 1 else HexColor("#EAEEF2")
        cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
    t.setStyle(TableStyle(cmds))
    return t


# ─────────────────────────────────────────────
# ONE MANUAL SCORECARD  (fits in HALF_W)
# ─────────────────────────────────────────────

def _manual_card(row, designer_raw):
    w    = CARD_W          # full page width – one card per page
    name = row["designer_name"].title()
    sel  = row["selection_pct"]
    stat = row["status"]
    stat_bg = C_GREEN if stat == "Excellent" else (C_BLUE if stat == "Good" else C_RED)

    n_s  = PS(fontName="Helvetica-Bold", fontSize=11,
                           textColor=C_WHITE, alignment=TA_LEFT)
    s_s  = PS(fontName="Helvetica", fontSize=7.5,
                           textColor=C_GOLD_LIGHT, alignment=TA_LEFT)
    st_s = PS(fontName="Helvetica-Bold", fontSize=8,
                           textColor=C_WHITE, alignment=TA_CENTER)

    left_cell = Table([
        [_P(name, n_s)],
        [_P(f"Manual Designer  |  Rank #{int(row['rank'])}", s_s)],
    ], colWidths=[w * 0.80])
    left_cell.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), C_NAVY),
        ("LEFTPADDING",(0,0),(-1,-1), 5),
        ("TOPPADDING",(0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ]))
    stat_cell = Table([[_P(stat, st_s)]], colWidths=[w * 0.20])
    stat_cell.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), stat_bg),
        ("TOPPADDING",(0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    hdr = Table([[left_cell, stat_cell]], colWidths=[w*0.80, w*0.20])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",(0,0),(-1,-1), 0),("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("LEFTPADDING",(0,0),(-1,-1), 0),("RIGHTPADDING",(0,0),(-1,-1), 0),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LINEBELOW",(0,0),(-1,-1), 2, C_GOLD),
    ]))

    def _kpi(label, val, accent, bg):
        v_s = PS(fontName="Helvetica-Bold",
                              fontSize=12 if len(str(val)) <= 5 else 10,
                              textColor=HexColor(accent), alignment=TA_CENTER)
        l_s = PS(fontName="Helvetica", fontSize=6.5,
                              textColor=C_GREY_DARK, alignment=TA_CENTER)
        t = Table([[_P(str(val), v_s)], [_P(label, l_s)]],
                  colWidths=[w * 0.20])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1), HexColor(bg)),
            ("TOPPADDING",(0,0),(-1,-1), 4),("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("BOX",(0,0),(-1,-1), 0.4, HexColor("#CCCCCC")),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ]))
        return t

    kpi_row = Table([[
        _kpi("Total Qty",   int(row["total_qty"]),    "#283593", "#E8EAF6"),
        _kpi("Selected",    int(row["selection_qty"]), "#2E7D32", "#E8F5E9"),
        _kpi("Rejected",    int(row["rejection_qty"]), "#C62828", "#FFEBEE"),
        _kpi("Sel %",       f"{sel:.1f}%",            "#2E7D32", "#E8F5E9"),
    ]], colWidths=[w*0.25]*4)
    kpi_row.setStyle(TableStyle([
        ("LEFTPADDING", (0,0),(-1,-1), 1),("RIGHTPADDING",(0,0),(-1,-1), 1),
        ("TOPPADDING",  (0,0),(-1,-1), 2),("BOTTOMPADDING",(0,0),(-1,-1), 2),
    ]))

    ddf = designer_raw[designer_raw["designer_name"] == row["designer_name"]]
    tw  = (w - 10) / 4
    prod_t = _mini_tbl_simple(ddf, "product",    "qty", "Product",    tw)
    proj_t = _mini_tbl_simple(ddf, "project",    "qty", "Project",    tw)
    coll_t = _mini_tbl_simple(ddf, "collection", "qty", "Collection", tw)
    loc_t  = _mini_tbl_simple(ddf, "location",   "qty", "Location",   tw)

    breakdown = Table([[prod_t, proj_t, coll_t, loc_t]], colWidths=[tw]*4)
    breakdown.setStyle(TableStyle([
        ("LEFTPADDING",(0,0),(-1,-1), 2),("RIGHTPADDING",(0,0),(-1,-1), 2),
        ("TOPPADDING", (0,0),(-1,-1), 2),("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))

    card = Table([
        [hdr],[Spacer(1,2)],[kpi_row],[Spacer(1,3)],[breakdown],[Spacer(1,3)],
    ], colWidths=[w])
    card.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1), 0.8, HexColor("#CCCCCC")),
        ("TOPPADDING",(0,0),(-1,-1), 0),("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("LEFTPADDING",(0,0),(-1,-1), 0),("RIGHTPADDING",(0,0),(-1,-1), 0),
        ("LINEBELOW",(0,-1),(-1,-1), 2, C_GOLD),
    ]))
    return card


# ─────────────────────────────────────────────
# PAGE TITLE BANNER
# ─────────────────────────────────────────────

def _page_title(text):
    s = PS(fontName="Helvetica-Bold", fontSize=13,
                        textColor=C_WHITE, alignment=TA_CENTER)
    t = Table([[Paragraph(text, s)]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",   (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LINEBELOW",    (0,0),(-1,-1), 2.5, C_GOLD),
    ]))
    return t


# ─────────────────────────────────────────────
# PUBLIC: CAD SCORECARDS  (2 per row)
# ─────────────────────────────────────────────

def build_cad_scorecards(data):
    cad     = data["cad_summary"]
    cad_raw = data["cad_raw"]
    if cad.empty:
        return []

    elems = [PageBreak(), _page_title("CAD DESIGNER SCORECARDS"), Spacer(1, 8)]

    # One designer per page — full width, PageBreak before each after the first
    for i, (_, row) in enumerate(cad.iterrows()):
        if i > 0:
            elems.append(PageBreak())
        elems.append(KeepTogether([_cad_card(row, cad_raw), Spacer(1, 6)]))

    return elems


# ─────────────────────────────────────────────
# PUBLIC: MANUAL SCORECARDS  (2 per row)
# ─────────────────────────────────────────────

def build_manual_scorecards(data):
    manual       = data["manual_summary"]
    designer_raw = data["designer_raw"]
    if manual.empty:
        return []

    elems = [PageBreak(), _page_title("MANUAL DESIGNER SCORECARDS"), Spacer(1, 8)]

    # One designer per page — full width card, PageBreak before each after the first
    for i, (_, row) in enumerate(manual.iterrows()):
        if i > 0:
            elems.append(PageBreak())
        elems.append(KeepTogether([_manual_card(row, designer_raw), Spacer(1, 6)]))

    return elems
