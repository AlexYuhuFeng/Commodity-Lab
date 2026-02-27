import duckdb
import pandas as pd

from core.db import (
    init_db,
    query_derived_long,
    upsert_derived_daily,
    upsert_derived_recipe,
    upsert_instruments,
    upsert_prices_daily,
)
from core.derived_engine import evaluate_recipe, recompute_recipe_graph


def _seed(con):
    init_db(con)
    upsert_instruments(
        con,
        pd.DataFrame(
            [
                {"ticker": "A", "name": "A", "quote_type": "futures", "exchange": "X"},
                {"ticker": "B", "name": "B", "quote_type": "futures", "exchange": "X"},
                {"ticker": "C", "name": "C", "quote_type": "futures", "exchange": "X"},
            ]
        ),
    )
    base = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])})
    upsert_prices_daily(con, "A", base.assign(close=[1.0, 2.0, 3.0]))
    upsert_prices_daily(con, "B", base.assign(close=[2.0, 4.0, 6.0]))
    upsert_prices_daily(con, "C", base.assign(close=[10.0, 20.0, 30.0]))


def test_evaluate_recipe_supports_math_and_functions():
    con = duckdb.connect(":memory:")
    try:
        _seed(con)
        out = evaluate_recipe(con, ["A", "B"], "rolling_mean((S1+S2),2)")
        assert not out.empty
        assert out["value"].iloc[-1] == 7.5
    finally:
        con.close()


def test_recompute_recipe_graph_supports_chain():
    con = duckdb.connect(":memory:")
    try:
        _seed(con)
        upsert_derived_recipe(con, "D1", ["A", "B"], "S1/S2")
        upsert_derived_recipe(con, "D2", ["D1", "C"], "S1*S2")
        upsert_derived_daily(con, "D1", pd.DataFrame(columns=["date", "value"]))
        upsert_derived_daily(con, "D2", pd.DataFrame(columns=["date", "value"]))

        results = recompute_recipe_graph(con, "D2")
        assert [r["ticker"] for r in results] == ["D1", "D2"]

        d2 = query_derived_long(con, ["D2"])
        assert not d2.empty
        # D1=0.5, D2=0.5*C
        assert d2["value"].iloc[0] == 5.0
    finally:
        con.close()


def test_recompute_recipe_graph_updates_downstream_dependents():
    con = duckdb.connect(":memory:")
    try:
        _seed(con)
        upsert_derived_recipe(con, "D1", ["A", "B"], "S1/S2")
        upsert_derived_recipe(con, "D2", ["D1", "C"], "S1*S2")

        recompute_recipe_graph(con, "D2")
        baseline = query_derived_long(con, ["D2"])["value"].iloc[0]
        assert baseline == 5.0

        # change upstream recipe and recompute only D1; D2 should be updated automatically
        upsert_derived_recipe(con, "D1", ["A", "B"], "(S1/S2)*2")
        results = recompute_recipe_graph(con, "D1")
        assert [r["ticker"] for r in results] == ["D1", "D2"]

        updated = query_derived_long(con, ["D2"])["value"].iloc[0]
        assert updated == 10.0
    finally:
        con.close()
