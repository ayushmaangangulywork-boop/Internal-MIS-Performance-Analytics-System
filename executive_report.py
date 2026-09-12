"""
executive_report.py  –  MAWSIM GOLD
Two one-page executive summaries:
  - build_cad_executive(data, analytics)   → CAD Department
  - build_manual_executive(data)           → Manual Department
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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from pdf_styles import (
    PS,
    C_NAVY, C_GOLD, C_GOLD_LIGHT, C_GREEN, C_GREEN_BG,
    C_RED, C_RED_BG, C_ORANGE, C_ORANGE_BG, C_BLUE, C_BLUE_LIGHT,
    C_GREY_DARK, C_WHITE, C_GREY_MID, C_ROW_EVEN, C_ROW_ODD,
    standard_table_style, compact_table_style,
)

PW, PH = landscape(A4)
MARGIN  = 10 * mm
CW      = PW - 2 * MARGIN


# ── helpers ──────────────────────────────────────────────────

def _P(text, style):
    return Paragraph(str(text), style)

def _fig_to_rl(fig, w, h):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return Image(buf, width=w, height=h)

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

def _kpi_row(items, w):
    """items = [(label, value, accent_hex)]"""
    n  = len(items)
    cw = (w - (n-1)*2) / n
    cells = []
    for label, value, accent in items:
        ac  = HexColor(accent)
        vs  = PS(fontName="Helvetica-Bold",
                 fontSize=14 if len(str(value)) <= 6 else 10,
                 textColor=ac, alignment=TA_CENTER)
        ls  = PS(fontName="Helvetica", fontSize=6.5,
                 textColor=C_GREY_DARK, alignment=TA_CENTER)
        inner = Table([[_P(str(value), vs)], [_P(label, ls)]],
                      colWidths=[cw-4])
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), HexColor("#F5F7FA")),
            ("TOPPADDING",    (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 3),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ]))
        card = Table([[inner]], colWidths=[cw], rowHeights=[36])
        card.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), HexColor("#F5F7FA")),
            ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#CCCCCC")),
            ("LINEBELOW",     (0,0),(-1,-1), 2.5, ac),
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
            ("LEFTPADDING",   (0,0),(-1,-1), 0),
            ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ]))
        cells.append(card)
    row = Table([cells], colWidths=[cw]*n)
    row.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 1),
        ("RIGHTPADDING", (0,0),(-1,-1), 1),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    return row

def _mini_bar_chart(names, values, title, w, h, color="#1A73C8"):
    fig, ax = plt.subplots(figsize=(w/72, h/72), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    y = np.arange(len(names))
    bars = ax.barh(y, values, color=color, height=0.55, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([str(n).title()[:14] for n in names], fontsize=6.5)
    ax.set_title(title, fontsize=8, fontweight="bold", color="#0D1B2A", pad=4)
    ax.tick_params(axis="x", labelsize=6)
    ax.tick_params(axis="y", length=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.grid(axis="x", color="#E8ECF0", linewidth=0.5)
    mx = max(values) if values else 1
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + mx*0.01, bar.get_y()+bar.get_height()/2,
                f"{v:.1f}" if isinstance(v, float) else str(int(v)),
                va="center", ha="left", fontsize=6.5, fontweight="bold", color="#0D1B2A")
    ax.set_xlim(0, mx * 1.2)
    fig.tight_layout(pad=0.4)
    return _fig_to_rl(fig, w, h)

def _donut_chart(pct, w=50, h=50):
    fig, ax = plt.subplots(figsize=(w/72, h/72), dpi=130)
    fig.patch.set_alpha(0)
    color  = "#2E7D32" if pct >= 80 else ("#E65100" if pct >= 50 else "#C62828")
    remain = max(0, 100-pct)
    ax.pie([min(pct,100), remain],
           colors=[color, "#E8ECEF"],
           startangle=90,
           wedgeprops={"width":0.38, "edgecolor":"white", "linewidth":0.8})
    ax.text(0, 0, f"{pct:.0f}%", ha="center", va="center",
            fontsize=8, fontweight="bold", color=color)
    ax.axis("equal")
    fig.tight_layout(pad=0)
    return _fig_to_rl(fig, w, h)

def _obs_table(lines, w):
    """Compact observations/recommendations block."""
    s = PS(fontName="Helvetica", fontSize=7, textColor=C_GREY_DARK,
           leading=10, spaceAfter=1)
    rows = [[_P(f"• {l}", s)] for l in lines]
    if not rows:
        return Spacer(w, 1)
    t = Table(rows, colWidths=[w-10])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#F5F7FA")),
        ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#CCCCCC")),
        ("LINEBEFORE",    (0,0),(0,-1),  3, C_GOLD),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
    ]))
    return t


# ══════════════════════════════════════════════════════════════
# CAD EXECUTIVE REPORT  (one page)
# ══════════════════════════════════════════════════════════════

def build_cad_executive(data, analytics=None):
    """Single-page executive summary for the CAD Design department."""
    elems = [PageBreak()]
    cad   = data["cad_summary"]
    raw   = data["cad_raw"]
    prod  = data["product_analysis"]
    proj  = data["project_analysis"]
    month = data["reporting_month"]

    # ── page title ────────────────────────────────────────────
    ts = PS(fontName="Helvetica-Bold", fontSize=14,
            textColor=C_WHITE, alignment=TA_CENTER)
    sub_s = PS(fontName="Helvetica", fontSize=8,
               textColor=C_GOLD_LIGHT, alignment=TA_CENTER)
    hdr = Table([
        [_P("CAD DESIGN DEPARTMENT  —  EXECUTIVE SUMMARY", ts)],
        [_P(f"Period: {month}   |   MAWSIM GOLD   |   Operations Intelligence", sub_s)],
    ], colWidths=[CW])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LINEBELOW",     (0,-1),(-1,-1), 2.5, C_GOLD),
    ]))
    elems.append(hdr)
    elems.append(Spacer(1, 5))

    if cad.empty:
        elems.append(_P("No CAD data available.", PS(fontName="Helvetica", fontSize=9, textColor=C_GREY_DARK)))
        return elems

    # ── KPI strip ─────────────────────────────────────────────
    t_pts    = round(cad["total_points"].sum(), 1)
    t_tgt    = round(cad["target"].sum(), 1)
    t_nod    = int(cad["total_nod"].sum())
    t_des    = int(cad["total_designs"].sum())
    ov_ach   = round((t_pts/t_tgt)*100, 1) if t_tgt else 0
    n_des    = len(cad)
    avg_pts  = round(t_pts/t_des, 3) if t_des else 0
    ach_col  = "#2E7D32" if ov_ach >= 80 else ("#E65100" if ov_ach >= 50 else "#C62828")

    kpis = [
        ("Designers",       n_des,          "#1565C0"),
        ("Total NOD",       t_nod,          "#E65100"),
        ("Points Earned",   t_pts,          "#283593"),
        ("Monthly Target",  t_tgt,          "#BF360C"),
        ("Achievement %",   f"{ov_ach}%",   ach_col),
        ("Avg Pts/Design",  avg_pts,        "#00695C"),
        ("Total Designs",   t_des,          "#4527A0"),
    ]
    elems.append(_kpi_row(kpis, CW))
    elems.append(Spacer(1, 5))

    # ── SECTION: 3-col layout ─────────────────────────────────
    # Left: designer performance table
    # Centre: achievement donut + top performers
    # Right: product + project mini charts
    L = CW * 0.38
    M = CW * 0.24
    R = CW * 0.38

    # LEFT — designer table
    elems.append(_banner("DESIGNER PERFORMANCE  |  PRODUCT ANALYSIS  |  PROJECT ANALYSIS", CW))
    elems.append(Spacer(1, 3))

    # Designer table data
    left_hdr = ["Designer", "NOD", "Pts", "Tgt", "Ach%", "Grade", "Status"]
    left_cw  = [L*0.30, L*0.10, L*0.12, L*0.12, L*0.12, L*0.12, L*0.12]
    left_rows = []
    for _, row in cad.iterrows():
        pct   = row["achievement_pct"]
        color = "#2E7D32" if pct >= 80 else ("#E65100" if pct >= 50 else "#C62828")
        ps    = PS(fontName="Helvetica", fontSize=6.5, textColor=HexColor(color))
        left_rows.append([
            _P(str(row["cad_designer"]).title()[:16],
               PS(fontName="Helvetica", fontSize=6.5, textColor=C_GREY_DARK)),
            _P(str(int(row["total_nod"])),  PS(fontName="Helvetica", fontSize=6.5, textColor=C_GREY_DARK, alignment=TA_CENTER)),
            _P(f"{row['total_points']:.1f}", PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=HexColor("#283593"), alignment=TA_CENTER)),
            _P(f"{row['target']:.0f}",       PS(fontName="Helvetica", fontSize=6.5, textColor=C_GREY_DARK, alignment=TA_CENTER)),
            _P(f"{pct:.1f}%",                PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=HexColor(color), alignment=TA_CENTER)),
            _P(str(row["grade"]),            PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=HexColor(color), alignment=TA_CENTER)),
            _P(str(row["status"]),           PS(fontName="Helvetica", fontSize=5.5, textColor=HexColor(color), alignment=TA_CENTER)),
        ])

    des_tbl = Table(
        [["Designer","NOD","Pts","Tgt","Ach%","Grade","Status"]] + left_rows,
        colWidths=left_cw
    )
    n_data = len(left_rows)
    style_cmds = [
        ("BACKGROUND",    (0,0),(-1,0),  C_NAVY),
        ("TEXTCOLOR",     (0,0),(-1,0),  C_WHITE),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,0),  7),
        ("ALIGN",         (0,0),(-1,0),  "CENTER"),
        ("BOTTOMPADDING", (0,0),(-1,0),  3),
        ("TOPPADDING",    (0,0),(-1,0),  3),
        ("LINEBELOW",     (0,0),(-1,0),  1.5, C_GOLD),
        ("FONTSIZE",      (0,1),(-1,-1), 6.5),
        ("BOTTOMPADDING", (0,1),(-1,-1), 2),
        ("TOPPADDING",    (0,1),(-1,-1), 2),
        ("GRID",          (0,0),(-1,-1), 0.3, HexColor("#CCCCCC")),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]
    for i in range(n_data):
        bg = C_ROW_EVEN if i%2==0 else HexColor("#EEF2F7")
        style_cmds.append(("BACKGROUND", (0,i+1),(-1,i+1), bg))
    des_tbl.setStyle(TableStyle(style_cmds))

    # CENTRE — donut + top/critical lists
    top3 = cad.head(3)[["cad_designer","achievement_pct","total_points"]].copy()
    cr   = cad[cad["achievement_pct"] < 50]

    donut = _donut_chart(ov_ach, w=int(M*0.7), h=int(M*0.7))

    cs = PS(fontName="Helvetica", fontSize=6.5, textColor=C_GREY_DARK, leading=10)
    cs_b = PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=C_GREY_DARK, leading=10)
    cs_g = PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=HexColor("#2E7D32"), leading=10)
    cs_r = PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=HexColor("#C62828"), leading=10)
    cs_lbl = PS(fontName="Helvetica-Bold", fontSize=7, textColor=C_NAVY, leading=10)

    mid_rows = [
        [_P("Overall Achievement", cs_lbl)],
        [donut],
        [_P("", cs)],
        [_P("TOP PERFORMERS:", cs_b)],
    ]
    for _, row in top3.iterrows():
        mid_rows.append([_P(f"  {row['cad_designer'].title()[:15]}  {row['achievement_pct']:.1f}%", cs_g)])
    if not cr.empty:
        mid_rows.append([_P("CRITICAL (<50%):", cs_r)])
        for _, row in cr.iterrows():
            mid_rows.append([_P(f"  {row['cad_designer'].title()[:15]}  {row['achievement_pct']:.1f}%", cs_r)])

    mid_tbl = Table(mid_rows, colWidths=[M-6])
    mid_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#F8FAFC")),
        ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#DDDDDD")),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ("RIGHTPADDING",  (0,0),(-1,-1), 4),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
    ]))

    # RIGHT — product bar + project bar
    rh_chart = 88
    if not prod.empty:
        ch_prod = _mini_bar_chart(
            prod["product"].tolist()[:8],
            prod["designs"].tolist()[:8],
            "Designs by Product", int(R-6), rh_chart, "#1A73C8")
    else:
        ch_prod = Spacer(R, rh_chart)

    if not proj.empty:
        ch_proj = _mini_bar_chart(
            proj["project"].tolist()[:6],
            proj["total_points"].tolist()[:6],
            "Points by Project", int(R-6), rh_chart, "#C9A84C")
    else:
        ch_proj = Spacer(R, rh_chart)

    right_tbl = Table([[ch_prod], [ch_proj]], colWidths=[R-4])
    right_tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))

    three_col = Table([[des_tbl, mid_tbl, right_tbl]], colWidths=[L, M, R])
    three_col.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 2),
        ("RIGHTPADDING", (0,0),(-1,-1), 2),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    elems.append(three_col)
    elems.append(Spacer(1, 5))

    # ── INSIGHTS + RECOMMENDATIONS ────────────────────────────
    elems.append(_banner("EXECUTIVE INSIGHTS  |  RISKS  |  MANAGEMENT RECOMMENDATIONS", CW))
    elems.append(Spacer(1, 3))

    obs_lines  = []
    rec_lines  = []

    if analytics:
        obs_lines = [o.text for o in analytics.observations[:6]]
        rec_lines = [f"[{r.priority}]  {r.action}" for r in analytics.recommendations[:5]]
    else:
        # Fallback: generate inline if analytics not passed
        if not cad.empty:
            top  = cad.iloc[0]
            avg  = cad["achievement_pct"].mean()
            bl   = cad[cad["achievement_pct"] < 80]
            cr_df = cad[cad["achievement_pct"] < 50]
            obs_lines.append(f"Overall dept achievement: {ov_ach:.1f}% | Team avg: {avg:.1f}%")
            obs_lines.append(f"Top performer: {top['cad_designer'].title()} — {top['achievement_pct']:.1f}% of target, {top['total_points']:.2f} pts")
            if not cr_df.empty:
                obs_lines.append(f"CRITICAL — {len(cr_df)} designer(s) below 50%: {', '.join(cr_df['cad_designer'].str.title())}")
            if len(bl) > 0:
                obs_lines.append(f"{len(bl)} designer(s) below 80% target — require monitoring and support")
            if not proj.empty:
                obs_lines.append(f"Top project: {proj.iloc[0]['project'].title()} — {proj.iloc[0]['contribution_pct']:.1f}% of dept output")
            if not prod.empty:
                obs_lines.append(f"Top product category: {prod.iloc[0]['product'].title()} — {int(prod.iloc[0]['designs'])} designs")

            if not cr_df.empty:
                rec_lines.append(f"[High]  Immediate review for {', '.join(cr_df['cad_designer'].str.title())} — under 50% of target")
            if len(bl) > 0:
                names = ', '.join(bl['cad_designer'].str.title())
                rec_lines.append(f"[Medium]  Weekly check-in for below-target designers: {names[:60]}")
            rec_lines.append(f"[Low]  Recognise top performer: {top['cad_designer'].title()} — set as benchmark for team")

    IW = CW / 2 - 4
    ins_tbl  = _obs_table(obs_lines,  IW)
    rec_tbl  = _obs_table(rec_lines,  IW)

    ir_row = Table([[ins_tbl, rec_tbl]], colWidths=[IW+4, IW+4])
    ir_row.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 2),
        ("RIGHTPADDING", (0,0),(-1,-1), 2),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    elems.append(ir_row)

    return elems


# ══════════════════════════════════════════════════════════════
# MANUAL EXECUTIVE REPORT  (one page)
# ══════════════════════════════════════════════════════════════

def build_manual_executive(data):
    """Single-page executive summary for the Manual Design department."""
    elems = [PageBreak()]
    man   = data["manual_summary"]
    raw   = data["designer_raw"]
    month = data["reporting_month"]

    # ── page title ────────────────────────────────────────────
    ts    = PS(fontName="Helvetica-Bold", fontSize=14,
               textColor=C_WHITE, alignment=TA_CENTER)
    sub_s = PS(fontName="Helvetica", fontSize=8,
               textColor=C_GOLD_LIGHT, alignment=TA_CENTER)
    hdr = Table([
        [_P("MANUAL DESIGN DEPARTMENT  —  EXECUTIVE SUMMARY", ts)],
        [_P(f"Period: {month}   |   MAWSIM GOLD   |   Operations Intelligence", sub_s)],
    ], colWidths=[CW])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LINEBELOW",     (0,-1),(-1,-1), 2.5, C_GOLD),
    ]))
    elems.append(hdr)
    elems.append(Spacer(1, 5))

    if man.empty:
        elems.append(_P("No manual designer data available.",
                        PS(fontName="Helvetica", fontSize=9, textColor=C_GREY_DARK)))
        return elems

    # ── KPIs ──────────────────────────────────────────────────
    t_qty  = int(man["total_qty"].sum())
    t_sel  = int(man["selection_qty"].sum())
    t_rej  = int(man["rejection_qty"].sum())
    t_jobs = int(man["total_jobs"].sum())
    n_des  = len(man)
    sel_pct = round(t_sel/t_qty*100, 1) if t_qty else 0
    rej_pct = round(t_rej/t_qty*100, 1) if t_qty else 0
    sel_col = "#2E7D32" if sel_pct >= 70 else ("#E65100" if sel_pct >= 50 else "#C62828")
    rej_col = "#2E7D32" if rej_pct < 20  else ("#E65100" if rej_pct < 35   else "#C62828")

    kpis = [
        ("Designers",       n_des,           "#1565C0"),
        ("Total Jobs",      t_jobs,          "#4527A0"),
        ("Total Qty",       t_qty,           "#E65100"),
        ("Selected",        t_sel,           "#2E7D32"),
        ("Rejected",        t_rej,           "#C62828"),
        ("Selection %",     f"{sel_pct}%",   sel_col),
        ("Rejection %",     f"{rej_pct}%",   rej_col),
    ]
    elems.append(_kpi_row(kpis, CW))
    elems.append(Spacer(1, 5))

    # ── 3-col layout ──────────────────────────────────────────
    L = CW * 0.40
    M = CW * 0.24
    R = CW * 0.36

    elems.append(_banner("DESIGNER PERFORMANCE  |  SELECTION ANALYSIS  |  PRODUCT & PROJECT BREAKDOWN", CW))
    elems.append(Spacer(1, 3))

    # LEFT — designer table
    left_cw = [L*0.30, L*0.12, L*0.12, L*0.12, L*0.16, L*0.12, L*0.06]
    left_rows = []
    for _, row in man.iterrows():
        sp = row["selection_pct"]; rp = row["rejection_pct"]
        sc = "#2E7D32" if sp >= 70 else ("#E65100" if sp >= 50 else "#C62828")
        rc = "#C62828" if rp > 30  else ("#E65100" if rp > 15  else "#2E7D32")
        ts_ = PS(fontName="Helvetica", fontSize=6.5, textColor=C_GREY_DARK)
        tc  = PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=HexColor(sc), alignment=TA_CENTER)
        tr  = PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=HexColor(rc), alignment=TA_CENTER)
        left_rows.append([
            _P(str(row["designer_name"]).title()[:16], ts_),
            _P(str(int(row["total_jobs"])), PS(fontName="Helvetica", fontSize=6.5, textColor=C_GREY_DARK, alignment=TA_CENTER)),
            _P(str(int(row["total_qty"])),  PS(fontName="Helvetica", fontSize=6.5, textColor=C_GREY_DARK, alignment=TA_CENTER)),
            _P(str(int(row["selection_qty"])), tc),
            _P(f"{sp:.1f}%", tc),
            _P(str(int(row["rejection_qty"])), tr),
            _P(str(row["grade"]), PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=HexColor(sc), alignment=TA_CENTER)),
        ])

    des_tbl = Table(
        [["Designer","Jobs","Qty","Sel","Sel%","Rej","Grd"]] + left_rows,
        colWidths=left_cw
    )
    n_d = len(left_rows)
    scmds = [
        ("BACKGROUND",    (0,0),(-1,0),  C_NAVY),
        ("TEXTCOLOR",     (0,0),(-1,0),  C_WHITE),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,0),  7),
        ("ALIGN",         (0,0),(-1,0),  "CENTER"),
        ("BOTTOMPADDING", (0,0),(-1,0),  3),
        ("TOPPADDING",    (0,0),(-1,0),  3),
        ("LINEBELOW",     (0,0),(-1,0),  1.5, C_GOLD),
        ("FONTSIZE",      (0,1),(-1,-1), 6.5),
        ("BOTTOMPADDING", (0,1),(-1,-1), 2),
        ("TOPPADDING",    (0,1),(-1,-1), 2),
        ("GRID",          (0,0),(-1,-1), 0.3, HexColor("#CCCCCC")),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]
    for i in range(n_d):
        bg = C_ROW_EVEN if i%2==0 else HexColor("#EEF2F7")
        scmds.append(("BACKGROUND", (0,i+1),(-1,i+1), bg))
    des_tbl.setStyle(TableStyle(scmds))

    # CENTRE — donut + top/bottom
    donut = _donut_chart(sel_pct, w=int(M*0.7), h=int(M*0.7))
    cs    = PS(fontName="Helvetica", fontSize=6.5, textColor=C_GREY_DARK, leading=10)
    cs_b  = PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=C_GREY_DARK, leading=10)
    cs_g  = PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=HexColor("#2E7D32"), leading=10)
    cs_r  = PS(fontName="Helvetica-Bold", fontSize=6.5, textColor=HexColor("#C62828"), leading=10)
    cs_lbl= PS(fontName="Helvetica-Bold", fontSize=7, textColor=C_NAVY, leading=10)

    top3_man = man.head(3)
    bot_man  = man[man["selection_pct"] < 50]
    mid_rows = [
        [_P("Selection Rate", cs_lbl)],
        [donut],
        [_P("", cs)],
        [_P("TOP DESIGNERS:", cs_b)],
    ]
    for _, row in top3_man.iterrows():
        mid_rows.append([_P(f"  {row['designer_name'].title()[:14]}  {row['selection_pct']:.1f}%", cs_g)])
    if not bot_man.empty:
        mid_rows.append([_P("NEEDS IMPROVEMENT:", cs_r)])
        for _, row in bot_man.iterrows():
            mid_rows.append([_P(f"  {row['designer_name'].title()[:14]}  {row['selection_pct']:.1f}%", cs_r)])

    mid_tbl = Table(mid_rows, colWidths=[M-6])
    mid_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#F8FAFC")),
        ("BOX",           (0,0),(-1,-1), 0.5, HexColor("#DDDDDD")),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ("RIGHTPADDING",  (0,0),(-1,-1), 4),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
    ]))

    # RIGHT — product + project bars (using manual data)
    rh_chart = 88
    if not raw.empty:
        prod_g = raw.groupby("product")["qty"].sum().sort_values(ascending=False).head(8)
        if not prod_g.empty:
            ch_prod = _mini_bar_chart(prod_g.index.tolist(), prod_g.values.tolist(),
                                      "Qty by Product", int(R-6), rh_chart, "#1A73C8")
        else:
            ch_prod = Spacer(R, rh_chart)

        proj_g = raw.groupby("project")["qty"].sum().sort_values(ascending=False).head(6)
        if not proj_g.empty:
            ch_proj = _mini_bar_chart(proj_g.index.tolist(), proj_g.values.tolist(),
                                      "Qty by Project", int(R-6), rh_chart, "#C9A84C")
        else:
            ch_proj = Spacer(R, rh_chart)
    else:
        ch_prod = ch_proj = Spacer(R, rh_chart)

    right_tbl = Table([[ch_prod], [ch_proj]], colWidths=[R-4])
    right_tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))

    three_col = Table([[des_tbl, mid_tbl, right_tbl]], colWidths=[L, M, R])
    three_col.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 2),
        ("RIGHTPADDING", (0,0),(-1,-1), 2),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    elems.append(three_col)
    elems.append(Spacer(1, 5))

    # ── INSIGHTS ──────────────────────────────────────────────
    elems.append(_banner("EXECUTIVE INSIGHTS  |  RISKS  |  MANAGEMENT RECOMMENDATIONS", CW))
    elems.append(Spacer(1, 3))

    obs_lines = []
    rec_lines = []
    if not man.empty:
        top_m   = man.iloc[0]
        avg_sel = man["selection_pct"].mean()
        low_m   = man[man["selection_pct"] < 50]
        obs_lines.append(f"Overall selection rate: {sel_pct:.1f}% | Rejection rate: {rej_pct:.1f}% | Dept avg selection: {avg_sel:.1f}%")
        obs_lines.append(f"Top performer: {top_m['designer_name'].title()} — {top_m['selection_pct']:.1f}% selection rate, {int(top_m['selection_qty'])} pieces selected")
        if not low_m.empty:
            obs_lines.append(f"Below 50% selection: {', '.join(low_m['designer_name'].str.title())} — quality review recommended")
        if t_rej > 0:
            obs_lines.append(f"Total {t_rej} pieces rejected this month — review rejection patterns by designer and product")
        if not raw.empty and "product" in raw.columns:
            top_prod = raw.groupby("product")["qty"].sum().idxmax()
            obs_lines.append(f"Highest volume product: {str(top_prod).title()} — review if aligned with business targets")

        if not low_m.empty:
            rec_lines.append(f"[High]  Quality review session for: {', '.join(low_m['designer_name'].str.title())}")
        if rej_pct > 30:
            rec_lines.append(f"[High]  Rejection rate {rej_pct:.1f}% exceeds 30% — audit design process and client brief quality")
        rec_lines.append(f"[Medium]  Review designs from top performer {top_m['designer_name'].title()} as quality benchmark")
        rec_lines.append(f"[Low]  Monitor and encourage consistent performance — team avg selection is {avg_sel:.1f}%")

    IW = CW / 2 - 4
    ins_tbl = _obs_table(obs_lines, IW)
    rec_tbl = _obs_table(rec_lines, IW)

    ir_row = Table([[ins_tbl, rec_tbl]], colWidths=[IW+4, IW+4])
    ir_row.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 2),
        ("RIGHTPADDING", (0,0),(-1,-1), 2),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    elems.append(ir_row)

    return elems
