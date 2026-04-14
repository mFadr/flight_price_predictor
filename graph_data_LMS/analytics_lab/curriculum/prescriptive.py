"""Module 4 - Prescriptive Analytics (Python, R)."""

from analytics_lab.models import Lesson, WorkedExample

LESSONS = [
    Lesson(
        id="ps1",
        module="prescriptive",
        level="Beginner",
        title="Optimisation fundamentals: decision variables, objectives and constraints",
        tools=["Python", "R"],
        minutes=50,
        competencies=["optimization_modeling", "decision_analysis"],
        objectives=[
            "Translate a business problem into decision variables, an objective and constraints.",
            "Recognise feasible, infeasible and unbounded problems.",
            "Solve a linear programme with scipy.optimize.linprog.",
            "Interpret binding constraints and slack.",
        ],
        concept="""
Prescriptive analytics recommends **actions**. Optimisation is its core tool. Every model has three parts:

| Part | Question | Product-mix example |
|---|---|---|
| Decision variables | What can we choose? | units of each kit to assemble per week (x1..x4) |
| Objective | What are we maximising or minimising? | total contribution margin = 24x1 + 41x2 + 13x3 + 30x4 |
| Constraints | What limits us? | assembly, testing, packing hours; demand caps; contractual minimums; x >= 0 |

**Linear programming (LP)** requires a linear objective and linear constraints. LPs are solved quickly and to proven optimality. The **feasible region** is the set of decisions satisfying all constraints; the optimum lies at a corner of it.

* *Infeasible* - no decision satisfies all constraints (e.g. minimum commitments exceed capacity). Report which constraints conflict.
* *Unbounded* - the objective can improve forever: a missing constraint.
* *Binding constraint* - used fully at the optimum (zero slack). Only binding constraints limit profit; relaxing a non-binding one changes nothing.
* *Integer variables* (units, yes/no decisions) need mixed-integer programming (`scipy.optimize.milp` or PuLP). Rounding an LP solution can be infeasible or suboptimal.

**scipy's form:** `linprog` **minimises** c @ x subject to `A_ub @ x <= b_ub`, `A_eq @ x == b_eq` and bounds. To maximise profit, minimise **negative** profit.

**R equivalent:**

```r
library(lpSolve)
sol <- lp("max", objective.in = profit, const.mat = A, const.dir = rep("<=", nrow(A)), const.rhs = b)
sol$solution; sol$objval
```
""",
        business_context="""
Meridian Supply assembles four kits on shared Assembly, Testing and Packing resources. The plant manager currently schedules "whatever sold well last week". You will compute the profit-maximising weekly mix and identify which resource is the bottleneck.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"prod": "operations.production_products", "cap": "operations.resource_capacity", "use": "operations.resource_usage"},
            code="""from scipy.optimize import linprog

products = prod["product"].tolist()
hours = use.pivot(index="resource", columns="product", values="hours_per_unit").loc[cap.resource, products]

c = -prod["profit_per_unit"].values                    # maximise profit -> minimise -profit
A_ub = hours.values                                    # hours used per resource
b_ub = cap["hours_available_per_week"].values
bounds = list(zip(prod["min_weekly_commitment"], prod["max_weekly_demand"]))

res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
print(res.message)
print(pd.Series(res.x, index=products).round(1))
print(f"Max weekly profit: EUR {-res.fun:,.0f}")
print(pd.DataFrame({"used": A_ub @ res.x, "available": b_ub, "slack": res.slack}, index=cap.resource).round(1))""",
            explanation="""
* Bounds encode the demand caps (upper) and contractual minimums (lower).
* `res.slack` shows unused hours: a resource with zero slack is a **binding** bottleneck. Extra hours there would increase profit; extra hours elsewhere would not.
* **Communicate as a decision:** "Assemble X Pro Kits ... Testing capacity is the bottleneck; every additional Testing hour is worth about EUR Y (see the sensitivity lesson)."
""",
        ),
        extra_examples=[
            WorkedExample(
                language="r",
                runnable=False,
                code="""# R equivalent with lpSolve (install.packages("lpSolve"))
library(lpSolve)
profit <- c(24, 41, 13, 30)
A <- rbind(c(0.6, 1.1, 0.3, 0.8),    # Assembly
           c(0.20, 0.55, 0.10, 0.15), # Testing
           c(0.25, 0.30, 0.20, 0.50), # Packing
           diag(4), diag(4))
rhs <- c(520, 210, 300, 400, 180, 600, 250, 50, 20, 0, 40)
dir <- c(rep("<=", 7), rep(">=", 4))
sol <- lp("max", profit, A, dir, rhs)
sol$solution; sol$objval""",
                explanation="lpSolve expresses bounds as extra constraint rows (max demand <=, min commitment >=). The optimum matches scipy's.",
            )
        ],
        knowledge_check=["q_ps_001", "q_ps_002", "q_ps_003"],
        guided_exercise="ex_py_ps1_product_mix",
        challenge=None,
        summary=[
            "Model = decision variables + objective + constraints.",
            "linprog minimises; negate the objective to maximise.",
            "Binding constraints are the bottlenecks that limit the objective.",
            "Use integer programming when decisions must be whole numbers.",
        ],
        common_mistakes=[
            "Forgetting to negate the objective when maximising.",
            "Omitting non-negativity or demand caps (unbounded solutions).",
            "Rounding LP solutions without re-checking feasibility.",
        ],
        revision="Remove the demand caps and observe what happens to the solution.",
        next_lesson="ps2",
        order=21,
    ),
    Lesson(
        id="ps2",
        module="prescriptive",
        level="Intermediate",
        title="Resource allocation, assignment and scheduling",
        tools=["Python"],
        minutes=45,
        competencies=["optimization_modeling"],
        objectives=[
            "Model assignment problems and solve them with linear_sum_assignment.",
            "Formulate capacity planning and resource allocation with mixed-integer programming.",
            "Represent scheduling rules (coverage, max hours) as constraints.",
        ],
        concept="""
**Assignment problems** match n workers to n tasks at minimum total cost (or maximum value), each worker doing one task. The Hungarian algorithm solves them exactly: `scipy.optimize.linear_sum_assignment(cost_matrix)`. Rectangular matrices are allowed (some workers stay unassigned).

**Resource allocation** splits a limited resource (budget, staff hours, trucks) across uses to maximise value. With linear returns this is an LP; with diminishing returns it becomes non-linear - often approximated piecewise linearly.

**Capacity planning** decides how much capacity to add (shifts, machines), usually with **integer** or **binary** decisions (open a second shift: yes/no) and fixed costs. Binary variables also model logic: "if we open warehouse B (y = 1) we can ship from it" -> `shipments_B <= M * y`.

**Scheduling** assigns people or jobs to time slots subject to rules:

* coverage: each hour needs at least k staff;
* limits: each person works at most 40 hours and at most 5 shifts;
* sequencing: job A before job B.

These become integer programmes. `scipy.optimize.milp` handles them; PuLP (optional) offers a friendlier modelling syntax.

**Modelling tips:** start small and verify by hand; name variables and constraints; check the solution against every business rule; ask stakeholders which rules are hard (must) vs soft (prefer) - soft rules become penalties in the objective.
""",
        business_context="""
Meridian's field-service manager must assign five technicians to five urgent repair jobs. Travel and skill differences make some assignments far more expensive. Today it is done by hand each morning.
""",
        worked_example=WorkedExample(
            language="python",
            code="""from scipy.optimize import linear_sum_assignment, milp, LinearConstraint, Bounds

# Hours needed by technician (rows) for each job (columns)
cost = np.array([[4, 9, 6, 7, 8],
                 [6, 4, 8, 5, 9],
                 [7, 8, 3, 9, 6],
                 [5, 7, 7, 4, 8],
                 [9, 6, 8, 7, 5]])
rows, cols = linear_sum_assignment(cost)
print({f"tech_{r + 1}": f"job_{c + 1}" for r, c in zip(rows, cols)}, "total hours:", cost[rows, cols].sum())

# Staffing as an integer programme: minimum staff per shift, minimise headcount cost
need = np.array([3, 5, 4])          # morning, afternoon, night requirements
cost_per_shift = np.array([100, 100, 130])
res = milp(c=cost_per_shift, constraints=LinearConstraint(np.eye(3), lb=need), integrality=np.ones(3), bounds=Bounds(0, 10))
print("staff per shift:", res.x, "cost:", res.fun)""",
            explanation="""
* `linear_sum_assignment` returns the optimal row/column pairs; the total (here 20 hours) is provably minimal.
* The staffing example is trivial on purpose: with coverage constraints only, staff equals need. Adding rules (e.g. people work two consecutive shifts) makes the integer programme meaningful.
* Always check: does each job have exactly one technician, and is the result explainable to the people affected?
""",
        ),
        knowledge_check=["q_ps_004", "q_ps_005", "q_ps_006"],
        guided_exercise="ex_py_ps2_assignment",
        challenge=None,
        summary=[
            "Assignment problems have exact, fast solutions (Hungarian algorithm).",
            "Binary variables model yes/no decisions and logical rules.",
            "Scheduling rules translate into coverage and limit constraints.",
            "Separate hard constraints from soft preferences (penalties).",
        ],
        common_mistakes=[
            "Using greedy rules (best match first) that miss the global optimum.",
            "Ignoring integrality for headcount or units.",
            "Encoding preferences as hard constraints and making the problem infeasible.",
        ],
        revision="Add a sixth job and a rule that technician 3 cannot do job 1 (cost = large number).",
        next_lesson="ps3",
        order=22,
    ),
    Lesson(
        id="ps3",
        module="prescriptive",
        level="Intermediate",
        title="Inventory, reorder and pricing decisions",
        tools=["Python"],
        minutes=50,
        competencies=["decision_analysis", "optimization_modeling"],
        objectives=[
            "Compute the economic order quantity (EOQ).",
            "Set reorder points and safety stock for a target service level.",
            "Evaluate pricing and discount scenarios with an explicit demand response.",
            "Run a cost-benefit analysis of an operational change.",
        ],
        concept="""
**Inventory trade-off:** ordering often costs order fees; ordering rarely means holding lots of stock.

**EOQ** (economic order quantity) minimises ordering + holding cost under steady demand:

```
EOQ = sqrt(2 * D * S / H)
D = annual demand (units), S = cost per order, H = annual holding cost per unit (= unit_cost * holding rate)
```

**Reorder point (ROP)** - when stock falls to ROP, place an order:

```
ROP = expected demand during lead time + safety stock = d * L + z * sigma_d * sqrt(L)
```

where d is average daily demand, sigma_d the daily standard deviation, L the lead time in days and z the service-level factor (z = 1.645 for 95% cycle service, 2.054 for 98%). This formula assumes independent daily demand and a fixed lead time; variable lead times need a larger buffer.

**Pricing scenarios.** Revenue and profit respond to price through demand. With a constant **price elasticity** e, `Q_new = Q * (P_new / P)^e`. For e = -1.5, a 10% discount raises volume by ~17% - but profit may still fall if margins are thin:

```
profit = Q_new * (P_new - unit_cost)
```

**Cost-benefit analysis:** list incremental costs and benefits, put them on a common time basis (annual or NPV), state assumptions, and compute break-even values ("the change pays off if lead time falls by at least 2 days").
""",
        business_context="""
Meridian's planners reorder "when it feels low". Stock-outs happen several times per month on fast movers, while slow movers tie up cash. You will set data-driven order quantities and reorder points, and evaluate a proposed 10% discount.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"inv": "operations.inventory", "dd": "operations.daily_demand", "sup": "operations.suppliers"},
            code="""from scipy.stats import norm

d24 = dd[dd.date.dt.year == 2024]
stats = d24.groupby("sku").units_demanded.agg(daily_mean="mean", daily_std="std")
df = inv.merge(stats, on="sku").merge(sup[["supplier_id", "contract_lead_time_days"]], on="supplier_id")
df = df.rename(columns={"reorder_point": "current_rop"})

df["annual_demand"] = df.daily_mean * 365
df["H"] = df.unit_cost * df.annual_holding_cost_rate
df["eoq"] = np.sqrt(2 * df.annual_demand * df.order_cost / df.H)
z = norm.ppf(0.95)
L = df.contract_lead_time_days
df["safety_stock"] = z * df.daily_std * np.sqrt(L)
df["reorder_point"] = df.daily_mean * L + df.safety_stock
print(df[["sku", "daily_mean", "eoq", "safety_stock", "reorder_point", "current_rop"]].round(0).head(8))

# Pricing scenario for one SKU with assumed elasticity -1.5
p, c, q = 20.0, 12.0, 1000
for disc in [0, 0.05, 0.10]:
    q_new = q * ((p * (1 - disc)) / p) ** -1.5
    print(f"discount {disc:.0%}: units {q_new:.0f}, profit {q_new * (p * (1 - disc) - c):,.0f}")""",
            explanation="""
* SKUs from long-lead-time suppliers need much larger safety stocks for the same service level - an argument for supplier diversification.
* Compare the computed reorder points with the current ones in `inventory` to find SKUs at risk of stock-outs.
* The pricing example shows that a discount which increases units can still **reduce profit** when margins are thin: elasticity assumptions drive the decision, so test several.
""",
        ),
        knowledge_check=["q_ps_007", "q_ps_008", "q_ps_009"],
        guided_exercise="ex_py_ps3_inventory",
        challenge=None,
        summary=[
            "EOQ balances ordering and holding costs.",
            "Reorder point = lead-time demand + safety stock; safety stock grows with variability and lead time.",
            "Price decisions depend on elasticity and margin - more volume is not always more profit.",
            "Make cost-benefit assumptions explicit and compute break-even values.",
        ],
        common_mistakes=[
            "Using average demand only (no safety stock).",
            "Mixing time units (annual holding cost with daily demand).",
            "Assuming a discount pays for itself because volume increases.",
        ],
        revision="Recompute safety stock at 98% service and compare the extra holding cost.",
        next_lesson="ps4",
        order=23,
    ),
    Lesson(
        id="ps4",
        module="prescriptive",
        level="Advanced",
        title="Monte Carlo simulation and risk",
        tools=["Python", "R"],
        minutes=50,
        competencies=["simulation_risk", "decision_analysis"],
        objectives=[
            "Represent uncertain inputs with probability distributions.",
            "Simulate outcome distributions with Monte Carlo methods.",
            "Summarise risk: expected value, probability of loss, percentiles (VaR).",
            "Compare decisions under uncertainty, not just at average inputs.",
        ],
        concept="""
Deterministic models use single "best guesses". But **the average of outcomes is not the outcome of averages** when models are non-linear or have caps and floors (e.g. sales cannot exceed stock).

**Monte Carlo simulation**

1. Identify uncertain inputs and choose distributions (normal, lognormal for positive skewed values, triangular when experts give min/likely/max, uniform when only a range is known).
2. Draw thousands of scenarios with a seeded random generator (`np.random.default_rng(42)`).
3. Compute the outcome for each scenario (vectorised NumPy, not Python loops).
4. Summarise the distribution: mean, standard deviation, percentiles, probability of meeting a target or making a loss.

**Risk measures**

* P(loss) - probability profit < 0.
* 5th percentile (Value at Risk at 95%) - a bad-but-plausible outcome.
* Expected shortfall - average outcome in the worst 5%.

**Decision rule.** Risk-neutral decision makers pick the highest expected value; risk-averse ones may prefer a slightly lower mean with a much smaller chance of loss. Make the risk appetite explicit.

**Good practice:** justify distributions with data or expert input; include correlations between inputs when they matter (e.g. demand and price); report Monte Carlo error (it shrinks with sqrt(n)); run sensitivity on the distribution assumptions.

**R equivalent:** `rnorm`, `runif`, `quantile(profit, 0.05)`, `mean(profit < 0)`.
""",
        business_context="""
Marketing proposes a one-off promotion with a EUR 5,000 fixed cost. Demand and unit margin are uncertain. The finance director asks: "What do we expect to make, and what is the chance we lose money?"
""",
        worked_example=WorkedExample(
            language="python",
            code="""rng = np.random.default_rng(42)
n = 100_000
units = rng.normal(1000, 250, n).clip(min=0)          # uncertain demand
margin = rng.triangular(4, 6, 9, n)                   # expert range for unit margin
fixed = 5000
profit = units * margin - fixed

print(f"expected profit:   {profit.mean():8,.0f}")
print(f"P(loss):           {(profit < 0).mean():8.1%}")
print(f"5th percentile:    {np.percentile(profit, 5):8,.0f}")
print(f"expected shortfall (worst 5%): {profit[profit <= np.percentile(profit, 5)].mean():8,.0f}")

# What if we cap stock at 1,100 units? Sales cannot exceed stock.
capped = np.minimum(units, 1100) * margin - fixed
print(f"with stock cap: expected {capped.mean():,.0f}, P(loss) {(capped < 0).mean():.1%}")
print(f"deterministic plan at average inputs: {1000 * margin.mean() - fixed:,.0f}")""",
            explanation="""
* The simulated distribution shows a meaningful probability of loss that a single 'average' calculation hides.
* The stock cap truncates the upside: expected profit falls below the deterministic estimate - an example of why averages of inputs mislead.
* **Recommendation framing:** "Expected profit about EUR X; roughly a Y% chance of a loss; in a bad case (5th percentile) we lose about EUR Z. Proceed if that risk is acceptable."
""",
        ),
        knowledge_check=["q_ps_010", "q_ps_011", "q_ps_012"],
        guided_exercise="ex_py_ps4_monte_carlo",
        challenge=None,
        summary=[
            "Model uncertain inputs as distributions; simulate thousands of scenarios.",
            "Report expected value and risk (P(loss), percentiles, expected shortfall).",
            "Non-linearities (caps, floors) make 'plan at averages' biased.",
            "Seed simulations for reproducibility and test distribution assumptions.",
        ],
        common_mistakes=[
            "Planning at average inputs and ignoring variability.",
            "Using Python loops instead of vectorised draws (slow).",
            "Choosing distributions without justification.",
        ],
        revision="Re-run with demand ~ lognormal and compare P(loss).",
        next_lesson="ps5",
        order=24,
    ),
    Lesson(
        id="ps5",
        module="prescriptive",
        level="Professional",
        title="Sensitivity analysis, scenarios and recommendations",
        tools=["Python"],
        minutes=55,
        competencies=["decision_analysis", "optimization_modeling", "simulation_risk"],
        objectives=[
            "Read shadow prices and reduced costs from an LP.",
            "Run one-way sensitivity (tornado) and scenario analyses.",
            "Balance trade-offs among profit, cost, service and risk.",
            "Write a recommendation with assumptions and change conditions.",
        ],
        concept="""
An optimal answer is only as good as its assumptions. **Sensitivity analysis** asks how the recommendation changes when inputs change.

**Shadow price (dual value)** of a constraint = change in the optimal objective per one-unit relaxation of that constraint, valid within a range. If the budget constraint has a shadow price of 0.22, one more euro of budget adds about EUR 0.22 profit - so extra budget is worth requesting only if its cost of capital is lower. In scipy (HiGHS), `res.ineqlin.marginals` gives the duals of the `<=` constraints for the *minimisation* problem; flip the sign when you maximised by minimising -profit.

**One-way sensitivity:** vary one input at a time (e.g. +/-20%) and record the objective -> a *tornado chart* ranks inputs by impact.

**Scenario analysis:** change several inputs consistently ("recession": lower margins, higher risk) and re-optimise. Present base / downside / upside scenarios side by side.

**Trade-offs.** Many decisions have several goals (profit vs risk vs service). Options:

* optimise one goal while constraining others (maximise profit subject to average risk <= 0.35);
* combine goals in a weighted objective (with stakeholder-agreed weights);
* trace the *efficient frontier* by re-solving with different limits.

**Recommendation structure**

1. **Decision:** what to do, in plain language and numbers.
2. **Expected impact** and range.
3. **Key assumptions** and data sources.
4. **Binding constraints** - what limits the result and what relaxing them is worth.
5. **When the recommendation changes** - thresholds from sensitivity ("if Email margin falls below 0.30, shift EUR 10k to Search").
6. **Risks and monitoring plan.**
""",
        business_context="""
The CMO must allocate a EUR 400,000 quarterly budget across six channels with minimum commitments, channel capacity limits and a risk policy (average risk score <= 0.35). She needs a recommendation, not just a solver output.
""",
        worked_example=WorkedExample(
            language="python",
            preload={"ca": "marketing.channel_assumptions"},
            code="""from scipy.optimize import linprog

def solve(budget=400_000, risk_cap=0.35, margins=None):
    m = ca.expected_margin_per_dollar.values if margins is None else margins
    A = np.vstack([np.ones(len(ca)), ca.risk_score.values - risk_cap])   # budget; risk-weighted average
    b = np.array([budget, 0.0])
    res = linprog(-m, A_ub=A, b_ub=b, bounds=list(zip(ca.min_spend, ca.max_spend)), method="highs")
    return res

res = solve()
alloc = pd.Series(res.x, index=ca.channel).round(0)
print(alloc, f"\\nexpected profit {-res.fun:,.0f}")
print("shadow price of budget:", round(-res.ineqlin.marginals[0], 3), "| of risk constraint:", round(-res.ineqlin.marginals[1], 3))

# Scenarios: budget and risk policy
for b in [300_000, 400_000, 500_000]:
    for r in [0.30, 0.35, 0.40]:
        s = solve(b, r)
        print(f"budget {b:>7,} risk<= {r:.2f}: " + (f"profit {-s.fun:9,.0f}" if s.status == 0 else s.message))""",
            explanation="""
* The budget's shadow price is **zero**: under the 0.35 risk policy the optimiser does not even spend the full EUR 400k. More budget is worthless unless the policy changes - a finding worth stating explicitly to the CMO.
* The **risk constraint is binding** (positive dual): loosening the risk policy increases profit. That is a **policy trade-off** for leadership, not a technical detail.
* The scenario grid shows where each lever matters: at EUR 300k the budget binds and the risk cap is irrelevant; at EUR 400-500k the risk cap decides the outcome. Always check `res.status` - tight policies combined with minimum commitments can make a scenario infeasible.
* Linear margins are an approximation valid between min and max spend (diminishing returns from Module 3 justify the caps).
""",
        ),
        knowledge_check=["q_ps_013", "q_ps_014", "q_ps_015", "q_ps_016"],
        guided_exercise="ex_py_ps5_budget",
        challenge=None,
        summary=[
            "Shadow prices value the relaxation of binding constraints.",
            "Tornado charts rank inputs; scenarios test coherent alternative futures.",
            "Make trade-offs explicit (constraints, weights or frontiers).",
            "Recommendations state the decision, impact, assumptions, constraints and change conditions.",
        ],
        common_mistakes=[
            "Presenting solver output without interpretation.",
            "Reading shadow prices with the wrong sign after negating the objective.",
            "Ignoring infeasible scenarios.",
        ],
        revision="Build a tornado chart for +/-20% changes in each channel's margin, then start Capstone 4.",
        next_lesson="vz1",
        order=25,
    ),
]
