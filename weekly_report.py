"""
weekly_report.py  —  MAWSIM GOLD
Weekly MIS module. Fully independent of Monthly MIS.
Reuses existing analytics engine by pre-filtering data to selected week.
Never modifies monthly data, rankings, or KPIs.
Week definition: Monday to Saturday (Sunday excluded).
"""

from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle,
    KeepTogether, PageBreak
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


def _P(text, style):
    return Paragraph(str(text), style)


def _page_title(text, sub=""):
    s1 = PS(fontName="Helvetica-Bold", fontSize=14,
                         textColor=C_WHITE, alignment=TA_CENTER)
    s2 = PS(fontName="Helvetica", fontSize=9,
                         textColor=C_GOLD_LIGHT, alignment=TA_CENTER)
    rows = [[_P(text, s1)]]
    if sub:
        rows.append([_P(sub, s2)])
    t = Table(rows, colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LINEBELOW",     (0,-1),(-1,-1), 2.5, C_GOLD),
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


def _kpi_tile(label, value, accent, bg, w):
    vs = PS(fontName="Helvetica-Bold",
                         fontSize=14 if len(str(value)) <= 6 else 11,
                         textColor=HexColor(accent), alignment=TA_CENTER)
    ls = PS(fontName="Helvetica", fontSize=6.5,
                         textColor=C_GREY_DARK, alignment=TA_CENTER)
    inner = Table([[_P(str(value), vs)], [_P(label, ls)]], colWidths=[w-6])
    inner.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor(bg)),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
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


def _data_tbl(headers, rows, cws):
    t = Table([headers] + rows, colWidths=cws)
    t.setStyle(standard_table_style())
    return t


# ─────────────────────────────────────────────────────────────
# OBSERVATIONS (weekly-specific)
# ─────────────────────────────────────────────────────────────

def _weekly_observations(week_data: dict, week_label: str) -> list:
    cad  = week_data["cad_summary"]
    proj = week_data["project_analysis"]
    prod = week_data["product_analysis"]
    obs  = []

    if cad.empty:
        return [("info", f"No completed designs recorded for {week_label}.")]

    total_pts  = round(cad["total_points"].sum(), 2)
    total_des  = int(cad["total_designs"].sum())
    n_active   = len(cad[cad["total_designs"] > 0])

    obs.append(("info",
        f"{n_active} CAD designer(s) completed work during {week_label}, "
        f"generating {total_des} designs totalling {total_pts:.2f} pts."))

    top = cad.iloc[0]
    obs.append(("good",
        f"Top performer this week: {top['cad_designer'].title()} "
        f"with {top['total_points']:.2f} pts ({int(top['total_designs'])} designs)."))

    zero = cad[cad["total_designs"] == 0]
    if not zero.empty:
        obs.append(("warning",
            f"{len(zero)} designer(s) recorded no completed work this week: "
            f"{', '.join(zero['cad_designer'].str.title().tolist())}."))

    if not proj.empty:
        tp = proj.iloc[0]
        obs.append(("info",
            f"Project {tp['project'].title()} led this week with "
            f"{int(tp['designs'])} designs ({tp['contribution_pct']:.1f}% of weekly output)."))

    if not prod.empty:
        tprod = prod.iloc[0]
        total_d = prod["designs"].sum()
        pct = round(tprod["designs"] / total_d * 100, 1) if total_d else 0
        obs.append(("info",
            f"{tprod['product'].title()} was the most produced item this week "
            f"({int(tprod['designs'])} designs, {pct:.1f}% of weekly volume)."))

    # concentration
    if not cad.empty and total_pts > 0:
        top3_pts  = cad.nlargest(3, "total_points")["total_points"].sum()
        top3_pct  = round(top3_pts / total_pts * 100, 1)
        if top3_pct > 75:
            obs.append(("warning",
                f"Top 3 contributors produced {top3_pct:.1f}% of this week's output — "
                f"consider whether workload distribution is balanced."))

    return obs


# ─────────────────────────────────────────────────────────────
# RECOMMENDATIONS (weekly)
# ─────────────────────────────────────────────────────────────

def _weekly_recommendations(week_data: dict) -> list:
    cad  = week_data["cad_summary"]
    recs = []
    if cad.empty:
        return recs

    zero = cad[cad["total_designs"] == 0]
    if not zero.empty:
        recs.append(("High",
            f"Follow up on zero-output designers: {', '.join(zero['cad_designer'].str.title())}",
            "No completed work was recorded this week. Determine whether there are "
            "capacity issues, assignment gaps, or other blockers."))

    low = cad[(cad["total_designs"] > 0) & (cad["total_points"] < cad["total_points"].mean() * 0.5)]
    if not low.empty:
        recs.append(("Medium",
            f"Review workload for below-average designers: {', '.join(low['cad_designer'].str.title())}",
            "These designers completed less than 50% of the team average this week. "
            "Assess whether design complexity, volume allocation, or other factors are limiting output."))

    top3 = cad.nlargest(3, "total_points")
    total = cad["total_points"].sum()
    if total > 0 and top3["total_points"].sum() / total > 0.75:
        recs.append(("Medium",
            "Rebalance weekly design assignments across the team",
            "A small group is carrying the majority of weekly output. "
            "Redistributing work more evenly reduces delivery risk and develops team capability."))

    return recs


# ─────────────────────────────────────────────────────────────
# OBSERVATION CARD RENDERER
# ─────────────────────────────────────────────────────────────

TAG_CFG = {
    "good":    ("#E8F5E9", "#2E7D32", "[+]"),
    "info":    ("#E3F2FD", "#1565C0", "[i]"),
    "warning": ("#FFF8E1", "#E65100", "[!]"),
    "critical":("#FFEBEE", "#C62828", "[X]"),
}


def _obs_card(tag, text, w):
    bg, fc, icon = TAG_CFG.get(tag, TAG_CFG["info"])
    icon_s = PS(fontName="Helvetica-Bold", fontSize=8,
                             textColor=HexColor(fc))
    body_s = PS(fontName="Helvetica", fontSize=7.8,
                             textColor=HexColor("#263238"), leading=11)
    body_w = w - 22   # icon col 13pt + paddings
    t = Table([[_P(icon, icon_s), _P(text, body_s)]],
              colWidths=[13, body_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), HexColor(bg)),
        ("BOX",          (0,0),(-1,-1), 0.4, HexColor(fc)),
        ("LINEBEFORE",   (0,0),(0,-1),  3,   HexColor(fc)),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
        ("RIGHTPADDING", (0,0),(-1,-1), 5),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
    ]))
    return t


def _obs_grid(observations, w):
    half = (w - 6) / 2
    pairs = []
    for i in range(0, len(observations), 2):
        c1 = _obs_card(*observations[i], half)
        c2 = _obs_card(*observations[i+1], half) if i+1 < len(observations) else Spacer(half, 1)
        row = Table([[c1, c2]], colWidths=[half, half])
        row.setStyle(TableStyle([
            ("TOPPADDING",    (0,0),(-1,-1), 2),
            ("BOTTOMPADDING", (0,0),(-1,-1), 2),
            ("LEFTPADDING",   (0,0),(-1,-1), 0),
            ("RIGHTPADDING",  (0,0),(-1,-1), 0),
            ("LEFTPADDING",   (1,0),(1,-1),  4),
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ]))
        pairs.append(row)
    return pairs


def _rec_table(recs, w):
    if not recs:
        return Spacer(w, 1)
    pri_c = {"High":("#FFEBEE","#C62828"), "Medium":("#FFF8E1","#E65100"), "Low":("#E8F5E9","#2E7D32")}
    hs  = PS(fontName="Helvetica-Bold", fontSize=7.5,
                          textColor=C_WHITE, alignment=TA_CENTER)
    as_ = PS(fontName="Helvetica-Bold", fontSize=7.5,
                          textColor=HexColor(NAVY_HEX), alignment=TA_LEFT)
    rs  = PS(fontName="Helvetica", fontSize=7.5,
                          textColor=HexColor("#37474F"), leading=10)
    cws = [48, w*0.30, w*0.54]
    rows = [[_P("Priority",hs), _P("Action",hs), _P("Rationale",hs)]]
    for pri, action, rationale in recs:
        bg, fc = pri_c.get(pri, ("#F5F5F5","#555"))
        ps = PS(fontName="Helvetica-Bold", fontSize=7.5,
                             textColor=HexColor(fc), alignment=TA_CENTER)
        rows.append([_P(pri,ps), _P(action,as_), _P(rationale,rs)])
    t = Table(rows, colWidths=cws)
    cmds = [
        ("BACKGROUND",(0,0),(-1,0), C_NAVY),
        ("LINEBELOW",(0,0),(-1,0), 1.5, C_GOLD),
        ("GRID",(0,0),(-1,-1), 0.3, HexColor("#CCCCCC")),
        ("FONTSIZE",(0,0),(-1,-1), 7.5),
        ("VALIGN",(0,0),(-1,-1), "TOP"),
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING",(0,0),(-1,-1), 5),
        ("RIGHTPADDING",(0,0),(-1,-1), 5),
    ]
    for i,(pri,_,__) in enumerate(recs,1):
        bg, _ = pri_c.get(pri, ("#F5F5F5","#555"))
        cmds.append(("BACKGROUND",(0,i),(0,i), HexColor(bg)))
        cmds.append(("BACKGROUND",(1,i),(-1,i), HexColor("#FAFAFA" if i%2==0 else "#EEF2F7")))
    t.setStyle(TableStyle(cmds))
    return t


# ─────────────────────────────────────────────────────────────
# MAIN PUBLIC BUILDER
# ─────────────────────────────────────────────────────────────

def build_weekly_report(week_data: dict, week_label: str) -> list:
    """
    Build a full weekly MIS PDF story from pre-filtered week_data.
    week_data has same structure as monthly data dict.
    Never modifies monthly data. Fully independent.
    """
    elems = [PageBreak()]
    cad    = week_data["cad_summary"]
    manual = week_data["manual_summary"]
    proj   = week_data["project_analysis"]
    prod   = week_data["product_analysis"]
    coll   = week_data["collection_analysis"]
    loc    = week_data["location_analysis"]
    wt     = week_data["worktype_analysis"]
    cad_raw = week_data["cad_raw"]

    # ── HEADER ────────────────────────────────────────────
    elems.append(_page_title(
        "WEEKLY MIS REPORT  —  MAWSIM GOLD",
        sub=f"Period: {week_label}  |  Generated: {week_data['generated_at']}"
    ))
    elems.append(Spacer(1, 5))

    # ── KPI STRIP ─────────────────────────────────────────
    n_cad     = len(cad[cad["total_designs"] > 0]) if not cad.empty else 0
    t_pts     = round(cad["total_points"].sum(), 1) if not cad.empty else 0
    t_des     = int(cad["total_designs"].sum())     if not cad.empty else 0
    t_nod     = int(cad["total_nod"].sum())          if not cad.empty else 0
    t_jobs    = int(manual["total_jobs"].sum())      if not manual.empty else 0
    t_qty     = int(manual["total_qty"].sum())       if not manual.empty else 0
    n_proj    = len(proj) if not proj.empty else 0
    n_prod    = len(prod) if not prod.empty else 0

    kpis = [
        ("Active CAD Designers", n_cad,       "#1565C0","#E3F2FD"),
        ("Total Designs",        t_des,        "#0D3B7A","#E8EAF6"),
        ("Total Points",         f"{t_pts}",   "#E65100","#FFF8E1"),
        ("Total NOD",            t_nod,        "#6A1B9A","#F3E5F5"),
        ("Manual Jobs",          t_jobs,       "#2E7D32","#E8F5E9"),
        ("Total Qty",            t_qty,        "#880E4F","#FCE4EC"),
        ("Projects Active",      n_proj,       "#00695C","#E0F2F1"),
        ("Products Active",      n_prod,       "#BF360C","#FFF3E0"),
    ]
    elems.append(_kpi_strip(kpis, CW))
    elems.append(Spacer(1, 6))

    # ── OBSERVATIONS ──────────────────────────────────────
    elems.append(_section_hdr("WEEKLY OBSERVATIONS  |  KEY FINDINGS"))
    elems.append(Spacer(1, 3))
    obs = _weekly_observations(week_data, week_label)
    elems += _obs_grid(obs, CW)
    elems.append(Spacer(1, 6))

    # ── CAD RANKING ───────────────────────────────────────
    if not cad.empty:
        elems.append(_section_hdr("CAD DESIGNER RANKING  (WEEK)"))
        elems.append(Spacer(1, 3))
        hdrs = ["Rank","Designer","Designs","NOD","Points","Avg Pts/Design","Contribution %"]
        cws  = [28, CW*0.26, 50, 40, 55, 70, 70]
        rows = []
        for _, r in cad.sort_values("total_points", ascending=False).reset_index(drop=True).iterrows():
            rows.append([
                str(int(r["rank"])),
                r["cad_designer"].title(),
                str(int(r["total_designs"])),
                str(int(r["total_nod"])),
                f"{r['total_points']:.2f}",
                f"{r['avg_pts_per_design']:.3f}",
                f"{r['contribution_pct']:.1f}%",
            ])
        elems.append(_data_tbl(hdrs, rows, cws))
        elems.append(Spacer(1, 8))

    # ── PROJECT + PRODUCT SIDE BY SIDE ────────────────────
    lw = CW * 0.48
    rw = CW * 0.52

    proj_elems = [_section_hdr("PROJECT ANALYSIS", lw), Spacer(1,3)]
    if not proj.empty:
        ph = ["Project","Designs","Points","Contribution%"]
        pc = [lw*0.40, lw*0.20, lw*0.20, lw*0.20]
        pr = [[r["project"].title(), str(int(r["designs"])),
               f"{r['total_points']:.2f}", f"{r['contribution_pct']:.1f}%"]
              for _,r in proj.iterrows()]
        proj_elems.append(_data_tbl(ph, pr, pc))

    prod_elems = [_section_hdr("PRODUCT ANALYSIS", rw), Spacer(1,3)]
    if not prod.empty:
        pdh = ["Product","Designs","Points","Contribution%"]
        pdc = [rw*0.38, rw*0.20, rw*0.22, rw*0.20]
        pdr = [[r["product"].title(), str(int(r["designs"])),
                f"{r['total_points']:.2f}", f"{r['contribution_pct']:.1f}%"]
               for _,r in prod.iterrows()]
        prod_elems.append(_data_tbl(pdh, pdr, pdc))

    # stack each side
    left_col  = Table([[e] for e in proj_elems], colWidths=[lw])
    right_col = Table([[e] for e in prod_elems], colWidths=[rw])
    left_col.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),0),
                                   ("BOTTOMPADDING",(0,0),(-1,-1),2),
                                   ("LEFTPADDING",(0,0),(-1,-1),0),
                                   ("RIGHTPADDING",(0,0),(-1,-1),0)]))
    right_col.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),0),
                                    ("BOTTOMPADDING",(0,0),(-1,-1),2),
                                    ("LEFTPADDING",(0,0),(-1,-1),6),
                                    ("RIGHTPADDING",(0,0),(-1,-1),0)]))

    side_by_side = Table([[left_col, right_col]], colWidths=[lw, rw])
    side_by_side.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
    ]))
    elems.append(side_by_side)
    elems.append(Spacer(1, 8))

    # ── COLLECTION + LOCATION + WORKTYPE ──────────────────
    w3 = CW / 3 - 4

    def _mini_tbl(title, headers, rows, cws, w):
        t = _section_hdr(title, w)
        d = _data_tbl(headers, rows, cws)
        return Table([[t],[Spacer(1,3)],[d]], colWidths=[w])

    coll_rows, loc_rows, wt_rows = [], [], []
    if not coll.empty:
        coll_rows = [[r["collection_name"].title(), str(int(r["designs"])),
                      f"{r['total_points']:.2f}"] for _,r in coll.iterrows()]
    if not loc.empty:
        loc_rows = [[r["cad_location"].title(), str(int(r["designers"])),
                     str(int(r["designs"]))] for _,r in loc.iterrows()]
    if not wt.empty:
        wt_rows = [[r["order_type"].title(), str(int(r["designs"])),
                    f"{r['total_points']:.2f}"] for _,r in wt.iterrows()]

    col1 = _mini_tbl("COLLECTION",["Collection","Designs","Points"],
                     coll_rows,[w3*0.50,w3*0.25,w3*0.25], w3)
    col2 = _mini_tbl("LOCATION",  ["Location","Designers","Designs"],
                     loc_rows, [w3*0.50,w3*0.25,w3*0.25], w3)
    col3 = _mini_tbl("WORK TYPE", ["Order Type","Designs","Points"],
                     wt_rows,  [w3*0.50,w3*0.25,w3*0.25], w3)

    three_col = Table([[col1, col2, col3]], colWidths=[w3]*3)
    three_col.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("LEFTPADDING",(1,0),(2,-1),6),
    ]))
    elems.append(three_col)
    elems.append(Spacer(1, 8))

    # ── RECOMMENDATIONS ───────────────────────────────────
    recs = _weekly_recommendations(week_data)
    if recs:
        elems.append(_section_hdr("MANAGEMENT RECOMMENDATIONS"))
        elems.append(Spacer(1, 3))
        elems.append(_rec_table(recs, CW))

    return elems
