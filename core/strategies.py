# core/strategies.py
from __future__ import annotations

from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np

from core.features import compute_zscore, compute_volatility, compute_momentum


class SignalType(Enum):
    """Signal strength enum"""
    STRONG_BUY = 2
    BUY = 1
    NEUTRAL = 0
    SELL = -1
    STRONG_SELL = -2


@dataclass
class StrategySignal:
    """Structure for strategy signals"""
    date: date
    ticker: str
    signal: int  # -2 to +2
    confidence: float  # 0 to 1
    reason: str
    entry: bool
    exit: bool


class MeanReversionStrategy:
    """
    Z-score based mean reversion strategy.
    Buy when price is > 2 std below mean, sell when > 2 std above mean.
    """
    
    def __init__(self, window: int = 20, entry_zscore: float = -2.0, exit_zscore: float = 2.0):
        self.window = window
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
    
    def generate_signals(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Generate mean reversion signals.
        """
        if df.empty or "close" not in df.columns:
            return pd.DataFrame()
        
        result = df[["date", "close"]].copy()
        result["ticker"] = ticker
        
        close_prices = df["close"]
        zscore = compute_zscore(close_prices, window=self.window)
        
        result["zscore"] = zscore
        result["signal"] = 0
        
        # Buy signal: zscore below entry threshold
        result.loc[zscore < self.entry_zscore, "signal"] = 1
        
        # Sell signal: zscore above exit threshold
        result.loc[zscore > self.exit_zscore, "signal"] = -1
        
        # Confidence based on zscore magnitude
        result["confidence"] = np.minimum(np.abs(zscore) / 3.0, 1.0)
        
        return result


class MomentumStrategy:
    """
    Momentum-based strategy.
    Buy on positive momentum, sell on negative momentum.
    """
    
    def __init__(self, window: int = 20, threshold: float = 1.0):
        self.window = window
        self.threshold = threshold
    
    def generate_signals(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Generate momentum signals.
        """
        if df.empty or "close" not in df.columns:
            return pd.DataFrame()
        
        result = df[["date", "close"]].copy()
        result["ticker"] = ticker
        
        close_prices = df["close"]
        momentum = compute_momentum(close_prices, window=self.window)
        
        result["momentum"] = momentum
        result["signal"] = 0
        
        # Buy on positive momentum
        result.loc[momentum > self.threshold, "signal"] = 1
        
        # Sell on negative momentum
        result.loc[momentum < -self.threshold, "signal"] = -1
        
        # Confidence
        result["confidence"] = np.minimum(np.abs(momentum) / 10.0, 1.0)
        
        return result


class VolatilityStrategy:
    """
    Volatility-based strategy.
    Buy in low volatility, sell in high volatility.
    """
    
    def __init__(self, window: int = 20):
        self.window = window
    
    def generate_signals(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Generate volatility regime signals.
        """
        if df.empty or "close" not in df.columns:
            return pd.DataFrame()
        
        result = df[["date", "close"]].copy()
        result["ticker"] = ticker
        
        close_prices = df["close"]
        volatility = compute_volatility(close_prices, window=self.window)
        
        median_vol = volatility.median()
        q25_vol = volatility.quantile(0.25)
        q75_vol = volatility.quantile(0.75)
        
        result["volatility"] = volatility
        result["signal"] = 0
        
        # Buy in low volatility
        result.loc[volatility < q25_vol, "signal"] = 1
        
        # Sell in high volatility
        result.loc[volatility > q75_vol, "signal"] = -1
        
        # Confidence
        result["confidence"] = np.minimum(
            np.abs(volatility - median_vol) / (median_vol + 0.001),
            1.0
        )
        
        return result


class CombinedStrategy:
    """
    Combine multiple strategies with weighted signals.
    """
    
    def __init__(self, strategies: list, weights: list):
        """
        Args:
            strategies: List of strategy objects
            weights: List of weights (sum to 1)
        """
        self.strategies = strategies
        weights = np.array(weights)
        self.weights = weights / weights.sum()  # Normalize
    
    def generate_signals(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Generate combined signals.
        """
        if not df.empty and len(self.strategies) > 0:
            signals = []
            for strategy in self.strategies:
                sig = strategy.generate_signals(df, ticker)
                signals.append(sig[["signal"]])
            
            combined = pd.concat(signals, axis=1)
            weighted_signal = (combined * self.weights).sum(axis=1)
            
            result = df[["date", "close"]].copy()
            result["ticker"] = ticker
            result["signal"] = weighted_signal.clip(-2, 2).astype(int)
            result["confidence"] = np.minimum(np.abs(weighted_signal) / 2.0, 1.0)
            
            return result
        
        return pd.DataFrame()


def signal_to_position(
    signals_df: pd.DataFrame,
    position_mode: str = "continuous"
) -> pd.DataFrame:
    """
    Convert signals to positions.
    
    Args:
        signals_df: DataFrame with 'signal' column
        position_mode: 'continuous' (follow signal) or 'binary' (in/out)
    
    Returns:
        DataFrame with 'position' column
    """
    if signals_df.empty:
        return pd.DataFrame()
    
    result = signals_df.copy()
    
    if position_mode == "continuous":
        result["position"] = result["signal"]
    else:
        result["position"] = (result["signal"] > 0).astype(int)
    
    return result


def evaluate_strategy(df: pd.DataFrame) -> dict:
    """
    Evaluate strategy performance metrics.
    """
    if df.empty or "signal" not in df.columns:
        return {}
    
    metrics = {
        "total_signals": int(df["signal"].ne(0).sum()),
        "buy_signals": int((df["signal"] > 0).sum()),
        "sell_signals": int((df["signal"] < 0).sum()),
    }
    
    if "confidence" in df.columns:
        metrics["avg_confidence"] = float(df["confidence"].mean())
    
    # Signal transitions (potential trades)
    if len(df) > 1:
        signal_change = df["signal"].diff().ne(0).sum()
        metrics["signal_transitions"] = int(signal_change)
    
    return metrics
