"""Run a small demo backtest using synthetic data to validate backtester."""
from __future__ import annotations

import numpy as np
import pandas as pd
import os
import sys

# ensure workspace root on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.backtest import SimpleBacktester
from core.strategy_examples import sma_crossover_signals
from core.backtest_report import save_backtest_report


def make_synthetic_prices(days: int = 500, seed: int = 42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
    prices = 100 + np.cumsum(rng.normal(loc=0, scale=1, size=days))
    df = pd.DataFrame({"date": dates, "close": prices})
    return df


def main():
    prices = make_synthetic_prices(500)
    signals = sma_crossover_signals(prices, short=10, long=30)

    bt = SimpleBacktester(prices_df=prices, signals_df=signals, capital=100000)
    result = bt.run()

    print("Metrics:")
    print(result.get("metrics", {}))

    paths = save_backtest_report(result, out_prefix="demo_backtest")
    print("Saved report files:", paths)


if __name__ == "__main__":
    main()
