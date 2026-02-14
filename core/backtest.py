# core/backtest.py
from __future__ import annotations

from datetime import datetime, date, timedelta
from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class Trade:
    """Represents a single trade"""
    entry_date: date
    exit_date: date | None
    entry_price: float
    exit_price: float | None
    direction: int  # 1 for long, -1 for short
    shares: float
    entry_signal: str
    exit_signal: str | None
    pnl: float | None
    pnl_pct: float | None


class SimpleBacktester:
    """
    Simple backtester for strategy performance evaluation.
    """
    
    def __init__(self, prices_df: pd.DataFrame, signals_df: pd.DataFrame, capital: float = 100000):
        """
        Args:
            prices_df: DataFrame with 'date', 'close' columns
            signals_df: DataFrame with 'date', 'signal' columns
            capital: Initial capital
        """
        self.prices_df = prices_df.copy().sort_values("date")
        self.signals_df = signals_df.copy().sort_values("date")
        self.capital = capital
        
        # Merge prices and signals
        self.df = pd.merge(self.prices_df, self.signals_df[["date", "signal"]], on="date", how="left")
        self.df["signal"] = self.df["signal"].fillna(0)
    
    def run(self, position_size_pct: float = 0.95, cost_per_trade: float = 0.0) -> dict:
        """
        Run backtest.
        
        Args:
            position_size_pct: Percentage of capital per trade
            cost_per_trade: Transaction cost per trade (e.g., 0.001 for 0.1%)
        
        Returns:
            Backtest results dict
        """
        if self.df.empty:
            return {}
        
        df = self.df.copy()
        
        # Initialize tracking
        trades = []
        equity_curve = [self.capital]
        dates = [df["date"].iloc[0]]
        
        position = 0  # Current position (shares)
        entry_price = 0
        entry_date = None
        entry_signal = None
        cash = self.capital
        
        for idx, row in df.iterrows():
            signal = int(row["signal"])
            price = row["close"]
            current_date = row["date"]
            
            # Close position if signal changes
            if position != 0 and signal != np.sign(position):
                # Exit trade
                exit_price = price
                pnl = (exit_price - entry_price) * position * (1 - cost_per_trade)
                pnl_pct = (pnl / (entry_price * position)) * 100 if entry_price != 0 else 0
                
                trade = Trade(
                    entry_date=entry_date,
                    exit_date=current_date,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    direction=np.sign(position),
                    shares=abs(position),
                    entry_signal=entry_signal,
                    exit_signal=f"signal_{signal}",
                    pnl=pnl,
                    pnl_pct=pnl_pct
                )
                trades.append(trade)
                
                cash += exit_price * position
                position = 0
            
            # Open new position
            if position == 0 and signal != 0:
                position_size = (cash * position_size_pct) / (price + 0.001)
                position = position_size * signal
                entry_price = price
                entry_date = current_date
                entry_signal = f"signal_{signal}"
                cash -= price * abs(position) * (1 + cost_per_trade)
            
            # Update equity
            current_equity = cash + position * price
            equity_curve.append(current_equity)
            dates.append(current_date)
        
        # Close final position
        if position != 0:
            exit_price = df["close"].iloc[-1]
            pnl = (exit_price - entry_price) * position * (1 - cost_per_trade)
            pnl_pct = (pnl / (entry_price * position)) * 100 if entry_price != 0 else 0
            
            trade = Trade(
                entry_date=entry_date,
                exit_date=df["date"].iloc[-1],
                entry_price=entry_price,
                exit_price=exit_price,
                direction=np.sign(position),
                shares=abs(position),
                entry_signal=entry_signal,
                exit_signal="exit_final",
                pnl=pnl,
                pnl_pct=pnl_pct
            )
            trades.append(trade)
        
        # Generate results
        return {
            "equity_curve": pd.DataFrame({
                "date": dates,
                "equity": equity_curve
            }),
            "trades": trades,
            "metrics": self._calculate_metrics(trades, equity_curve)
        }
    
    def _calculate_metrics(self, trades: list, equity_curve: list) -> dict:
        """Calculate performance metrics"""
        equity = np.array(equity_curve)
        returns = np.diff(equity) / equity[:-1]
        
        total_return_pct = ((equity[-1] - self.capital) / self.capital) * 100
        
        # Drawdown
        cummax = np.maximum.accumulate(equity)
        drawdown = (equity - cummax) / cummax
        max_drawdown_pct = np.min(drawdown) * 100
        
        # Win rate
        if trades:
            winning_trades = sum(1 for t in trades if t.pnl and t.pnl > 0)
            win_rate = (winning_trades / len(trades)) * 100 if trades else 0
            avg_win = np.mean([t.pnl for t in trades if t.pnl and t.pnl > 0]) if winning_trades > 0 else 0
            avg_loss = np.mean([t.pnl for t in trades if t.pnl and t.pnl < 0]) if (len(trades) - winning_trades) > 0 else 0
            profit_factor = abs(sum(t.pnl for t in trades if t.pnl and t.pnl > 0) / 
                             sum(t.pnl for t in trades if t.pnl and t.pnl < 0)) if sum(t.pnl for t in trades if t.pnl and t.pnl < 0) != 0 else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
        
        # Sharpe ratio (simplified)
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        return {
            "total_return_pct": float(total_return_pct),
            "max_drawdown_pct": float(max_drawdown_pct),
            "num_trades": len(trades),
            "win_rate": float(win_rate),
            "avg_win": float(avg_win),
            "avg_loss": float(avg_loss),
            "profit_factor": float(profit_factor),
            "sharpe_ratio": float(sharpe)
        }


def walk_forward_backtest(
    prices_df: pd.DataFrame,
    signals_df: pd.DataFrame,
    train_window: int = 756,
    test_window: int = 252,
    capital: float = 100000
) -> dict:
    """
    Run walk-forward backtest to avoid look-ahead bias.
    
    Args:
        prices_df: Full prices DataFrame
        signals_df: Full signals DataFrame
        train_window: Training window size (days)
        test_window: Testing window size (days)
        capital: Initial capital
    
    Returns:
        Walk-forward backtest results
    """
    if prices_df.empty:
        return {}
    
    prices_df = prices_df.sort_values("date")
    signals_df = signals_df.sort_values("date")
    
    results = []
    
    total_days = len(prices_df)
    periods = []
    
    # Generate walk-forward periods
    start_idx = 0
    while start_idx + train_window + test_window <= total_days:
        train_start = start_idx
        train_end = start_idx + train_window
        test_start = train_end
        test_end = test_start + test_window
        
        periods.append({
            "train": (train_start, train_end),
            "test": (test_start, test_end)
        })
        
        start_idx += test_window  # Roll forward by test window
    
    # Run backtest for each period
    all_trades = []
    for period_idx, period in enumerate(periods):
        test_start, test_end = period["test"]
        
        test_prices = prices_df.iloc[test_start:test_end].copy()
        test_signals = signals_df.iloc[test_start:test_end].copy()
        
        if not test_prices.empty:
            bt = SimpleBacktester(test_prices, test_signals, capital=capital)
            result = bt.run()
            
            if result and "trades" in result:
                period_result = {
                    "period": period_idx,
                    "start_date": test_prices["date"].iloc[0],
                    "end_date": test_prices["date"].iloc[-1],
                    "metrics": result.get("metrics", {})
                }
                results.append(period_result)
                all_trades.extend(result["trades"])
    
    return {
        "periods": results,
        "summary_metrics": _summarize_wf_results(results)
    }


def _summarize_wf_results(period_results: list) -> dict:
    """Summarize walk-forward results"""
    if not period_results:
        return {}
    
    metrics = [p["metrics"] for p in period_results]
    
    return {
        "avg_return_pct": float(np.mean([m.get("total_return_pct", 0) for m in metrics])),
        "avg_drawdown_pct": float(np.mean([m.get("max_drawdown_pct", 0) for m in metrics])),
        "avg_win_rate": float(np.mean([m.get("win_rate", 0) for m in metrics])),
        "avg_sharpe": float(np.mean([m.get("sharpe_ratio", 0) for m in metrics])),
        "num_periods": len(period_results)
    }
