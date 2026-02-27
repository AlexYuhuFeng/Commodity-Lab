"""Simple example strategies that produce signal DataFrames.
"""
from __future__ import annotations

import pandas as pd


def sma_crossover_signals(prices_df: pd.DataFrame, short: int = 20, long: int = 50) -> pd.DataFrame:
    df = prices_df.copy().sort_values("date").reset_index(drop=True)
    df = df[["date", "close"]].copy()
    df[f"sma_{short}"] = df["close"].rolling(short, min_periods=1).mean()
    df[f"sma_{long}"] = df["close"].rolling(long, min_periods=1).mean()
    df["signal"] = 0
    df.loc[df[f"sma_{short}"] > df[f"sma_{long}"], "signal"] = 1
    df.loc[df[f"sma_{short}"] < df[f"sma_{long}"], "signal"] = -1
    return df[["date", "signal"]]


def rsi_mean_reversion_signals(prices_df: pd.DataFrame, window: int = 14, lower: int = 30, upper: int = 70) -> pd.DataFrame:
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


def bollinger_reversion_signals(prices_df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    df = prices_df.copy().sort_values("date").reset_index(drop=True)
    ma = df["close"].rolling(window, min_periods=1).mean()
    sd = df["close"].rolling(window, min_periods=1).std().fillna(0)
    upper = ma + num_std * sd
    lower = ma - num_std * sd
    df["signal"] = 0
    df.loc[df["close"] < lower, "signal"] = 1
    df.loc[df["close"] > upper, "signal"] = -1
    return df[["date", "signal"]]


def breakout_signals(prices_df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    df = prices_df.copy().sort_values("date").reset_index(drop=True)
    hh = df["close"].rolling(window, min_periods=1).max().shift(1)
    ll = df["close"].rolling(window, min_periods=1).min().shift(1)
    df["signal"] = 0
    df.loc[df["close"] > hh, "signal"] = 1
    df.loc[df["close"] < ll, "signal"] = -1
    return df[["date", "signal"]]
