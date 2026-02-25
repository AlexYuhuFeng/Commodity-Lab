import pandas as pd
import duckdb

from core.auto_strategy import run_auto_strategy_search, detect_hardware_acceleration
from core.db import init_db, insert_strategy_run, list_strategy_runs


def make_prices(days=250):
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
    trend = pd.Series(range(days), dtype=float) * 0.12
    prices = 100 + trend
    return pd.DataFrame({"date": dates, "close": prices})


def test_auto_strategy_search_returns_ranked_candidates():
    prices = make_prices(260)
    out = run_auto_strategy_search(prices, top_k=5)

    assert not out.empty
    assert out.shape[0] <= 5
    assert {"strategy_name", "score", "params"}.issubset(out.columns)
    assert out["score"].iloc[0] >= out["score"].iloc[-1]


def test_detect_hardware_acceleration_shape():
    caps = detect_hardware_acceleration()
    assert "numba" in caps
    assert "cupy" in caps
    assert isinstance(caps["numba"], bool)
    assert isinstance(caps["cupy"], bool)


def test_strategy_run_persistence_roundtrip():
    con = duckdb.connect(":memory:")
    try:
        init_db(con)
        insert_strategy_run(
            con,
            {
                "run_id": "r1",
                "ticker": "TEST",
                "strategy_name": "sma_crossover",
                "params_json": '{"short":20,"long":50}',
                "score": 1.23,
                "total_return_pct": 10.0,
                "max_drawdown_pct": -5.0,
                "sharpe_ratio": 1.1,
                "win_rate": 52.0,
            },
        )
        out = list_strategy_runs(con, ticker="TEST")
        assert not out.empty
        assert out.iloc[0]["strategy_name"] == "sma_crossover"
    finally:
        con.close()
