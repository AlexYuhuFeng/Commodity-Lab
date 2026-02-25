import pandas as pd
from core.strategy_examples import sma_crossover_signals
from core.backtest import SimpleBacktester


def make_prices(days=120):
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
    prices = 100 + pd.Series(range(days)).apply(lambda x: x*0.05)
    return pd.DataFrame({"date": dates, "close": prices})


def test_backtest_runs_and_returns_metrics():
    prices = make_prices(120)
    signals = sma_crossover_signals(prices, short=5, long=15)
    bt = SimpleBacktester(prices_df=prices, signals_df=signals, capital=100000)
    res = bt.run(position_size_pct=0.5, cost_per_trade=0.0, slippage=0.0, fixed_fee=0.0)
    assert isinstance(res, dict)
    assert "metrics" in res
    assert "equity_curve" in res
    assert res["equity_curve"].shape[0] > 0
