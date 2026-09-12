"""
reports.py
All analysis and ranking report builders:
  - CAD Ranking, Manual Ranking
  - Project, Collection, Product, Location, Work Type Analysis
  - Target Achievement Report
  - Monthly Work Register
  - Management Summary
"""
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import pandas as pd

from pdf_styles import (
    PS,
    C_NAVY, C_GOLD, C_GOLD_LIGHT, C_GREEN, C_GREEN_BG, C_RED, C_RED_BG,
    C_ORANGE, C_ORANGE_BG, C_BLUE, C_BLUE_LIGHT, C_GREY_DARK, C_GREY_LIGHT,
    C_WHITE, C_GREY_MID, C_ROW_EVEN, C_ROW_ODD,
    get_styles, standard_table_style
)
import insight_blocks as _ib

PAGE_W, PAGE_H = landscape(A4)
MARGIN = 14 * mm
CW = PAGE_W - 2 * MARGIN


# ── shared helpers ────────────────────────────

def _page_title(text):
    s = PS(fontName="Helvetica-Bold", fontSize=16,
                        textColor=C_WHITE, alignment=TA_CENTER)
    t = Table([[Paragraph(text, s)]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LINEBELOW",     (0,0),(-1,-1), 3, C_GOLD),
    ]))
    return t


def _section_hdr(text, width=None):
    if width is None:
        width = CW
    s = PS(fontName="Helvetica-Bold", fontSize=9,
                        textColor=C_WHITE, alignment=TA_LEFT)
    t = Table([[Paragraph(f"  {text}", s)]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LINEBELOW",     (0,0),(-1,-1), 2, C_GOLD),
    ]))
    return t


def _data_table(headers, rows, col_widths):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths)
    t.setStyle(standard_table_style())
    return t


# ── 1. CAD Designer Ranking ───────────────────

def build_cad_ranking(data):
    cad = data["cad_summary"]
    elems = [PageBreak(), _page_title("CAD DESIGNER RANKING"), Spacer(1, 10)]
    if cad.empty:
        elems.append(Paragraph("No CAD data.", get_styles()["body"]))
        return elems

    hdrs = ["Rank", "Designer Name", "NOD", "Total Points", "Target",
            "Remaining", "Achievement %", "Contribution %", "Status"]
    cws  = [28, CW*0.24, 30, 55, 45, 50, 60, 60, 70]
    rows = []
    for _, r in cad.iterrows():
        rows.append([
            str(int(r["rank"])),
            r["cad_designer"].title(),
            str(int(r["total_nod"])),
            f"{r['total_points']:.2f}",
            f"{r['target']:.2f}",
            f"{r['remaining']:.2f}",
            f"{r['achievement_pct']:.1f}%",
            f"{r['contribution_pct']:.1f}%",
            r["status"],
        ])
    elems.append(_data_table(hdrs, rows, cws))
    return elems


# ── 2. Manual Designer Ranking ────────────────

def build_manual_ranking(data):
    manual = data["manual_summary"]
    elems = [PageBreak(), _page_title("MANUAL DESIGNER RANKING"), Spacer(1, 10)]
    if manual.empty:
        elems.append(Paragraph("No manual designer data.", get_styles()["body"]))
        return elems

    hdrs = ["Rank", "Designer Name", "Total Jobs", "Total Qty",
            "Selection Qty", "Rejection Qty", "Selection %", "Rejection %", "Status"]
    cws  = [28, CW*0.24, 48, 40, 55, 55, 55, 55, 80]
    rows = []
    for _, r in manual.iterrows():
        rows.append([
            str(int(r["rank"])),
            r["designer_name"].title(),
            str(int(r["total_jobs"])),
            str(int(r["total_qty"])),
            str(int(r["selection_qty"])),
            str(int(r["rejection_qty"])),
            f"{r['selection_pct']:.1f}%",
            f"{r['rejection_pct']:.1f}%",
            r["status"],
        ])
    elems.append(_data_table(hdrs, rows, cws))
    return elems


# ── 3. Project Analysis ───────────────────────

def build_project_analysis(data):
    proj = data["project_analysis"]
    elems = [PageBreak(), _page_title("PROJECT ANALYSIS"), Spacer(1, 10)]
    if proj.empty:
        elems.append(Paragraph("No project data.", get_styles()["body"]))
        return elems

    hdrs = ["Project", "Total Designs", "Total NOD", "Total Points", "Contribution %"]
    cws  = [CW*0.28, 70, 60, 70, 70]
    rows = []
    for _, r in proj.iterrows():
        rows.append([
            r["project"].title(),
            str(int(r["designs"])),
            str(int(r["total_nod"])),
            f"{r['total_points']:.2f}",
            f"{r['contribution_pct']:.1f}%",
        ])
    elems.append(_data_table(hdrs, rows, cws))

    # Per-designer breakdown per project
    cad_raw = data["cad_raw"]
    if not cad_raw.empty:
        elems.append(Spacer(1, 10))
        elems.append(_section_hdr("DESIGNER-WISE PROJECT BREAKDOWN"))
        g = cad_raw.groupby(["project","cad_designer"]).agg(
            designs=("cad_design_no","count"),
            pts=("points","sum")
        ).reset_index().sort_values(["project","pts"], ascending=[True, False])
        hdrs2 = ["Project", "Designer", "Designs", "Points"]
        cws2  = [CW*0.28, CW*0.3, 60, 60]
        rows2 = []
        for _, r in g.iterrows():
            rows2.append([r["project"].title(), r["cad_designer"].title(),
                          str(int(r["designs"])), f"{r['pts']:.2f}"])
        elems.append(_data_table(hdrs2, rows2, cws2))
    return elems


# ── 4. Collection Analysis ────────────────────

def build_collection_analysis(data):
    coll = data["collection_analysis"]
    elems = [PageBreak(), _page_title("COLLECTION ANALYSIS"), Spacer(1, 10)]
    if coll.empty:
        elems.append(Paragraph("No collection data.", get_styles()["body"]))
        return elems

    hdrs = ["Collection", "Total Designs", "Total NOD", "Total Points", "Contribution %"]
    cws  = [CW*0.30, 70, 60, 70, 70]
    rows = []
    for _, r in coll.iterrows():
        rows.append([
            r["collection_name"].title(),
            str(int(r["designs"])),
            str(int(r["total_nod"])),
            f"{r['total_points']:.2f}",
            f"{r['contribution_pct']:.1f}%",
        ])
    elems.append(_data_table(hdrs, rows, cws))
    return elems


# ── 5. Product Analysis ───────────────────────

def build_product_analysis(data):
    prod = data["product_analysis"]
    elems = [PageBreak(), _page_title("PRODUCT ANALYSIS"), Spacer(1, 10)]
    if prod.empty:
        elems.append(Paragraph("No product data.", get_styles()["body"]))
        return elems

    hdrs = ["Product", "Total Designs", "Total NOD", "Total Points", "Contribution %"]
    cws  = [CW*0.28, 70, 60, 70, 70]
    rows = []
    for _, r in prod.iterrows():
        rows.append([
            r["product"].title(),
            str(int(r["designs"])),
            str(int(r["total_nod"])),
            f"{r['total_points']:.2f}",
            f"{r['contribution_pct']:.1f}%",
        ])
    elems.append(_data_table(hdrs, rows, cws))
    return elems


# ── 6. Location Analysis ──────────────────────

def build_location_analysis(data):
    loc = data["location_analysis"]
    elems = [PageBreak(), _page_title("LOCATION ANALYSIS"), Spacer(1, 10)]
    if loc.empty:
        elems.append(Paragraph("No location data.", get_styles()["body"]))
        return elems

    hdrs = ["Location", "Designers", "Total Designs", "Total NOD", "Total Points"]
    cws  = [CW*0.30, 55, 70, 60, 70]
    rows = []
    for _, r in loc.iterrows():
        rows.append([
            r["cad_location"].title(),
            str(int(r["designers"])),
            str(int(r["designs"])),
            str(int(r["total_nod"])),
            f"{r['total_points']:.2f}",
        ])
    elems.append(_data_table(hdrs, rows, cws))
    return elems


# ── 7. Work Type Analysis ─────────────────────

def build_worktype_analysis(data):
    wt = data["worktype_analysis"]
    elems = [PageBreak(), _page_title("WORK TYPE ANALYSIS"), Spacer(1, 10)]
    if wt.empty:
        elems.append(Paragraph("No work type data.", get_styles()["body"]))
        return elems

    hdrs = ["Order / Work Type", "Total Designs", "Total NOD", "Total Points"]
    cws  = [CW*0.35, 70, 60, 70]
    rows = []
    for _, r in wt.iterrows():
        rows.append([
            r["order_type"].title(),
            str(int(r["designs"])),
            str(int(r["total_nod"])),
            f"{r['total_points']:.2f}",
        ])
    elems.append(_data_table(hdrs, rows, cws))
    return elems


# ── 8. Target Achievement Report ─────────────

def build_target_achievement(data):
    cad = data["cad_summary"]
    elems = [PageBreak(), _page_title("TARGET ACHIEVEMENT REPORT"), Spacer(1, 10)]

    if not cad.empty:
        elems.append(_section_hdr("CAD DESIGNER TARGET VS ACHIEVEMENT"))
        hdrs = ["Designer", "Points Earned", "Monthly Target", "Remaining",
                "Achievement %", "Avg Pts/Design", "Status"]
        cws  = [CW*0.24, 60, 65, 55, 70, 65, 70]
        rows = []
        for _, r in cad.sort_values("achievement_pct", ascending=False).iterrows():
            bar = "█" * int(r["achievement_pct"] / 10) + "░" * (10 - int(r["achievement_pct"] / 10))
            rows.append([
                r["cad_designer"].title(),
                f"{r['total_points']:.2f}",
                f"{r['target']:.2f}",
                f"{r['remaining']:.2f}",
                f"{r['achievement_pct']:.1f}%  {bar[:5]}",
                f"{r['avg_pts_per_design']:.3f}",
                r["status"],
            ])
        # totals row
        total_pts  = cad["total_points"].sum()
        total_tgt  = cad["target"].sum()
        total_rem  = cad["remaining"].sum()
        ov_pct     = round((total_pts / total_tgt) * 100, 1) if total_tgt else 0
        rows.append(["TOTAL", f"{total_pts:.2f}", f"{total_tgt:.2f}",
                     f"{total_rem:.2f}", f"{ov_pct:.1f}%", "-", "-", "-"])
        t = Table([hdrs] + rows, colWidths=cws)
        ts = standard_table_style()
        # Highlight totals row
        ts.add("BACKGROUND", (0, len(rows)), (-1, len(rows)), C_NAVY)
        ts.add("TEXTCOLOR",  (0, len(rows)), (-1, len(rows)), C_GOLD)
        ts.add("FONTNAME",   (0, len(rows)), (-1, len(rows)), "Helvetica-Bold")
        t.setStyle(ts)
        elems.append(t)

    return elems


# ── 9. Monthly Work Register (CAD) ────────────

def build_work_register(data):
    cad_raw = data["cad_raw"]
    elems   = [PageBreak(), _page_title("MONTHLY WORK REGISTER"), Spacer(1, 8)]
    if cad_raw.empty:
        elems.append(Paragraph("No work register data.", get_styles()["body"]))
        return elems

    S = get_styles()
    emp_hdr_style = PS(fontName="Helvetica-Bold", fontSize=10,
                                    textColor=C_WHITE, alignment=TA_LEFT)
    sub_style = PS(fontName="Helvetica", fontSize=8,
                                textColor=C_GOLD_LIGHT, alignment=TA_LEFT)

    sorted_raw = cad_raw.sort_values(["cad_designer","cam_date"])
    designers  = sorted_raw["cad_designer"].dropna().unique()

    hdrs = ["#", "Design No", "Date", "Collection", "Project",
            "Product", "Order Type", "Karat", "DC/Die", "NOD", "Points"]
    cws  = [20, CW*0.14, 50, CW*0.14, CW*0.12,
            CW*0.10, 60, 32, 35, 28, 38]

    for designer in sorted(designers):
        df = sorted_raw[sorted_raw["cad_designer"] == designer].copy()
        if df.empty:
            continue

        # Designer header banner
        d_pts   = df["points"].sum()
        d_nod   = int(df["nod"].sum())
        d_cnt   = len(df)
        emp_banner = Table(
            [[Paragraph(f"  {designer.title()}", emp_hdr_style),
              Paragraph(f"Designs: {d_cnt}  |  NOD: {d_nod}  |  Points: {d_pts:.2f}",
                        sub_style)]],
            colWidths=[CW * 0.55, CW * 0.45]
        )
        emp_banner.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("LEFTPADDING",   (0,0),(-1,-1), 5),
            ("LINEBELOW",     (0,0),(-1,-1), 2, C_GOLD),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))

        rows = []
        for i, (_, row) in enumerate(df.iterrows(), 1):
            date_str = row["cam_date"].strftime("%d/%m/%Y") if pd.notna(row["cam_date"]) else "-"
            rows.append([
                str(i),
                str(row.get("cad_design_no",""))[:14],
                date_str,
                str(row.get("collection_name","")).title()[:16],
                str(row.get("project","")).title()[:14],
                str(row.get("product","")).title()[:12],
                str(row.get("order_type","")).title()[:10],
                str(row.get("karat","")),
                str(row.get("dc_die","")),
                str(int(row.get("nod",0))),
                f"{float(row.get('points',0)):.2f}",
            ])

        # Totals row
        rows.append(["", "TOTALS", "", "", "", "", "", "", "",
                     str(d_nod), f"{d_pts:.2f}"])
        detail_tbl = Table([hdrs] + rows, colWidths=cws)
        ts = standard_table_style()
        ts.add("BACKGROUND", (0, len(rows)), (-1, len(rows)), C_GREY_LIGHT)
        ts.add("FONTNAME",   (0, len(rows)), (-1, len(rows)), "Helvetica-Bold")
        ts.add("TEXTCOLOR",  (0, len(rows)), (-1, len(rows)), C_NAVY)
        detail_tbl.setStyle(ts)

        elems.append(KeepTogether([emp_banner, Spacer(1,2)]))
        elems.append(detail_tbl)
        elems.append(Spacer(1, 8))

    return elems


# ── 10. Management Summary ────────────────────

def build_management_summary(data, analytics=None):
    cad    = data["cad_summary"]
    manual = data["manual_summary"]
    proj   = data["project_analysis"]
    coll   = data["collection_analysis"]
    prod   = data["product_analysis"]
    month  = data["reporting_month"]

    elems = [PageBreak(), _page_title("MANAGEMENT SUMMARY"), Spacer(1, 10)]
    S     = get_styles()

    body_s = PS(fontName="Helvetica", fontSize=9,
                             textColor=C_GREY_DARK, spaceAfter=5, leading=14)
    bold_s = PS(fontName="Helvetica-Bold", fontSize=9,
                             textColor=C_NAVY, spaceAfter=3)
    head_s = PS(fontName="Helvetica-Bold", fontSize=11,
                             textColor=C_WHITE, spaceBefore=6, spaceAfter=3,
                             alignment=TA_LEFT)

    def section(title):
        t = Table([[Paragraph(f"  {title}", head_s)]], colWidths=[CW])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),C_NAVY),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LINEBELOW",(0,0),(-1,-1),2,C_GOLD),
        ]))
        return t

    # ── Overview ──
    elems.append(section("OVERVIEW"))
    total_pts   = round(cad["total_points"].sum(), 2) if not cad.empty else 0
    total_tgt   = round(cad["target"].sum(), 2) if not cad.empty else 0
    ov_pct      = round((total_pts / total_tgt)*100, 1) if total_tgt else 0
    n_cad       = len(cad) if not cad.empty else 0
    n_man       = len(manual) if not manual.empty else 0
    elems += [
        Paragraph(f"Reporting Month: <b>{month}</b>", body_s),
        Paragraph(f"Total CAD Designers: <b>{n_cad}</b>  |  Total Manual Designers: <b>{n_man}</b>", body_s),
        Paragraph(f"Total Points Earned: <b>{total_pts}</b>  |  Monthly Target: <b>{total_tgt}</b>  |  Overall Achievement: <b>{ov_pct}%</b>", body_s),
    ]

    # ── CAD Performance ──
    if not cad.empty:
        elems.append(Spacer(1,6))
        elems.append(section("CAD PERFORMANCE HIGHLIGHTS"))
        top3  = cad.head(3)
        below = cad[cad["achievement_pct"] < 80]
        crit  = cad[cad["achievement_pct"] < 50]
        for i, (_, r) in enumerate(top3.iterrows(), 1):
            elems.append(Paragraph(
                f"{'🥇' if i==1 else '🥈' if i==2 else '🥉'}  <b>#{i} {r['cad_designer'].title()}</b> — "
                f"{r['total_points']:.2f} pts / {r['target']:.2f} target "
                f"({r['achievement_pct']:.1f}%) — Grade {r['grade']}", body_s))
        if not below.empty:
            elems.append(Paragraph(
                f"[!]  <b>{len(below)} designer(s) below 80% target:</b> "
                f"{', '.join(below['cad_designer'].str.title().tolist())}", body_s))
        if not crit.empty:
            elems.append(Paragraph(
                f"[X]  <b>Critical ({len(crit)} designer(s) below 50%):</b> "
                f"{', '.join(crit['cad_designer'].str.title().tolist())}", body_s))

    # ── Best Project / Collection / Product ──
    elems.append(Spacer(1,6))
    elems.append(section("BUSINESS HIGHLIGHTS"))
    if not proj.empty:
        bp = proj.iloc[0]
        elems.append(Paragraph(
            f"[*]  <b>Best Project:</b> {bp['project'].title()} — "
            f"{bp['total_points']:.2f} pts ({bp['contribution_pct']:.1f}% contribution)", body_s))
    if not coll.empty:
        bc = coll.iloc[0]
        elems.append(Paragraph(
            f"[*]  <b>Best Collection:</b> {bc['collection_name'].title()} — "
            f"{bc['total_points']:.2f} pts ({bc['contribution_pct']:.1f}% contribution)", body_s))
    if not prod.empty:
        bprod = prod.iloc[0]
        elems.append(Paragraph(
            f"[*]  <b>Top Product by Volume:</b> {bprod['product'].title()} — "
            f"{int(bprod['designs'])} designs, {bprod['total_points']:.2f} pts", body_s))

    # ── Recommendations ──
    elems.append(Spacer(1,6))
    elems.append(section("RECOMMENDATIONS"))
    recs = []
    if not cad.empty:
        crit = cad[cad["achievement_pct"] < 50]
        if not crit.empty:
            recs.append(f"Immediate coaching needed for: "
                        f"{', '.join(crit['cad_designer'].str.title().tolist())}")
        below = cad[(cad["achievement_pct"] >= 50) & (cad["achievement_pct"] < 80)]
        if not below.empty:
            recs.append(f"Monitor and support designers below 80%: "
                        f"{', '.join(below['cad_designer'].str.title().tolist())}")
        top = cad[cad["achievement_pct"] >= 90]
        if not top.empty:
            recs.append(f"Recognise top performers: "
                        f"{', '.join(top['cad_designer'].str.title().tolist())}")
    recs.append("Review target allocations for next month based on current trajectory.")
    recs.append("Ensure consistent workload distribution across all designers.")
    for rec in recs:
        elems.append(Paragraph(f"•  {rec}", body_s))

    # MDSS Analytics section disabled pending layout fix
    # Will be re-enabled in next update
    _ = analytics  # suppress unused warning

    return elems
