import pandas as pd
import pytest
import duckdb

from core.db import init_db, upsert_prices_daily, query_prices_long


def test_query_prices_long_rejects_invalid_field():
    con = duckdb.connect(":memory:")
    try:
        init_db(con)
        df_prices = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                "open": [100.0, 101.0],
                "high": [102.0, 103.0],
                "low": [99.0, 100.0],
                "close": [101.0, 102.0],
                "adj_close": [101.0, 102.0],
                "volume": [1000, 1200],
            }
        )
        upsert_prices_daily(con, "TEST", df_prices)

        with pytest.raises(ValueError, match="Unsupported field"):
            query_prices_long(con, ["TEST"], field="close; DROP TABLE prices_daily;--")
    finally:
        con.close()


def test_query_prices_long_allows_valid_field():
    con = duckdb.connect(":memory:")
    try:
        init_db(con)
        df_prices = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01"]),
                "close": [101.0],
            }
        )
        upsert_prices_daily(con, "TEST", df_prices)

        out = query_prices_long(con, ["TEST"], field="close")
        assert not out.empty
        assert out["value"].iloc[0] == 101.0
    finally:
        con.close()
