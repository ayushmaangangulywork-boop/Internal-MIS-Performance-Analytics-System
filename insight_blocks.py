"""
insight_blocks.py  -  MAWSIM GOLD
BI insight blocks for management reports.
Uses only Paragraphs (no nested Tables) for observations to avoid
ReportLab 5.x height computation issues.
"""

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from pdf_styles import (
    PS,
    C_NAVY, C_GOLD, C_GOLD_LIGHT, C_GREEN, C_GREEN_BG,
    C_RED, C_RED_BG, C_ORANGE, C_ORANGE_BG,
    C_BLUE, C_BLUE_LIGHT, C_GREY_DARK, C_WHITE,
    C_GREY_MID, C_GREY_LIGHT, C_ROW_EVEN, C_ROW_ODD,
)
from analytics import Analytics, Observation, Recommendation

PW, PH = landscape(A4)
MARGIN = 10 * mm
CW     = PW - 2 * MARGIN

PRIORITY_STYLES = {
    "High":   ("#FFEBEE", "#C62828"),
    "Medium": ("#FFF8E1", "#E65100"),
    "Low":    ("#E8F5E9", "#2E7D32"),
}

OBS_COLORS = {
    "good":     ("#E8F5E9", "#2E7D32"),
    "info":     ("#E3F2FD", "#1565C0"),
    "warning":  ("#FFF8E1", "#E65100"),
    "critical": ("#FFEBEE", "#C62828"),
}

OBS_PREFIX = {
    "good":    "GOOD",
    "info":    "INFO",
    "warning": "WARN",
    "critical":"CRIT",
}


def _P(text, style):
    return Paragraph(str(text), style)


# ─────────────────────────────────────────────────────────────
# SECTION HEADER
# ─────────────────────────────────────────────────────────────

def section_header(title: str, width: float = None) -> Table:
    w = width or CW
    s = PS(fontName="Helvetica-Bold", fontSize=9,
           textColor=C_WHITE, alignment=TA_LEFT)
    t = Table([[_P(f"  {title.upper()}", s)]], colWidths=[w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW",     (0, 0), (-1, -1), 2, C_GOLD),
    ]))
    return t


# ─────────────────────────────────────────────────────────────
# DEPT HEALTH BADGE  (flat single-row table, no nesting)
# ─────────────────────────────────────────────────────────────

def dept_health_badge(analytics: Analytics, width: float = None) -> Table:
    w    = width or CW
    h    = analytics.dept_health
    c    = HexColor(h.color)
    pct  = analytics.overall_ach_pct
    avg  = analytics.avg_ach_pct
    gap  = analytics.performance_gap
    prod = analytics.productivity_label

    HEALTH_BG = {
        "Excellent": "#C8E6C9", "Good": "#DCEDC8",
        "Moderate":  "#FFF9C4", "Poor": "#FFCCBC", "Critical": "#FFCDD2",
    }
    hbg = HexColor(HEALTH_BG.get(h.label, "#F5F7FA"))

    prod_c = "#2E7D32" if prod == "High" else ("#E65100" if prod == "Moderate" else "#C62828")
    gap_c  = "#C62828" if gap > 50 else ("#E65100" if gap > 30 else "#2E7D32")

    tw = (w - 12) / 7

    def _cell(label, val, ac):
        s1 = PS(fontName="Helvetica-Bold",
                fontSize=11 if len(str(val)) <= 6 else 9,
                textColor=HexColor(ac), alignment=TA_CENTER)
        s2 = PS(fontName="Helvetica", fontSize=6.5,
                textColor=C_GREY_DARK, alignment=TA_CENTER)
        tbl = Table([[_P(str(val), s1)], [_P(label, s2)]], colWidths=[tw])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), HexColor("#F5F7FA")),
            ("BOX",           (0, 0), (-1, -1), 0.5, HexColor("#DDDDDD")),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("LINEBELOW",     (0, -1), (-1, -1), 2.5, HexColor(ac)),
        ]))
        return tbl

    hs1 = PS(fontName="Helvetica-Bold", fontSize=11, textColor=c, alignment=TA_CENTER)
    hs2 = PS(fontName="Helvetica", fontSize=6.5, textColor=C_GREY_DARK, alignment=TA_CENTER)
    hcell = Table([[_P(h.label.upper(), hs1)], [_P("Dept. Health", hs2)]], colWidths=[tw])
    hcell.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), hbg),
        ("BOX",           (0, 0), (-1, -1), 1.5, c),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))

    cells = [
        hcell,
        _cell("Overall Ach.",  f"{pct:.1f}%",              h.color),
        _cell("Avg Ach.",       f"{avg:.1f}%",              h.color),
        _cell("Gap",            f"{gap:.1f}pp",             gap_c),
        _cell("Productivity",   prod,                       prod_c),
        _cell("Total Points",   f"{analytics.total_pts:.1f}", "#283593"),
        _cell("Total Target",   f"{analytics.total_target:.1f}", "#BF360C"),
    ]

    row = Table([cells], colWidths=[tw] * 7)
    row.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return row


# ─────────────────────────────────────────────────────────────
# OBSERVATIONS  — pure Paragraphs, NO nested tables
# ─────────────────────────────────────────────────────────────

def observations_block(observations: list, width: float = None,
                       max_show: int = 10) -> list:
    """
    Returns a list of Paragraph flowables.
    Each observation is a single styled Paragraph — no nested tables.
    This is the only safe approach in ReportLab 5.x.
    """
    w     = width or CW
    shown = observations[:max_show]
    result = []

    for obs in shown:
        bg, fc = OBS_COLORS.get(obs.tag, OBS_COLORS["info"])
        prefix = OBS_PREFIX.get(obs.tag, "INFO")
        s = PS(
            fontName="Helvetica", fontSize=8,
            textColor=HexColor(fc),
            backColor=HexColor(bg),
            borderPad=4,
            borderColor=HexColor(fc),
            borderWidth=0,
            leading=12,
            leftIndent=6,
            rightIndent=4,
            spaceAfter=3,
            spaceBefore=2,
        )
        result.append(_P(f"<b>[{prefix}]</b>  {obs.text}", s))

    return result


# ─────────────────────────────────────────────────────────────
# RECOMMENDATIONS TABLE
# ─────────────────────────────────────────────────────────────

def recommendations_block(recs: list, width: float = None) -> Table:
    w = width or CW
    if not recs:
        return Spacer(w, 1)

    hdr_s = PS(fontName="Helvetica-Bold", fontSize=7.5,
               textColor=C_WHITE, alignment=TA_CENTER)
    act_s = PS(fontName="Helvetica-Bold", fontSize=7.5,
               textColor=HexColor("#0D1B2A"))
    rat_s = PS(fontName="Helvetica", fontSize=7.5,
               textColor=HexColor("#37474F"), leading=10)

    cws  = [48, w * 0.30, w * 0.54]
    rows = [[_P("Priority", hdr_s),
             _P("Recommended Action", hdr_s),
             _P("Rationale", hdr_s)]]

    for r in recs:
        bg, fc = PRIORITY_STYLES.get(r.priority, ("#F5F5F5", "#777"))
        ps = PS(fontName="Helvetica-Bold", fontSize=7.5,
                textColor=HexColor(fc), alignment=TA_CENTER)
        rows.append([_P(r.priority, ps), _P(r.action, act_s), _P(r.rationale, rat_s)])

    tbl = Table(rows, colWidths=cws)
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), C_NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), C_WHITE),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.5, C_GOLD),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("GRID",          (0, 0), (-1, -1), 0.3, HexColor("#CCCCCC")),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ]
    for i, r in enumerate(recs, 1):
        bg, _ = PRIORITY_STYLES.get(r.priority, ("#F5F5F5", "#777"))
        row_bg = "#FAFAFA" if i % 2 == 0 else "#EEF2F7"
        cmds.append(("BACKGROUND", (0, i), (0, i),  HexColor(bg)))
        cmds.append(("BACKGROUND", (1, i), (-1, i), HexColor(row_bg)))
    tbl.setStyle(TableStyle(cmds))
    return tbl


# ─────────────────────────────────────────────────────────────
# PARETO SUMMARY
# ─────────────────────────────────────────────────────────────

def pareto_summary(analytics: Analytics, width: float = None) -> Table:
    w = width or CW
    s = PS(fontName="Helvetica", fontSize=8,
           textColor=HexColor("#263238"), leading=12)
    names_str = ", ".join(analytics.pareto_designers[:5])
    if len(analytics.pareto_designers) > 5:
        names_str += f" (+{len(analytics.pareto_designers)-5} more)"
    text = (
        f"<b>Pareto (80/20 Rule):</b>  "
        f"{len(analytics.pareto_designers)} designer(s) — <b>{names_str}</b> — "
        f"account for 80% of total points output.  "
        f"Top-2 alone: <b>{analytics.top2_contribution:.1f}%</b> of output."
    )
    t = Table([[_P(text, s)]], colWidths=[w - 12])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), HexColor("#FFF8E1")),
        ("BOX",           (0, 0), (-1, -1), 0.5, HexColor("#C9A84C")),
        ("LINEBEFORE",    (0, 0), (0, -1),  3,   C_GOLD),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ─────────────────────────────────────────────────────────────
# DESIGNER COMMENTARY
# ─────────────────────────────────────────────────────────────

def designer_commentary(text: str, width: float = None) -> Table:
    w = width or CW
    s = PS(fontName="Helvetica-Oblique", fontSize=7.8,
           textColor=HexColor("#37474F"), leading=11)
    t = Table([[_P(f'"{text}"', s)]], colWidths=[w - 16])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), HexColor("#F8F9FA")),
        ("BOX",           (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("LINEBEFORE",    (0, 0), (0, -1),  3,   C_GOLD),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


# ─────────────────────────────────────────────────────────────
# FULL INSIGHTS SECTION ASSEMBLER
# ─────────────────────────────────────────────────────────────

def full_insights_section(
    analytics: Analytics,
    title: str = "Analysis & Management Insights",
    width: float = None,
    show_health: bool = True,
    show_pareto: bool = True,
    max_obs: int = 10,
    max_recs: int = 6,
) -> list:
    w     = width or CW
    elems = []

    sub_s = PS(fontName="Helvetica-Bold", fontSize=8.5,
               textColor=C_NAVY, spaceAfter=4)

    elems.append(Spacer(1, 6))
    elems.append(section_header(title, w))
    elems.append(Spacer(1, 5))

    if show_health and analytics.dept_health is not None:
        elems.append(dept_health_badge(analytics, w))
        elems.append(Spacer(1, 6))

    if show_pareto and analytics.pareto_designers:
        elems.append(pareto_summary(analytics, w))
        elems.append(Spacer(1, 6))

    obs = analytics.observations[:max_obs]
    if obs:
        elems.append(_P("Key Observations", sub_s))
        elems.extend(observations_block(obs, w))
        elems.append(Spacer(1, 6))

    recs = analytics.recommendations[:max_recs]
    if recs:
        elems.append(_P("Management Recommendations", sub_s))
        elems.append(Spacer(1, 2))
        elems.append(recommendations_block(recs, w))

    return elems
