"""
pdf_styles.py  —  MAWSIM GOLD
Shared colours, table styles. Compatible with ReportLab 5.x.
ROWBACKGROUNDS removed — alternating rows handled via explicit BACKGROUND commands.
"""

import uuid as _uuid
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import TableStyle

# ── Palette ───────────────────────────────────────────────────
C_NAVY       = HexColor("#0D1B2A")
C_NAVY2      = HexColor("#1A2E45")
C_GOLD       = HexColor("#C9A84C")
C_GOLD_LIGHT = HexColor("#F0D58C")
C_BLUE       = HexColor("#1565C0")
C_BLUE_LIGHT = HexColor("#E3F2FD")
C_GREEN      = HexColor("#2E7D32")
C_GREEN_BG   = HexColor("#E8F5E9")
C_RED        = HexColor("#C62828")
C_RED_BG     = HexColor("#FFEBEE")
C_ORANGE     = HexColor("#E65100")
C_ORANGE_BG  = HexColor("#FFF3E0")
C_GREY_DARK  = HexColor("#263238")
C_GREY_MID   = HexColor("#607D8B")
C_GREY_LIGHT = HexColor("#ECEFF1")
C_GREY_BG    = HexColor("#F5F7FA")
C_WHITE      = HexColor("#FFFFFF")
C_BLACK      = HexColor("#000000")
C_ROW_EVEN   = HexColor("#F8FAFC")
C_ROW_ODD    = HexColor("#EEF2F7")

STATUS_COLORS = {
    "On Track":          C_GREEN,
    "Below Target":      C_ORANGE,
    "Critical":          C_RED,
    "Excellent":         C_GREEN,
    "Good":              C_BLUE,
    "Needs Improvement": C_RED,
}


# ─────────────────────────────────────────────────────────────
# STYLE FACTORY  — unique name every call, no global collisions
# ─────────────────────────────────────────────────────────────

def PS(**kwargs) -> ParagraphStyle:
    """Create a ParagraphStyle with a guaranteed-unique name."""
    return ParagraphStyle(f"_s{_uuid.uuid4().hex[:10]}", **kwargs)


def get_styles():
    return {
        "section_header": PS(fontName="Helvetica-Bold", fontSize=9,
                              textColor=C_WHITE, alignment=TA_LEFT),
        "body":           PS(fontName="Helvetica", fontSize=8,
                              textColor=C_GREY_DARK, spaceAfter=2),
        "footer":         PS(fontName="Helvetica", fontSize=7,
                              textColor=C_GREY_MID, alignment=TA_CENTER),
    }


# ─────────────────────────────────────────────────────────────
# ALTERNATING ROW BACKGROUNDS  (ReportLab 5.x safe)
# ─────────────────────────────────────────────────────────────

def _alt_rows(num_data_rows: int,
              even_color=None, odd_color=None) -> list:
    """
    Returns explicit BACKGROUND commands for alternating rows.
    Only generates commands for rows that actually exist.
    num_data_rows MUST equal the actual number of data rows.
    """
    ev = even_color or C_ROW_EVEN
    od = odd_color  or C_ROW_ODD
    cmds = []
    for i in range(num_data_rows):
        row_idx = i + 1
        color   = ev if i % 2 == 0 else od
        cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), color))
    return cmds


def standard_table_style(header_bg=None, num_data_rows: int = 0):
    """
    Standard data table style.
    Pass num_data_rows=len(your_rows) to enable alternating row colours.
    Leave at 0 (default) to skip alternating rows — safe for any table size.
    """
    bg = header_bg or C_NAVY
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0),  bg),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  7.5),
        ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  4),
        ("TOPPADDING",    (0, 0), (-1, 0),  4),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.5, C_GOLD),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 7.5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
        ("TOPPADDING",    (0, 1), (-1, -1), 3),
        ("BACKGROUND",    (0, 1), (-1, -1), C_ROW_EVEN),
        ("GRID",          (0, 0), (-1, -1), 0.3, HexColor("#CCCCCC")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (1, 1), (-1, -1), "CENTER"),
    ]
    if num_data_rows > 0:
        cmds += _alt_rows(num_data_rows)
    return TableStyle(cmds)


def compact_table_style(header_bg=None, num_data_rows: int = 0):
    bg = header_bg or C_NAVY
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0),  bg),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  7),
        ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  3),
        ("TOPPADDING",    (0, 0), (-1, 0),  3),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.2, C_GOLD),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 2),
        ("TOPPADDING",    (0, 1), (-1, -1), 2),
        ("BACKGROUND",    (0, 1), (-1, -1), C_ROW_EVEN),
        ("GRID",          (0, 0), (-1, -1), 0.3, HexColor("#DDDDDD")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (1, 1), (-1, -1), "CENTER"),
    ]
    if num_data_rows > 0:
        cmds += _alt_rows(num_data_rows)
    return TableStyle(cmds)


def scorecard_section_style(num_data_rows: int = 0):
    return compact_table_style(C_NAVY2, num_data_rows)
