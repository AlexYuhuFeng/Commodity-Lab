import duckdb
import pandas as pd

from core.db import (
    init_db,
    list_derived_recipes,
    query_series_long,
    upsert_derived_daily,
    upsert_derived_recipe,
    upsert_instruments,
    upsert_prices_daily,
)


def test_query_series_long_supports_mixed_raw_and_derived():
    con = duckdb.connect(":memory:")
    try:
        init_db(con)
        upsert_instruments(
            con,
            pd.DataFrame(
                [
                    {"ticker": "RAW_A", "name": "RAW_A", "quote_type": "futures", "exchange": "NYM"},
                    {"ticker": "DRV_A", "name": "DRV_A", "quote_type": "derived", "exchange": "local"},
                ]
            ),
        )
        upsert_prices_daily(
            con,
            "RAW_A",
            pd.DataFrame({"date": pd.to_datetime(["2024-01-01"]), "close": [10.0]}),
        )
        upsert_derived_daily(
            con,
            "DRV_A",
            pd.DataFrame({"date": pd.to_datetime(["2024-01-01"]), "value": [5.0]}),
        )

        out = query_series_long(con, ["RAW_A", "DRV_A"])
        assert set(out["ticker"].unique().tolist()) == {"RAW_A", "DRV_A"}
    finally:
        con.close()


def test_upsert_derived_recipe_roundtrip():
    con = duckdb.connect(":memory:")
    try:
        init_db(con)
        upsert_derived_recipe(con, "DRV_X", ["A", "B"], "S1-S2")
        recipes = list_derived_recipes(con)
        assert not recipes.empty
        assert recipes.iloc[0]["derived_ticker"] == "DRV_X"
    finally:
        con.close()
