"""
time_intelligence.py  —  MAWSIM GOLD
Time Intelligence Module  (NEW, fully independent).
Only uses records where time_taken has a valid numeric value.
Never modifies any existing report, ranking, KPI, or calculation.
"""

import io
import numpy as np
import pandas as pd
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
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from pdf_styles import (
    PS,
    C_NAVY, C_GOLD, C_GOLD_LIGHT, C_GREEN, C_GREEN_BG,
    C_RED, C_RED_BG, C_ORANGE, C_ORANGE_BG,
    C_BLUE, C_BLUE_LIGHT, C_GREY_DARK, C_WHITE, C_GREY_MID,
    C_ROW_EVEN, C_ROW_ODD, standard_table_style,
)

PW, PH  = landscape(A4)
MARGIN  = 10 * mm
CW      = PW - 2 * MARGIN

GOLD_HEX = "#C9A84C"
NAVY_HEX = "#0D1B2A"


# ─────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────

def _P(text, style):
    return Paragraph(str(text), style)


def _fig_to_rl(fig, w, h):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=w, height=h)


def _page_title(text):
    s = PS(fontName="Helvetica-Bold", fontSize=14,
                        textColor=C_WHITE, alignment=TA_CENTER)
    t = Table([[_P(text, s)]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LINEBELOW",     (0,0),(-1,-1), 2.5, C_GOLD),
    ]))
    return t


def _section_hdr(text, w=None):
    w = w or CW
    s = PS(fontName="Helvetica-Bold", fontSize=8.5,
                        textColor=C_WHITE, alignment=TA_LEFT)
    t = Table([[_P(f"  {text}", s)]], colWidths=[w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#1A2E45")),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LINEBELOW",     (0,0),(-1,-1), 1.5, C_GOLD),
    ]))
    return t


def _no_data_msg(reason: str):
    s = PS(fontName="Helvetica-Oblique", fontSize=9,
                        textColor=HexColor("#607D8B"), alignment=TA_CENTER)
    t = Table([[_P(reason, s)]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#F5F7FA")),
        ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0),(-1,-1), 18),
        ("BOTTOMPADDING", (0,0),(-1,-1), 18),
        ("LINEBEFORE",    (0,0),(0,-1),  3, C_GOLD),
    ]))
    return t


# ─────────────────────────────────────────────────────────────
# KPI TILE
# ─────────────────────────────────────────────────────────────

def _kpi_tile(label, value, accent, bg, w):
    vs = PS(fontName="Helvetica-Bold",
                         fontSize=14 if len(str(value)) <= 6 else 11,
                         textColor=HexColor(accent), alignment=TA_CENTER)
    ls = PS(fontName="Helvetica", fontSize=6.5,
                         textColor=C_GREY_DARK, alignment=TA_CENTER)
    inner = Table([[_P(str(value), vs)], [_P(label, ls)]], colWidths=[w - 6])
    inner.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor(bg)),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
    ]))
    card = Table([[inner]], colWidths=[w], rowHeights=[44])
    card.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), HexColor(bg)),
        ("BOX",          (0,0),(-1,-1), 0.5, HexColor("#CCCCCC")),
        ("LINEBELOW",    (0,0),(-1,-1), 2.5, HexColor(accent)),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
    ]))
    return card


def _kpi_strip(kpis, w):
    n  = len(kpis)
    cw = (w - (n-1)*2) / n
    cells = [_kpi_tile(lbl, val, ac, bg, cw) for lbl, val, ac, bg in kpis]
    row = Table([cells], colWidths=[cw]*n)
    row.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 1),
        ("RIGHTPADDING", (0,0),(-1,-1), 1),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    return row


# ─────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────

def _bar_h(labels, values, title, color, w, h, unit="hrs"):
    n = len(labels)
    fig, ax = plt.subplots(figsize=(w/72, h/72), dpi=140)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    y = np.arange(n)
    bars = ax.barh(y, values, color=color, height=0.52, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([str(l)[:18] for l in labels], fontsize=7)
    ax.set_title(title, fontsize=9, fontweight="bold", color=NAVY_HEX, pad=5)
    ax.set_xlabel(unit, fontsize=7, color="#546E7A")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#DDDDDD")
    ax.tick_params(axis="x", labelsize=6.5)
    ax.tick_params(axis="y", length=0)
    ax.xaxis.grid(True, color="#EEEEEE", linewidth=0.5, zorder=0)
    mx = max(values) if values else 1
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + mx*0.01, bar.get_y() + bar.get_height()/2,
                f"{v:.2f}", va="center", fontsize=6.5, fontweight="bold", color=NAVY_HEX)
    ax.set_xlim(0, mx * 1.18)
    fig.tight_layout(pad=0.5)
    return _fig_to_rl(fig, w, h)


def _bar_v(labels, values, title, color, w, h, unit="hrs"):
    n = len(labels)
    fig, ax = plt.subplots(figsize=(w/72, h/72), dpi=140)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    x = np.arange(n)
    bars = ax.bar(x, values, color=color, width=0.52,
                  edgecolor="white", linewidth=0.5, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([str(l)[:14] for l in labels],
                       fontsize=6.5, rotation=15, ha="right")
    ax.set_title(title, fontsize=9, fontweight="bold", color=NAVY_HEX, pad=5)
    ax.set_ylabel(unit, fontsize=7, color="#546E7A")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=6.5)
    ax.tick_params(axis="x", length=0)
    ax.yaxis.grid(True, color="#EEEEEE", linewidth=0.5, zorder=0)
    mx = max(values) if values else 1
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + mx*0.01,
                f"{v:.2f}", ha="center", va="bottom", fontsize=6.5,
                fontweight="bold", color=NAVY_HEX)
    ax.set_ylim(0, mx * 1.22)
    fig.tight_layout(pad=0.5)
    return _fig_to_rl(fig, w, h)


def _scatter_productivity(df_summary, w, h):
    """Scatter: designs on x, total_time on y, sized by points."""
    fig, ax = plt.subplots(figsize=(w/72, h/72), dpi=140)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    xs = df_summary["designs"].tolist()
    ys = df_summary["total_time"].tolist()
    sz = (df_summary["pts"].fillna(1) * 40).clip(20, 300).tolist()
    palette = ["#1A73C8","#C9A84C","#2E7D32","#E65100","#6A1B9A",
               "#00838F","#AD1457","#546E7A","#558B2F","#BF360C","#37474F","#0D47A1"]
    for i, (x, y, s, name) in enumerate(zip(xs, ys, sz, df_summary["name"].tolist())):
        ax.scatter(x, y, s=s, color=palette[i % len(palette)],
                   alpha=0.85, edgecolors="white", linewidth=0.8, zorder=3)
        ax.annotate(name[:10], (x, y), fontsize=6, ha="center",
                    xytext=(0, 6), textcoords="offset points", color=NAVY_HEX)
    ax.set_xlabel("Designs Completed", fontsize=7, color="#546E7A")
    ax.set_ylabel("Total Time (hrs)", fontsize=7, color="#546E7A")
    ax.set_title("Productivity vs Time by Designer", fontsize=9,
                 fontweight="bold", color=NAVY_HEX, pad=5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.xaxis.grid(True, color="#EEEEEE", linewidth=0.5, zorder=0)
    ax.yaxis.grid(True, color="#EEEEEE", linewidth=0.5, zorder=0)
    ax.tick_params(labelsize=6.5)
    fig.tight_layout(pad=0.5)
    return _fig_to_rl(fig, w, h)


# ─────────────────────────────────────────────────────────────
# ANALYTICS ENGINE  (time-specific, isolated)
# ─────────────────────────────────────────────────────────────

def _compute_time_analytics(df: pd.DataFrame) -> dict:
    """
    df = cad_raw filtered to rows with valid time_taken.
    Returns dict of aggregated stats. Pure computation, no side effects.
    """
    a = {}
    a["total_time"]      = round(df["time_taken"].sum(), 2)
    a["avg_per_design"]  = round(df["time_taken"].mean(), 3)
    a["median_design"]   = round(df["time_taken"].median(), 3)
    a["min_time"]        = round(df["time_taken"].min(), 3)
    a["max_time"]        = round(df["time_taken"].max(), 3)
    a["record_count"]    = len(df)

    # by designer
    des = df.groupby("cad_designer").agg(
        total_time=("time_taken", "sum"),
        avg_time=("time_taken", "mean"),
        designs=("cad_design_no", "count"),
        pts=("points", "sum"),
    ).reset_index().sort_values("total_time", ascending=False)
    des["avg_time"] = des["avg_time"].round(3)
    des["total_time"] = des["total_time"].round(2)
    a["by_designer"] = des

    # avg time per designer
    a["avg_per_designer"] = round(des["total_time"].mean(), 2) if not des.empty else 0

    # by product
    prod = df.groupby("product").agg(
        total_time=("time_taken", "sum"),
        avg_time=("time_taken", "mean"),
        designs=("cad_design_no", "count"),
    ).reset_index().sort_values("total_time", ascending=False)
    prod["avg_time"]   = prod["avg_time"].round(3)
    prod["total_time"] = prod["total_time"].round(2)
    prod["pct"] = (prod["total_time"] / a["total_time"] * 100).round(1) if a["total_time"] else 0
    a["by_product"] = prod

    # by project
    proj = df.groupby("project").agg(
        total_time=("time_taken", "sum"),
        avg_time=("time_taken", "mean"),
        designs=("cad_design_no", "count"),
    ).reset_index().sort_values("total_time", ascending=False)
    proj["avg_time"]   = proj["avg_time"].round(3)
    proj["total_time"] = proj["total_time"].round(2)
    proj["pct"] = (proj["total_time"] / a["total_time"] * 100).round(1) if a["total_time"] else 0
    a["by_project"] = proj

    # by collection
    coll = df.groupby("collection_name").agg(
        total_time=("time_taken", "sum"),
        avg_time=("time_taken", "mean"),
        designs=("cad_design_no", "count"),
    ).reset_index().sort_values("total_time", ascending=False)
    coll["avg_time"]   = coll["avg_time"].round(3)
    coll["total_time"] = coll["total_time"].round(2)
    coll["pct"] = (coll["total_time"] / a["total_time"] * 100).round(1) if a["total_time"] else 0
    a["by_collection"] = coll

    # Pareto — which products consume 80% of time?
    total = a["total_time"]
    prod_sorted = prod.sort_values("total_time", ascending=False).copy()
    prod_sorted["cum_pct"] = prod_sorted["total_time"].cumsum() / total * 100 if total else 0
    pareto_cut = prod_sorted[prod_sorted["cum_pct"].shift(1, fill_value=0) < 80]
    a["pareto_products"]    = pareto_cut["product"].str.title().tolist()
    a["pareto_time_pct"]    = round(pareto_cut["total_time"].sum() / total * 100, 1) if total else 0

    # fastest / slowest designer (by avg time per design)
    if not des.empty:
        a["fastest_designer"] = des.nsmallest(1, "avg_time").iloc[0]["cad_designer"].title()
        a["slowest_designer"] = des.nlargest(1, "avg_time").iloc[0]["cad_designer"].title()
        a["fastest_avg"]      = des.nsmallest(1, "avg_time").iloc[0]["avg_time"]
        a["slowest_avg"]      = des.nlargest(1, "avg_time").iloc[0]["avg_time"]
        a["most_time_designer"] = des.iloc[0]["cad_designer"].title()
    else:
        a["fastest_designer"] = a["slowest_designer"] = a["most_time_designer"] = ""
        a["fastest_avg"] = a["slowest_avg"] = 0

    # top time-consuming product
    if not prod.empty:
        a["top_time_product"]     = prod.iloc[0]["product"].title()
        a["top_time_product_pct"] = prod.iloc[0]["pct"]
        a["top_time_project"]     = proj.iloc[0]["project"].title() if not proj.empty else ""

    return a


# ─────────────────────────────────────────────────────────────
# OBSERVATIONS & RECOMMENDATIONS (dynamic, from completed data)
# ─────────────────────────────────────────────────────────────

def _generate_observations(a: dict, df: pd.DataFrame) -> list:
    obs = []
    total = a["total_time"]
    recs  = a["record_count"]
    prod  = a["by_product"]
    proj  = a["by_project"]
    des   = a["by_designer"]

    # overall
    obs.append(("info",
        f"Time analysis is based on {recs} completed design records "
        f"with recorded time data. Total time consumed: {total:.2f} hrs."))

    # product concentration
    if a.get("pareto_products"):
        obs.append(("warning" if len(a["pareto_products"]) <= 2 else "info",
            f"{', '.join(a['pareto_products'][:3])} account for approximately "
            f"{a['pareto_time_pct']:.0f}% of total design effort."))

    # top product
    if a.get("top_time_product"):
        obs.append(("info",
            f"{a['top_time_product']} designs consumed the most time "
            f"({a['by_product'].iloc[0]['pct']:.1f}% of total effort)."))

    # top project
    if a.get("top_time_project"):
        obs.append(("info",
            f"Project {a['top_time_project']} required the greatest design effort "
            f"({a['by_project'].iloc[0]['pct']:.1f}% of total time)."))

    # fastest / slowest
    if a.get("fastest_designer") and a.get("slowest_designer"):
        obs.append(("good",
            f"{a['fastest_designer']} had the lowest average completion time "
            f"per design ({a['fastest_avg']:.3f} hrs) — highest throughput efficiency."))
        if a["slowest_avg"] > a["fastest_avg"] * 2:
            obs.append(("warning",
                f"{a['slowest_designer']} averaged {a['slowest_avg']:.3f} hrs per design — "
                f"{round(a['slowest_avg'] / a['fastest_avg'], 1)}x slower than the fastest. "
                f"Review complexity of assigned work."))

    # designer with most total time
    if a.get("most_time_designer"):
        top_row = des.iloc[0]
        obs.append(("info",
            f"{a['most_time_designer']} spent the most total time "
            f"({top_row['total_time']:.2f} hrs across {int(top_row['designs'])} designs)."))

    # avg vs median gap
    avg = a["avg_per_design"]
    med = a["median_design"]
    if abs(avg - med) / (med if med else 1) > 0.3:
        obs.append(("warning",
            f"Average time per design ({avg:.3f} hrs) is significantly higher than "
            f"the median ({med:.3f} hrs) — a small number of complex designs are "
            f"skewing the average upward."))
    else:
        obs.append(("good",
            f"Average ({avg:.3f} hrs) and median ({med:.3f} hrs) time per design "
            f"are closely aligned — workload complexity is relatively consistent."))

    return obs


def _generate_recommendations(a: dict) -> list:
    recs = []

    if a.get("slowest_designer") and a.get("fastest_designer"):
        if a["slowest_avg"] > a["fastest_avg"] * 1.8:
            recs.append(("High",
                f"Review design assignments for {a['slowest_designer']}",
                f"Average completion time ({a['slowest_avg']:.3f} hrs/design) is "
                f"significantly above team average. Assess whether work complexity, "
                f"tool proficiency, or design type allocation is the root cause."))

    if a.get("pareto_products") and len(a["pareto_products"]) <= 2:
        names = ", ".join(a["pareto_products"])
        recs.append(("Medium",
            f"Optimise processes for high-effort products: {names}",
            f"These products consume the majority of design time. "
            f"Process improvements, templates, or tooling upgrades could "
            f"significantly reduce total effort."))

    if a.get("top_time_project"):
        recs.append(("Low",
            f"Evaluate time allocation for Project {a['top_time_project']}",
            f"This project requires the most design effort. Assess whether the "
            f"current time investment aligns with its business priority and revenue contribution."))

    if a["avg_per_design"] > 0.5:
        recs.append(("Medium",
            "Review design workflow for high-complexity pieces",
            f"Average time per design is {a['avg_per_design']:.3f} hrs. "
            f"Consider whether standard templates or reference libraries "
            f"could reduce average completion time."))

    return recs


# ─────────────────────────────────────────────────────────────
# OBSERVATION CARD RENDERER
# ─────────────────────────────────────────────────────────────

TAG_CFG = {
    "good":     ("#E8F5E9", "#2E7D32", "[+]"),
    "info":     ("#E3F2FD", "#1565C0", "[i]"),
    "warning":  ("#FFF8E1", "#E65100", "[!]"),
    "critical": ("#FFEBEE", "#C62828", "[X]"),
}


def _obs_card(tag, text, w):
    bg, fc, icon = TAG_CFG.get(tag, TAG_CFG["info"])
    icon_s = PS(fontName="Helvetica-Bold", fontSize=8,
                             textColor=HexColor(fc))
    body_s = PS(fontName="Helvetica", fontSize=7.8,
                             textColor=HexColor("#263238"), leading=11)
    t = Table([[_P(icon, icon_s), _P(text, body_s)]],
              colWidths=[12, w - 28])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor(bg)),
        ("BOX",           (0,0),(-1,-1), 0.5, HexColor(fc + "55")),
        ("LINEBEFORE",    (0,0),(0,-1),  3,   HexColor(fc)),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    outer = Table([[t]], colWidths=[w])
    outer.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))
    return outer


def _obs_grid(observations, w):
    half = (w - 6) / 2
    pairs = []
    for i in range(0, len(observations), 2):
        tag1, txt1 = observations[i]
        c1 = _obs_card(tag1, txt1, half)
        if i + 1 < len(observations):
            tag2, txt2 = observations[i+1]
            c2 = _obs_card(tag2, txt2, half)
        else:
            c2 = Spacer(half, 1)
        row = Table([[c1, c2]], colWidths=[half, half])
        row.setStyle(TableStyle([
            ("LEFTPADDING",  (0,0),(-1,-1), 0),
            ("RIGHTPADDING", (0,0),(-1,-1), 0),
            ("TOPPADDING",   (0,0),(-1,-1), 0),
            ("BOTTOMPADDING",(0,0),(-1,-1), 0),
            ("LEFTPADDING",  (1,0),(1,-1), 4),
        ]))
        pairs.append(row)
    return pairs


def _rec_table(recs, w):
    if not recs:
        return Spacer(w, 1)
    pri_colors = {"High": ("#FFEBEE","#C62828"),
                  "Medium": ("#FFF8E1","#E65100"),
                  "Low": ("#E8F5E9","#2E7D32")}
    hs  = PS(fontName="Helvetica-Bold", fontSize=7.5,
                          textColor=C_WHITE, alignment=TA_CENTER)
    as_ = PS(fontName="Helvetica-Bold", fontSize=7.5,
                          textColor=HexColor(NAVY_HEX), alignment=TA_LEFT)
    rs  = PS(fontName="Helvetica", fontSize=7.5,
                          textColor=HexColor("#37474F"), leading=10)
    cws = [48, w*0.30, w*0.54]
    rows = [[_P("Priority",hs), _P("Action",hs), _P("Rationale",hs)]]
    for pri, action, rationale in recs:
        bg, fc = pri_colors.get(pri, ("#F5F5F5","#555"))
        ps = PS(fontName="Helvetica-Bold", fontSize=7.5,
                             textColor=HexColor(fc), alignment=TA_CENTER)
        rows.append([_P(pri,ps), _P(action,as_), _P(rationale,rs)])
    t = Table(rows, colWidths=cws)
    cmds = [
        ("BACKGROUND",    (0,0),(-1,0), C_NAVY),
        ("LINEBELOW",     (0,0),(-1,0), 1.5, C_GOLD),
        ("GRID",          (0,0),(-1,-1), 0.3, HexColor("#CCCCCC")),
        ("FONTSIZE",      (0,0),(-1,-1), 7.5),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
        ("RIGHTPADDING",  (0,0),(-1,-1), 5),
    ]
    for i, (pri,_,__) in enumerate(recs, 1):
        bg, _ = pri_colors.get(pri, ("#F5F5F5","#555"))
        cmds.append(("BACKGROUND", (0,i),(0,i), HexColor(bg)))
        bg_r = "#FAFAFA" if i % 2 == 0 else "#EEF2F7"
        cmds.append(("BACKGROUND", (1,i),(-1,i), HexColor(bg_r)))
    t.setStyle(TableStyle(cmds))
    return t


# ─────────────────────────────────────────────────────────────
# DATA TABLE HELPER
# ─────────────────────────────────────────────────────────────

def _data_tbl(headers, rows, cws):
    t = Table([headers] + rows, colWidths=cws)
    t.setStyle(standard_table_style())
    return t


# ─────────────────────────────────────────────────────────────
# MAIN PUBLIC BUILDER
# ─────────────────────────────────────────────────────────────

def build_time_intelligence(data: dict) -> list:
    """
    Returns list of ReportLab flowables for the Time Intelligence section.
    Safe to call even when time_taken data is entirely missing.
    Never modifies data dict. Fully isolated from existing reports.
    """
    elems = [PageBreak()]

    cad_raw = data.get("cad_raw", pd.DataFrame())

    # ── Guard: no time_taken column or all blank ────────────
    if cad_raw.empty or "time_taken" not in cad_raw.columns:
        elems.append(_page_title("TIME INTELLIGENCE  —  MAWSIM GOLD"))
        elems.append(Spacer(1, 20))
        elems.append(_no_data_msg(
            "Time analysis is unavailable because no Time Taken data has been "
            "recorded for this period. Add the TIME TAKEN column to the CAD DATA "
            "SOURCE sheet to enable this module."))
        return elems

    df = cad_raw[cad_raw["time_taken"].notna()].copy()

    if df.empty:
        elems.append(_page_title("TIME INTELLIGENCE  —  MAWSIM GOLD"))
        elems.append(Spacer(1, 20))
        elems.append(_no_data_msg(
            "Time analysis is unavailable because no Time Taken data has been "
            "recorded for the selected period. All other reports remain unaffected."))
        return elems

    # ── Compute analytics ──────────────────────────────────
    a = _compute_time_analytics(df)

    # ── PAGE TITLE ─────────────────────────────────────────
    elems.append(_page_title("TIME INTELLIGENCE  —  MAWSIM GOLD"))
    elems.append(Spacer(1, 5))

    # ── KPI STRIP ──────────────────────────────────────────
    kpis = [
        ("Records Analysed",    a["record_count"],           "#1565C0", "#E3F2FD"),
        ("Total Time (hrs)",    f"{a['total_time']:.2f}",    "#0D3B7A", "#E8EAF6"),
        ("Avg / Design (hrs)",  f"{a['avg_per_design']:.3f}",  "#E65100", "#FFF8E1"),
        ("Median / Design",     f"{a['median_design']:.3f}", "#6A1B9A", "#F3E5F5"),
        ("Avg / Designer",      f"{a['avg_per_designer']:.2f}", "#2E7D32", "#E8F5E9"),
        ("Min Time",            f"{a['min_time']:.3f}",      "#00695C", "#E0F2F1"),
        ("Max Time",            f"{a['max_time']:.3f}",      "#BF360C", "#FFF3E0"),
    ]
    elems.append(_kpi_strip(kpis, CW))
    elems.append(Spacer(1, 6))

    # ── ROW A: Designer time bars (left) + Product time bars (right) ──
    lw = CW * 0.48
    rw = CW * 0.52
    rh = 150

    elems.append(_section_hdr("DESIGNER TIME ANALYSIS  |  PRODUCT TIME ANALYSIS"))

    des = a["by_designer"]
    prod = a["by_product"]

    ch_des = _bar_h(
        des["cad_designer"].str.title().tolist()[::-1],
        des["total_time"].tolist()[::-1],
        "Total Time by Designer (hrs)", "#1A73C8", int(lw-4), rh)

    ch_prod = _bar_v(
        prod["product"].str.title().tolist()[:9],
        prod["total_time"].tolist()[:9],
        "Total Time by Product (hrs)", "#C9A84C", int(rw-4), rh)

    row_a = Table([[ch_des, ch_prod]], colWidths=[lw, rw])
    row_a.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 2),
        ("RIGHTPADDING", (0,0),(-1,-1), 2),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ]))
    elems.append(row_a)
    elems.append(Spacer(1, 5))

    # ── ROW B: Avg time per product (left) + project time (mid) + scatter (right) ──
    bw1 = CW * 0.32
    bw2 = CW * 0.32
    bw3 = CW * 0.36
    rh2 = 120

    elems.append(_section_hdr("AVG TIME / PRODUCT  |  PROJECT EFFORT  |  PRODUCTIVITY vs TIME"))

    ch_avg_prod = _bar_h(
        prod["product"].str.title().tolist()[:8][::-1],
        prod["avg_time"].tolist()[:8][::-1],
        "Avg Time per Design by Product", "#2E7D32", int(bw1-4), rh2, "hrs/design")

    proj = a["by_project"]
    ch_proj = _bar_v(
        proj["project"].str.title().tolist(),
        proj["total_time"].tolist(),
        "Total Time by Project (hrs)", "#6A1B9A", int(bw2-4), rh2)

    scatter_data = des[["cad_designer","total_time","designs","pts"]].copy()
    scatter_data.columns = ["name","total_time","designs","pts"]
    ch_scatter = _scatter_productivity(scatter_data, int(bw3-4), rh2)

    row_b = Table([[ch_avg_prod, ch_proj, ch_scatter]], colWidths=[bw1, bw2, bw3])
    row_b.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 2),
        ("RIGHTPADDING", (0,0),(-1,-1), 2),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ]))
    elems.append(row_b)
    elems.append(Spacer(1, 5))

    # ── OBSERVATIONS ───────────────────────────────────────
    elems.append(PageBreak())
    elems.append(_page_title("TIME INTELLIGENCE  —  ANALYSIS & INSIGHTS"))
    elems.append(Spacer(1, 6))

    observations = _generate_observations(a, df)
    elems.append(_section_hdr("KEY OBSERVATIONS"))
    elems.append(Spacer(1, 3))
    elems += _obs_grid(observations, CW)
    elems.append(Spacer(1, 8))

    # ── DETAIL TABLES ──────────────────────────────────────
    elems.append(_section_hdr("DETAILED TIME TABLES"))
    elems.append(Spacer(1, 4))

    tw = (CW - 8) / 2

    # Designer table
    des_hdrs = ["Designer", "Total Time (hrs)", "Avg Time/Design", "Designs", "Points"]
    des_cws  = [tw*0.38, tw*0.18, tw*0.18, tw*0.13, tw*0.13]
    des_rows = []
    for _, r in des.iterrows():
        des_rows.append([
            r["cad_designer"].title(),
            f"{r['total_time']:.2f}",
            f"{r['avg_time']:.3f}",
            str(int(r["designs"])),
            f"{r['pts']:.2f}",
        ])
    des_tbl = _data_tbl(des_hdrs, des_rows, des_cws)

    # Product table
    prod_hdrs = ["Product", "Total Time (hrs)", "Avg Time/Design", "Designs", "% Share"]
    prod_cws  = [tw*0.36, tw*0.18, tw*0.18, tw*0.14, tw*0.14]
    prod_rows = []
    for _, r in prod.iterrows():
        prod_rows.append([
            r["product"].title(),
            f"{r['total_time']:.2f}",
            f"{r['avg_time']:.3f}",
            str(int(r["designs"])),
            f"{r['pct']:.1f}%",
        ])
    prod_tbl = _data_tbl(prod_hdrs, prod_rows, prod_cws)

    tables_row = Table([[des_tbl, prod_tbl]], colWidths=[tw, tw])
    tables_row.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("LEFTPADDING",  (1,0),(1,-1), 6),
    ]))
    elems.append(tables_row)
    elems.append(Spacer(1, 8))

    # Project + Collection tables
    lw2 = CW * 0.48
    rw2 = CW * 0.52

    proj_hdrs = ["Project", "Total Time (hrs)", "Avg Time/Design", "Designs", "% Share"]
    proj_cws  = [lw2*0.36, lw2*0.18, lw2*0.18, lw2*0.14, lw2*0.14]
    proj_rows = []
    for _, r in proj.iterrows():
        proj_rows.append([r["project"].title(), f"{r['total_time']:.2f}",
                          f"{r['avg_time']:.3f}", str(int(r["designs"])), f"{r['pct']:.1f}%"])
    proj_tbl = _data_tbl(proj_hdrs, proj_rows, proj_cws)

    coll = a["by_collection"]
    coll_hdrs = ["Collection", "Total Time (hrs)", "Avg Time/Design", "Designs", "% Share"]
    coll_cws  = [rw2*0.40, rw2*0.16, rw2*0.16, rw2*0.14, rw2*0.14]
    coll_rows = []
    for _, r in coll.iterrows():
        coll_rows.append([r["collection_name"].title(), f"{r['total_time']:.2f}",
                          f"{r['avg_time']:.3f}", str(int(r["designs"])), f"{r['pct']:.1f}%"])
    coll_tbl = _data_tbl(coll_hdrs, coll_rows, coll_cws)

    pc_row = Table([[proj_tbl, coll_tbl]], colWidths=[lw2, rw2])
    pc_row.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("LEFTPADDING",  (1,0),(1,-1), 6),
    ]))
    elems.append(pc_row)
    elems.append(Spacer(1, 8))

    # ── RECOMMENDATIONS ────────────────────────────────────
    recs = _generate_recommendations(a)
    if recs:
        elems.append(_section_hdr("MANAGEMENT RECOMMENDATIONS"))
        elems.append(Spacer(1, 3))
        elems.append(_rec_table(recs, CW))

    return elems
