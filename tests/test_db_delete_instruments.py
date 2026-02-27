import duckdb
import pandas as pd

from core.db import (
    delete_instruments,
    init_db,
    list_transforms,
    query_derived_long,
    upsert_derived_daily,
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
