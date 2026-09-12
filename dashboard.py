"""
dashboard.py  –  Executive MIS Dashboard  (Page 1, landscape A4)
BI quality: grouped bar charts, clean axes, data labels, tight layout.
"""

import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams
rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.color":        "#E8ECF0",
    "grid.linewidth":    0.6,
    "axes.axisbelow":    True,
})

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from pdf_styles import (
    PS,
    C_NAVY, C_GOLD, C_GOLD_LIGHT, C_BLUE, C_BLUE_LIGHT,
    C_GREEN, C_GREEN_BG, C_RED, C_RED_BG, C_ORANGE, C_ORANGE_BG,
    C_GREY_DARK, C_WHITE, C_GREY_MID, C_ROW_EVEN, C_ROW_ODD,
    get_styles, standard_table_style,
)
from insight_blocks import (
    section_header, dept_health_badge, observations_block,
    recommendations_block, pareto_summary,
)

PW, PH = landscape(A4)
MARGIN = 10 * mm
CW     = PW - 2 * MARGIN   # usable width ≈ 762 pt

# ── Colour palette (matches your reference graphs) ─────────────
BLU1 = "#1A73C8"   # light blue  (TARGET)
BLU2 = "#0D3B7A"   # dark blue   (CURRENT POINTS)
GRN  = "#2E7D32"
ORG  = "#E65100"
RED  = "#C62828"
GOLD = "#C9A84C"

BAR_PALETTE = ["#1A73C8","#C9A84C","#2E7D32","#E65100","#6A1B9A",
               "#00838F","#AD1457","#546E7A","#558B2F","#BF360C"]


# ─────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────

def _fig_to_rl(fig, w, h):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=w, height=h)


def _P(text, style):
    return Paragraph(str(text), style)


def _banner(text, w, bg=None):
    bg = bg or C_NAVY
    s = PS(fontName="Helvetica-Bold", fontSize=8.5,
                       textColor=C_WHITE, alignment=TA_LEFT)
    t = Table([[_P(f"  {text}", s)]], colWidths=[w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LINEBELOW",     (0,0),(-1,-1), 1.8, C_GOLD),
    ]))
    return t


# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────

def _header(company, month, generated_at, w):
    t1 = PS(fontName="Helvetica-Bold", fontSize=20,
                         textColor=C_WHITE, alignment=TA_CENTER)
    t2 = PS(fontName="Helvetica", fontSize=9,
                         textColor=C_GOLD_LIGHT, alignment=TA_CENTER)
    t3 = PS(fontName="Helvetica", fontSize=7.5,
                         textColor=HexColor("#90A4AE"), alignment=TA_CENTER)
    tbl = Table([
        [_P(company.upper(), t1)],
        [_P("Jewellery Design  |  MIS Dashboard", t2)],
        [_P(f"Period: {month}   |   Generated: {generated_at}", t3)],
    ], colWidths=[w])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LINEBELOW",     (0,-1),(-1,-1), 2.5, C_GOLD),
    ]))
    return tbl


# ─────────────────────────────────────────────────────────────
# KPI STRIP  (compact inline cards)
# ─────────────────────────────────────────────────────────────

def _kpi_strip(kpis, w):
    """kpis = list of (label, value, accent_hex).  Single row of mini-cards."""
    n = len(kpis)
    cw = (w - (n - 1) * 2) / n
    cells = []
    for label, value, accent in kpis:
        ac = HexColor(accent)
        val_s = PS(fontName="Helvetica-Bold",
                                fontSize=16 if len(str(value)) <= 5 else 12,
                                textColor=ac, alignment=TA_CENTER)
        lbl_s = PS(fontName="Helvetica", fontSize=6.5,
                                textColor=C_GREY_DARK, alignment=TA_CENTER)
        inner = Table([[_P(str(value), val_s)], [_P(label, lbl_s)]],
                      colWidths=[cw - 4])
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), HexColor("#F5F7FA")),
            ("TOPPADDING",    (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 3),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ]))
        card = Table([[inner]], colWidths=[cw], rowHeights=[40])
        card.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), HexColor("#F5F7FA")),
            ("BOX",          (0,0),(-1,-1), 0.5, HexColor("#CCCCCC")),
            ("LINEBELOW",    (0,0),(-1,-1), 2.5, ac),
            ("TOPPADDING",   (0,0),(-1,-1), 0),
            ("BOTTOMPADDING",(0,0),(-1,-1), 0),
            ("LEFTPADDING",  (0,0),(-1,-1), 0),
            ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ]))
        cells.append(card)

    row_tbl = Table([cells], colWidths=[cw] * n)
    row_tbl.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 1),
        ("RIGHTPADDING", (0,0),(-1,-1), 1),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    return row_tbl


# ─────────────────────────────────────────────────────────────
# CHART 1 – Grouped bar: Target vs Current Points (like your Page 4)
# ─────────────────────────────────────────────────────────────

def _chart_target_vs_points(names, targets, points, w, h):
    n   = len(names)
    x   = np.arange(n)
    bw  = 0.38

    fig, ax = plt.subplots(figsize=(w / 72, h / 72), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    b1 = ax.bar(x - bw/2, targets, bw, color=BLU1, label="Target",  zorder=3)
    b2 = ax.bar(x + bw/2, points,  bw, color=BLU2, label="Points Earned", zorder=3)

    # data labels
    for bar in b1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{bar.get_height():.1f}", ha="center", va="bottom",
                fontsize=5.5, color=BLU1, fontweight="bold")
    for bar in b2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{bar.get_height():.1f}", ha="center", va="bottom",
                fontsize=5.5, color=BLU2, fontweight="bold")

    ax.set_xticks(x)
    def _short(nm):
        parts = str(nm).strip().split()
        if not parts:
            return ""
        return parts[0] + ("\n" + parts[1] if len(parts) > 1 else "")
    ax.set_xticklabels([_short(nm) for nm in names], fontsize=6, rotation=0)
    ax.set_ylabel("Points", fontsize=7, color="#546E7A")
    ax.set_title("Target vs Points Earned by Designer", fontsize=9,
                 fontweight="bold", color="#0D1B2A", pad=6)
    ax.legend(fontsize=7, frameon=False, loc="upper right",
              ncol=2, handlelength=1.2)
    ax.tick_params(axis="y", labelsize=6.5)
    ax.tick_params(axis="x", length=0)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.set_ylim(0, max(max(targets), max(points)) * 1.25)
    fig.tight_layout(pad=0.5)
    return _fig_to_rl(fig, w, h)


# ─────────────────────────────────────────────────────────────
# CHART 2 – Horizontal bar: NOD by designer (like your Page 2 bottom)
# ─────────────────────────────────────────────────────────────

def _chart_nod_by_designer(names, nods, w, h):
    n = len(names)
    y = np.arange(n)

    fig, ax = plt.subplots(figsize=(w / 72, h / 72), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bars = ax.barh(y, nods, color=BAR_PALETTE[0], height=0.55, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7)
    ax.set_title("Designs (NOD) by Designer", fontsize=9,
                 fontweight="bold", color="#0D1B2A", pad=5)
    ax.set_xlabel("Number of Designs", fontsize=7, color="#546E7A")
    ax.tick_params(axis="x", labelsize=6.5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")

    mx = max(nods) if nods else 1
    for bar, v in zip(bars, nods):
        ax.text(bar.get_width() + mx * 0.015, bar.get_y() + bar.get_height()/2,
                str(int(v)), va="center", ha="left",
                fontsize=7, fontweight="bold", color="#0D1B2A")
    ax.set_xlim(0, mx * 1.18)
    fig.tight_layout(pad=0.5)
    return _fig_to_rl(fig, w, h)


# ─────────────────────────────────────────────────────────────
# CHART 3 – Vertical bar: NOD by Product (like your Page 2 top / Page 3)
# ─────────────────────────────────────────────────────────────

def _chart_nod_by_product(labels, values, w, h):
    n = len(labels)
    x = np.arange(n)

    fig, ax = plt.subplots(figsize=(w / 72, h / 72), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bars = ax.bar(x, values, color=BAR_PALETTE[:n], width=0.55,
                  edgecolor="white", linewidth=0.5, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([str(l).title() for l in labels], fontsize=6.5, rotation=15, ha="right")
    ax.set_ylabel("Count", fontsize=7, color="#546E7A")
    ax.set_title("Designs by Product", fontsize=9,
                 fontweight="bold", color="#0D1B2A", pad=5)
    ax.tick_params(axis="y", labelsize=6.5)
    ax.tick_params(axis="x", length=0)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    mx = max(values) if values else 1
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + mx * 0.01,
                str(int(v)), ha="center", va="bottom",
                fontsize=6.5, fontweight="bold", color="#0D1B2A")
    ax.set_ylim(0, mx * 1.22)
    fig.tight_layout(pad=0.5)
    return _fig_to_rl(fig, w, h)


# ─────────────────────────────────────────────────────────────
# CHART 4 – Vertical grouped: Designs by Project + Order Type
# ─────────────────────────────────────────────────────────────

def _chart_project_by_worktype(cad_raw, w, h):
    if cad_raw.empty:
        return Spacer(w, h)
    g = cad_raw.groupby(["project", "order_type"])["cad_design_no"].count().unstack(fill_value=0)
    projects = g.index.tolist()
    work_types = g.columns.tolist()
    x = np.arange(len(projects))
    bw = 0.8 / max(len(work_types), 1)

    fig, ax = plt.subplots(figsize=(w / 72, h / 72), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    for i, wt in enumerate(work_types):
        vals = g[wt].tolist()
        offset = (i - len(work_types)/2 + 0.5) * bw
        bars = ax.bar(x + offset, vals, bw * 0.9,
                      color=BAR_PALETTE[i % len(BAR_PALETTE)],
                      label=str(wt).title(), zorder=3)
        for bar, v in zip(bars, vals):
            if v > 0:
                ax.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + 1,
                        str(int(v)), ha="center", va="bottom",
                        fontsize=6, fontweight="bold", color="#0D1B2A")

    ax.set_xticks(x)
    ax.set_xticklabels([str(p).title() for p in projects], fontsize=7)
    ax.set_title("Designs by Project & Order Type", fontsize=9,
                 fontweight="bold", color="#0D1B2A", pad=5)
    ax.set_ylabel("Count", fontsize=7, color="#546E7A")
    ax.legend(fontsize=7, frameon=False, loc="upper right", ncol=2)
    ax.tick_params(axis="y", labelsize=6.5)
    ax.tick_params(axis="x", length=0)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    fig.tight_layout(pad=0.5)
    return _fig_to_rl(fig, w, h)


# ─────────────────────────────────────────────────────────────
# INSIGHTS BLOCK
# ─────────────────────────────────────────────────────────────

def _insights(data, w):
    cad  = data["cad_summary"]
    proj = data["project_analysis"]
    prod = data["product_analysis"]
    lines = []
    if not cad.empty:
        top  = cad.iloc[0]
        avg  = cad["achievement_pct"].mean()
        bl   = cad[cad["achievement_pct"] < 80]
        cr   = cad[cad["achievement_pct"] < 50]
        lines.append(f"Top Performer: {top['cad_designer'].title()} — {top['achievement_pct']:.1f}% of target")
        lines.append(f"Team Average Achievement: {avg:.1f}%")
        if not bl.empty:
            lines.append(f"Below 80% Target ({len(bl)}): {', '.join(bl['cad_designer'].str.title())}")
        if not cr.empty:
            lines.append(f"Critical <50% ({len(cr)}): {', '.join(cr['cad_designer'].str.title())}")
    if not proj.empty:
        bp = proj.iloc[0]
        lines.append(f"Best Project: {bp['project'].title()} ({bp['total_points']:.1f} pts, {bp['contribution_pct']:.0f}%)")
    if not prod.empty:
        tp = prod.iloc[0]
        lines.append(f"Top Product: {tp['product'].title()} — {int(tp['designs'])} designs")
    # recommendation
    if not cad.empty and not cad[cad["achievement_pct"] < 50].empty:
        cr = cad[cad["achievement_pct"] < 50]
        lines.append(f"Action Required: {', '.join(cr['cad_designer'].str.title())}")

    hdr_s = PS(fontName="Helvetica-Bold", fontSize=8,
                            textColor=C_NAVY, spaceAfter=3)
    row_s = PS(fontName="Helvetica", fontSize=7.5,
                            textColor=C_GREY_DARK, leading=11, spaceAfter=2)

    rows = [[_P("Management Insights", hdr_s)]]
    for l in lines:
        rows.append([_P(f"• {l}", row_s)])

    t = Table(rows, colWidths=[w - 8])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#F5F7FA")),
        ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#CCCCCC")),
        ("LINEBEFORE",    (0,0),(0,-1),  3, HexColor("#C9A84C")),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
    ]))
    return t


# ─────────────────────────────────────────────────────────────
# MAIN BUILDER
# ─────────────────────────────────────────────────────────────

def build_dashboard_elements(data, company="MAWSIM GOLD", analytics=None):
    elems = []
    cad  = data["cad_summary"]
    man  = data["manual_summary"]
    prod = data["product_analysis"]
    proj = data["project_analysis"]
    raw  = data["cad_raw"]

    # ── 1. HEADER ────────────────────────────────────────────
    elems.append(_header(company, data["reporting_month"],
                         data["generated_at"], CW))
    elems.append(Spacer(1, 4))

    # ── 2. KPI STRIP ─────────────────────────────────────────
    n_cad  = len(cad)  if not cad.empty  else 0
    n_man  = len(man)  if not man.empty  else 0
    t_nod  = int(cad["total_nod"].sum())        if not cad.empty else 0
    t_pts  = round(cad["total_points"].sum(), 1) if not cad.empty else 0
    t_des  = int(cad["total_designs"].sum())    if not cad.empty else 0
    t_tgt  = round(cad["target"].sum(), 1)      if not cad.empty else 0
    t_jobs = int(man["total_jobs"].sum())        if not man.empty else 0
    t_qty  = int(man["total_qty"].sum())         if not man.empty else 0
    ov_ach = round((t_pts / t_tgt) * 100, 1) if t_tgt else 0
    ach_color = "#2E7D32" if ov_ach >= 80 else ("#E65100" if ov_ach >= 50 else "#C62828")

    kpis = [
        ("CAD Designers",  n_cad,        "#1565C0"),
        ("Total NOD",      t_nod,        "#E65100"),
        ("Total Points",   t_pts,        "#283593"),
        ("CAD Designs",    t_des,        "#00695C"),
        ("Monthly Target", t_tgt,        "#BF360C"),
        ("Achievement %",  f"{ov_ach}%", ach_color),
    ]
    elems.append(_kpi_strip(kpis, CW))
    elems.append(Spacer(1, 4))

    # ── 2b. DEPT HEALTH BADGE + TOP OBSERVATIONS ──────────────
    if analytics is not None:
        elems.append(_banner("DEPARTMENT HEALTH  |  KEY OBSERVATIONS", CW))
        elems.append(Spacer(1, 3))
        elems.append(dept_health_badge(analytics, CW))
        elems.append(Spacer(1, 4))
        top_obs = analytics.observations[:4]
        if top_obs:
            elems.append(observations_block(top_obs, CW, max_show=4))
        elems.append(Spacer(1, 4))
    else:
        elems.append(Spacer(1, 5))

    # ── 3. ROW A: Grouped bar (Target vs Points) + NOD by Designer ──
    left_w = CW * 0.62
    rght_w = CW * 0.38
    rh_a   = 155

    elems.append(_banner("TARGET vs POINTS EARNED  |  DESIGNS BY DESIGNER", CW))

    if not cad.empty:
        names_s  = cad["cad_designer"].str.title().tolist()
        tgts_s   = cad["target"].tolist()
        pts_s    = cad["total_points"].tolist()
        nods_s   = cad["total_nod"].tolist()
        ch_grp   = _chart_target_vs_points(names_s, tgts_s, pts_s,
                                           int(left_w - 4), rh_a)
        ch_nod   = _chart_nod_by_designer(names_s[::-1], nods_s[::-1],
                                           int(rght_w - 4), rh_a)
    else:
        ch_grp = Spacer(left_w, rh_a)
        ch_nod = Spacer(rght_w, rh_a)

    row_a = Table([[ch_grp, ch_nod]], colWidths=[left_w, rght_w])
    row_a.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 2),
        ("RIGHTPADDING", (0,0),(-1,-1), 2),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
    ]))
    elems.append(row_a)
    elems.append(Spacer(1, 4))

    # ── 4. ROW B: Product bar | Project+WorkType | Insights ──
    p1_w = CW * 0.30
    p2_w = CW * 0.32
    p3_w = CW * 0.38
    rh_b = 115

    elems.append(_banner("DESIGNS BY PRODUCT  |  PROJECT & ORDER TYPE  |  INSIGHTS", CW))

    if not prod.empty:
        ch_prod = _chart_nod_by_product(
            prod["product"].str.title().tolist()[:9],
            prod["designs"].tolist()[:9],
            int(p1_w - 4), rh_b)
    else:
        ch_prod = Spacer(p1_w, rh_b)

    ch_proj = _chart_project_by_worktype(raw, int(p2_w - 4), rh_b)

    ins = _insights(data, p3_w)

    row_b = Table([[ch_prod, ch_proj, ins]], colWidths=[p1_w, p2_w, p3_w])
    row_b.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 2),
        ("RIGHTPADDING", (0,0),(-1,-1), 2),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ]))
    elems.append(row_b)

    return elems


# ─────────────────────────────────────────────────────────────
# MANUAL DEPARTMENT DASHBOARD  (Page 1 of Manual MIS PDF)
# ─────────────────────────────────────────────────────────────

def _chart_sel_by_designer(names, sel_pcts, w, h):
    """Horizontal bar — selection % per designer."""
    import numpy as np
    n = len(names)
    y = np.arange(n)
    fig, ax = plt.subplots(figsize=(w / 72, h / 72), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    colors = ["#2E7D32" if p >= 80 else ("#E65100" if p >= 50 else "#C62828") for p in sel_pcts]
    bars = ax.barh(y, sel_pcts, color=colors, height=0.55, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlim(0, 115)
    ax.set_xlabel("Selection %", fontsize=7, color="#546E7A")
    ax.set_title("Selection Rate by Designer", fontsize=9,
                 fontweight="bold", color="#0D1B2A", pad=5)
    ax.tick_params(axis="x", labelsize=6.5)
    ax.tick_params(axis="y", length=0)

    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    for bar, v in zip(bars, sel_pcts):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", ha="left",
                fontsize=7.5, fontweight="bold",
                color="#2E7D32" if v >= 80 else ("#E65100" if v >= 50 else "#C62828"))
    fig.tight_layout(pad=0.5)
    return _fig_to_rl(fig, w, h)


def _chart_qty_by_product(labels, sel_vals, rej_vals, w, h):
    """Grouped bar — selected vs rejected qty by product."""
    import numpy as np
    n  = len(labels)
    x  = np.arange(n)
    bw = 0.38
    fig, ax = plt.subplots(figsize=(w / 72, h / 72), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    b1 = ax.bar(x - bw / 2, sel_vals, bw, color="#2E7D32", label="Selected", zorder=3)
    b2 = ax.bar(x + bw / 2, rej_vals, bw, color="#C62828", label="Rejected",  zorder=3)
    for bar in b1:
        if bar.get_height() > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(int(bar.get_height())), ha="center", va="bottom",
                    fontsize=6, fontweight="bold", color="#2E7D32")
    for bar in b2:
        if bar.get_height() > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(int(bar.get_height())), ha="center", va="bottom",
                    fontsize=6, fontweight="bold", color="#C62828")
    ax.set_xticks(x)
    ax.set_xticklabels([str(l).title() for l in labels], fontsize=6.5, rotation=15, ha="right")
    ax.set_ylabel("Qty", fontsize=7, color="#546E7A")
    ax.set_title("Selected vs Rejected by Product", fontsize=9,
                 fontweight="bold", color="#0D1B2A", pad=5)
    ax.legend(fontsize=7, frameon=False, loc="upper right", ncol=2)
    ax.tick_params(axis="y", labelsize=6.5)
    ax.tick_params(axis="x", length=0)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    mx = max(max(sel_vals + [0]), max(rej_vals + [0]))
    ax.set_ylim(0, mx * 1.25 + 1)
    fig.tight_layout(pad=0.5)
    return _fig_to_rl(fig, w, h)


def _chart_qty_by_project(labels, qty_vals, w, h):
    """Horizontal bar — qty by project."""
    import numpy as np
    n = len(labels)
    y = np.arange(n)
    fig, ax = plt.subplots(figsize=(w / 72, h / 72), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    bars = ax.barh(y, qty_vals, color=BAR_PALETTE[1], height=0.55, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([str(l).title() for l in labels], fontsize=7.5)
    ax.set_title("Qty by Project", fontsize=9,
                 fontweight="bold", color="#0D1B2A", pad=5)
    ax.set_xlabel("Quantity", fontsize=7, color="#546E7A")
    ax.tick_params(axis="x", labelsize=6.5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    mx = max(qty_vals) if qty_vals else 1
    for bar, v in zip(bars, qty_vals):
        ax.text(bar.get_width() + mx * 0.015, bar.get_y() + bar.get_height() / 2,
                str(int(v)), va="center", ha="left",
                fontsize=7.5, fontweight="bold", color="#0D1B2A")
    ax.set_xlim(0, mx * 1.18)
    fig.tight_layout(pad=0.5)
    return _fig_to_rl(fig, w, h)


def _manual_insights(data, w):
    man = data["manual_summary"]
    raw = data.get("designer_raw")
    lines = []
    if not man.empty:
        t_qty  = int(man["total_qty"].sum())
        t_sel  = int(man["selection_qty"].sum())
        t_rej  = int(man["rejection_qty"].sum())
        sel_pct = round(t_sel / t_qty * 100, 1) if t_qty else 0
        avg_sel = man["selection_pct"].mean()
        top     = man.iloc[0]
        low     = man[man["selection_pct"] < 50]
        lines.append(f"Overall Selection Rate: {sel_pct:.1f}%  |  Avg: {avg_sel:.1f}%")
        lines.append(f"Top Performer: {top['designer_name'].title()}  —  {top['selection_pct']:.1f}% selection")
        lines.append(f"Total Qty: {t_qty}  |  Selected: {t_sel}  |  Rejected: {t_rej}")
        if not low.empty:
            lines.append(f"Needs Review: {', '.join(low['designer_name'].str.title())}")
        if raw is not None and not raw.empty and "product" in raw.columns:
            top_prod = raw.groupby("product")["qty"].sum().idxmax()
            lines.append(f"Highest Volume Product: {str(top_prod).title()}")
        lines.append("Action: Maintain 100% selection rate as quality benchmark")

    hdr_s = PS(fontName="Helvetica-Bold", fontSize=8,
               textColor=C_NAVY, spaceAfter=3)
    row_s = PS(fontName="Helvetica", fontSize=7.5,
               textColor=C_GREY_DARK, leading=11, spaceAfter=2)
    rows = [[_P("Management Insights", hdr_s)]]
    for l in lines:
        rows.append([_P(f"• {l}", row_s)])

    t = Table(rows, colWidths=[w - 8])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), HexColor("#F5F7FA")),
        ("BOX",           (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("LINEBEFORE",    (0, 0), (0, -1),  3, HexColor("#C9A84C")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def build_manual_dashboard(data, company="MAWSIM GOLD"):
    """Full-page professional dashboard for the Manual MIS PDF (page 1)."""
    elems = []
    man   = data["manual_summary"]
    raw   = data.get("designer_raw")

    # ── HEADER ──────────────────────────────────────────────
    t1 = PS(fontName="Helvetica-Bold", fontSize=20,
            textColor=C_WHITE, alignment=TA_CENTER)
    t2 = PS(fontName="Helvetica", fontSize=9,
            textColor=C_GOLD_LIGHT, alignment=TA_CENTER)
    t3 = PS(fontName="Helvetica", fontSize=7.5,
            textColor=HexColor("#90A4AE"), alignment=TA_CENTER)
    hdr = Table([
        [_P(company.upper(), t1)],
        [_P("Manual Design Department  |  MIS Dashboard", t2)],
        [_P(f"Period: {data['reporting_month']}   |   Generated: {data['generated_at']}", t3)],
    ], colWidths=[CW])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW",     (0, -1), (-1, -1), 2.5, C_GOLD),
    ]))
    elems.append(hdr)
    elems.append(Spacer(1, 4))

    # ── KPI STRIP ───────────────────────────────────────────
    if not man.empty:
        n_des   = len(man)
        t_jobs  = int(man["total_jobs"].sum())
        t_qty   = int(man["total_qty"].sum())
        t_sel   = int(man["selection_qty"].sum())
        t_rej   = int(man["rejection_qty"].sum())
        sel_pct = round(t_sel / t_qty * 100, 1) if t_qty else 0
        rej_pct = round(t_rej / t_qty * 100, 1) if t_qty else 0
        sel_col = "#2E7D32" if sel_pct >= 80 else ("#E65100" if sel_pct >= 50 else "#C62828")
    else:
        n_des = t_jobs = t_qty = t_sel = t_rej = 0
        sel_pct = rej_pct = 0.0
        sel_col = "#C62828"

    kpis = [
        ("Designers",   n_des,           "#1565C0"),
        ("Total Qty",   t_qty,           "#E65100"),
        ("Selected",    t_sel,           "#2E7D32"),
        ("Rejected",    t_rej,           "#C62828"),
        ("Selection %", f"{sel_pct}%",   sel_col),
        ("Rejection %", f"{rej_pct}%",   "#C62828" if rej_pct > 20 else "#2E7D32"),
    ]
    elems.append(_kpi_strip(kpis, CW))
    elems.append(Spacer(1, 4))

    # ── ROW A: Selection % by Designer + Qty by Project ─────
    left_w = CW * 0.55
    rght_w = CW * 0.45
    rh_a   = 155

    elems.append(_banner("SELECTION RATE BY DESIGNER  |  QTY BY PROJECT", CW))

    if not man.empty:
        names    = man["designer_name"].str.title().tolist()[::-1]
        sel_pcts = man["selection_pct"].tolist()[::-1]
        ch_sel   = _chart_sel_by_designer(names, sel_pcts, int(left_w - 4), rh_a)
    else:
        ch_sel = Spacer(left_w, rh_a)

    if raw is not None and not raw.empty and "project" in raw.columns:
        proj_g   = raw.groupby("project")["qty"].sum().sort_values(ascending=True)
        ch_proj  = _chart_qty_by_project(proj_g.index.tolist(), proj_g.values.tolist(),
                                          int(rght_w - 4), rh_a)
    else:
        ch_proj = Spacer(rght_w, rh_a)

    row_a = Table([[ch_sel, ch_proj]], colWidths=[left_w, rght_w])
    row_a.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))
    elems.append(row_a)
    elems.append(Spacer(1, 4))

    # ── ROW B: Product chart + Insights ─────────────────────
    p1_w = CW * 0.55
    p2_w = CW * 0.45
    rh_b = 118

    elems.append(_banner("QTY BY PRODUCT  |  INSIGHTS", CW))

    if raw is not None and not raw.empty and "product" in raw.columns:
        prod_g = raw.groupby("product")["qty"].sum().sort_values(ascending=False).head(8)
        ch_prod = _chart_qty_by_project(
            prod_g.index.str.title().tolist(),
            prod_g.values.tolist(),
            int(p1_w - 4), rh_b
        )
    else:
        ch_prod = Spacer(p1_w, rh_b)

    ins = _manual_insights(data, p2_w)

    row_b = Table([[ch_prod, ins]], colWidths=[p1_w, p2_w])
    row_b.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    elems.append(row_b)

    return elems
