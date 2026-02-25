import pandas as pd
from core.strategy_examples import sma_crossover_signals, rsi_mean_reversion_signals


def make_prices(days=100):
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
    prices = 100 + (pd.Series(range(days)).cumsum() * 0.0) + pd.Series([i*0.1 for i in range(days)])
    return pd.DataFrame({"date": dates, "close": prices})


def test_sma_signals_length():
    prices = make_prices(60)
    sig = sma_crossover_signals(prices, short=5, long=20)
    assert "signal" in sig.columns
    assert len(sig) == len(prices)


def test_rsi_signals_length():
    prices = make_prices(60)
    sig = rsi_mean_reversion_signals(prices, window=14)
    assert "signal" in sig.columns
    assert len(sig) == len(prices)
