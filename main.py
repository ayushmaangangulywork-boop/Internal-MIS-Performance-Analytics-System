"""
main.py
MAWSIM GOLD — Jewellery Design MIS Report Generator
=====================================================
Usage:
  python main.py                         → Monthly MIS (auto-detect Excel)
  python main.py file.xlsx               → Monthly MIS (specific file)
  python main.py file.xlsx --weekly      → All weekly MIS reports
  python main.py file.xlsx --week 1      → Specific week (1-based index)

Outputs (inside ./OUTPUT/):
  - MIS_Report_<Month>_<ts>.pdf
  - MIS_Summary_<Month>_<ts>.xlsx
  - MIS_Weekly_<Week>_<ts>.pdf          (if --weekly or --week N)
"""

import os
import sys
import glob
import traceback
from datetime import datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor

from data_reader        import MISDataReader
from dashboard          import build_dashboard_elements, build_manual_dashboard
from scorecards         import build_cad_scorecards, build_manual_scorecards
from reports            import (
    build_cad_ranking, build_manual_ranking,
    build_project_analysis, build_collection_analysis,
    build_product_analysis, build_location_analysis,
    build_worktype_analysis, build_target_achievement,
    build_work_register, build_management_summary,
)
from executive_report   import build_cad_executive, build_manual_executive
from excel_export       import build_excel_report
from time_intelligence  import build_time_intelligence
from weekly_report      import build_weekly_report
from individual_reports import generate_individual_reports

COMPANY  = "MAWSIM GOLD"
PAGE_W, PAGE_H = landscape(A4)
MARGIN   = 10 * mm
C_NAVY   = HexColor("#0D1B2A")
C_GOLD   = HexColor("#C9A84C")
C_GREY   = HexColor("#78909C")


# ─────────────────────────────────────────────
# PAGE HEADER / FOOTER CALLBACK
# ─────────────────────────────────────────────

class _HeaderFooter:
    def __init__(self, month, company):
        self.month   = month
        self.company = company

    def __call__(self, canvas, doc):
        canvas.saveState()
        w, h = PAGE_W, PAGE_H
        canvas.setStrokeColor(C_GOLD)
        canvas.setLineWidth(1)
        canvas.line(MARGIN, 10 * mm, w - MARGIN, 10 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(C_GREY)
        canvas.drawString(MARGIN, 7 * mm,
                          f"{self.company}  |  {self.month}  |  Confidential")
        canvas.drawRightString(w - MARGIN, 7 * mm, f"Page {doc.page}")
        canvas.restoreState()


# ─────────────────────────────────────────────
# FIND EXCEL FILE
# ─────────────────────────────────────────────

def _find_excel(base_dir):
    """Return path to the first .xlsx found in base_dir."""
    patterns = [
        os.path.join(base_dir, "*.xlsx"),
        os.path.join(base_dir, "*.xls"),
        os.path.join(base_dir, "*.XLSX"),
    ]
    for pat in patterns:
        hits = glob.glob(pat)
        if hits:
            return hits[0]
    return None


# ─────────────────────────────────────────────
# BUILD PDF
# ─────────────────────────────────────────────

def _make_doc(pdf_path, month, title, company):
    """Create a BaseDocTemplate with standard frame and header/footer."""
    hf        = _HeaderFooter(month, company)
    content_w = PAGE_W - 2 * MARGIN
    content_h = PAGE_H - 2 * MARGIN - 8 * mm
    doc = BaseDocTemplate(
        pdf_path,
        pagesize=landscape(A4),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=13 * mm,
        title=title,
        author=company,
    )
    frame = Frame(
        MARGIN, 13 * mm,
        content_w, content_h,
        leftPadding=0, rightPadding=0,
        topPadding=0,  bottomPadding=0,
        id="main",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=hf)])
    return doc


def _strip_leading_pagebreak(elems):
    if elems and elems[0].__class__.__name__ == 'PageBreak':
        return elems[1:]
    return elems


def _build_cad_pdf(data, pdf_path, company):
    """CAD MIS PDF:
    Dashboard → CAD Scorecards → CAD Ranking → All Analyses →
    Target Achievement → Work Register → CAD Executive Summary
    """
    month = data["reporting_month"]
    doc   = _make_doc(pdf_path, month, f"MAWSIM GOLD CAD MIS – {month}", company)

    story = []
    story += build_dashboard_elements(data, company)
    story += build_cad_scorecards(data)
    story += build_cad_ranking(data)
    story += build_project_analysis(data)
    story += build_collection_analysis(data)
    story += build_product_analysis(data)
    story += build_location_analysis(data)
    story += build_worktype_analysis(data)
    story += build_target_achievement(data)
    story += build_work_register(data)
    # CAD Executive Summary appended as final page
    story += build_cad_executive(data, analytics=None)

    doc.build(story)
    print(f"[CAD MIS PDF] Saved: {pdf_path}")


def _build_manual_pdf(data, pdf_path, company):
    """Manual MIS PDF:
    Manual Scorecards → Manual Ranking → Manual Executive Summary
    """
    month = data["reporting_month"]
    doc   = _make_doc(pdf_path, month, f"MAWSIM GOLD Manual MIS – {month}", company)

    story = []
    story += build_manual_dashboard(data, company)
    # Strip leading PageBreak from each section so dashboard is truly page 1
    for builder in [build_manual_scorecards, build_manual_ranking, build_manual_executive]:
        section = builder(data) if builder != build_manual_executive else build_manual_executive(data)
        if section and section[0].__class__.__name__ == "PageBreak":
            section = section[1:]
        story += [PageBreak()] + section

    doc.build(story)
    print(f"[Manual MIS PDF] Saved: {pdf_path}")


def _build_executive_pdf(story_elements, title_suffix, pdf_path, month, company):
    """Build a standalone executive-report PDF from pre-built story elements."""
    hf = _HeaderFooter(month, company)
    content_w = PAGE_W - 2 * MARGIN
    content_h = PAGE_H - 2 * MARGIN - 8 * mm

    doc = BaseDocTemplate(
        pdf_path,
        pagesize=landscape(A4),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=13 * mm,
        title=f"MAWSIM GOLD {title_suffix} – {month}",
        author=company,
    )
    frame = Frame(MARGIN, 13*mm, content_w, content_h,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=hf)])
    doc.build(story_elements)
    print(f"[Executive PDF] Saved: {pdf_path}")


def _build_weekly_pdf(week_data, week_label, pdf_path, company):
    hf = _HeaderFooter(week_label, company)
    content_w = PAGE_W - 2 * MARGIN
    content_h = PAGE_H - 2 * MARGIN - 8 * mm

    doc = BaseDocTemplate(
        pdf_path,
        pagesize=landscape(A4),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=13 * mm,
        title=f"MAWSIM GOLD Weekly MIS – {week_label}",
        author=company,
    )
    frame = Frame(MARGIN, 13*mm, content_w, content_h,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=hf)])
    story = build_weekly_report(week_data, week_label)
    doc.build(story)
    print(f"[Weekly PDF] Saved: {pdf_path}")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    base_dir   = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "OUTPUT")
    os.makedirs(output_dir, exist_ok=True)

    # ── Parse arguments ──────────────────────
    args = sys.argv[1:]
    weekly_all  = "--weekly" in args
    weekly_idx  = None
    excel_path  = None

    clean_args = [a for a in args if not a.startswith("--")]
    if clean_args:
        excel_path = clean_args[0]

    if "--week" in args:
        idx = args.index("--week")
        if idx + 1 < len(args):
            try:
                weekly_idx = int(args[idx + 1]) - 1  # 1-based → 0-based
            except ValueError:
                pass

    if not excel_path:
        excel_path = _find_excel(base_dir)

    if not excel_path or not os.path.exists(excel_path):
        print("ERROR: No Excel workbook found.")
        print(f"Usage: python main.py [file.xlsx] [--weekly] [--week N]")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  {COMPANY}  —  MIS Report Generator")
    print(f"{'='*60}")
    print(f"  Source : {excel_path}")
    print(f"  Output : {output_dir}")
    print(f"{'='*60}\n")

    # ── Read data ──────────────────────────
    print("[1/4] Reading Excel workbook...")
    reader = MISDataReader(excel_path)
    data   = reader.load()
    month  = data["reporting_month"].replace(" ", "_")
    ts     = datetime.now().strftime("%Y%m%d_%H%M")

    # ── CAD MIS PDF ────────────────────────────────────────────
    print("[2/5] Generating CAD MIS PDF...")
    cad_pdf_path = os.path.join(output_dir, f"MIS_CAD_{month}_{ts}.pdf")
    try:
        _build_cad_pdf(data, cad_pdf_path, COMPANY)
    except Exception as e:
        print(f"[CAD PDF ERROR] {e}")
        traceback.print_exc()

    # ── Manual MIS PDF ──────────────────────────────────────────
    print("[3/5] Generating Manual MIS PDF...")
    man_pdf_path = os.path.join(output_dir, f"MIS_Manual_{month}_{ts}.pdf")
    try:
        _build_manual_pdf(data, man_pdf_path, COMPANY)
    except Exception as e:
        print(f"[Manual PDF ERROR] {e}")
        traceback.print_exc()

    # ── Excel Summary ──────────────────────────────────────────
    print("[4/5] Generating Excel summary...")
    xl_path = os.path.join(output_dir, f"MIS_Summary_{month}_{ts}.xlsx")
    try:
        build_excel_report(data, xl_path)
    except Exception as e:
        print(f"[Excel ERROR] {e}")
        traceback.print_exc()

    # ── Individual Per-Person PDFs ──────────────
    print("[5/5] Generating Individual Designer PDFs...")
    try:
        indiv_dir = os.path.join(output_dir, "INDIVIDUAL")
        generate_individual_reports(data, indiv_dir)
    except Exception as e:
        print(f"[Individual PDF ERROR] {e}")
        traceback.print_exc()

    # ── Weekly Reports (additive, optional) ──
    if weekly_all or weekly_idx is not None:
        print("\n[Weekly] Generating weekly reports...")
        weeks = reader.get_available_weeks(data["cad_raw"])
        if not weeks:
            print("[Weekly] No weekly data found.")
        else:
            targets = ([weeks[weekly_idx]] if weekly_idx is not None
                       and 0 <= weekly_idx < len(weeks) else weeks)
            for label, ws, we in targets:
                try:
                    wdata    = reader.build_weekly_data(data, ws, we)
                    safe_lbl = label.replace(" ", "_").replace("–", "-")[:40]
                    wpdf     = os.path.join(output_dir, f"MIS_Weekly_{safe_lbl}_{ts}.pdf")
                    _build_weekly_pdf(wdata, label, wpdf, COMPANY)
                except Exception as e:
                    print(f"[Weekly ERROR] {label}: {e}")
                    traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"  ✓ Done!  Reports saved in OUTPUT folder.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
