import duckdb
import pandas as pd

from core.db import (
    delete_instruments,
    init_db,
    list_transforms,
    query_derived_long,
    set_watch,
    upsert_derived_daily,
    upsert_derived_recipe,
    upsert_instruments,
    upsert_transform,
)


def test_delete_instruments_removes_related_derived_and_transforms():
    con = duckdb.connect(":memory:")
    try:
        init_db(con)
        upsert_instruments(
            con,
            pd.DataFrame(
                [
                    {"ticker": "RAW_A", "name": "A", "quote_type": "futures", "exchange": "NYM"},
                    {"ticker": "SPREAD_A", "name": "Spread", "quote_type": "derived", "exchange": "local"},
                ]
            ),
        )
        upsert_transform(
            con,
            {
                "transform_id": "SPREAD_A",
                "derived_ticker": "SPREAD_A",
                "base_ticker": "RAW_A",
                "fx_ticker": "",
            },
        )
        upsert_derived_daily(
            con,
            "SPREAD_A",
            pd.DataFrame(
                {
                    "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                    "value": [1.0, 2.0],
                }
            ),
        )

        delete_instruments(con, ["SPREAD_A"], delete_prices=True)

        assert query_derived_long(con, ["SPREAD_A"]).empty
        assert list_transforms(con, enabled_only=False).empty
        left = con.execute("SELECT COUNT(*) FROM instruments WHERE ticker='SPREAD_A'").fetchone()[0]
        assert left == 0
    finally:
        con.close()


def test_delete_instruments_also_removes_recipes_referencing_deleted_source_ticker():
    con = duckdb.connect(":memory:")
    try:
        init_db(con)
        upsert_instruments(
            con,
            pd.DataFrame(
                [
                    {"ticker": "AU9999.SS", "name": "Shanghai Gold", "quote_type": "spot", "exchange": "SSE"},
                    {"ticker": "SPREAD_AU", "name": "AU Spread", "quote_type": "derived", "exchange": "local"},
                ]
            ),
        )
        upsert_derived_recipe(con, "SPREAD_AU", ["AU9999.SS", "GC=F"], "S1 - S2")

        delete_instruments(con, ["au9999.ss"], delete_prices=True)

        left = con.execute("SELECT COUNT(*) FROM derived_recipes WHERE derived_ticker='SPREAD_AU'").fetchone()[0]
        assert left == 0
    finally:
        con.close()


def test_ticker_normalization_for_upsert_watch_and_delete():
    con = duckdb.connect(":memory:")
    try:
        init_db(con)
        upsert_instruments(
            con,
            pd.DataFrame(
                [{"ticker": " au9999.ss ", "name": "Shanghai Gold", "quote_type": "spot", "exchange": "SSE"}],
            ),
        )

        set_watch(con, ["AU9999.SS"], True)
        is_watched = con.execute("SELECT is_watched FROM instruments WHERE ticker='AU9999.SS'").fetchone()[0]
        assert bool(is_watched) is True

        delete_instruments(con, [" au9999.ss "], delete_prices=True)
        left = con.execute("SELECT COUNT(*) FROM instruments WHERE ticker='AU9999.SS'").fetchone()[0]
        assert left == 0
    finally:
        con.close()
