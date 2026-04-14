"""Scenario-based business case assessments.

Each case combines objectively graded decision questions with a free-text answer
that is assessed transparently: the learner scores themselves against a published
rubric after seeing an exemplar. No automatic grading of free text is claimed; an
optional keyword-coverage indicator is shown as *advisory only* and never scored.
"""

from __future__ import annotations

import io
import re

import numpy as np
import pandas as pd

from analytics_lab.i18n import t
from analytics_lab.models import BusinessCase, CaseObjective, RubricCriterion

LEVELS = ["0 - Missing or wrong", "1 - Partial", "2 - Solid", "3 - Excellent"]

STANDARD_RUBRIC = [
    RubricCriterion("Methodological correctness", "Uses appropriate methods and avoids analytical errors (e.g. mixing grains, causal overreach).", LEVELS, 1.0,
                    ["compare", "segment", "baseline", "control", "same period"]),
    RubricCriterion("Evidence", "Cites specific numbers from the evidence and connects them to the claim.", LEVELS, 1.0, ["%", "eur", "k", "rate"]),
    RubricCriterion("Reasoning", "Considers alternative explanations, assumptions and limitations.", LEVELS, 1.0,
                    ["alternative", "assum", "limitation", "however", "rule out", "consistent with"]),
    RubricCriterion("Communication", "Leads with the answer; clear, concise, audience-appropriate.", LEVELS, 1.0, []),
    RubricCriterion("Business relevance", "Ends with a concrete, owned, actionable recommendation.", LEVELS, 1.0, ["recommend", "should", "next step", "owner", "action"]),
]


# --------------------------------------------------------------------------- #
# Evidence builders (trusted app code; return a list of display blocks)          #
# --------------------------------------------------------------------------- #
def _fig_png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    import matplotlib.pyplot as plt

    plt.close(fig)
    return buf.getvalue()


def evidence_revenue_decline() -> list[tuple[str, object]]:
    from analytics_lab.data.loader import query_df

    monthly = query_df(
        """SELECT CAST(DATE_TRUNC('month', o.order_date) AS DATE) AS month, o.region,
                  SUM(oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0))) AS revenue
           FROM retail.orders o JOIN retail.order_items oi USING (order_id)
           WHERE o.status = 'Completed' AND o.order_date >= DATE '2024-01-01'
           GROUP BY ALL ORDER BY 1"""
    )
    cat = query_df(
        """SELECT c.category_name,
                  ROUND(SUM(CASE WHEN YEAR(o.order_date) = 2023 THEN oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0)) END), 0) AS aug_sep_2023,
                  ROUND(SUM(CASE WHEN YEAR(o.order_date) = 2024 THEN oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0)) END), 0) AS aug_sep_2024
           FROM retail.orders o JOIN retail.order_items oi USING (order_id)
           JOIN retail.products p USING (product_id) JOIN retail.categories c USING (category_id)
           WHERE o.status = 'Completed' AND o.region = 'West' AND MONTH(o.order_date) IN (8, 9)
           GROUP BY 1 ORDER BY 1"""
    )
    cat["change"] = cat["aug_sep_2024"] - cat["aug_sep_2023"]
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 3.6))
    for region, g in monthly.groupby("region"):
        ax.plot(pd.to_datetime(g["month"]), g["revenue"] / 1e3, label=region, linewidth=2.5 if region == "West" else 1.2,
                color="#d55e00" if region == "West" else None, alpha=1 if region == "West" else 0.6)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Revenue (EUR k)")
    ax.set_title("2024 monthly revenue by region")
    ax.legend(ncol=5, frameon=False, fontsize=8)
    return [
        ("md", t("**Exhibit 1** - Monthly completed revenue by region, 2024.")),
        ("img", _fig_png(fig)),
        ("md", t("**Exhibit 2** - West region revenue by category, August-September, 2023 vs 2024 (EUR).")),
        ("table", cat),
        ("md", t("**Exhibit 3** - Note from the regional VP: *\"A competitor launched an aggressive promotion in our region in August. We need to cut prices across the board.\"*")),
    ]


def evidence_churn_increase() -> list[tuple[str, object]]:
    from analytics_lab.data.loader import load_table

    cf = load_table("subscription", "churn_features")
    cf["period"] = np.where(cf["signup_date"] < pd.Timestamp("2024-04-01"), "Jan 2023-Mar 2024", "Apr-Sep 2024")
    overall = cf.groupby("period")["churned_6m"].agg(customers="size", churn_rate="mean").round(3)
    by_src = cf.pivot_table(index="acquisition_source", columns="period", values="churned_6m", aggfunc="mean").round(3)
    mix = pd.crosstab(cf["acquisition_source"], cf["period"], normalize="columns").round(3)
    return [
        ("md", t("**Exhibit 1** - 6-month churn by signup period.")),
        ("table", overall.reset_index()),
        ("md", t("**Exhibit 2** - 6-month churn rate by acquisition source and period.")),
        ("table", by_src.reset_index()),
        ("md", t("**Exhibit 3** - Share of sign-ups by acquisition source (columns sum to 1).")),
        ("table", mix.reset_index()),
        ("md", t("**Exhibit 4** - Context: the onboarding flow was redesigned in March 2024; the Basic plan price rose from EUR 19 to EUR 24 in July 2024; Paid Social spend tripled from April 2024.")),
    ]


def evidence_model_selection() -> list[tuple[str, object]]:
    table = pd.DataFrame(
        {
            "model": ["A: Random forest (all columns)", "B: Logistic regression", "C: Gradient boosting", "D: Majority-class baseline"],
            "features": ["engagement + plan + source + cancellation_reason", "engagement + plan + source", "engagement + plan + source + region + size", "none"],
            "cv_roc_auc": [0.995, 0.712, 0.724, 0.500],
            "cv_auc_std": [0.002, 0.014, 0.017, 0.0],
            "test_pr_auc": [0.990, 0.468, 0.481, 0.323],
            "train_auc": [1.000, 0.718, 0.861, 0.500],
            "explainability": ["low", "high", "medium", "n/a"],
        }
    )
    return [
        ("md", t("**Exhibit 1** - Results from the team's model comparison (temporal test set = sign-ups from April 2024, positive rate 32.3%).")),
        ("table", table),
        ("md", t("**Exhibit 2** - Business context: Customer Success can call 30% of new customers per month. Calls must be explainable to the account managers who make them.")),
    ]


def evidence_budget() -> list[tuple[str, object]]:
    from scipy.optimize import linprog

    from analytics_lab.data.loader import load_table

    ca = load_table("marketing", "channel_assumptions")
    A = np.vstack([np.ones(len(ca)), ca["risk_score"].values - 0.35])
    res = linprog(-ca["expected_margin_per_dollar"].values, A_ub=A, b_ub=[400_000, 0], bounds=list(zip(ca["min_spend"], ca["max_spend"])), method="highs")
    out = ca.copy()
    out["optimal_spend"] = np.round(res.x, 0)
    rows = []
    for b in (400_000, 500_000):
        for r in (0.35, 0.40):
            A2 = np.vstack([np.ones(len(ca)), ca["risk_score"].values - r])
            s = linprog(-ca["expected_margin_per_dollar"].values, A_ub=A2, b_ub=[b, 0], bounds=list(zip(ca["min_spend"], ca["max_spend"])), method="highs")
            rows.append({"budget": b, "risk_cap": r, "optimal_profit": round(-s.fun) if s.status == 0 else None, "total_spend": round(s.x.sum()) if s.status == 0 else None})
    return [
        ("md", t("**Exhibit 1** - Channel assumptions and the optimal allocation for EUR 400k with average risk <= 0.35.")),
        ("table", out),
        ("md", t("Optimal expected profit: **EUR {p:,.0f}**; total spend EUR {s:,.0f}. Dual values (profit per unit relaxation): budget {b:.3f}, risk constraint {r:.3f}.",
                 p=-res.fun, s=res.x.sum(), b=-res.ineqlin.marginals[0], r=-res.ineqlin.marginals[1])),
        ("md", t("**Exhibit 2** - Scenarios.")),
        ("table", pd.DataFrame(rows)),
        ("md", t("**Exhibit 3** - The CMO says: *\"Give me another EUR 100k and I'll deliver much more profit.\"*")),
    ]


def misleading_dashboard_png() -> bytes:
    """A deliberately flawed dashboard used for critique exercises (flaws listed in CRITIQUE_FLAWS)."""
    import matplotlib.pyplot as plt

    from analytics_lab.data.loader import query_df

    m = query_df(
        """SELECT CAST(DATE_TRUNC('month', o.order_date) AS DATE) AS month,
                  SUM(oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0))) AS revenue,
                  COUNT(DISTINCT o.order_id) AS orders
           FROM retail.orders o JOIN retail.order_items oi USING (order_id)
           WHERE o.status = 'Completed' AND o.region = 'West' AND o.order_date >= DATE '2024-03-01' AND o.order_date < DATE '2024-11-01'
           GROUP BY 1 ORDER BY 1"""
    )
    cats = query_df(
        """SELECT c.category_name, SUM(oi.quantity * oi.unit_price) AS rev
           FROM retail.order_items oi JOIN retail.products p USING (product_id) JOIN retail.categories c USING (category_id)
           GROUP BY 1 ORDER BY 2 DESC"""
    )
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    # Flaw: cumulative chart hides the Aug-Sep collapse; no axis labels.
    axes[0].plot(pd.to_datetime(m["month"]), m["revenue"].cumsum(), color="green", linewidth=3)
    axes[0].set_title("West revenue is GROWING strongly!")
    # Flaw: dual axis with arbitrary scales.
    ax2 = axes[1].twinx()
    axes[1].bar(pd.to_datetime(m["month"]), m["orders"], width=20, color="#7dd3fc")
    ax2.plot(pd.to_datetime(m["month"]), m["revenue"], color="red")
    ax2.set_ylim(m["revenue"].min() * 0.95, m["revenue"].max() * 1.02)
    axes[1].set_ylim(m["orders"].min() * 0.9, m["orders"].max() * 1.01)  # Flaw: truncated bar axis
    axes[1].set_title("Orders and revenue move together")
    axes[1].tick_params(axis="x", rotation=60)
    # Flaw: pie with 8 slices, rainbow colours, revenue before discounts.
    axes[2].pie(cats["rev"], labels=cats["category_name"], colors=plt.cm.rainbow(np.linspace(0, 1, len(cats))), startangle=90, textprops={"fontsize": 7})
    axes[2].set_title("Category share")
    fig.suptitle("WEST REGION - EXECUTIVE DASHBOARD", fontweight="bold")
    fig.tight_layout()
    return _fig_png(fig)


def evidence_chart_critique() -> list[tuple[str, object]]:
    return [
        ("md", t("**Exhibit** - The regional dashboard presented to the executive team last week.")),
        ("img", misleading_dashboard_png()),
        ("md", t("Data notes from the analyst: revenue for the pie chart was summed from list prices; the period shown is March-October 2024.")),
    ]


def evidence_kpis() -> list[tuple[str, object]]:
    return [
        ("md", t("""**Exhibit** - CloudNest's leadership team (CEO, CFO, Head of Customer Success, CMO) meets monthly. They want a single dashboard to track the health of the subscription business and know where to intervene.

Available data: `subscriptions`, `subscription_months` (MRR), `product_usage`, `support_tickets`, acquisition source and plan.

The current draft dashboard shows: total registered users (all time), website page views, number of support tickets, and a word cloud of ticket text.""")),
    ]


CRITIQUE_FLAWS = [
    ("Cumulative revenue line hides the August-September collapse", True),
    ("Dual axes with arbitrary scales imply a relationship", True),
    ("Truncated bar axis exaggerates differences in orders", True),
    ("Pie chart with eight slices and rainbow colours is hard to compare", True),
    ("Missing axis labels and units", True),
    ("Pie chart uses revenue before discounts, inconsistent with the KPI definition", True),
    ("The dashboard uses too few colours", False),
    ("Revenue is shown in EUR instead of USD", False),
]


# --------------------------------------------------------------------------- #
# Cases                                                                        #
# --------------------------------------------------------------------------- #
CASES: list[BusinessCase] = [
    BusinessCase(
        id="case_revenue_decline",
        title="Explain a sudden decline in revenue",
        module="diagnostic",
        competencies=["segmentation_rca", "causal_reasoning", "kpi_reporting"],
        scenario="West region revenue fell sharply in August and September 2024. The regional VP attributes it to a competitor promotion and proposes region-wide price cuts. You have 30 minutes before the leadership call.",
        evidence_builder="evidence_revenue_decline",
        objectives=[
            CaseObjective("Which explanation is most consistent with the evidence?",
                          ["A competitor promotion reduced demand across the region", "A supply problem (e.g. stock-out) in West Electronics", "A region-wide pricing error", "Normal seasonality"],
                          [1], "The decline is concentrated in a single category in a single region for exactly two months, then recovers - a supply pattern. A competitor promotion would typically affect several categories."),
            CaseObjective("Which additional evidence would best confirm your explanation? (select all that apply)",
                          ["Inventory / stock-out records for West Electronics", "Electronics website traffic and add-to-cart rates in West", "Competitor price data for other categories", "Company-wide employee headcount"],
                          [0, 1, 2], "Inventory records test the supply hypothesis directly; stable traffic with falling sales supports it; competitor prices for other categories help rule out the promotion story.", multi=True),
            CaseObjective("Should Northwind cut prices across the West region?",
                          ["Yes, immediately", "No - the evidence points to supply, not price; fix availability first", "Yes, but only for Electronics", "Only if revenue falls again next month"],
                          [1], "Price cuts would reduce margin on categories that are performing normally and would not fix a stock-out."),
        ],
        prompt="Write a short message (5-8 sentences) to the regional VP explaining what happened, how confident you are, what you would check next and what you recommend.",
        rubric=STANDARD_RUBRIC,
        exemplar="""West revenue fell ~39% in Aug-Sep 2024 versus 2023 (EUR ~79k -> ~49k), but almost all of it - and more - is Electronics, which collapsed from ~EUR 50k to ~EUR 8k while every other category was flat or up. The drop starts abruptly in August, ends in October, and does not appear in other regions. That pattern is more consistent with a supply problem (a stock-out or listing issue) than with a competitor promotion, which would normally hit several categories. We have not yet seen inventory records, so this remains a strong hypothesis rather than a confirmed cause. **Next step:** Operations to confirm Electronics stock levels for West in Aug-Sep (today); I will also check web traffic to Electronics pages. **Recommendation:** do not cut prices region-wide - it would reduce margin on healthy categories without addressing availability. Instead, add a stock-level alert for top Electronics SKUs.""",
    ),
    BusinessCase(
        id="case_churn_increase",
        title="Determine why customer churn increased",
        module="diagnostic",
        competencies=["causal_reasoning", "cohort_funnel", "segmentation_rca"],
        scenario="CloudNest's 6-month churn rose by about 7 percentage points for customers who signed up from April 2024. Product, marketing and finance each have a different explanation. The CEO asks you to settle it.",
        evidence_builder="evidence_churn_increase",
        objectives=[
            CaseObjective("What explains most of the increase in overall churn?",
                          ["Every acquisition source got substantially worse", "The mix shifted towards Paid Social, a high-churn source", "The onboarding redesign failed for all customers", "Random variation"],
                          [1], "Within-source churn is roughly stable while Paid Social's share jumped from ~15% to ~40% - a composition effect."),
            CaseObjective("Which statement is NOT supported by the evidence shown?",
                          ["Paid Social customers churn about twice as often as other customers", "The onboarding redesign caused the churn increase", "Paid Social's share of sign-ups increased after April 2024", "Within-source churn changed relatively little"],
                          [1], "If onboarding had failed broadly, churn would have risen within established sources too; it did not."),
            CaseObjective("What is the best next analysis to evaluate the price increase separately?",
                          ["Compare Basic vs other plans before/after July, excluding Paid Social (difference-in-differences)", "Compare total churn in 2023 vs 2024", "Survey current customers about price", "Count support tickets about billing"],
                          [0], "Comparing changes for the affected group against a comparison group, while removing the mix shift, isolates the price effect under a parallel-trends assumption."),
        ],
        prompt="Write a short memo for the CEO: what happened, what explains it, what is still uncertain, and what to do.",
        rubric=STANDARD_RUBRIC,
        exemplar="""Churn rose from ~25% to ~32% for April-September 2024 sign-ups. Most of the increase is a **mix effect**: Paid Social grew from ~15% to ~40% of sign-ups and churns at ~50% versus ~20% for other sources, while churn *within* each source changed little. This does not support a broad onboarding failure. The July Basic price rise may add a smaller effect; we will estimate it by comparing Basic with other plans before/after July, excluding Paid Social. **Uncertain:** whether Paid Social users churn because of poor fit or weak onboarding - a targeted onboarding experiment would tell us. **Actions:** judge Paid Social on 6-month retained revenue (CMO), run the onboarding test for Paid Social users (Product), and report Basic churn monthly (Finance).""",
    ),
    BusinessCase(
        id="case_model_selection",
        title="Select and evaluate a predictive model",
        module="predictive",
        competencies=["model_validation", "responsible_ml", "classification_modeling"],
        scenario="The data science team compared churn models. The project sponsor wants to deploy the one with the 'best number'.",
        evidence_builder="evidence_model_selection",
        objectives=[
            CaseObjective("Why must Model A be rejected?", ["It is too slow", "It uses cancellation_reason, which is only known after churn (target leakage)", "Random forests cannot be deployed", "Its AUC is too low"],
                          [1], "Near-perfect AUC driven by a post-outcome field is leakage; the model will fail in production."),
            CaseObjective("Between B and C, which is the more defensible choice for this use case?",
                          ["B: similar AUC within noise, far more explainable, smaller train-test gap", "C: highest AUC wins", "Neither: AUC below 0.8 is useless", "Average B and C without testing"],
                          [0], "The 0.012 AUC difference is within the CV standard deviations; explainability matters for account managers; C shows more overfitting."),
            CaseObjective("Which metric best communicates expected call outcomes to Customer Success?",
                          ["Precision at the threshold that flags 30% of customers", "Training accuracy", "R-squared", "Number of trees"],
                          [0], "Precision at the capacity-based threshold tells them how many calls reach true churn risks."),
        ],
        prompt="Write a recommendation to the sponsor: which model to deploy, why, how to set the threshold, and what to monitor.",
        rubric=STANDARD_RUBRIC,
        exemplar="""Deploy **Model B (logistic regression)**. Model A's AUC of 0.995 comes from `cancellation_reason`, which only exists after a customer cancels - it cannot work in production. B and C perform the same within noise (0.712 vs 0.724, std ~0.015), but B is explainable to account managers and overfits less (train 0.718 vs CV 0.712). Set the threshold to flag the top 30% of risk scores to match call capacity, and report precision at that threshold (expected ~4-5 in 10 calls reach a real churn risk vs ~3 in 10 at random). Monitor input drift (acquisition mix is shifting), monthly precision once outcomes arrive, and calibration; retrain quarterly or when precision drops by more than 5 points.""",
    ),
    BusinessCase(
        id="case_budget",
        title="Recommend a budget allocation",
        module="prescriptive",
        competencies=["optimization_modeling", "decision_analysis"],
        scenario="The optimisation model for next quarter's marketing budget has been run. The CMO wants an extra EUR 100k and asks for your recommendation.",
        evidence_builder="evidence_budget",
        objectives=[
            CaseObjective("Which constraint limits profit in the base case?", ["The total budget", "The average-risk policy", "Email's maximum spend only", "None - profit is unlimited"],
                          [1], "The budget's dual value is zero and spend is below EUR 400k; the risk constraint has a positive dual value."),
            CaseObjective("What happens if the budget rises to EUR 500k with the same risk policy?", ["Profit rises substantially", "Profit is unchanged", "The problem becomes infeasible", "Profit falls"],
                          [1], "Extra budget cannot be spent profitably without breaching the risk policy."),
            CaseObjective("What should you tell the CMO?", ["Approve the extra EUR 100k", "Extra budget adds nothing unless the risk policy is relaxed; discuss the policy instead", "Cut the budget by EUR 100k", "Spend the extra on the riskiest channel"],
                          [1], "The binding constraint is the policy; the decision belongs to leadership's risk appetite."),
        ],
        prompt="Write the recommendation for the CMO (allocation, why, what limits it, and when it would change).",
        rubric=STANDARD_RUBRIC,
        exemplar="""Allocate ~EUR 398k: Search 120k, Social 90k, Display 60k, Email 25k, Affiliate 50k and Video ~53k, for expected profit of ~EUR 143k. The binding constraint is the **average-risk policy (<= 0.35)**, not the budget - the model leaves ~EUR 2k unspent, and an extra EUR 100k would add **no** profit under the current policy. If leadership is willing to raise the risk cap to 0.40, profit rises to ~EUR 145k at the current budget and ~EUR 149k with EUR 500k. **Recommendation:** decline the extra budget for now and bring the risk-policy trade-off to the leadership meeting. **Assumptions:** linear margins within channel limits; subjective risk scores - revisit if Email or Search margins change by more than ~20%.""",
    ),
    BusinessCase(
        id="case_chart_critique",
        title="Critique a misleading chart",
        module="visualization",
        competencies=["viz_integrity", "chart_selection", "storytelling"],
        scenario="The West region dashboard below was presented to executives during the stock-out period. Nobody noticed the problem.",
        evidence_builder="evidence_chart_critique",
        objectives=[
            CaseObjective("Which problems does the dashboard have? (select all that apply)", [f[0] for f in CRITIQUE_FLAWS], [i for i, f in enumerate(CRITIQUE_FLAWS) if f[1]],
                          "Six genuine flaws: cumulative line, dual axes, truncated bars, eight-slice rainbow pie, missing labels and an inconsistent revenue definition. Colour count and currency are not problems.", multi=True),
            CaseObjective("What is the single most consequential flaw for decision makers?",
                          ["The cumulative revenue line hid a 39% two-month decline", "The pie chart colours", "The title font", "The x-axis tick rotation"],
                          [0], "It concealed the very event executives needed to see."),
        ],
        prompt="Propose a redesigned dashboard: list each problem, its effect on interpretation, and a specific fix.",
        rubric=STANDARD_RUBRIC,
        exemplar="""1. **Cumulative line** always rises and hid the Aug-Sep collapse -> plot monthly revenue with a zero baseline and annotate the stock-out. 2. **Dual axes** with arbitrary scales suggest orders and revenue move together -> two aligned panels or an indexed chart (Mar = 100). 3. **Truncated bar axis** exaggerates month-to-month order changes -> start bars at zero. 4. **Eight-slice rainbow pie** -> sorted horizontal bars with direct labels, colour-blind-safe palette. 5. **Missing labels/units** -> label axes (EUR, orders). 6. **Revenue before discounts** in the pie contradicts the KPI definition -> use completed revenue after discounts and state the definition in a footnote. Finally, replace the celebratory title with a neutral, finding-based one.""",
    ),
    BusinessCase(
        id="case_kpis",
        title="Recommend KPIs for a management dashboard",
        module="descriptive",
        competencies=["kpi_reporting", "storytelling"],
        scenario="CloudNest's leadership asks you to redesign their monthly dashboard so it shows the health of the business and where to intervene.",
        evidence_builder="evidence_kpis",
        objectives=[
            CaseObjective("Which KPIs belong on the leadership dashboard? (select all that apply)",
                          ["Monthly recurring revenue (MRR) and its growth", "6-month churn by signup cohort", "Net revenue retention", "First-month activation rate (e.g. share with >= 5 logins)", "Total registered users, all time", "Website page views", "Word cloud of ticket text"],
                          [0, 1, 2, 3], "MRR, cohort churn, net revenue retention and activation are outcome and driver metrics leadership can act on. All-time registered users and page views are vanity metrics; word clouds are not quantitative.", multi=True),
            CaseObjective("Why is 'total registered users (all time)' a poor leadership KPI?",
                          ["It can only go up and ignores churn, so it cannot signal problems", "It is too hard to compute", "It is a ratio", "It is confidential"],
                          [0], "A cumulative count hides losses - a vanity metric."),
        ],
        prompt="Propose 5-7 KPIs with a one-line definition each (formula, filter, owner, target) and explain how they connect (outcome vs driver metrics).",
        rubric=STANDARD_RUBRIC,
        exemplar="""**Outcome:** (1) MRR = sum of mrr for active customers in the month (owner CFO; target +3% MoM); (2) Net revenue retention = MRR this month from customers active 12 months ago / their MRR then (CFO; >= 100%). **Drivers:** (3) 6-month churn by signup cohort and source (Head of CS; <= 25%); (4) Activation = share of new customers with >= 5 logins in month 1 (Product; >= 60%); (5) New MRR by acquisition source, judged on 6-month retained revenue (CMO); (6) Support CSAT and median resolution time (Head of CS; >= 4.0, <= 24h). Outcome metrics tell leadership *whether* the business is healthy; driver metrics show *where* to intervene. Remove all-time registered users and page views (vanity) and the word cloud (not decision-relevant).""",
    ),
]

CASES_BY_ID = {c.id: c for c in CASES}
EVIDENCE_BUILDERS = {
    "evidence_revenue_decline": evidence_revenue_decline,
    "evidence_churn_increase": evidence_churn_increase,
    "evidence_model_selection": evidence_model_selection,
    "evidence_budget": evidence_budget,
    "evidence_chart_critique": evidence_chart_critique,
    "evidence_kpis": evidence_kpis,
}


def score_objectives(case: BusinessCase, answers: list[list[int]]) -> tuple[float, list[bool]]:
    results = [sorted(a) == sorted(obj.correct) for obj, a in zip(case.objectives, answers)]
    return (100.0 * sum(results) / len(results) if results else 0.0), results


def score_self_assessment(rubric: list[RubricCriterion], levels: dict[str, int]) -> float:
    total_w = sum(c.weight for c in rubric)
    got = sum(c.weight * levels.get(c.name, 0) for c in rubric)
    return round(100.0 * got / (3 * total_w), 1) if total_w else 0.0


def keyword_coverage(rubric: list[RubricCriterion], text: str) -> dict[str, list[str]]:
    """Advisory only: which indicator words appear in the answer. Not used for scoring."""
    low = text.lower()
    return {c.name: [k for k in c.indicators if re.search(re.escape(k), low)] for c in rubric if c.indicators}


def combined_score(objective: float, self_score: float) -> float:
    """Documented weighting: 50% objective questions, 50% rubric self-assessment."""
    return round(0.5 * objective + 0.5 * self_score, 1)
