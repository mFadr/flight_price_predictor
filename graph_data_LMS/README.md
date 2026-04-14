# Data Analytics Learning & Testing Lab

A local, offline-first learning platform for data analytics. It runs in your browser at `http://localhost:8501`. You learn by doing: write and run real SQL, Python and R against realistic datasets, get automated feedback, and track measurable competency across five modules:

| Module | Core question | Tools |
|---|---|---|
| Descriptive Analytics | What happened? | SQL, Excel, Power BI |
| Diagnostic Analytics | Why did it happen? | Python, R, SQL |
| Predictive Analytics | What is likely to happen? | Python, R |
| Prescriptive Analytics | What should we do? | Python (SciPy), R |
| Data Visualization | How do we communicate it? | Matplotlib, Tableau, Looker Studio, Power BI, Excel |

**What's inside**
- 32 lessons across four levels (Beginner to Professional). Each lesson has the same ten parts: objectives, concept, business context, a worked solution you can edit and run, a knowledge check, a guided exercise, an independent challenge, feedback, a summary, and next steps.
- 47 auto-graded coding exercises: 14 SQL, 30 Python and 3 R.
- 103 multiple-choice questions, each with an explanation for every option.
- 6 business-case assessments and 5 capstone projects.
- A final competency assessment.
- An adaptive dashboard with recommendations. Each recommendation says why it was made.
- Workshops for Excel, Power BI, Tableau and Looker Studio, plus a dashboard critique exercise.

---

## 1. Setup

Requirements: **Python 3.11 or newer** (tested with 3.13). R is optional.

```bash
# from the project folder
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 2. Launch

```bash
streamlit run app.py
```

Then open **http://localhost:8501**. The first start generates the practice datasets into `data/`, which takes a few seconds. After installation, everything works offline.

To use a different port, run `streamlit run app.py --server.port 8502`.

## 3. Using the lab

| Section | What you do there |
|---|---|
| **Dashboard** | See completion, quiz accuracy, exercise pass rate, streak, competency by module, strongest and weakest competencies, recommendations, and outstanding work. |
| **Learning Path** | Browse the recommended path. Search and filter lessons, exercises and capstones. |
| **5 module pages** | Take the lessons. Each module also has *All module exercises* and *Tool workshops* tabs. |
| **Practice & Coding Lab** | Use the SQL workbench (schema browser, EXPLAIN), the Python lab, the R lab, all coding challenges, the dataset explorer (profile, dictionary, charts, downloads), the import tool for your own files, and the tool workshops. |
| **Assessment Center** | Build quizzes, take business cases, take the final assessment, and review past attempts. Quizzes can give feedback immediately, at the end, or in exam mode, and can be timed with randomized answers. |
| **Capstone Projects** | Work through briefs, data packs, milestones with automated checks, rubrics, and strong example submissions. |
| **My Progress** | See your competency profile, history and improvement, and repeated mistakes. Export to JSON or CSV. |
| **Settings & Help** | Set the mastery threshold, timeout and execution backend. Check the system and R status. Search the glossary and cheat sheets. Read help, and manage data or reset progress. |

Tips:
- Each code run starts fresh, so define everything you need in the same editor.
- In Python, `load_table("retail.orders")` and `sql("SELECT ...")` return DataFrames. A DataFrame assigned to `result` is displayed, and figures are captured automatically.
- Hints are revealed one at a time. The reference solution unlocks after your first submission, or earlier if you explicitly confirm. A pass after viewing the solution counts as *assisted*.

## 4. How assessment works

- **SQL** is graded on the **returned data**, never on the query text. The grader checks column names (case-insensitive, falling back to position), the row count, and values with numeric tolerance. Row order is checked only when the task requires it. Any equivalent query earns full marks, and partial credit comes with specific feedback.
- **Python and R** are graded by hidden checks run in the same child process as your code. They compare your variables against a reference solution, or test task-specific criteria. For example, the threshold exercise checks that about 30% of customers are flagged, that precision and recall match your own predictions, and that AUC is useful but not suspiciously high (which would indicate leakage). Visualization checks inspect your actual Matplotlib figure: bars, axis limits, labels, colors and error bars.
- **Multiple choice** questions are tagged by module, topic, tool, difficulty and competency. A multi-select question counts as correct only when every choice matches.
- **Business cases** combine automatically graded decision questions with a written answer. You score the written answer yourself against a published rubric, after reading an exemplar. Free text is **not** graded automatically. A keyword indicator is shown for guidance only and never affects the score. The total is 50% decision questions and 50% rubric.
- **Competency model.** Scores are shown transparently on *My Progress*:
  - Knowledge: recency-weighted quiz accuracy (35%).
  - Practical: best exercise scores, with assisted passes capped at 70 (45%).
  - Application: cases and capstone deliverables (20%).
  - Mastery requires a score at or above the threshold (default 80%, configurable). For competencies flagged as needing practical evidence, it also requires a practical score at or above the threshold and at least 50% exercise coverage. **Quiz scores alone never produce mastery of these.**

## 5. Datasets

Every dataset is fictional and generated locally from seeded random generators (`analytics_lab/data/generate.py`), so it is identical on every machine. The data is stored as CSV files and in a read-only DuckDB warehouse with these schemas:

| Schema | Contents |
|---|---|
| `retail` | Customers, orders, order items, products, categories, marketing channels, returns and discounts (2023–2024). |
| `subscription` | Subscriptions, signup and cancellation dates, monthly revenue, product usage, support tickets, acquisition source, and a churn-classification snapshot. |
| `operations` | Suppliers, inventory, daily demand per SKU (time series), deliveries, operating costs, production capacity and resource usage. |
| `marketing` | Weekly channel spend and revenue, budget planning assumptions, and a 20,000-user A/B test. |

The datasets contain deliberate analytical pitfalls: missing values, duplicate customers, outliers, a regional stock-out, a shift in acquisition mix (Simpson's paradox), a price change, a leaky column, censored demand, and a novelty effect. Data dictionaries, pitfalls and suggested questions are listed in the dataset explorer and can be downloaded as Markdown.

To regenerate the data, use **Settings & Help → Data management → Regenerate datasets**, or run `python scripts/generate_datasets.py --force`.

## 6. Excel, Power BI, Tableau, Looker Studio

The lab **does not run these products**. Each workshop provides datasets, step-by-step tasks, and expected results computed from the same data so you can check your work. Some workshops add in-app practice:
- **Excel:** download a practice workbook, fill in formulas in Excel or LibreOffice, and upload it. The checker reads both the calculated values and the formulas: typed-in numbers are rejected, and the scenario must reference the input cell. There are also a PivotTable simulator and a what-if / Goal Seek simulator.
- **Power BI:** a model designer (fact versus dimension tables, cardinality, filter direction) and DAX filter-context questions, both graded. A Power BI Desktop assignment comes with expected card values.
- **Tableau and Looker Studio:** guided assignments with data packs, expected values and a self-check. The self-check is recorded as self-assessed.

## 7. R (optional)

R exercises run when `Rscript` is available. The lab finds it on `PATH`, or in the standard install folder (`C:\Program Files\R\R-x.y.z\bin` on Windows). You can also enter the path in Settings. Graded R exercises use base R only. `dplyr` and `ggplot2` are used in lesson examples if installed. Without R, those exercises show installation instructions and everything else works normally.

## 8. Execution safety and trust model

The lab assumes **one local user on their own computer**.

- Your code (Python, SQL, R) runs in a **separate child process**, never inside the Streamlit server.
- Each run has a wall-clock **timeout** (configurable) and a **temporary working directory** that is deleted afterwards.
- Each run gets a **minimal environment**: environment variables such as API keys are not passed through.
- Python runs in isolated mode. On Linux and macOS, memory and CPU limits are also applied.
- SQL opens the warehouse **read-only**, with DuckDB file and network access disabled and locked.

**This is not a security sandbox.** Python or R code can still read files your user account can access. Do not run untrusted code.

Hidden tests and reference solutions are never displayed before an attempt. Because everything runs locally, they are not cryptographically secret.

**Optional Docker isolation** (stronger, for shared or untrusted use):

```bash
docker build -f docker/Dockerfile.runner -t analytics-lab-runner:latest .
```

Then choose **Settings → Execution backend → docker**. Containers run with `--network none`, a read-only root filesystem, a read-only data mount, memory, CPU and process limits, and `no-new-privileges`.

*Limitation:* Docker wasn't available on the development machine, so the Docker backend is implemented and its command construction is unit-tested, but it **has not been run end-to-end**.

## 9. Tests

```bash
python -m pytest            # 193 tests, about 2.5 minutes
python scripts/validate_content.py   # content integrity + all reference solutions + worked examples
```

The tests cover:
- Dataset reproducibility and documentation coverage.
- Execution: timeouts, secret stripping, temp directories, read-only SQL, blocked file access, and R.
- SQL result-set grading.
- Multiple-choice, Python, R and visualization grading.
- Every reference solution passing its own checks, and every starter code failing them.
- Persistence across restarts, reset, export, and recovery of a corrupted database.
- Competency rules and recommendations.
- Uploads, the Excel checker, and case scoring.
- Headless rendering of every page and lesson, a quiz flow, and an exercise submission through the UI.

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` on start | Activate the virtual environment, then run `pip install -r requirements.txt`. |
| Port 8501 already in use | Run `streamlit run app.py --server.port 8502`. |
| Code runs time out | Look for loops over rows or accidental cross joins. You can raise the timeout in Settings. |
| R exercises are disabled | Install R from https://cran.r-project.org, or set the Rscript path in Settings, then click *Re-check capabilities*. |
| The Excel checker finds no values | Open the workbook in Excel or LibreOffice and save it, so the calculated values are stored in the file. |
| Strange data or errors after an update | Use Settings → Data management → Regenerate datasets. Your progress is kept. |
| The progress database is corrupted | It is backed up automatically (`data/progress.corrupt-*.db`) and a fresh one is created. |

## 11. Reset and data locations

- Progress, attempts and settings are stored in `data/progress.db` (SQLite).
- Imported files are stored in `data/uploads.duckdb`.
- Generated datasets are in `data/generated/`.
- To relocate all data, set the environment variable `ANALYTICS_LAB_HOME` (see `.env.example`).
- To reset, use **Settings & Help → Data management → Reset all progress** (type `RESET` to confirm). You can export your data first from My Progress → Export. Deleting the `data/` folder also resets everything; the datasets are regenerated on the next start.

## 12. Project structure

```
app.py                         Streamlit entry point and navigation
requirements.txt, pytest.ini, .env.example, .streamlit/config.toml
analytics_lab/
  config.py, capabilities.py   paths/settings; dependency, R and Docker detection
  models.py                    typed content models
  data/                        generate.py (seeded generators), catalog.py (dictionaries), loader.py (queries, uploads)
  execution/                   sandbox.py (process/Docker launcher), python_harness.py, sql_harness.py, runners.py (Python/SQL/R)
  curriculum/                  lessons for the 5 modules, competencies.py, reference.py (glossary, cheat sheets)
  assessment/                  question banks, exercises, grading.py, cases.py, capstones.py, bank.py
  progress/store.py            SQLite persistence
  competency.py                competency scoring and adaptive recommendations
  tools/workshops.py           Excel/Power BI/Tableau/Looker workshop logic
  ui/                          state.py, components/ (exercise, mcq, outputs, workshops), pages/
scripts/                       generate_datasets.py, validate_content.py
docker/Dockerfile.runner       optional isolated runner image
tests/                         pytest suite
```

## 13. Known limitations

- Free-text answers are self-assessed against rubrics. No automatic grading of written work is claimed.
- The code editor is a plain multiline text area. Syntax highlighting appears in the output and solution views only.
- The quiz timer refreshes when you interact with the page, and the deadline is enforced when you submit.
- Excel, Power BI, Tableau and Looker Studio work is completed in those products. The lab verifies results through the expected values and the Excel checker, and records self-checks as self-assessed.
- Process isolation is not a security sandbox (see section 8). The Docker backend has not been tested end-to-end.
