import duckdb
import pandas as pd

from core.db import init_db, upsert_instruments, upsert_prices_daily, upsert_transform, query_derived_long
from core.transforms import recompute_transform


def test_recompute_transform_accepts_transform_id_string():
    con = duckdb.connect(":memory:")
    try:
        init_db(con)
        upsert_instruments(
            con,
            pd.DataFrame(
                [
                    {"ticker": "BASE_A", "name": "Base", "quote_type": "futures", "exchange": "NYM"},
                    {"ticker": "DERIVED_A", "name": "Derived", "quote_type": "derived", "exchange": "local"},
                ]
            ),
        )
        upsert_prices_daily(
            con,
            "BASE_A",
            pd.DataFrame(
                {
                    "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                    "close": [10.0, 12.0],
                }
            ),
        )
        upsert_transform(
            con,
            {
                "transform_id": "DERIVED_A",
                "derived_ticker": "DERIVED_A",
                "base_ticker": "BASE_A",
                "multiplier": 2.0,
                "divider": 1.0,
            },
        )

        result = recompute_transform(con, "DERIVED_A")

        assert result["status"] == "success"
        out = query_derived_long(con, ["DERIVED_A"])
        assert len(out) == 2
        assert out["value"].iloc[0] == 20.0
    finally:
        con.close()
