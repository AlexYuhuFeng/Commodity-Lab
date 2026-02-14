# core/features.py
from __future__ import annotations

from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from core.db import get_conn


def compute_rolling_stats(
    series: pd.Series,
    window: int = 20,
    stat: str = "mean"
) -> pd.Series:
    """
    Compute rolling statistics (mean, std, min, max) on a series.
    
    Args:
        series: Input time series
        window: Rolling window size
        stat: Type of statistic ('mean', 'std', 'min', 'max')
    """
    if stat == "mean":
        return series.rolling(window=window, min_periods=1).mean()
    elif stat == "std":
        return series.rolling(window=window, min_periods=1).std()
    elif stat == "min":
        return series.rolling(window=window, min_periods=1).min()
    elif stat == "max":
        return series.rolling(window=window, min_periods=1).max()
    else:
        raise ValueError(f"Unknown stat: {stat}")


def compute_zscore(series: pd.Series, window: int = 20) -> pd.Series:
    """
    Compute z-score (standardized values) with rolling mean and std.
    """
    rolling_mean = series.rolling(window=window, min_periods=1).mean()
    rolling_std = series.rolling(window=window, min_periods=1).std()
    rolling_std = rolling_std.replace(0, np.nan)  # Avoid division by zero
    return (series - rolling_mean) / rolling_std


def compute_returns(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Compute percentage returns.
    """
    return series.pct_change(periods=periods) * 100


def compute_volatility(series: pd.Series, window: int = 20) -> pd.Series:
    """
    Compute rolling volatility (standard deviation of returns).
    """
    returns = compute_returns(series, periods=1)
    return returns.rolling(window=window, min_periods=1).std()


def compute_momentum(series: pd.Series, window: int = 20) -> pd.Series:
    """
    Compute momentum (rate of change over window).
    """
    return series.pct_change(periods=window) * 100


def compute_rolling_correlation(
    series1: pd.Series,
    series2: pd.Series,
    window: int = 20
) -> pd.Series:
    """
    Compute rolling correlation between two series.
    """
    df = pd.DataFrame({"s1": series1, "s2": series2})
    return df["s1"].rolling(window=window, min_periods=1).corr(df["s2"])


def compute_percentile(series: pd.Series, window: int = 20, pct: float = 50) -> pd.Series:
    """
    Compute rolling percentile.
    
    Args:
        series: Input series
        window: Rolling window size
        pct: Percentile (0-100)
    """
    return series.rolling(window=window, min_periods=1).quantile(pct / 100)


def engineer_features(
    df: pd.DataFrame,
    ticker: str,
    window: int = 20,
    include_zscore: bool = True,
    include_volatility: bool = True,
    include_momentum: bool = True,
    include_percentiles: bool = True,
) -> pd.DataFrame:
    """
    Engineer features from a price dataframe.
    
    Args:
        df: DataFrame with 'date' and 'close' columns
        ticker: Ticker symbol
        window: Rolling window size for calculations
        include_*: Whether to compute each feature type
    
    Returns:
        DataFrame with engineered features
    """
    if df.empty or "close" not in df.columns:
        return pd.DataFrame()
    
    features = df[["date", "close"]].copy()
    features["ticker"] = ticker
    
    close_prices = df["close"]
    
    if include_zscore:
        features["zscore"] = compute_zscore(close_prices, window=window)
    
    if include_volatility:
        features["volatility"] = compute_volatility(close_prices, window=window)
        features["volatility_ma"] = features["volatility"].rolling(window=window, min_periods=1).mean()
    
    if include_momentum:
        features["momentum"] = compute_momentum(close_prices, window=window)
        features["momentum_ma"] = features["momentum"].rolling(window=window, min_periods=1).mean()
    
    if include_percentiles:
        features["percentile_25"] = compute_percentile(close_prices, window=window, pct=25)
        features["percentile_50"] = compute_percentile(close_prices, window=window, pct=50)
        features["percentile_75"] = compute_percentile(close_prices, window=window, pct=75)
    
    features["close_ma"] = compute_rolling_stats(close_prices, window=window, stat="mean")
    features["close_std"] = compute_rolling_stats(close_prices, window=window, stat="std")
    
    return features


def detect_regime(
    df: pd.DataFrame,
    volatility_threshold: float = 1.5,
    correlation_threshold: float = 0.5,
    zscore_threshold: float = 2.0
) -> pd.DataFrame:
    """
    Detect market regimes based on volatility and other metrics.
    
    Args:
        df: Features dataframe with volatility and zscore columns
        volatility_threshold: Threshold for high volatility (as multiplier of median)
        correlation_threshold: Threshold for high correlation
        zscore_threshold: Threshold for extreme values
    
    Returns:
        DataFrame with regime labels
    """
    if df.empty:
        return pd.DataFrame()
    
    regime = df[["date"]].copy()
    
    # Determine volatility regime
    if "volatility" in df.columns:
        median_vol = df["volatility"].median()
        regime["high_vol"] = df["volatility"] > (median_vol * volatility_threshold)
    else:
        regime["high_vol"] = False
    
    # Determine extreme value regime
    if "zscore" in df.columns:
        regime["extreme"] = np.abs(df["zscore"]) > zscore_threshold
    else:
        regime["extreme"] = False
    
    # Combined regime label
    def label_regime(row):
        if row.get("extreme", False):
            return "EXTREME"
        elif row.get("high_vol", False):
            return "HIGH_VOL"
        else:
            return "NORMAL"
    
    regime["regime"] = regime.apply(label_regime, axis=1)
    
    return regime


def feature_summary(features_df: pd.DataFrame) -> dict:
    """
    Generate summary statistics for engineered features.
    """
    if features_df.empty:
        return {}
    
    numeric_cols = features_df.select_dtypes(include=[np.number]).columns
    
    summary = {}
    for col in numeric_cols:
        summary[col] = {
            "mean": float(features_df[col].mean()),
            "std": float(features_df[col].std()),
            "min": float(features_df[col].min()),
            "max": float(features_df[col].max()),
            "median": float(features_df[col].median())
        }
    
    return summary
