"""Coding exercises for Module 5 - Data Visualization.

Checks inspect the learner's actual Matplotlib figure objects (bars, labels,
limits, colours, error bars), not the code text.
"""

from analytics_lab.models import Check, Exercise

# Shared snippet: find the first axes and its bars regardless of orientation.
AX = """assert figs, 'No figure was created. Use fig, ax = plt.subplots() and draw on ax.'
ax = figs[-1].axes[0]
"""
BARS = AX + """import matplotlib.patches as mpatches
bars = [p for p in ax.patches if isinstance(p, mpatches.Rectangle) and (p.get_width() != 0 and p.get_height() != 0)]
assert bars, 'No bars found on the chart. Use ax.bar or ax.barh.'
horizontal = len({round(b.get_x(), 6) for b in bars}) == 1 and len(bars) > 1
lengths = [b.get_width() if horizontal else b.get_height() for b in bars]
labels_axis = ax.get_yticklabels() if horizontal else ax.get_xticklabels()
tick_text = [t.get_text() for t in labels_axis]
"""

PREP_REV = "df = items.merge(orders, on='order_id')\ndf = df[(df['status'] == 'Completed') & (df['order_date'].dt.year == 2024)]\ndf = df.merge(products[['product_id', 'category_id']], on='product_id').merge(categories, on='category_id')\ndf['revenue'] = df['quantity'] * df['unit_price'] * (1 - df['discount_pct'].fillna(0))\n"

EXERCISES = [
    Exercise(
        id="ex_py_vz1_bar",
        title="Sorted bar chart of category revenue",
        module="visualization", language="python", difficulty="Beginner", topic="Bar charts",
        competencies=["chart_selection", "viz_coding"], lesson="vz1",
        business_question="Which categories earned the most revenue in 2024?",
        dataset="retail", tables=["retail.orders", "retail.order_items", "retail.products", "retail.categories"],
        preload={"orders": "retail.orders", "items": "retail.order_items", "products": "retail.products", "categories": "retail.categories"},
        requirements=[
            "`cat_rev`: Series of 2024 completed revenue by category_name, sorted descending.",
            "One bar chart (vertical or horizontal) with one bar per category, ordered by revenue (largest first for vertical; largest at top for horizontal is fine).",
            "A title and an axis label that mentions the unit (EUR).",
        ],
        expected_output="A Series and a bar chart with 8 bars.",
        starter_code=PREP_REV + "\ncat_rev = None\n\nfig, ax = plt.subplots(figsize=(9, 4))\n# draw the bars here\n",
        solution=PREP_REV + "\ncat_rev = df.groupby('category_name')['revenue'].sum().sort_values(ascending=False)\nfig, ax = plt.subplots(figsize=(9, 4))\nax.barh(cat_rev.index[::-1], cat_rev.values[::-1] / 1e3, color='#2563eb')\nax.set_title('Electronics dominates 2024 revenue')\nax.set_xlabel('Revenue (EUR thousands)')\nfig.tight_layout()\n",
        explanation="Sorted bars make ranking instant. Horizontal bars keep long category names readable. Dividing by 1,000 is fine as long as the label states the unit.",
        hints=["groupby('category_name')['revenue'].sum().sort_values(ascending=False).", "ax.barh(names, values) draws horizontal bars; reverse the order to put the largest at the top.", "Use ax.set_title and ax.set_xlabel / set_ylabel."],
        checks=[
            Check("cat_rev values", "s = need('cat_rev', pd.Series)\nassert np.allclose(sorted(s.values, reverse=True), sorted(ref['cat_rev'].values, reverse=True), rtol=1e-6), 'cat_rev values differ - check 2024 + Completed filters and missing discounts.'\nassert list(s.values) == sorted(s.values, reverse=True), 'cat_rev should be sorted descending.'"),
            Check("8 bars, ordered by value", BARS + "assert len(bars) == 8, f'Expected 8 bars (one per category), found {len(bars)}.'\nok = lengths == sorted(lengths, reverse=True) or lengths == sorted(lengths)\nassert ok, 'Bars are not sorted by value. Sort the data before plotting.'", weight=2),
            Check("bars proportional to revenue", BARS + "r = np.array(sorted(lengths)) / max(lengths)\ne = np.array(sorted(ref['cat_rev'].values)) / ref['cat_rev'].max()\nassert np.allclose(r, e, rtol=1e-3), 'Bar lengths are not proportional to category revenue.'"),
            Check("title and labelled unit", AX + "assert ax.get_title().strip(), 'Add a title.'\nlab = (ax.get_xlabel() + ' ' + ax.get_ylabel()).lower()\nassert 'eur' in lab or '€' in lab, 'An axis label should state the unit (EUR).'"),
        ],
        visible_tests=["cat_rev correct and sorted", "8 sorted bars proportional to revenue", "Title and unit label present"],
        rubric=[("Correct data", 30), ("Appropriate sorted chart", 40), ("Labelling", 30)],
    ),
    Exercise(
        id="ex_py_vz2_line",
        title="Annotated monthly revenue trend",
        module="visualization", language="python", difficulty="Intermediate", topic="Line charts and annotation",
        competencies=["viz_coding", "storytelling"], lesson="vz2",
        business_question="Show the 2023-2024 monthly revenue trend and point out the peak month.",
        dataset="retail", tables=["retail.orders", "retail.order_items"],
        preload={"orders": "retail.orders", "items": "retail.order_items"},
        requirements=[
            "`monthly`: Series of completed revenue per month (24 values, chronological).",
            "A line chart of monthly revenue with a y-axis starting at 0.",
            "Title, x-axis label and a y-axis label with the unit (EUR).",
            "At least one annotation (ax.annotate or ax.text) marking the peak month.",
        ],
        expected_output="A Series and an annotated line chart.",
        starter_code="df = items.merge(orders, on='order_id')\ndf = df[df['status'] == 'Completed']\ndf['revenue'] = df['quantity'] * df['unit_price'] * (1 - df['discount_pct'].fillna(0))\n\nmonthly = None\n\nfig, ax = plt.subplots(figsize=(10, 4))\n",
        solution="df = items.merge(orders, on='order_id')\ndf = df[df['status'] == 'Completed']\ndf['revenue'] = df['quantity'] * df['unit_price'] * (1 - df['discount_pct'].fillna(0))\nmonthly = df.groupby(df['order_date'].dt.to_period('M'))['revenue'].sum()\nx = monthly.index.to_timestamp()\nfig, ax = plt.subplots(figsize=(10, 4))\nax.plot(x, monthly.values, color='#2563eb', linewidth=2)\nax.set_ylim(bottom=0)\nax.set_title('Revenue peaks every December')\nax.set_xlabel('Month')\nax.set_ylabel('Revenue (EUR)')\npk = monthly.values.argmax()\nax.annotate(f'Peak: {x[pk]:%b %Y}', xy=(x[pk], monthly.values[pk]), xytext=(x[pk - 6], monthly.values[pk] * 1.02), arrowprops=dict(arrowstyle='->'))\nfig.tight_layout()\n",
        explanation="The annotation puts the key fact where the eye is; the zero baseline keeps seasonal swings in proportion.",
        hints=["Group by df['order_date'].dt.to_period('M').", "ax.set_ylim(bottom=0).", "ax.annotate('text', xy=(x, y), xytext=(x2, y2), arrowprops=dict(arrowstyle='->'))."],
        checks=[
            Check("monthly values", "m = pd.Series(need('monthly'))\nassert len(m) == 24, f'Expected 24 months, got {len(m)}.'\nassert np.allclose(m.values, ref['monthly'].values, rtol=1e-6), 'Monthly revenue values differ or are not in chronological order.'"),
            Check("line with 24 points", AX + "lines = [l for l in ax.get_lines() if len(l.get_xdata()) >= 20]\nassert lines, 'Draw a line chart with ax.plot (24 monthly points).'\nassert len(lines[0].get_xdata()) == 24, 'The line should have 24 points.'"),
            Check("zero baseline", AX + "assert abs(ax.get_ylim()[0]) < 1e-9, f'The y-axis starts at {ax.get_ylim()[0]:.0f}; set ax.set_ylim(bottom=0).'"),
            Check("labels and title", AX + "assert ax.get_title().strip(), 'Add a title.'\nassert ax.get_xlabel().strip(), 'Label the x-axis.'\nassert 'eur' in ax.get_ylabel().lower() or '€' in ax.get_ylabel(), 'The y-axis label should include the unit (EUR).'"),
            Check("annotation present", AX + "assert len(ax.texts) >= 1, 'Add an annotation for the peak month (ax.annotate or ax.text).'"),
        ],
        visible_tests=["24 monthly values", "Line with 24 points", "y-axis starts at 0", "Title and labels with unit", "At least one annotation"],
        rubric=[("Correct data", 25), ("Honest scale", 25), ("Labelling", 25), ("Annotation", 25)],
    ),
    Exercise(
        id="ex_py_vz3_highlight",
        title="Highlight the problem channel",
        module="visualization", language="python", difficulty="Intermediate", topic="Highlight colour and direct labels",
        competencies=["viz_integrity", "viz_coding"], lesson="vz3",
        business_question="Make it obvious which acquisition source has the highest churn.",
        dataset="subscription", tables=["subscription.churn_features"], preload={"cf": "subscription.churn_features"},
        requirements=[
            "One bar per acquisition source (5 bars) showing 6-month churn rate.",
            "Exactly one bar (Paid Social, the highest) in a highlight colour; all other bars share one neutral colour.",
            "No legend. Category names on the axis. A title.",
        ],
        expected_output="A bar chart with 5 bars, one highlighted.",
        starter_code="rates = cf.groupby('acquisition_source')['churned_6m'].mean().sort_values()\n\nfig, ax = plt.subplots(figsize=(8, 3.5))\n",
        solution="rates = cf.groupby('acquisition_source')['churned_6m'].mean().sort_values()\ncolors = ['#b0b7c3' if s != 'Paid Social' else '#d55e00' for s in rates.index]\nfig, ax = plt.subplots(figsize=(8, 3.5))\nbars = ax.barh(rates.index, rates.values * 100, color=colors)\nax.bar_label(bars, labels=[f'{v:.0%}' for v in rates.values], padding=3)\nax.set_title('Paid Social churns about twice as often')\nax.set_xlabel('6-month churn rate (%)')\nfig.tight_layout()\n",
        explanation="Grey for context and one accent colour for the focus is the fastest way to direct attention, and it works for colour-blind readers when paired with labels.",
        hints=["Build a list of colours: neutral for all, accent for 'Paid Social'.", "Pass color=colors to ax.bar/ax.barh.", "Don't call ax.legend()."],
        checks=[
            Check("five bars", BARS + "assert len(bars) == 5, f'Expected 5 bars, found {len(bars)}.'"),
            Check("exactly one highlighted bar", BARS + "import matplotlib.colors as mc\ncols = [mc.to_hex(b.get_facecolor()) for b in bars]\nfrom collections import Counter\ncnt = Counter(cols)\nassert len(cnt) == 2, f'Use exactly two colours (neutral + highlight); found {len(cnt)}.'\nassert sorted(cnt.values()) == [1, 4], 'Exactly one bar should use the highlight colour.'", weight=2),
            Check("highlight is Paid Social (the highest)", BARS + "import matplotlib.colors as mc\nfrom collections import Counter\ncols = [mc.to_hex(b.get_facecolor()) for b in bars]\nodd = [c for c, n in Counter(cols).items() if n == 1][0]\ni = cols.index(odd)\nassert lengths[i] == max(lengths), 'The highlighted bar should be the one with the highest churn.'\nif any(tick_text):\n    assert 'Paid Social' in tick_text[i] or tick_text[i] == '', f'Highlighted bar is labelled {tick_text[i]!r}, expected Paid Social.'"),
            Check("no legend, has title", AX + "assert ax.get_legend() is None, 'Remove the legend; label categories on the axis instead.'\nassert ax.get_title().strip(), 'Add a title that states the takeaway.'"),
        ],
        visible_tests=["5 bars", "Exactly one highlighted bar", "Highlight = highest churn (Paid Social)", "No legend, title present"],
        rubric=[("Correct data", 25), ("Purposeful colour", 50), ("Clean design", 25)],
    ),
    Exercise(
        id="ex_py_vz4_fix",
        title="Fix the misleading A/B chart",
        module="visualization", language="python", difficulty="Advanced", topic="Truncated axes",
        competencies=["viz_integrity"], lesson="vz4",
        business_question="The starter code reproduces a misleading slide. Make it honest.",
        dataset="marketing", tables=["marketing.ab_test"], preload={"ab": "marketing.ab_test"},
        requirements=[
            "Keep a bar chart of conversion rate (%) for control and treatment.",
            "The value axis must start at 0.",
            "Value-axis label must state the unit (% or percent). Add a neutral, accurate title (no 'huge win').",
            "Add value labels to the bars (ax.bar_label or ax.text).",
        ],
        expected_output="A corrected bar chart with 2 bars.",
        starter_code="rates = ab.groupby('variant')['converted'].mean() * 100\n\nfig, ax = plt.subplots(figsize=(6, 4))\nax.bar(rates.index, rates.values, color=['grey', 'green'])\nax.set_ylim(9.9, 10.8)          # <- misleading\nax.set_title('Treatment is a HUGE win!')\n",
        solution="rates = ab.groupby('variant')['converted'].mean() * 100\nfig, ax = plt.subplots(figsize=(6, 4))\nbars = ax.bar(rates.index, rates.values, color=['#94a3b8', '#2563eb'])\nax.set_ylim(0, 12)\nax.set_ylabel('Conversion rate (%)')\nax.set_title('Conversion: 10.1% vs 10.7% (difference not significant)')\nax.bar_label(bars, labels=[f'{v:.1f}%' for v in rates.values], padding=3)\nfig.tight_layout()\n",
        explanation="Starting bars at zero restores proportional lengths; labels give exact values; the title reports the result honestly.",
        hints=["ax.set_ylim(0, ...) or simply remove the custom limits.", "ax.set_ylabel('Conversion rate (%)').", "ax.bar_label(bars) adds value labels."],
        checks=[
            Check("two bars", BARS + "assert len(bars) == 2, f'Expected 2 bars, found {len(bars)}.'"),
            Check("zero baseline", BARS + "lo = (ax.get_xlim() if horizontal else ax.get_ylim())[0]\nassert abs(lo) < 1e-9, f'The value axis starts at {lo}; bars must start at 0.'", weight=2),
            Check("unit label", BARS + "lab = (ax.get_xlabel() if horizontal else ax.get_ylabel()).lower()\nassert '%' in lab or 'percent' in lab, 'Label the value axis with its unit (%).'"),
            Check("honest title", AX + "t = ax.get_title().lower()\nassert t.strip(), 'Add a title.'\nassert 'huge' not in t and 'win' not in t, 'The title still overstates the result.'"),
            Check("value labels", AX + "assert len(ax.texts) >= 2, 'Add value labels to both bars (ax.bar_label).'"),
        ],
        visible_tests=["2 bars", "Value axis starts at 0", "Unit label", "Neutral title", "Value labels"],
        rubric=[("Proportional bars", 40), ("Clear labelling", 30), ("Honest framing", 30)],
    ),
    Exercise(
        id="ex_py_vz5_uncertainty",
        title="Show the uncertainty",
        module="visualization", language="python", difficulty="Professional", topic="Error bars and confidence intervals",
        competencies=["storytelling", "viz_integrity", "statistical_inference"], lesson="vz5",
        business_question="Present A/B conversion by device with honest uncertainty.",
        dataset="marketing", tables=["marketing.ab_test"], preload={"ab": "marketing.ab_test"},
        requirements=[
            "`ci_table`: DataFrame with columns device, variant, rate, ci_low, ci_high (95% Wald CI: rate +/- 1.96*sqrt(rate*(1-rate)/n), as fractions). 6 rows.",
            "A chart with error bars (ax.errorbar or bar yerr) showing all 6 estimates.",
            "Title and a y-axis label with the unit.",
        ],
        expected_output="A 6-row DataFrame and a chart with error bars.",
        starter_code="g = ab.groupby(['device', 'variant'])['converted'].agg(['mean', 'count']).reset_index()\n\nci_table = None\n\nfig, ax = plt.subplots(figsize=(8, 4))\n",
        solution="g = ab.groupby(['device', 'variant'])['converted'].agg(['mean', 'count']).reset_index()\nse = np.sqrt(g['mean'] * (1 - g['mean']) / g['count'])\nci_table = pd.DataFrame({'device': g['device'], 'variant': g['variant'], 'rate': g['mean'], 'ci_low': g['mean'] - 1.96 * se, 'ci_high': g['mean'] + 1.96 * se})\nfig, ax = plt.subplots(figsize=(8, 4))\nfor j, v in enumerate(['control', 'treatment']):\n    s = ci_table[ci_table['variant'] == v]\n    x = np.arange(len(s)) + (j - 0.5) * 0.25\n    ax.errorbar(x, s['rate'] * 100, yerr=[(s['rate'] - s['ci_low']) * 100, (s['ci_high'] - s['rate']) * 100], fmt='o', capsize=5, label=v)\nax.set_xticks(range(3), sorted(ci_table['device'].unique()))\nax.set_ylim(0, 16)\nax.set_ylabel('Conversion rate (%)')\nax.set_title('Device-level differences are within the uncertainty')\nax.legend(frameon=False)\nfig.tight_layout()\n",
        explanation="Interval widths show where evidence is weak (tablet). Visualising uncertainty prevents over-interpreting small differences.",
        hints=["se = sqrt(p(1-p)/n) for each device x variant.", "ax.errorbar(x, y, yerr=..., fmt='o', capsize=5).", "Offset x positions slightly for the two variants."],
        checks=[
            Check("ci_table values", "frames_match(need('ci_table'), ref['ci_table'], sort_by=['device', 'variant'], rtol=1e-4, atol=1e-6)", weight=2),
            Check("error bars drawn", AX + "import matplotlib.container as mcont\nhas = any(isinstance(c, mcont.ErrorbarContainer) for c in ax.containers)\nassert has, 'No error bars found. Use ax.errorbar(...) or ax.bar(..., yerr=...).'\nn = sum(len(c.lines[0].get_xdata()) if c.lines[0] is not None else 0 for c in ax.containers if isinstance(c, mcont.ErrorbarContainer))\nbars_n = sum(len(c.patches) for c in ax.containers if isinstance(c, mcont.BarContainer))\nassert max(n, bars_n) >= 6 or n >= 6, f'Show all 6 device x variant estimates (found {max(n, bars_n)}).'"),
            Check("labels", AX + "assert ax.get_title().strip(), 'Add a title.'\nlab = ax.get_ylabel().lower()\nassert '%' in lab or 'rate' in lab, 'Label the y-axis with the metric and unit.'"),
        ],
        visible_tests=["ci_table matches the reference", "Error bars for all 6 estimates", "Title and y-axis label"],
        rubric=[("Correct intervals", 40), ("Uncertainty visible", 40), ("Labelling", 20)],
    ),
]
