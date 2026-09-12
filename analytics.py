"""
analytics.py  —  MAWSIM GOLD Intelligence Engine
Computes all business insights, Pareto analysis, performance gaps,
risk flags, and dynamic management recommendations from raw data.
Returns a structured dict consumed by all report builders.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ─────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────

@dataclass
class Observation:
    """A single natural-language observation with a severity tag."""
    text: str
    tag: str = "info"   # info | good | warning | critical


@dataclass
class Recommendation:
    priority: str        # High | Medium | Low
    action: str
    rationale: str


@dataclass
class DeptHealth:
    score: float         # 0–100
    label: str           # Excellent / Good / Moderate / Poor / Critical
    color: str           # hex


@dataclass
class DesignerInsight:
    name: str
    observations: List[str] = field(default_factory=list)
    commentary: str = ""


@dataclass
class Analytics:
    # ── top-level ──────────────────────────────────────────────
    dept_health:        DeptHealth = None
    overall_ach_pct:    float = 0.0
    avg_ach_pct:        float = 0.0
    total_pts:          float = 0.0
    total_target:       float = 0.0
    total_designs:      int   = 0
    total_nod:          int   = 0

    # ── designer groupings ─────────────────────────────────────
    top_performers:     List[str] = field(default_factory=list)   # ≥90%
    on_track:           List[str] = field(default_factory=list)   # 80-90%
    below_target:       List[str] = field(default_factory=list)   # 50-80%
    critical:           List[str] = field(default_factory=list)   # <50%
    zero_target:        List[str] = field(default_factory=list)   # no target set
    top_contributor:    str = ""
    lowest_contributor: str = ""
    most_designs:       str = ""
    least_designs:      str = ""
    near_target:        List[str] = field(default_factory=list)   # within 10% of target
    best_avg_pts:       str = ""  # highest avg points per design

    # ── concentration / Pareto ────────────────────────────────
    pareto_designers:   List[str] = field(default_factory=list)   # designers covering 80% output
    pareto_pct:         float = 0.0                               # % of team that covers 80%
    top2_contribution:  float = 0.0
    workload_balanced:  bool  = True
    concentration_risk: bool  = False

    # ── product / project / collection ────────────────────────
    top_product:        str = ""
    top_product_pct:    float = 0.0
    top2_products_pct:  float = 0.0
    top_project:        str = ""
    top_project_pct:    float = 0.0
    low_products:       List[str] = field(default_factory=list)   # <2% share
    single_project_risk: bool = False

    # ── work type ─────────────────────────────────────────────
    top_worktype:       str = ""
    top_worktype_pct:   float = 0.0

    # ── per-designer insights ──────────────────────────────────
    designer_insights:  Dict[str, DesignerInsight] = field(default_factory=dict)

    # ── observations & recommendations ───────────────────────
    observations:       List[Observation] = field(default_factory=list)
    recommendations:    List[Recommendation] = field(default_factory=list)

    # ── performance gap ───────────────────────────────────────
    performance_gap:    float = 0.0   # best - worst achievement %
    productivity_label: str   = ""    # High / Moderate / Low


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _health(pct: float) -> DeptHealth:
    if pct >= 90:
        return DeptHealth(pct, "Excellent",  "#1B5E20")
    elif pct >= 75:
        return DeptHealth(pct, "Good",       "#2E7D32")
    elif pct >= 55:
        return DeptHealth(pct, "Moderate",   "#E65100")
    elif pct >= 35:
        return DeptHealth(pct, "Poor",       "#C62828")
    else:
        return DeptHealth(pct, "Critical",   "#7B0000")


def _productivity(avg_pts: float) -> str:
    if avg_pts >= 0.40:
        return "High"
    elif avg_pts >= 0.25:
        return "Moderate"
    else:
        return "Low"


def _pareto(values: pd.Series, names: pd.Series, threshold=0.80):
    """Return names that cover `threshold` of total."""
    total = values.sum()
    if total == 0:
        return [], 0.0
    df = pd.DataFrame({"name": names, "val": values}).sort_values("val", ascending=False)
    df["cum"] = df["val"].cumsum() / total
    covering = df[df["cum"].shift(1, fill_value=0) < threshold]
    pct_team  = len(covering) / len(df) * 100
    return covering["name"].tolist(), round(pct_team, 1)


# ─────────────────────────────────────────────────────────────
# MAIN ENGINE
# ─────────────────────────────────────────────────────────────

def run(data: dict) -> Analytics:
    a   = Analytics()
    cad = data["cad_summary"]
    raw = data["cad_raw"]
    proj_a = data["project_analysis"]
    prod_a = data["product_analysis"]
    wt_a   = data["worktype_analysis"]
    coll_a = data["collection_analysis"]

    if cad.empty:
        return a

    # ── totals ────────────────────────────────────────────────
    a.total_pts     = round(cad["total_points"].sum(), 2)
    a.total_target  = round(cad["target"].sum(), 2)
    a.total_designs = int(cad["total_designs"].sum())
    a.total_nod     = int(cad["total_nod"].sum())
    a.overall_ach_pct = round((a.total_pts / a.total_target) * 100, 1) if a.total_target else 0
    a.avg_ach_pct   = round(cad["achievement_pct"].mean(), 1)
    a.dept_health   = _health(a.avg_ach_pct)

    avg_pts_per_design = round(a.total_pts / a.total_designs, 3) if a.total_designs else 0
    a.productivity_label = _productivity(avg_pts_per_design)

    # ── designer groups ────────────────────────────────────────
    a.top_performers  = cad[cad["achievement_pct"] >= 90]["cad_designer"].str.title().tolist()
    a.on_track        = cad[(cad["achievement_pct"] >= 80) & (cad["achievement_pct"] < 90)]["cad_designer"].str.title().tolist()
    a.below_target    = cad[(cad["achievement_pct"] >= 50) & (cad["achievement_pct"] < 80)]["cad_designer"].str.title().tolist()
    a.critical        = cad[cad["achievement_pct"] < 50]["cad_designer"].str.title().tolist()
    a.zero_target     = cad[cad["target"] == 0]["cad_designer"].str.title().tolist()

    # near target: remaining ≤ 10% of target (i.e. ≥ 90% done but < 100%)
    near = cad[(cad["achievement_pct"] >= 88) & (cad["achievement_pct"] < 100)]
    a.near_target = near["cad_designer"].str.title().tolist()

    top_c = cad.nlargest(1, "total_points")
    low_c = cad.nsmallest(1, "total_points")
    a.top_contributor    = top_c.iloc[0]["cad_designer"].title() if not top_c.empty else ""
    a.lowest_contributor = low_c.iloc[0]["cad_designer"].title() if not low_c.empty else ""

    top_d = cad.nlargest(1, "total_designs")
    low_d = cad.nsmallest(1, "total_designs")
    a.most_designs  = top_d.iloc[0]["cad_designer"].title() if not top_d.empty else ""
    a.least_designs = low_d.iloc[0]["cad_designer"].title() if not low_d.empty else ""

    top_avg = cad.nlargest(1, "avg_pts_per_design")
    a.best_avg_pts = top_avg.iloc[0]["cad_designer"].title() if not top_avg.empty else ""

    # ── Pareto ────────────────────────────────────────────────
    a.pareto_designers, a.pareto_pct = _pareto(
        cad["total_points"], cad["cad_designer"])
    n_pareto = len(a.pareto_designers)
    n_total  = len(cad)
    # top-2 contribution
    top2 = cad.nlargest(2, "total_points")
    a.top2_contribution = round(top2["total_points"].sum() / a.total_pts * 100, 1) if a.total_pts else 0

    a.concentration_risk = (n_pareto / n_total) <= 0.35 if n_total > 0 else False
    a.workload_balanced  = not a.concentration_risk

    # ── performance gap ───────────────────────────────────────
    a.performance_gap = round(
        cad["achievement_pct"].max() - cad["achievement_pct"].min(), 1)

    # ── product analysis ──────────────────────────────────────
    if not prod_a.empty:
        total_d = prod_a["designs"].sum()
        top_p   = prod_a.iloc[0]
        a.top_product     = str(top_p["product"]).title()
        a.top_product_pct = round(top_p["designs"] / total_d * 100, 1) if total_d else 0
        top2p = prod_a.head(2)
        a.top2_products_pct = round(top2p["designs"].sum() / total_d * 100, 1) if total_d else 0
        a.low_products = prod_a[prod_a["contribution_pct"] < 2]["product"].str.title().tolist()

    # ── project analysis ──────────────────────────────────────
    if not proj_a.empty:
        top_prj = proj_a.iloc[0]
        a.top_project     = str(top_prj["project"]).title()
        a.top_project_pct = round(top_prj["contribution_pct"], 1)
        a.single_project_risk = (a.top_project_pct > 70)

    # ── work type ─────────────────────────────────────────────
    if not wt_a.empty:
        total_wt = wt_a["designs"].sum()
        tw = wt_a.iloc[0]
        a.top_worktype     = str(tw["order_type"]).title()
        a.top_worktype_pct = round(tw["designs"] / total_wt * 100, 1) if total_wt else 0

    # ── per-designer insights ──────────────────────────────────
    for _, row in cad.iterrows():
        name = row["cad_designer"].title()
        obs  = []
        pct  = row["achievement_pct"]

        if pct >= 90:
            obs.append(f"Outstanding — achieved {pct:.1f}% of monthly target.")
        elif pct >= 80:
            obs.append(f"On track — {pct:.1f}% of target achieved.")
        elif pct >= 60:
            obs.append(f"Below target — {pct:.1f}% achieved. "
                       f"{row['remaining']:.2f} pts remaining.")
        elif pct >= 40:
            obs.append(f"Significantly below target — only {pct:.1f}% achieved. "
                       f"Needs immediate focus.")
        else:
            obs.append(f"Critical underperformance — {pct:.1f}% of target. "
                       f"Management intervention required.")

        # avg pts per design commentary
        avg = row["avg_pts_per_design"]
        if avg >= 0.45:
            obs.append(f"High average complexity per design ({avg:.3f} pts/design) — "
                       f"working on premium pieces.")
        elif avg <= 0.20:
            obs.append(f"Low average complexity ({avg:.3f} pts/design) — "
                       f"high volume, simpler designs.")

        # contribution
        obs.append(f"Contributed {row['contribution_pct']:.1f}% of department's total output.")

        # NOD vs designs
        if row["total_nod"] > 0:
            nod_ratio = row["total_designs"] / row["total_nod"] if row["total_nod"] else 0

        # commentary sentence
        if pct >= 80:
            commentary = (
                f"{name} is performing well this month with {row['total_points']:.2f} pts "
                f"against a target of {row['target']:.2f}, achieving {pct:.1f}%. "
                f"Contribution to department output is {row['contribution_pct']:.1f}%."
            )
        else:
            gap = row["remaining"]
            commentary = (
                f"{name} has earned {row['total_points']:.2f} pts against a target of "
                f"{row['target']:.2f} ({pct:.1f}%). A gap of {gap:.2f} pts remains. "
                f"At current pace, the monthly target may not be met."
            )

        a.designer_insights[row["cad_designer"]] = DesignerInsight(
            name=name, observations=obs, commentary=commentary)

    # ── observations ──────────────────────────────────────────
    obs = a.observations

    # Department health
    obs.append(Observation(
        f"Overall department achievement is {a.overall_ach_pct:.1f}% — "
        f"department health rated {a.dept_health.label}.",
        tag="good" if a.overall_ach_pct >= 75 else "warning" if a.overall_ach_pct >= 50 else "critical"
    ))

    # Top / bottom
    if a.top_performers:
        obs.append(Observation(
            f"{', '.join(a.top_performers)} achieved 90%+ of target — "
            f"exceptional performance this month.", tag="good"))
    if a.critical:
        obs.append(Observation(
            f"{len(a.critical)} designer(s) achieved less than 50% of target: "
            f"{', '.join(a.critical)}. Immediate management attention required.", tag="critical"))
    if a.below_target:
        obs.append(Observation(
            f"{len(a.below_target)} designer(s) are between 50–80% of target: "
            f"{', '.join(a.below_target)}. Require monitoring and support.", tag="warning"))

    # Near target
    if a.near_target:
        obs.append(Observation(
            f"{', '.join(a.near_target)} are within 12% of their target — "
            f"a final push could close the gap this month.", tag="info"))

    # Pareto / concentration
    pareto_names = ", ".join(a.pareto_designers[:4]) if a.pareto_designers else ""
    obs.append(Observation(
        f"{len(a.pareto_designers)} designer(s) ({pareto_names}) account for 80% "
        f"of the department's total points output.", tag="warning" if a.concentration_risk else "info"))

    if a.top2_contribution > 40:
        obs.append(Observation(
            f"Top 2 contributors ({a.top_contributor} and the next highest) generated "
            f"{a.top2_contribution:.1f}% of total points — "
            f"{'high concentration risk' if a.top2_contribution > 55 else 'moderate concentration'}.",
            tag="warning" if a.top2_contribution > 55 else "info"))

    # Performance gap
    obs.append(Observation(
        f"Performance gap between best and lowest achiever is {a.performance_gap:.1f} percentage points — "
        f"{'significant disparity requiring balancing' if a.performance_gap > 40 else 'manageable spread'}.",
        tag="warning" if a.performance_gap > 40 else "info"))

    # Product concentration
    if a.top_product:
        obs.append(Observation(
            f"{a.top_product} and {prod_a.iloc[1]['product'].title() if len(prod_a) > 1 else 'next product'} "
            f"account for {a.top2_products_pct:.1f}% of total design volume.",
            tag="info"))
    if a.low_products:
        obs.append(Observation(
            f"{', '.join(a.low_products)} collectively represent less than 2% each of production — "
            f"consider whether these categories need prioritisation or are declining.",
            tag="warning"))

    # Project risk
    if a.single_project_risk:
        obs.append(Observation(
            f"Project {a.top_project} contributes {a.top_project_pct:.1f}% of total output — "
            f"high dependence on a single project creates business risk.",
            tag="warning"))

    # Workload balance
    if not a.workload_balanced:
        obs.append(Observation(
            f"Workload is unevenly distributed. A small group is carrying the majority of output. "
            f"Review capacity allocation across the team.", tag="warning"))

    # Productivity
    obs.append(Observation(
        f"Average points per design is {avg_pts_per_design:.3f} — "
        f"design complexity productivity is {a.productivity_label}.",
        tag="good" if a.productivity_label == "High" else "warning" if a.productivity_label == "Low" else "info"))

    # ── recommendations ───────────────────────────────────────
    recs = a.recommendations

    if a.critical:
        recs.append(Recommendation(
            priority="High",
            action=f"Immediate performance review for: {', '.join(a.critical)}",
            rationale=f"These designers achieved less than 50% of their monthly target. "
                      f"Root causes must be identified — workload issues, complexity of assignments, "
                      f"or skill gaps — and corrective action taken before month-end."
        ))

    if a.below_target:
        recs.append(Recommendation(
            priority="Medium",
            action=f"Weekly check-in and support for: {', '.join(a.below_target)}",
            rationale=f"Designers between 50–80% of target need structured support to "
                      f"close the gap. Consider redistributing simpler work to accelerate points."
        ))

    if a.near_target:
        recs.append(Recommendation(
            priority="Medium",
            action=f"Prioritise remaining designs for: {', '.join(a.near_target)}",
            rationale=f"These designers are very close to their target. "
                      f"Clearing their pending work before month-end is a high-return action."
        ))

    if a.top_performers:
        recs.append(Recommendation(
            priority="Low",
            action=f"Recognise and reward: {', '.join(a.top_performers)}",
            rationale=f"Top performers set the standard for the department. "
                      f"Recognition reinforces performance culture and motivates the team."
        ))

    if a.concentration_risk:
        recs.append(Recommendation(
            priority="High",
            action="Rebalance workload distribution across the design team",
            rationale=f"A small group is generating 80% of output. This creates delivery risk "
                      f"if key designers are unavailable. Spread complex assignments more evenly."
        ))

    if a.single_project_risk:
        recs.append(Recommendation(
            priority="Medium",
            action=f"Diversify work allocation away from Project {a.top_project}",
            rationale=f"Over-reliance on a single project ({a.top_project_pct:.1f}% of output) "
                      f"is a business risk. Build capacity in other project categories."
        ))

    if a.low_products:
        recs.append(Recommendation(
            priority="Low",
            action=f"Review demand strategy for low-volume products: "
                   f"{', '.join(a.low_products[:4])}",
            rationale=f"These products have minimal design activity this month. "
                      f"Assess whether this reflects market demand changes or internal prioritisation."
        ))

    if a.productivity_label == "Low":
        recs.append(Recommendation(
            priority="Medium",
            action="Assess design complexity allocation and process efficiency",
            rationale=f"Average points per design is below 0.25, indicating a high volume of "
                      f"low-complexity work. Review if this aligns with business objectives "
                      f"or if higher-value designs can be incorporated."
        ))

    if a.performance_gap > 50:
        recs.append(Recommendation(
            priority="High",
            action="Investigate and address the wide performance gap across the team",
            rationale=f"A {a.performance_gap:.1f}-point gap between top and bottom achievers "
                      f"indicates structural inequities in workload, target-setting, or capability. "
                      f"A root-cause review is essential."
        ))

    return a
