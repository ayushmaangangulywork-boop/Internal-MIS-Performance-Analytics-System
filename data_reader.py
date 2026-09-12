
"""
data_reader.py
Reads and parses the Jewellery Design MIS Excel workbook.
Returns clean, structured data for all report generators.
"""
 
import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
 
 
# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
 
def _clean(val):
    """Strip whitespace from string values."""
    if isinstance(val, str):
        return val.strip()
    return val
 
 
def _safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default
 
 
def _safe_str(val):
    try:
        if isinstance(val, str):
            return val.strip()
        if val is None:
            return ""
        import math
        if isinstance(val, float) and math.isnan(val):
            return ""
        return str(val).strip()
    except Exception:
        return ""
 
 
# ─────────────────────────────────────────────
# MAIN READER CLASS
# ─────────────────────────────────────────────
 
class MISDataReader:
 
    def __init__(self, filepath: str):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Excel file not found: {filepath}")
        self.filepath = filepath
        self.xl = pd.ExcelFile(filepath, engine="openpyxl")
        self.sheet_names = self.xl.sheet_names
        print(f"[DataReader] Found sheets: {self.sheet_names}")
 
        # Populated by load()
        self.reporting_month = ""
        self.cad_raw = pd.DataFrame()
        self.designer_raw = pd.DataFrame()
        self.cad_targets = {}          # {designer_name: target_points}
        self.cad_designers = []
        self.manual_designers = []
 
    # ─────────────────────────────────────────
    # PUBLIC ENTRY POINT
    # ─────────────────────────────────────────
 
    def load(self) -> dict:
        """Load all sheets and return a unified data dictionary."""
        cad_raw = self._load_cad_data_source()
        designer_raw = self._load_designer_data_source()
        cad_targets = self._load_cad_targets()
        reporting_month = self._detect_reporting_month(cad_raw)
 
        self.cad_raw = cad_raw
        self.designer_raw = designer_raw
        self.cad_targets = cad_targets
        self.reporting_month = reporting_month
        self.cad_designers = sorted(cad_raw["cad_designer"].dropna().unique().tolist()) if not cad_raw.empty else []
        self.manual_designers = sorted(designer_raw["designer_name"].dropna().unique().tolist()) if not designer_raw.empty else []
 
        data = {
            "reporting_month": reporting_month,
            "generated_at": datetime.now().strftime("%d %B %Y, %I:%M %p"),
            "cad_raw": cad_raw,
            "designer_raw": designer_raw,
            "cad_targets": cad_targets,
            "cad_summary": self._build_cad_summary(cad_raw, cad_targets),
            "manual_summary": self._build_manual_summary(designer_raw),
            "project_analysis": self._build_project_analysis(cad_raw),
            "collection_analysis": self._build_collection_analysis(cad_raw),
            "product_analysis": self._build_product_analysis(cad_raw),
            "location_analysis": self._build_location_analysis(cad_raw),
            "worktype_analysis": self._build_worktype_analysis(cad_raw),
        }
        print(f"[DataReader] Load complete. CAD rows={len(cad_raw)}, Designer rows={len(designer_raw)}")
        return data
 
    # ─────────────────────────────────────────
    # SHEET: CAD DATA SOURCE
    # ─────────────────────────────────────────
 
    def _load_cad_data_source(self) -> pd.DataFrame:
        """Find and parse the CAD data source sheet."""
        sheet = self._find_sheet(["CAD DATA SOURCE", "CAD DATA"])
        if sheet is None:
            print("[DataReader] WARNING: CAD DATA SOURCE sheet not found.")
            return pd.DataFrame()
 
        raw = self.xl.parse(sheet, header=None)
        # Find header row — look for 'S.no' or 'S.NO'
        header_row = self._find_header_row(raw, ["S.no", "S.NO", "Sno"])
        if header_row is None:
            print("[DataReader] WARNING: CAD DATA SOURCE header row not found.")
            return pd.DataFrame()
 
        df = self.xl.parse(sheet, header=header_row)
        # Deduplicate column names before anything else
        seen = {}
        new_cols = []
        for c in df.columns:
            cs = _safe_str(c).strip().lower().replace(" ", "_")
            if cs in seen:
                seen[cs] += 1
                cs = f"{cs}_{seen[cs]}"
            else:
                seen[cs] = 0
            new_cols.append(cs)
        df.columns = new_cols
 
        # Rename columns to standard names
        col_map = {
            "s.no": "sno",
            "order_type": "order_type",
            "designer": "designer",
            "cad_designer": "cad_designer",
            "cad_design_no": "cad_design_no",
            "collection_name": "collection_name",
            "project": "project",
            "product": "product",
            "nod": "nod",
            "points": "points",
            "cam_date": "cam_date",
            "karat": "karat",
            "dc/die": "dc_die",
            "status": "status",
            "cad_location": "cad_location",
            "time_taken": "time_taken",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
 
        # Keep only the standard columns we need (drop extra lookup cols)
        keep = ["sno","order_type","designer","cad_designer","cad_design_no",
                "collection_name","project","product","nod","points",
                "cam_date","karat","dc_die","status","cad_location","time_taken"]
        df = df[[c for c in keep if c in df.columns]].copy()
 
        # Add time_taken column if missing (optional field)
        if "time_taken" not in df.columns:
            df["time_taken"] = float("nan")
 
        # Keep only rows where sno is numeric
        if "sno" in df.columns:
            df = df[pd.to_numeric(df["sno"], errors="coerce").notna()].copy()
 
        # Clean numeric columns
        for col in ["nod", "points"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
 
        # time_taken is OPTIONAL — keep NaN for missing, never fill with 0
        if "time_taken" in df.columns:
            df["time_taken"] = pd.to_numeric(df["time_taken"], errors="coerce")
 
        # Clean string columns
        for col in ["cad_designer", "project", "collection_name", "product",
                    "order_type", "cad_location", "dc_die", "status", "karat"]:
            if col in df.columns:
                df[col] = df[col].apply(_safe_str).str.strip().str.upper()
 
        # Parse cam_date
        if "cam_date" in df.columns:
            df["cam_date"] = pd.to_datetime(df["cam_date"], errors="coerce", dayfirst=True)
 
        df = df.reset_index(drop=True)
        return df
 
    # ─────────────────────────────────────────
    # SHEET: DESIGNER DATA SOURCE
    # ─────────────────────────────────────────
 
    def _load_designer_data_source(self) -> pd.DataFrame:
        """Find and parse the manual designer data source sheet."""
        sheet = self._find_sheet(["DESIGNER DATA SOURCE", "DESIGNER DATA"])
        if sheet is None:
            print("[DataReader] WARNING: DESIGNER DATA SOURCE sheet not found.")
            return pd.DataFrame()
 
        raw = self.xl.parse(sheet, header=None)
        header_row = self._find_header_row(raw, ["S.NO", "S.No", "DATE", "DESIGNER NAME"])
        if header_row is None:
            print("[DataReader] WARNING: DESIGNER DATA SOURCE header row not found.")
            return pd.DataFrame()
 
        df = self.xl.parse(sheet, header=header_row)
        # Deduplicate column names
        seen = {}
        new_cols = []
        for c in df.columns:
            cs = _safe_str(c).strip().lower().replace(" ", "_")
            if cs in seen:
                seen[cs] += 1
                cs = f"{cs}_{seen[cs]}"
            else:
                seen[cs] = 0
            new_cols.append(cs)
        df.columns = new_cols
 
        col_map = {
            "s.no": "sno",
            "date": "date",
            "designer_name": "designer_name",
            "qty": "qty",
            "design_no": "design_no",
            "product": "product",
            "project": "project",
            "collection": "collection",
            "selection_qty": "selection_qty",
            "rejection_qty": "rejection_qty",
            "design_approved": "design_approved",
            "location": "location",
            "remark": "remark",
            "software_no": "software_no",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
 
        # Keep only needed columns
        keep = ["sno","date","designer_name","qty","design_no","product",
                "project","collection","selection_qty","rejection_qty",
                "design_approved","location","remark","software_no"]
        df = df[[c for c in keep if c in df.columns]].copy()
 
        # Keep only rows with numeric sno
        if "sno" in df.columns:
            df = df[pd.to_numeric(df["sno"], errors="coerce").notna()].copy()
 
        # Clean string columns early so we can filter blank names
        for col in ["designer_name", "product", "project", "collection", "location"]:
            if col in df.columns:
                df[col] = df[col].apply(_safe_str).astype(str).str.strip().str.upper()
 
        # IMPORTANT: remove rows with blank/empty designer name (not real persons)
        if "designer_name" in df.columns:
            df = df[df["designer_name"].str.strip().ne("")].copy()
 
        # Clean numeric columns
        for col in ["qty", "selection_qty", "rejection_qty"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
 
        # Parse date
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
 
        df = df.reset_index(drop=True)
        return df
 
    # ─────────────────────────────────────────
    # SHEET: CAD DESIGNER REPORT (targets)
    # ─────────────────────────────────────────
 
    def _load_cad_targets(self) -> dict:
        """
        Extract DESIGNER NAME → TARGET mapping from CAD DESIGNER REPORT sheet.
        The target table has columns: DESIGNER NAME | CURRENT POINTS | TARGET | PERCENTAGE
        """
        sheet = self._find_sheet(["CAD DESIGNER REPORT", "CAD DESIGNER"])
        if sheet is None:
            return {}
 
        raw = self.xl.parse(sheet, header=None)
        targets = {}
 
        # Scan for a cell containing 'DESIGNER NAME' (case-insensitive)
        for ri in range(len(raw)):
            for ci in range(len(raw.columns)):
                cell = _safe_str(raw.iloc[ri, ci])
                has_target_col = (ci + 2 < len(raw.columns) and
                                  "TARGET" in _safe_str(raw.iloc[ri, ci + 2]).upper())
                if "DESIGNER NAME" in cell.upper() and has_target_col:
                    # This row is the header; parse below
                    for offset in range(1, 30):
                        row_idx = ri + offset
                        if row_idx >= len(raw):
                            break
                        name_val = _safe_str(raw.iloc[row_idx, ci])
                        tgt_val = raw.iloc[row_idx, ci + 2] if ci + 2 < len(raw.columns) else None
                        if not name_val or name_val.upper() in ("DESIGNER NAME", "GRAND TOTAL", ""):
                            continue
                        tgt = _safe_float(tgt_val, 0.0)
                        if tgt > 0:
                            targets[name_val.upper().strip()] = tgt
                    break
            if targets:
                break
 
        # Fallback: scan for rows that look like name/points/target triples
        if not targets:
            for ri in range(len(raw)):
                row = raw.iloc[ri]
                for ci in range(len(row) - 2):
                    name = _safe_str(row.iloc[ci])
                    pts = row.iloc[ci + 1]
                    tgt = row.iloc[ci + 2]
                    if (len(name) > 3 and name.replace(" ", "").isalpha()
                            and _safe_float(pts) > 0 and _safe_float(tgt) > 0
                            and _safe_float(tgt) <= 200):
                        targets[name.upper().strip()] = _safe_float(tgt)
 
        print(f"[DataReader] CAD Targets loaded: {targets}")
        return targets
 
    # ─────────────────────────────────────────
    # AGGREGATIONS
    # ─────────────────────────────────────────
 
    def _build_cad_summary(self, df: pd.DataFrame, targets: dict) -> pd.DataFrame:
        """Per-designer CAD summary with points, NOD, target, achievement %."""
        if df.empty:
            return pd.DataFrame()
 
        grp = df.groupby("cad_designer").agg(
            total_nod=("nod", "sum"),
            total_points=("points", "sum"),
            total_designs=("cad_design_no", "count"),
        ).reset_index()
 
        grp["target"] = grp["cad_designer"].map(
            lambda n: targets.get(n.upper().strip(), 0.0)
        )
        grp["achievement_pct"] = grp.apply(
            lambda r: round((r["total_points"] / r["target"]) * 100, 2) if r["target"] > 0 else 0.0,
            axis=1
        )
        grp["remaining"] = (grp["target"] - grp["total_points"]).clip(lower=0)
        grp["avg_pts_per_design"] = grp.apply(
            lambda r: round(r["total_points"] / r["total_designs"], 3) if r["total_designs"] > 0 else 0.0,
            axis=1
        )
        # Contribution % across all designers
        total_pts = grp["total_points"].sum()
        grp["contribution_pct"] = grp["total_points"].apply(
            lambda p: round((p / total_pts) * 100, 2) if total_pts > 0 else 0.0
        )
        grp["rank"] = grp["achievement_pct"].rank(method="dense", ascending=False).astype(int)
        grp["grade"] = grp["achievement_pct"].apply(_grade)
        grp["status"] = grp["achievement_pct"].apply(
            lambda p: "On Track" if p >= 80 else ("Below Target" if p >= 50 else "Critical")
        )
 
        return grp.sort_values("rank").reset_index(drop=True)
 
    def _build_manual_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Per-designer manual summary.
        Selection = qty where design_approved == YES.
        Rejection = total_qty - selection_qty.
        No longer uses the selection_qty / rejection_qty columns.
        """
        if df.empty:
            return pd.DataFrame()
 
        # selection = sum of qty for rows where design_approved is YES
        df = df.copy()
        df["_approved"] = df["design_approved"].apply(
            _safe_str).str.strip().str.upper().eq("YES")
        df["_sel_qty"] = df["qty"].where(df["_approved"], other=0)
 
        # Build location map: primary location per designer
        if "location" in df.columns:
            loc_map = df[df["location"].str.strip().ne("")].groupby("designer_name")["location"].agg(
                lambda x: x.mode().iloc[0] if len(x) > 0 else ""
            )
        else:
            loc_map = pd.Series(dtype=str)
 
        grp = df.groupby("designer_name").agg(
            total_qty=("qty", "sum"),
            selection_qty=("_sel_qty", "sum"),
            total_jobs=("sno", "count"),
        ).reset_index()
 
        grp["rejection_qty"] = grp["total_qty"] - grp["selection_qty"]
        grp["location"] = grp["designer_name"].map(loc_map).fillna("")
 
        grp["selection_pct"] = grp.apply(
            lambda r: round((r["selection_qty"] / r["total_qty"]) * 100, 2) if r["total_qty"] > 0 else 0.0,
            axis=1
        )
        grp["rejection_pct"] = grp.apply(
            lambda r: round((r["rejection_qty"] / r["total_qty"]) * 100, 2) if r["total_qty"] > 0 else 0.0,
            axis=1
        )
        grp["rank"] = grp["selection_pct"].rank(method="dense", ascending=False).astype(int)
        grp["grade"] = grp["selection_pct"].apply(_grade)
        grp["status"] = grp["selection_pct"].apply(
            lambda p: "Excellent" if p >= 80 else ("Good" if p >= 60 else "Needs Improvement")
        )
 
        return grp.sort_values("rank").reset_index(drop=True)
 
    def _build_project_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        g = df.groupby("project").agg(
            designs=("cad_design_no", "count"),
            total_nod=("nod", "sum"),
            total_points=("points", "sum"),
        ).reset_index()
        total = g["total_points"].sum()
        g["contribution_pct"] = g["total_points"].apply(
            lambda p: round((p / total) * 100, 2) if total > 0 else 0.0
        )
        return g.sort_values("total_points", ascending=False).reset_index(drop=True)
 
    def _build_collection_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        g = df.groupby("collection_name").agg(
            designs=("cad_design_no", "count"),
            total_nod=("nod", "sum"),
            total_points=("points", "sum"),
        ).reset_index()
        total = g["total_points"].sum()
        g["contribution_pct"] = g["total_points"].apply(
            lambda p: round((p / total) * 100, 2) if total > 0 else 0.0
        )
        return g.sort_values("total_points", ascending=False).reset_index(drop=True)
 
    def _build_product_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        g = df.groupby("product").agg(
            designs=("cad_design_no", "count"),
            total_nod=("nod", "sum"),
            total_points=("points", "sum"),
        ).reset_index()
        total = g["total_points"].sum()
        g["contribution_pct"] = g["total_points"].apply(
            lambda p: round((p / total) * 100, 2) if total > 0 else 0.0
        )
        return g.sort_values("designs", ascending=False).reset_index(drop=True)
 
    def _build_location_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        g = df.groupby("cad_location").agg(
            designers=("cad_designer", pd.Series.nunique),
            designs=("cad_design_no", "count"),
            total_nod=("nod", "sum"),
            total_points=("points", "sum"),
        ).reset_index()
        return g.sort_values("total_points", ascending=False).reset_index(drop=True)
 
    def _build_worktype_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        g = df.groupby("order_type").agg(
            designs=("cad_design_no", "count"),
            total_nod=("nod", "sum"),
            total_points=("points", "sum"),
        ).reset_index()
        return g.sort_values("designs", ascending=False).reset_index(drop=True)
 
    # ─────────────────────────────────────────
    # UTILITIES
    # ─────────────────────────────────────────
 
    def _find_sheet(self, candidates: list):
        """Case-insensitive sheet name match."""
        for name in self.sheet_names:
            for c in candidates:
                if c.upper() in name.upper():
                    return name
        return None
 
    def _find_header_row(self, raw: pd.DataFrame, keywords: list):
        """Find the row index that contains any of the given keywords."""
        for ri in range(min(30, len(raw))):
            row_vals = [_safe_str(v).upper() for v in raw.iloc[ri]]
            for kw in keywords:
                if kw.upper() in row_vals:
                    return ri
        return None
 
    def _detect_reporting_month(self, cad_df: pd.DataFrame) -> str:
        """Infer reporting month from cam_date column."""
        if cad_df.empty or "cam_date" not in cad_df.columns:
            return datetime.now().strftime("%B %Y")
        dates = cad_df["cam_date"].dropna()
        if dates.empty:
            return datetime.now().strftime("%B %Y")
        mode_date = dates.mode().iloc[0]
        return mode_date.strftime("%B %Y")
 
    # ─────────────────────────────────────────
    # WEEKLY SUPPORT  (additive, non-breaking)
    # ─────────────────────────────────────────
 
    def get_available_weeks(self, cad_df: pd.DataFrame) -> list:
        """
        Return sorted list of (week_label, week_start, week_end) tuples.
        Week = Monday to Saturday (Sunday excluded).
        """
        if cad_df.empty or "cam_date" not in cad_df.columns:
            return []
        dates = cad_df["cam_date"].dropna()
        if dates.empty:
            return []
 
        import pandas as pd
        weeks = []
        seen  = set()
        for d in sorted(dates.dt.date.unique()):
            # Monday of this date's week
            week_start = d - __import__("datetime").timedelta(days=d.weekday())
            week_end   = week_start + __import__("datetime").timedelta(days=5)  # Saturday
            key = str(week_start)
            if key not in seen:
                seen.add(key)
                label = f"Week of {week_start.strftime('%d %b %Y')} – {week_end.strftime('%d %b %Y')}"
                weeks.append((label, week_start, week_end))
        return sorted(weeks, key=lambda x: x[1])
 
    def build_weekly_data(self, full_data: dict, week_start, week_end) -> dict:
        """
        Filter full_data for a single week (Mon-Sat) and rebuild all aggregations.
        Returns a new data dict identical in structure to load().
        Does NOT modify the original data dict.
        """
        import pandas as pd
        import datetime as dt_mod
 
        ws = pd.Timestamp(week_start)
        we = pd.Timestamp(week_end)
 
        cad_raw     = full_data["cad_raw"].copy()
        designer_raw = full_data["designer_raw"].copy()
 
        # Filter by week
        if not cad_raw.empty and "cam_date" in cad_raw.columns:
            cad_raw = cad_raw[
                (cad_raw["cam_date"] >= ws) &
                (cad_raw["cam_date"] <= we)
            ].copy()
 
        if not designer_raw.empty and "date" in designer_raw.columns:
            designer_raw = designer_raw[
                (designer_raw["date"] >= ws) &
                (designer_raw["date"] <= we)
            ].copy()
 
        week_label = f"{ws.strftime('%d %b')} – {we.strftime('%d %b %Y')}"
 
        data = {
            "reporting_month": f"Week {week_label}",
            "generated_at": datetime.now().strftime("%d %B %Y, %I:%M %p"),
            "cad_raw":      cad_raw,
            "designer_raw": designer_raw,
            "cad_targets":  full_data["cad_targets"],
            "cad_summary":  self._build_cad_summary(cad_raw, full_data["cad_targets"]),
            "manual_summary": self._build_manual_summary(designer_raw),
            "project_analysis":    self._build_project_analysis(cad_raw),
            "collection_analysis": self._build_collection_analysis(cad_raw),
            "product_analysis":    self._build_product_analysis(cad_raw),
            "location_analysis":   self._build_location_analysis(cad_raw),
            "worktype_analysis":   self._build_worktype_analysis(cad_raw),
        }
        return data
 
 
# ─────────────────────────────────────────────
# GRADING HELPER
# ─────────────────────────────────────────────
 
def _grade(pct: float) -> str:
    if pct >= 90:
        return "A+"
    elif pct >= 75:
        return "A"
    elif pct >= 60:
        return "B"
    elif pct >= 45:
        return "C"
    else:
        return "D"
 

























