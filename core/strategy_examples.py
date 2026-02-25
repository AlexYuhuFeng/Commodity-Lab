"""Simple example strategies that produce signal DataFrames.
"""
from __future__ import annotations

import pandas as pd

def sma_crossover_signals(prices_df: pd.DataFrame, short: int = 20, long: int = 50) -> pd.DataFrame:
    """Generate simple SMA crossover signals.

    Returns a DataFrame with columns `date` and `signal` where signal is 1 (long), -1 (short), or 0.
    """
    df = prices_df.copy().sort_values("date").reset_index(drop=True)
    df = df[["date", "close"]].copy()
    df[f"sma_{short}"] = df["close"].rolling(short, min_periods=1).mean()
    df[f"sma_{long}"] = df["close"].rolling(long, min_periods=1).mean()

    df["signal"] = 0
    df.loc[df[f"sma_{short}"] > df[f"sma_{long}"], "signal"] = 1
    df.loc[df[f"sma_{short}"] < df[f"sma_{long}"], "signal"] = -1

    return df[["date", "signal"]]


def rsi_mean_reversion_signals(prices_df: pd.DataFrame, window: int = 14, lower: int = 30, upper: int = 70) -> pd.DataFrame:
    """Generate simple RSI mean reversion signals: long when RSI < lower, short when RSI > upper."""
    df = prices_df.copy().sort_values("date").reset_index(drop=True)
    close = df["close"]
    delta = close.diff().fillna(0)
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window, min_periods=1).mean()
    avg_loss = loss.rolling(window, min_periods=1).mean()
    rs = avg_gain / (avg_loss.replace(0, 1e-8))
    rsi = 100 - (100 / (1 + rs))

    df["signal"] = 0
    df.loc[rsi < lower, "signal"] = 1
    df.loc[rsi > upper, "signal"] = -1
    return df[["date", "signal"]]
