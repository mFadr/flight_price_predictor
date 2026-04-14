"""Coding exercises for Module 4 - Prescriptive Analytics.

Optimisation problems can have several optimal solutions, so checks verify the
objective value and feasibility of the learner's own plan rather than an exact match.
"""

from analytics_lab.models import Check, Exercise

ASSIGN_COST = """cost = np.array([
    [42, 35, 28, 21, 39, 30],
    [30, 25, 32, 40, 27, 36],
    [26, 38, 30, 33, 41, 22],
    [37, 29, 24, 31, 26, 34],
    [33, 40, 36, 28, 22, 31],
    [28, 31, 39, 25, 35, 29],
])
technicians = ['Ana', 'Ben', 'Chen', 'Dara', 'Eli', 'Femi']
jobs = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6']
"""

EXERCISES = [
    Exercise(
        id="ex_py_ps1_product_mix",
        title="Optimal weekly product mix",
        module="prescriptive", language="python", difficulty="Intermediate", topic="Linear programming",
        competencies=["optimization_modeling"], lesson="ps1",
        business_question="Which weekly mix of kits maximises contribution margin within resource capacity, demand caps and commitments?",
        dataset="operations", tables=["operations.production_products", "operations.resource_capacity", "operations.resource_usage"],
        preload={"prod": "operations.production_products", "cap": "operations.resource_capacity", "use": "operations.resource_usage"},
        requirements=[
            "Decision variables: weekly units of each product (continuous is fine).",
            "Each product between min_weekly_commitment and max_weekly_demand; resource hours <= hours_available_per_week.",
            "`plan`: Series of units indexed by product name. `max_profit`: optimal weekly profit.",
            "`binding`: list of resource names whose capacity is fully used (slack < 1e-6).",
        ],
        expected_output="A Series, a float and a list.",
        starter_code="from scipy.optimize import linprog\n\nproducts = prod['product'].tolist()\nhours = use.pivot(index='resource', columns='product', values='hours_per_unit').loc[cap['resource'], products]\n\nplan = None\nmax_profit = None\nbinding = []\n",
        solution="from scipy.optimize import linprog\nproducts = prod['product'].tolist()\nhours = use.pivot(index='resource', columns='product', values='hours_per_unit').loc[cap['resource'], products]\nres = linprog(-prod['profit_per_unit'].values, A_ub=hours.values, b_ub=cap['hours_available_per_week'].values,\n              bounds=list(zip(prod['min_weekly_commitment'], prod['max_weekly_demand'])), method='highs')\nplan = pd.Series(res.x, index=products)\nmax_profit = -res.fun\nbinding = [r for r, s in zip(cap['resource'], res.slack) if s < 1e-6]\n",
        explanation="linprog minimises, so pass the negative profit vector and negate the optimum. Resources with zero slack are bottlenecks: only they constrain profit.",
        hints=["c = -profit_per_unit (maximise by minimising the negative).", "bounds = list(zip(min_weekly_commitment, max_weekly_demand)).", "res.slack holds unused hours per resource (A_ub rows)."],
        checks=[
            Check("optimal profit", "assert close(need('max_profit'), ref['max_profit'], tol=0.5), f'Your profit {need(\"max_profit\")} differs from the optimum. Did you negate the objective?'", weight=2),
            Check("plan is feasible", "p = pd.Series(need('plan'))\nprod = user['prod'].set_index('product'); cap = user['cap'].set_index('resource')\nu = user['use'].pivot(index='resource', columns='product', values='hours_per_unit')\np = p.reindex(prod.index)\nassert p.notna().all(), 'plan must contain every product name as index.'\nassert (p >= prod['min_weekly_commitment'] - 1e-6).all() and (p <= prod['max_weekly_demand'] + 1e-6).all(), 'plan violates a demand cap or commitment.'\nused = u[p.index].values @ p.values\nassert (used <= cap.loc[u.index, 'hours_available_per_week'].values + 1e-6).all(), 'plan exceeds a resource capacity.'"),
            Check("plan achieves the stated profit", "p = pd.Series(need('plan'))\nprofit = (p * user['prod'].set_index('product')['profit_per_unit'].reindex(p.index)).sum()\nassert close(profit, need('max_profit'), tol=0.5), 'max_profit does not equal the profit of your plan.'"),
            Check("bottlenecks identified", "assert sorted(need('binding')) == sorted(ref['binding']), f'Binding resources should be {sorted(ref[\"binding\"])}.'"),
        ],
        visible_tests=["Profit equals the optimum", "Plan satisfies all constraints", "Bottleneck resources identified"],
        rubric=[("Correct formulation", 40), ("Optimal and feasible", 40), ("Bottleneck interpretation", 20)],
    ),
    Exercise(
        id="ex_py_ps2_assignment",
        title="Assign technicians to jobs",
        module="prescriptive", language="python", difficulty="Intermediate", topic="Assignment problem",
        competencies=["optimization_modeling"], lesson="ps2",
        business_question="Assign six technicians to six jobs to minimise total travel-plus-work minutes.",
        dataset="none", tables=[],
        requirements=[
            "Use the provided cost matrix (rows = technicians, columns = jobs).",
            "`assignment`: dict technician -> job, each job used exactly once.",
            "`total_cost`: total minutes of your assignment (must be minimal).",
        ],
        expected_output="A dict with 6 entries and an integer.",
        starter_code="from scipy.optimize import linear_sum_assignment\n" + ASSIGN_COST + "\nassignment = {}\ntotal_cost = None\n",
        solution="from scipy.optimize import linear_sum_assignment\n" + ASSIGN_COST + "\nrows, cols = linear_sum_assignment(cost)\nassignment = {technicians[r]: jobs[c] for r, c in zip(rows, cols)}\ntotal_cost = int(cost[rows, cols].sum())\n",
        explanation="A greedy approach (each technician takes their cheapest remaining job) usually misses the optimum; the Hungarian algorithm guarantees the minimum total.",
        hints=["linear_sum_assignment(cost) returns row and column indices.", "Total = cost[rows, cols].sum()."],
        checks=[
            Check("valid one-to-one assignment", "a = need('assignment', dict)\nassert sorted(a.keys()) == sorted(user['technicians']), 'Every technician needs exactly one job.'\nassert sorted(a.values()) == sorted(user['jobs']), 'Every job must be assigned exactly once.'"),
            Check("total matches assignment", "a = need('assignment', dict)\nt = sum(user['cost'][user['technicians'].index(k), user['jobs'].index(v)] for k, v in a.items())\nassert int(need('total_cost')) == int(t), f'total_cost should equal the cost of your assignment ({t}).'"),
            Check("assignment is optimal", "assert int(need('total_cost')) == ref['total_cost'], f'Your total {need(\"total_cost\")} is not minimal. A greedy rule often misses the optimum.'", weight=2),
        ],
        visible_tests=["One-to-one assignment", "Total consistent with assignment", "Total is minimal"],
        rubric=[("Valid assignment", 40), ("Optimal", 60)],
    ),
    Exercise(
        id="ex_py_ps3_inventory",
        title="Reorder policy per SKU",
        module="prescriptive", language="python", difficulty="Intermediate", topic="EOQ and safety stock",
        competencies=["decision_analysis"], lesson="ps3",
        business_question="Set order quantities and reorder points for a 95% cycle service level.",
        dataset="operations", tables=["operations.inventory", "operations.daily_demand", "operations.suppliers"],
        preload={"inv": "operations.inventory", "dd": "operations.daily_demand", "sup": "operations.suppliers"},
        requirements=[
            "Use 2024 units_demanded: per SKU daily mean `d` and standard deviation `sd` (pandas default ddof=1).",
            "Lead time L = supplier contract_lead_time_days. z = scipy.stats.norm.ppf(0.95).",
            "eoq = sqrt(2 * (d * 365) * order_cost / (unit_cost * annual_holding_cost_rate)).",
            "safety_stock = z * sd * sqrt(L); reorder_point = d * L + safety_stock.",
            "`policy`: DataFrame with columns sku, eoq, safety_stock, reorder_point (one row per SKU).",
        ],
        expected_output="20 rows x 4 columns.",
        starter_code="from scipy.stats import norm\n\npolicy = None\n",
        solution="from scipy.stats import norm\nd24 = dd[dd['date'].dt.year == 2024]\nst = d24.groupby('sku')['units_demanded'].agg(d='mean', sd='std').reset_index()\ndf = inv.merge(st, on='sku').merge(sup[['supplier_id', 'contract_lead_time_days']], on='supplier_id')\nz = norm.ppf(0.95)\nL = df['contract_lead_time_days']\ndf['eoq'] = np.sqrt(2 * df['d'] * 365 * df['order_cost'] / (df['unit_cost'] * df['annual_holding_cost_rate']))\ndf['safety_stock'] = z * df['sd'] * np.sqrt(L)\ndf['reorder_point'] = df['d'] * L + df['safety_stock']\npolicy = df[['sku', 'eoq', 'safety_stock', 'reorder_point']]\n",
        explanation="Safety stock scales with demand variability and the square root of lead time; SKUs from slow suppliers need larger buffers for the same service level.",
        hints=["Filter dates with dd['date'].dt.year == 2024.", "Merge inventory with suppliers to get lead times.", "Watch units: annual demand = daily mean * 365; holding cost per unit per year = unit_cost * rate."],
        checks=[
            Check("structure", "p = need('policy', pd.DataFrame)\nassert len(p) == 20, f'Expected 20 SKUs, got {len(p)}.'\nfor c in ['sku', 'eoq', 'safety_stock', 'reorder_point']:\n    assert c in p.columns, f'Missing column {c}.'"),
            Check("EOQ", "frames_match(need('policy'), ref['policy'], columns=['sku', 'eoq'], sort_by=['sku'], rtol=1e-6)"),
            Check("safety stock and reorder point", "frames_match(need('policy'), ref['policy'], columns=['sku', 'safety_stock', 'reorder_point'], sort_by=['sku'], rtol=1e-6)", weight=2),
        ],
        visible_tests=["20 SKUs with required columns", "EOQ, safety stock and reorder point match the reference"],
        rubric=[("Correct demand statistics", 30), ("Correct EOQ", 30), ("Correct safety stock / ROP", 40)],
    ),
    Exercise(
        id="ex_py_ps4_monte_carlo",
        title="Promotion risk simulation",
        module="prescriptive", language="python", difficulty="Advanced", topic="Monte Carlo",
        competencies=["simulation_risk"], lesson="ps4",
        business_question="What is the expected profit and risk of loss of the promotion?",
        dataset="none", tables=[],
        requirements=[
            "Simulate at least 100,000 scenarios: units ~ Normal(1000, 250) clipped at 0; unit margin ~ Uniform(4, 9); fixed cost EUR 5,000.",
            "profit = units * margin - 5000.",
            "`expected_profit` (mean), `prob_loss` (share of scenarios with profit < 0), `p5` (5th percentile).",
        ],
        expected_output="Three floats (any seed; Monte Carlo tolerance applies).",
        starter_code="rng = np.random.default_rng(42)\nn = 100_000\n\nexpected_profit = None\nprob_loss = None\np5 = None\n",
        solution="rng = np.random.default_rng(42)\nn = 100_000\nunits = rng.normal(1000, 250, n).clip(min=0)\nmargin = rng.uniform(4, 9, n)\nprofit = units * margin - 5000\nexpected_profit = profit.mean()\nprob_loss = (profit < 0).mean()\np5 = np.percentile(profit, 5)\n",
        explanation="Expected profit is about EUR 1,500, but roughly a quarter of scenarios lose money, and the 5th percentile is a loss of roughly EUR 1,700. The decision depends on risk appetite.",
        hints=["Draw arrays of size n - no loops needed.", "rng.uniform(4, 9, n) for margins.", "np.percentile(profit, 5)."],
        checks=[
            Check("expected profit", "v = float(need('expected_profit'))\nassert abs(v - ref['expected_profit']) < 60, f'Expected profit {v:,.0f} is outside Monte Carlo tolerance of ~{ref[\"expected_profit\"]:,.0f}. Check the distributions and fixed cost.'", weight=2),
            Check("probability of loss", "v = float(need('prob_loss'))\nassert 0 <= v <= 1, 'prob_loss should be a fraction between 0 and 1.'\nassert abs(v - ref['prob_loss']) < 0.012, f'P(loss) {v:.3f} differs from ~{ref[\"prob_loss\"]:.3f}.'", weight=2),
            Check("5th percentile", "v = float(need('p5'))\nassert abs(v - ref['p5']) < 80, f'5th percentile {v:,.0f} differs from ~{ref[\"p5\"]:,.0f}.'"),
        ],
        visible_tests=["Expected profit, P(loss) and 5th percentile within Monte Carlo tolerance"],
        rubric=[("Correct distributions", 40), ("Correct risk measures", 40), ("Vectorised, reproducible", 20)],
    ),
    Exercise(
        id="ex_py_ps5_budget",
        title="Marketing budget allocation with a risk policy",
        module="prescriptive", language="python", difficulty="Professional", topic="LP with sensitivity",
        competencies=["optimization_modeling", "decision_analysis"], lesson="ps5",
        business_question="Allocate EUR 400,000 across channels to maximise expected profit with a portfolio risk limit.",
        dataset="marketing", tables=["marketing.channel_assumptions"], preload={"ca": "marketing.channel_assumptions"},
        requirements=[
            "Maximise sum(expected_margin_per_dollar * spend). Spend per channel between min_spend and max_spend.",
            "Total spend <= 400,000. Spend-weighted average risk_score <= 0.35 (linearise: sum((risk - 0.35) * spend) <= 0).",
            "`allocation`: Series of spend indexed by channel. `expected_profit`: optimal objective.",
            "`budget_shadow_price`: extra profit per extra EUR of budget (zero or positive).",
        ],
        expected_output="A Series and two floats.",
        starter_code="from scipy.optimize import linprog\n\nallocation = None\nexpected_profit = None\nbudget_shadow_price = None\n",
        solution="from scipy.optimize import linprog\nA = np.vstack([np.ones(len(ca)), ca['risk_score'].values - 0.35])\nb = np.array([400_000, 0.0])\nres = linprog(-ca['expected_margin_per_dollar'].values, A_ub=A, b_ub=b, bounds=list(zip(ca['min_spend'], ca['max_spend'])), method='highs')\nallocation = pd.Series(res.x, index=ca['channel'])\nexpected_profit = -res.fun\nbudget_shadow_price = -res.ineqlin.marginals[0]\n",
        explanation="The risk constraint is binding, so the optimiser cannot use the whole budget profitably: the budget's shadow price is 0. Telling the CMO 'extra budget is worth nothing under the current risk policy; relaxing the policy is what adds profit' is the key insight - solver output alone would hide it.",
        hints=["Two inequality rows: total spend and risk-weighted spend.", "Negate margins to maximise; negate the dual of the budget row to get a positive shadow price.", "Alternatively re-solve with budget + 1,000 and divide the profit change by 1,000."],
        checks=[
            Check("optimal profit", "assert close(need('expected_profit'), ref['expected_profit'], tol=1.0), 'Expected profit is not optimal. Check both constraints and bounds.'", weight=2),
            Check("allocation feasible", "a = pd.Series(need('allocation')).reindex(user['ca']['channel']).values.astype(float)\nca_ = user['ca']\nassert not np.isnan(a).any(), 'allocation must be indexed by channel name.'\nassert a.sum() <= 400_000 + 1e-3, 'Total spend exceeds the budget.'\nassert ((a >= ca_['min_spend'].values - 1e-3) & (a <= ca_['max_spend'].values + 1e-3)).all(), 'A channel is outside its min/max spend.'\nassert (a * ca_['risk_score'].values).sum() / a.sum() <= 0.35 + 1e-6, 'Average risk exceeds 0.35.'"),
            Check("budget shadow price", "assert close(need('budget_shadow_price'), ref['budget_shadow_price'], tol=0.005), f'Shadow price should be about {ref[\"budget_shadow_price\"]:.3f} profit per extra EUR. Mind the sign when you minimised -profit, and check whether the budget is actually fully used.'"),
        ],
        visible_tests=["Profit is optimal", "Allocation respects budget, bounds and risk policy", "Budget shadow price correct"],
        rubric=[("Correct formulation incl. risk linearisation", 40), ("Optimal & feasible", 30), ("Sensitivity (shadow price)", 30)],
    ),
]
