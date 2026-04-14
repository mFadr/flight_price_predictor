"""Dataset generation, reproducibility, documentation and embedded patterns."""

import pandas as pd

from analytics_lab.config import get_paths
from analytics_lab.data import generate
from analytics_lab.data.catalog import DATASETS, dataset_markdown
from analytics_lab.data.loader import list_tables, load_table, query_df, table_columns


def test_generation_is_reproducible():
    a = generate.generate_retail()
    b = generate.generate_retail()
    for name in a:
        pd.testing.assert_frame_equal(a[name], b[name])


def test_warehouse_and_manifest_exist():
    p = get_paths()
    assert p.warehouse_db.exists() and p.manifest.exists()
    assert generate.datasets_ready(p)


def test_all_documented_tables_exist_with_documented_columns():
    tables = list_tables()
    for schema, ds in DATASETS.items():
        for t in ds.tables:
            assert ((tables["schema"] == schema) & (tables["table"] == t.name)).any(), f"{schema}.{t.name} missing"
            cols = set(table_columns(schema, t.name)["column_name"])
            assert cols == set(t.columns), f"{schema}.{t.name}: undocumented or missing columns {cols ^ set(t.columns)}"


def test_minimum_required_content():
    tables = list_tables()
    assert len(tables) >= 18
    assert len(load_table("retail", "orders")) > 15000
    assert len(load_table("operations", "daily_demand")) == 20 * 731  # time-series dataset
    cf = load_table("subscription", "churn_features")  # classification dataset
    assert set(cf["churned_6m"].unique()) == {0, 1}


def test_date_columns_are_dates():
    types = dict(table_columns("retail", "orders")[["column_name", "data_type"]].values)
    assert types["order_date"] == "DATE"


def test_embedded_west_stockout_pattern():
    df = query_df(
        """SELECT YEAR(order_date) y, SUM(quantity * oi.unit_price) rev
           FROM retail.orders o JOIN retail.order_items oi USING (order_id) JOIN retail.products p USING (product_id)
           WHERE region = 'West' AND p.category_id = 1 AND MONTH(order_date) IN (8, 9) AND status = 'Completed' GROUP BY 1"""
    ).set_index("y")["rev"]
    assert df[2024] < 0.3 * df[2023]


def test_known_pitfalls_present():
    customers = load_table("retail", "customers")
    assert customers["customer_id"].is_unique
    assert customers["email_hash"].duplicated().sum() == 30
    items = load_table("retail", "order_items")
    assert items["discount_pct"].isna().sum() > 0
    cf = load_table("subscription", "churn_features")
    assert cf.loc[cf["churned_6m"] == 0, "cancellation_reason"].isna().all()  # leakage trap


def test_data_dictionary_markdown():
    md = dataset_markdown("retail")
    assert "## orders" in md and "Known analytical pitfalls" in md and "generate_retail" in md
